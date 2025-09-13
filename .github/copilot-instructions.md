# ChargeGhar PowerBank Network - AI Coding Guide

## Project Overview
ChargeGhar is a **shared powerbank charging station network** for Nepal. Users rent powerbanks via QR codes at physical kiosks and return them at any station. This is a Django REST API powering the mobile app backend.

**Key Business Logic**: Station-to-station rental system with real-time IoT communication, multi-payment gateways (Khalti, eSewa), and gamified user engagement.

## Architecture & Module Organization

### Core Django Apps Structure
```
api/
├── users/          # Authentication, profiles, KYC
├── stations/       # Physical stations and slot management
├── rentals/        # Rental lifecycle and powerbank tracking
├── payments/       # Wallet, payments, multi-gateway integration
├── notifications/  # FCM push notifications and in-app alerts
├── points/         # Gamification and rewards system
├── admin_panel/    # Custom admin interface
├── common/         # Shared utilities, base classes, services
└── config/         # Split Django settings architecture
```

### Settings Architecture Pattern
Uses `django-split-settings` - **never edit `settings.py` directly**:
- `config/base.py` - Core Django settings
- `config/database.py` - Database configuration
- `config/rest.py` - DRF settings
- `config/celery.py` - Background tasks
- See `api/config/settings.py` for full include list

### Service Layer Pattern
**Critical**: This project uses a service layer architecture. Business logic lives in `services.py`, NOT views:
```python
# api/users/services.py
class AuthService(BaseService):
    def register_user(self, data):
        # Complex business logic here
        
# api/users/views.py  
class RegisterView(GenericAPIView):
    def post(self, request):
        service = AuthService()
        return service.register_user(request.data)
```

All services inherit from `api.common.services.base.BaseService` which provides logging, transaction management, and error handling.

## Development Workflows

### Essential Commands (use Makefile)
```bash
# Development server (auto-restart on crashes)
make run.server.local

# Background tasks (required for notifications, payments)
make run.celery.local

# Database operations
make makemigrations
make migrate

# Code quality
make format          # ruff formatting
make lint           # ruff + mypy checks
make test           # pytest

# Docker development
docker compose up -d
make logs           # View all service logs
make logs.errors    # Filter for errors only
```

### Package Management
Uses **uv** package manager (not pip):
```bash
uv sync --all-extras --dev  # Install dependencies
uv add package-name         # Add new dependency
uv run manage.py <command>  # Run Django commands
```

## Key Patterns & Conventions

### Model Patterns
- All models inherit from `BaseModel` (UUID primary keys, timestamps)
- Use explicit `db_table` names and `related_name` for foreign keys
- Status fields use `CHOICES` tuples with uppercase values
- JSON fields for flexible data (`hardware_info`, `metadata`)

### API Patterns
- Views use `GenericAPIView` (not ViewSets) for fine-grained control
- Custom router: `api.common.routers.CustomViewRouter`
- DRF Spectacular for API docs - use `@extend_schema` decorators
- JWT authentication via `djangorestframework_simplejwt`

### Authentication & OTP Patterns
**Critical**: OTP requests are ONLY for new user registration and password reset:
```python
# OTP purposes: 'REGISTER' (user must not exist) | 'RESET_PASSWORD' (user must exist)
# LOGIN purpose is NOT supported - users login with password only
```
- `REGISTER`: Validates user doesn't exist, sends OTP for new registration
- `RESET_PASSWORD`: Validates user exists, sends OTP for password reset
- Service layer validates user existence before sending OTP

### Notification System Patterns
**Template-based notifications** with multi-channel delivery:
```python
# Use NotificationService for creating notifications
from api.notifications.services import NotificationService, FCMService, SMSService

# Create notification with template
service = NotificationService()
service.create_notification(
    user=user,
    title="Rental Started",
    message="Your powerbank rental has started",
    notification_type='rental',
    channel='in_app',
    template_slug='rental_started'
)

# Send push notification
fcm_service = FCMService()
fcm_service.send_push_notification(user, title, message, data)

# Send SMS (Nepal-specific formatting)
sms_service = SMSService()
sms_service.send_sms(phone_number, message, user)
```
- **Templates**: Use `NotificationTemplate` for consistent messaging
- **Rules**: `NotificationRule` defines which channels to use per type
- **Channels**: `in_app`, `push`, `sms`, `email`
- **Background Tasks**: All notifications sent via Celery tasks

