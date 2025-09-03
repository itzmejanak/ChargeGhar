# 📁 Project Structure Guide

**Understanding the PowerBank Backend Architecture - Files, Folders, and Organization**

---

## 📋 Table of Contents

1. [🎯 Overview](#-overview)
2. [📂 Root Directory Structure](#-root-directory-structure)
3. [🏗️ Django Apps Organization](#️-django-apps-organization)
4. [⚙️ Configuration Files](#️-configuration-files)
5. [🔄 Background Tasks Structure](#-background-tasks-structure)
6. [🧪 Testing Organization](#-testing-organization)
7. [📚 Documentation Files](#-documentation-files)
8. [🚀 Deployment Files](#-deployment-files)
9. [💡 Benefits of This Structure](#-benefits-of-this-structure)
10. [🛠️ Development Workflow](#️-development-workflow)

---

## 🎯 Overview

This project follows a **feature-driven architecture** where each Django app represents a complete business domain. This approach ensures:

- **🔍 Easy Navigation**: Find any feature quickly
- **🧩 Modular Development**: Work on features independently
- **👥 Team Collaboration**: Multiple developers can work without conflicts
- **🔧 Maintainability**: Easy to update, debug, and extend
- **📈 Scalability**: Add new features without affecting existing ones

---

## 📂 Root Directory Structure

```
powerbank-backend/
├── 📁 api/                          # Main Django application
├── 📁 tasks/                        # Celery configuration and tasks
├── 📁 tests/                        # Test suites
├── 📁 logs/                         # Application logs (auto-created)
├── 📁 backups/                      # Database backups (auto-created)
├── 📄 manage.py                     # Django management script
├── 📄 pyproject.toml               # Python dependencies and tools
├── 📄 Makefile                     # Development commands
├── 📄 docker-compose.yaml          # Docker services configuration
├── 📄 Dockerfile                   # Container build instructions
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 README.md                    # Project overview and setup
├── 📄 Features TOC.md              # Complete API specification
├── 📄 PowerBank_ER_Diagram.md     # Database design
├── 📄 DEVELOPMENT_GUIDE.md         # Development workflow
├── 📄 ASYNC_WORKFLOW_GUIDE.md      # Background tasks guide
└── 📄 PROJECT_STRUCTURE.md         # This file
```

### 🎯 Why This Structure?

#### **Separation of Concerns**
- **`api/`**: Core business logic and API endpoints
- **`tasks/`**: Background processing and async operations
- **`tests/`**: Quality assurance and validation
- **Documentation**: Complete project knowledge base

#### **Development Efficiency**
- **`Makefile`**: One-command operations (`make migrate`, `make test`)
- **`pyproject.toml`**: Modern Python dependency management
- **`.env.example`**: Quick environment setup template

---

## 🏗️ Django Apps Organization

### Feature-Based App Structure
```
api/
├── 📁 common/                       # Shared utilities and base classes
├── 📁 app_core/                     # App Features (health, version, upload)
├── 📁 user/                         # User Features (auth, profile, KYC)
├── 📁 stations/                     # Station Features (CRUD, favorites, issues)
├── 📁 rentals/                      # Rental Features (lifecycle, payments)
├── 📁 payments/                     # Payment Features (gateways, wallet)
├── 📁 notifications/                # Notification Features (FCM, in-app)
├── 📁 points/                       # Points & Referral Features
├── 📁 social/                       # Social Features (leaderboard, achievements)
├── 📁 promotions/                   # Promotion Features (coupons)
├── 📁 content/                      # Content Management (CMS, FAQ)
├── 📁 admin_panel/                  # Admin Features (analytics, management)
├── 📁 config/                       # Django settings and configuration
└── 📁 web/                          # WSGI/ASGI configuration
```

### 🎯 One App = One Feature Domain

Each app follows this standardized structure:

```
api/user/                            # Example: User Features App
├── 📄 __init__.py                   # Python package marker
├── 📄 apps.py                       # Django app configuration
├── 📄 models.py                     # Database models (User, UserProfile, UserKYC)
├── 📄 serializers.py                # DRF serializers for API responses
├── 📄 views.py                      # API endpoints and business logic
├── 📄 urls.py                       # URL routing for this app
├── 📄 admin.py                      # Django admin interface
├── 📄 permissions.py                # Custom permissions and access control
├── 📄 utils.py                      # Helper functions and utilities
├── 📄 tasks.py                      # Celery background tasks
├── 📁 migrations/                   # Database migration files
│   ├── 📄 0001_initial.py
│   └── 📄 __init__.py
└── 📁 tests/                        # App-specific tests
    ├── 📄 test_models.py
    ├── 📄 test_views.py
    ├── 📄 test_serializers.py
    └── 📄 test_tasks.py
```

### 🔗 How Apps Connect

#### **URL Routing Flow**
```
1. api/web/urls.py (Main URL config)
   ↓
2. api/user/urls.py (App-specific URLs)
   ↓
3. api/user/views.py (Business logic)
   ↓
4. api/user/serializers.py (Data formatting)
   ↓
5. api/user/models.py (Database operations)
```

#### **Database Relationships**
```python
# Cross-app model relationships
api/user/models.py:
    User → api/rentals/models.py: Rental (OneToMany)
    User → api/payments/models.py: Wallet (OneToOne)
    User → api/points/models.py: UserPoints (OneToOne)

api/stations/models.py:
    Station → api/rentals/models.py: Rental (OneToMany)
    Station → api/notifications/models.py: StationAlert (OneToMany)
```

---

## ⚙️ Configuration Files

### Django Configuration Structure
```
api/config/
├── 📄 __init__.py                   # Package marker
├── 📄 settings.py                   # Main settings loader
├── 📄 base.py                       # Base paths and core settings
├── 📄 application.py                # Django apps and middleware
├── 📄 auth.py                       # Authentication and JWT settings
├── 📄 database.py                   # PostgreSQL configuration
├── 📄 cache.py                      # Redis caching setup
├── 📄 celery.py                     # Background task configuration
├── 📄 rest.py                       # Django REST Framework settings
├── 📄 security.py                   # CORS, CSRF, security headers
├── 📄 spectacular.py                # API documentation settings
├── 📄 sentry.py                     # Error monitoring configuration
├── 📄 silk.py                       # Performance profiling setup
├── 📄 storage.py                    # File storage (S3, Cloudinary)
├── 📄 logging.py                    # Logging configuration
└── 📁 __app_template__/             # Template for new Django apps
    ├── 📄 __init__.py
    ├── 📄 apps.py
    ├── 📄 models.py
    ├── 📄 serializers.py
    ├── 📄 views.py
    ├── 📄 urls.py
    ├── 📄 permissions.py
    ├── 📄 utils.py
    ├── 📄 tasks.py
    └── 📁 tests/
```

### 🎯 Why Modular Configuration?

#### **Benefits**
- **🔍 Easy to Find**: Each configuration type has its own file
- **🔧 Easy to Modify**: Change only what you need
- **👥 Team Friendly**: Multiple developers can work on different configs
- **🚀 Environment Specific**: Easy to override for production/staging

#### **Usage Example**
```python
# api/config/settings.py
from split_settings.tools import include

include(
    "base.py",           # Core Django settings
    "application.py",    # Apps and middleware
    "database.py",       # Database configuration
    "auth.py",          # Authentication setup
    "rest.py",          # DRF configuration
    "celery.py",        # Background tasks
    # ... other config files
)
```

---

## 🔄 Background Tasks Structure

### Celery Organization
```
tasks/
├── 📄 __init__.py                   # Package marker
├── 📄 app.py                        # Main Celery application
├── 📄 auth.py                       # Authentication-related tasks
├── 📄 payments.py                   # Payment processing tasks
├── 📄 notifications.py              # Notification delivery tasks
├── 📄 rentals.py                    # Rental processing tasks
├── 📄 stations.py                   # Station management tasks
├── 📄 points.py                     # Points and rewards tasks
├── 📄 analytics.py                  # Data processing tasks
└── 📄 utils.py                      # Shared task utilities
```

### 🎯 Task Organization Benefits

#### **Feature Alignment**
- Each task file corresponds to a Django app
- Easy to find tasks related to specific features
- Clear separation of concerns

#### **Example Task Structure**
```python
# tasks/auth.py
@celery_app.task(queue='critical')
def send_otp_task(phone_number, otp_code):
    """Send OTP via SMS - Critical priority"""
    pass

@celery_app.task(queue='default')
def post_registration_tasks(user_id):
    """Setup user profile after registration"""
    pass

# tasks/payments.py
@celery_app.task(queue='payments')
def process_payment_webhook(webhook_data):
    """Process payment gateway webhooks"""
    pass
```

---

## 🧪 Testing Organization

### Test Structure
```
tests/
├── 📁 unit/                         # Unit tests for individual components
│   ├── 📁 test_user/
│   │   ├── 📄 test_models.py        # User model tests
│   │   ├── 📄 test_views.py         # User API endpoint tests
│   │   ├── 📄 test_serializers.py   # User serializer tests
│   │   └── 📄 test_tasks.py         # User background task tests
│   ├── 📁 test_stations/
│   ├── 📁 test_rentals/
│   └── 📁 test_payments/
├── 📁 integration/                  # Integration tests
│   ├── 📄 test_rental_flow.py       # Complete rental process
│   ├── 📄 test_payment_flow.py      # Payment processing
│   └── 📄 test_notification_flow.py # Notification delivery
├── 📁 load/                         # Performance and load tests
│   ├── 📄 test_api_performance.py
│   └── 📄 test_database_load.py
├── 📁 fixtures/                     # Test data
│   ├── 📄 users.json
│   ├── 📄 stations.json
│   └── 📄 packages.json
└── 📄 conftest.py                   # Pytest configuration and fixtures
```

### 🎯 Testing Benefits

#### **Comprehensive Coverage**
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test complete workflows
- **Load Tests**: Ensure performance under stress

#### **Easy Test Discovery**
```bash
# Run all tests
make test

# Run specific app tests
pytest tests/unit/test_user/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=api tests/
```

---

## 📚 Documentation Files

### Documentation Structure
```
📄 README.md                        # Project overview and quick start
📄 Features TOC.md                  # Complete API specification
📄 PowerBank_ER_Diagram.md         # Database design and relationships
📄 DEVELOPMENT_GUIDE.md             # Development workflow and best practices
📄 ASYNC_WORKFLOW_GUIDE.md          # Background tasks and deployment
📄 PROJECT_STRUCTURE.md             # This file - project organization
```

### 🎯 Documentation Purpose

#### **For Different Audiences**
- **README.md**: New developers and quick setup
- **Features TOC.md**: Product managers and API consumers
- **PowerBank_ER_Diagram.md**: Database designers and backend developers
- **DEVELOPMENT_GUIDE.md**: Development team and contributors
- **ASYNC_WORKFLOW_GUIDE.md**: DevOps engineers and system architects

#### **Knowledge Management**
- **Complete Coverage**: Every aspect of the project documented
- **Easy Updates**: Markdown format for version control
- **Searchable**: Easy to find specific information
- **Visual**: Diagrams and examples for better understanding

---

## 🚀 Deployment Files

### Deployment Configuration
```
📄 Dockerfile                       # Container build instructions
📄 docker-compose.yaml              # Multi-service orchestration
📄 .env.example                     # Environment variables template
📄 Makefile                         # Development and deployment commands
📄 pyproject.toml                   # Dependencies and tool configuration
```

### 🎯 Deployment Benefits

#### **Container Ready**
```dockerfile
# Dockerfile - Multi-stage build for optimization
FROM python:3.12-slim as builder
# ... build dependencies

FROM python:3.12-slim as runtime
# ... runtime setup
```

#### **Service Orchestration**
```yaml
# docker-compose.yaml - Complete stack
services:
  api:          # Django application
  db:           # PostgreSQL database
  redis:        # Cache and session storage
  rabbitmq:     # Message broker
  celery:       # Background workers
```

#### **Development Commands**
```makefile
# Makefile - One-command operations
migrate:
	uv run manage.py migrate

test:
	uv run pytest

format:
	uv run ruff format .
```

---

## 💡 Benefits of This Structure

### 🎯 For Developers

#### **Easy Navigation**
```bash
# Need to work on user authentication?
cd api/user/

# Need to add a payment method?
cd api/payments/

# Need to check background tasks?
cd tasks/
```

#### **Clear Responsibilities**
- Each file has a single, clear purpose
- No confusion about where to add new code
- Easy to find existing functionality

#### **Consistent Patterns**
- Every app follows the same structure
- Predictable file locations
- Standardized naming conventions

### 🎯 For Teams

#### **Parallel Development**
- Multiple developers can work on different apps simultaneously
- Minimal merge conflicts
- Clear ownership of features

#### **Code Reviews**
- Easy to review changes within a specific domain
- Clear impact assessment
- Focused discussions

#### **Knowledge Sharing**
- New team members can quickly understand the structure
- Documentation is always up-to-date
- Examples and patterns are consistent

### 🎯 For Maintenance

#### **Bug Fixing**
```bash
# Bug in rental calculation?
# Check: api/rentals/utils.py

# Payment webhook failing?
# Check: tasks/payments.py

# Database query slow?
# Check: api/*/models.py
```

#### **Feature Addition**
```bash
# New feature: Loyalty Program
# 1. Create: api/loyalty/
# 2. Add tasks: tasks/loyalty.py
# 3. Add tests: tests/unit/test_loyalty/
# 4. Update docs: Features TOC.md
```

#### **Performance Optimization**
- Easy to identify bottlenecks by app
- Clear separation of concerns
- Targeted improvements possible

---

## 🛠️ Development Workflow

### 🚀 Starting a New Feature

#### Step 1: Create Django App
```bash
# Creates app with standard structure
python manage.py startapp loyalty

# Result: api/loyalty/ with all standard files
```

#### Step 2: Define Models
```python
# api/loyalty/models.py
class LoyaltyProgram(BaseModel):
    name = models.CharField(max_length=100)
    # ... other fields
```

#### Step 3: Create API Endpoints
```python
# api/loyalty/views.py
class LoyaltyViewSet(viewsets.ModelViewSet):
    # ... API logic
```

#### Step 4: Add Background Tasks
```python
# tasks/loyalty.py
@celery_app.task
def process_loyalty_rewards(user_id):
    # ... background processing
```

#### Step 5: Write Tests
```python
# tests/unit/test_loyalty/test_models.py
def test_loyalty_program_creation():
    # ... test logic
```

#### Step 6: Update Documentation
```markdown
# Features TOC.md
## Loyalty Features
| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Get Programs | `/api/loyalty/programs` | GET | List loyalty programs |
```

### 🔄 Daily Development

#### **Working on User Features**
```bash
# Navigate to user app
cd api/user/

# Edit models
vim models.py

# Create migrations
make makemigrations

# Run tests
pytest tests/unit/test_user/

# Start development server
make run.server.local
```

#### **Working on Background Tasks**
```bash
# Navigate to tasks
cd tasks/

# Edit payment tasks
vim payments.py

# Test tasks
pytest tests/unit/test_tasks/

# Start celery worker
make run.celery.local
```

### 🧪 Testing Workflow

#### **Test Specific Feature**
```bash
# Test user authentication
pytest tests/unit/test_user/test_views.py::TestAuthViewSet

# Test payment processing
pytest tests/integration/test_payment_flow.py

# Test with coverage
pytest --cov=api/user tests/unit/test_user/
```

#### **Test Everything**
```bash
# Run all tests
make test

# Run with coverage report
pytest --cov=api --cov-report=html tests/
```

### 📊 Monitoring and Debugging

#### **Check Logs**
```bash
# Application logs
tail -f logs/django.log

# Celery logs
tail -f logs/celery.log

# Docker logs
make logs
```

#### **Database Operations**
```bash
# Create backup
make db.dump.all

# Run migrations
make migrate

# Access database shell
uv run manage.py dbshell
```

---

## 🎯 Summary

This project structure provides:

### ✅ **Clean Organization**
- Feature-based apps for logical separation
- Consistent file structure across all apps
- Clear naming conventions and patterns

### ✅ **Easy Development**
- Predictable file locations
- Standardized development workflow
- Comprehensive documentation

### ✅ **Team Collaboration**
- Parallel development capabilities
- Clear ownership and responsibilities
- Minimal merge conflicts

### ✅ **Maintainability**
- Easy to find and fix bugs
- Simple to add new features
- Clear upgrade paths

### ✅ **Scalability**
- Modular architecture
- Independent feature development
- Easy to split into microservices if needed

This structure ensures that whether you're a new developer joining the team or an experienced developer working on complex features, you can quickly understand, navigate, and contribute to the PowerBank charging station backend.

**Happy coding! 🚀**