### Error Handling
```python
from api.common.services.base import ServiceException

# In services
raise ServiceException("User already exists", status_code=status.HTTP_409_CONFLICT)

# Views automatically handle ServiceException
```

### Background Tasks
Uses Celery with RabbitMQ. Task files: `api/*/tasks.py`
```python
from tasks.app import app

@app.task
def send_notification(user_id, message):
    # Task implementation
```

## Critical Integration Points

### Payment Flow
- Multi-gateway: Khalti (Nepal), eSewa (Nepal), Stripe (International)
- Wallet system with transaction logging
- Rental deposits and automatic refunds

### Real-time Features
- FCM push notifications via `api/notifications/`
- WebSocket for live station status (check `api/stations/views.py`)
- Redis caching for frequently accessed data

## Database & Migrations

### Migration Strategy
- Always run `make makemigrations` before `make migrate`
- Use `--name` flag for descriptive migration names
- Check migration dependencies in multi-app changes

### Key Models Relationships
- `User` → `UserProfile`, `UserKYC`, `Wallet`
- `Station` → `StationSlot` → `PowerBank`
- `Rental` connects User, PowerBank, Station (pickup/return)
- Points system tracks user engagement

## Environment & Configuration

### Required Environment Variables
```bash
# Core (copy from .env.example)
POSTGRES_PASSWORD=your-secret-password
DJANGO_SECRET_KEY=your-secret-key
RABBITMQ_DEFAULT_PASS=your-secret-password

# Firebase Cloud Messaging (FCM)
FCM_SERVER_KEY=your_fcm_server_key_here
FIREBASE_CREDENTIALS_PATH=path/to/firebase-service-account.json
# Alternative: Base64 encoded service account JSON
FIREBASE_CREDENTIALS_BASE64=your_base64_encoded_service_account_json

# Sparrow SMS (Nepal SMS Provider)
SPARROW_SMS_TOKEN=your_sparrow_sms_token_here
SPARROW_SMS_FROM=ChargeGhar
SPARROW_SMS_BASE_URL=https://sms.sparrowsms.com/v2/

# Email Configuration
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here

# External Payment APIs
KHALTI_SECRET_KEY=    # Nepal payment gateway
ESEWA_SECRET_KEY=     # Nepal payment gateway
FCM_SERVER_KEY=       # Firebase notifications
```

### Docker vs Local Development
- **Local**: Faster iteration, use `make run.server.local`
- **Docker**: Production-like environment, use `docker compose up -d`
- Services: PostgreSQL, Redis, RabbitMQ, Celery workers

## Testing & Debugging

### Test Structure
```
tests/
├── unit/          # Model and service tests
├── integration/   # API endpoint tests
└── load/          # Performance tests
```

### Debugging Tools
- Django Silk: `/silk/` (performance profiling)
- Admin interface: `/admin/` (enhanced with django-admin-interface)
- API docs: `/api/schema/swagger-ui/`

## Common Gotchas

1. **Service Layer**: Business logic must be in services, not views
2. **Celery Required**: Many features depend on background tasks running
3. **uv not pip**: Use `uv` commands for package management
4. **Split Settings**: Never edit `settings.py` directly
5. **UUID Models**: All models use UUID primary keys, not integers
6. **Nepal Context**: Payment gateways, time zone (Asia/Kathmandu), local regulations

## Quick Reference
- **Main URLs**: `api/web/urls.py`
- **Base Service**: `api/common/services/base.py`
- **Custom Router**: `api/common/routers.py`
- **Documentation**: See `README.md`, `Features TOC.md`, `PowerBank_ER_Diagram.md`