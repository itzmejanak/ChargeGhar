# 🔋 PowerBank Charging Station Backend - Byterover Handbook

## Layer 1: System Overview

### Purpose
A comprehensive Django REST API for Nepal's shared charging station network that enables users to rent power banks via mobile app by scanning QR codes at physical kiosks. The system allows flexible return of power banks to any station in the network.

### Architecture Pattern
**Docker-First Containerized Architecture with Django MTV Pattern**
- **Model-View-Template (MTV)** through Django's framework
- **RESTful API Design** for mobile app integration
- **Microservice-ready** containerized architecture
- **Full Docker Stack** for development and production consistency

### Technology Stack
- **Backend Framework**: Django 5.2 with Django REST Framework
- **Database**: PostgreSQL (Docker container) with PgBouncer connection pooling
- **Message Queue**: RabbitMQ (Docker container) for async communication
- **Caching**: Redis (Docker container) for session and data caching
- **Background Tasks**: Celery (Docker container) for asynchronous job processing
- **Authentication**: JWT token-based with django-axes protection
- **Documentation**: DRF Spectacular (OpenAPI/Swagger)
- **Monitoring**: Django Silk for performance profiling
- **Error Tracking**: Sentry integration
- **Package Management**: uv for modern Python dependency management
- **Containerization**: Docker & Docker Compose for all services

### Key Technical Decisions
- **Docker-First Approach**: All services run in containers for consistency
- **Modular Configuration**: Split Django settings across multiple files for maintainability
- **Feature-based App Organization**: Each Django app represents a business domain
- **Environment-based Configuration**: Extensive use of environment variables
- **Container-ready**: Full Docker Compose setup for development and production
- **Security-first**: Built-in brute force protection and secure defaults

## Layer 2: Module Map

### Core Modules

#### **api/config/** - Configuration Hub
- **Purpose**: Centralized Django settings management
- **Key Files**: 
  - `settings.py` - Main settings loader using split-settings
  - `database.py` - PostgreSQL configuration with environment support
  - `auth.py` - JWT authentication and user model settings
  - `security.py` - CORS, CSRF, and security headers
  - `rest.py` - Django REST Framework configuration
  - `celery.py` - Background task configuration
- **Responsibilities**: Environment-specific configurations, security settings, third-party integrations

#### **api/user/** - User Management
- **Purpose**: Complete user lifecycle management
- **Components**: Authentication, profile management, KYC verification
- **Key Features**: Custom user model, JWT authentication, permissions system
- **Database Models**: User, UserProfile, KYC data

#### **api/common/** - Shared Utilities
- **Purpose**: Reusable components across all apps
- **Key Files**: `routers.py` - Common routing utilities
- **Responsibilities**: Base classes, shared utilities, common middleware

#### **api/web/** - Web Configuration
- **Purpose**: WSGI/ASGI application configuration
- **Key Files**: 
  - `wsgi.py` - Production WSGI application
  - `asgi.py` - Async ASGI application for WebSocket support
  - `urls.py` - Main URL routing configuration

#### **tasks/** - Background Job Processing
- **Purpose**: Celery task definitions and async processing
- **Key Files**: `app.py` - Celery application configuration
- **Responsibilities**: Async notifications, data processing, scheduled tasks

### Data Layer
- **PostgreSQL** (Docker container) as primary database with full ACID compliance
- **Redis** (Docker container) for caching and session storage
- **Connection Pooling** via PgBouncer (Docker container) for production scalability
- **Migration System** with Django's built-in migration framework

### Message Queue Layer
- **RabbitMQ** (Docker container) with management interface
- **Management UI**: Available at http://localhost:15672
- **Credentials**: powerbank/chargeghar5060
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Integration**: Celery workers connect via Docker network

### Utilities & Tools
- **Development Tools**: Ruff (formatting/linting), pytest (testing), mypy (type checking)
- **Build Tools**: Makefile for common operations, Docker Compose for containerization
- **Monitoring**: Django Silk profiling, structured logging

## Layer 3: Integration Guide

### API Structure
- **Base URL**: `/api/` (configured in `api/web/urls.py`)
- **Authentication**: JWT tokens via `rest_framework_simplejwt`
- **Documentation**: Auto-generated OpenAPI specs at `/api/schema/swagger-ui/`
- **Admin Interface**: Django admin at `/admin/`

### Database Configuration (Docker)
```python
# Environment Variables for Docker PostgreSQL
POSTGRES_HOST=db  # Docker service name
POSTGRES_USER=powerbank_user
POSTGRES_PASSWORD=chargeghar5060
POSTGRES_DB=powerbank_db
DATABASE_URL=postgres://powerbank_user:chargeghar5060@db:5432/powerbank_db
```

### RabbitMQ Configuration (Docker)
```python
# Environment Variables for Docker RabbitMQ
RABBITMQ_DEFAULT_USER=powerbank
RABBITMQ_DEFAULT_PASS=chargeghar5060
RABBITMQ_HOST=rabbitmq  # Docker service name
RABBITMQ_PORT=5672
RABBITMQ_DASHBOARD_PORT=15672
CELERY_BROKER_URL=amqp://powerbank:chargeghar5060@rabbitmq:5672/
```

### Database Configuration
```python
# Environment Variables for PostgreSQL
DATABASE_URL=postgres://user:pass@host:port/db
CONN_MAX_AGE=600  # Connection pooling timeout

# Docker Compose PostgreSQL
POSTGRES_USER=powerbank_user
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=powerbank_db
```

### External Service Integration Points
- **FCM Push Notifications**: Firebase Cloud Messaging for mobile notifications
- **Payment Gateways**: Khalti, eSewa, Stripe integration endpoints
- **IoT Communication**: MQTT protocol for hardware station control
- **File Storage**: AWS S3 and Cloudinary for media uploads
- **Error Monitoring**: Sentry DSN configuration for production monitoring

### Docker Environment Setup
```bash
# Complete Docker Stack Startup
docker compose up -d

# Services Started:
# - PostgreSQL (db): Internal database service
# - RabbitMQ (rabbitmq): Message broker with management UI
# - Redis (redis): Cache and session storage
# - PgBouncer (pgbouncer): Connection pooling
# - Django API (api): Main application server
# - Celery (celery): Background task workers
```

### Development Environment Setup
```bash
# Docker-First Development Workflow
docker compose up -d          # Start all services
docker logs <service-name>    # Check service logs
docker exec <container> bash  # Access container shell
docker compose down          # Stop all services
docker compose restart <service>  # Restart specific service
```

### Service Access Points
- **Django API**: http://localhost:8010
- **RabbitMQ Management**: http://localhost:15672 (powerbank/chargeghar5060)
- **PostgreSQL**: localhost:5432 (via Docker network)
- **Redis**: localhost:6379 (via Docker network)

### Docker Integration
- **Development**: `docker compose up -d` starts all services
- **Services**: PostgreSQL (5432), Redis (6379), RabbitMQ (15672), API (8010)
- **Volumes**: Persistent data storage for database, cache, and message queue

## Layer 4: Extension Points

### Design Patterns Used

#### **Configuration Pattern**
- **Split Settings**: Modular configuration files in `api/config/`
- **Environment Variables**: Extensive use of `getenv()` for flexible deployment
- **Default Fallbacks**: Safe defaults for development with warnings

#### **App Template Pattern**
- **Standardized Structure**: Each Django app follows identical file organization
- **Template Directory**: `api/config/__app_template__/` for new app generation
- **Feature Isolation**: One app per business domain (user, stations, rentals, etc.)

#### **Middleware Pattern**
- **Security Middleware**: CORS, CSRF, authentication in defined order
- **Performance Middleware**: Django Silk for request profiling
- **Security Enhancement**: django-axes for brute force protection

### Customization Areas

#### **Adding New Apps**
```bash
# Using built-in template
python manage.py startapp new_feature
# Automatically uses template from api/config/__app_template__/
```

#### **Database Extensions**
- **Custom Fields**: Add to `api/config/database.py`
- **Connection Pooling**: Modify PgBouncer settings in `docker-compose.yaml`
- **Migration Customization**: Override in individual app migrations

#### **Authentication Extensions**
- **Custom User Fields**: Extend `api/user/models.py`
- **Permission Systems**: Add to `api/user/permissions.py`
- **JWT Customization**: Modify `api/config/auth.py`

### Plugin Architecture Points
- **DRF Extensions**: Custom serializers, viewsets, and permissions
- **Celery Task Extensions**: Add new background tasks in app-specific `tasks.py`
- **Middleware Extensions**: Custom middleware in any app for request/response processing
- **Storage Backends**: Configurable file storage (local, S3, Cloudinary)

### Environment-Specific Overrides
- **Local Development**: Uses SQLite by default, switches to PostgreSQL via `DATABASE_URL`
- **Production Deployment**: Full containerized stack with connection pooling
- **Testing Environment**: Isolated test database with pytest configuration
- **CI/CD Integration**: GitHub Actions ready with test and lint workflows

### Future Extension Capabilities
- **Microservice Migration**: Services already containerized for easy extraction
- **API Versioning**: DRF structure supports versioned APIs
- **Multi-tenancy**: Database and authentication structure supports tenant separation
- **Horizontal Scaling**: Docker Compose and Kubernetes ready for distributed processing
- **Service Mesh**: Ready for advanced container orchestration patterns

## Layer 5: Docker Infrastructure Status

### **🎯 DEVELOPMENT READY - ALL SERVICES VERIFIED**

#### Container Status (Verified Working)
```
powerbank_local-db-1         Up 10 minutes   5432/tcp
powerbank_local-rabbitmq-1   Up 10 minutes   0.0.0.0:15672->15672/tcp
powerbank_local-redis-1      Up 10 minutes   6379/tcp
powerbank_local-pgbouncer-1  Up 10 minutes   5432/tcp
powerbank_local-api-1        Up 7 minutes    0.0.0.0:8010->80/tcp
powerbank_local-celery-1     Up 10 minutes
```

#### Service Integration Verification ✅
- **Django ↔ PostgreSQL**: Database connections established
- **Django ↔ Redis**: Cache working properly (verified)
- **Celery ↔ RabbitMQ**: Workers connected to message broker
- **Celery ↔ Redis**: Result backend operational
- **Task Discovery**: Custom test tasks loading successfully

#### Infrastructure Capabilities
- **Development Command**: `docker compose up -d` starts complete stack
- **API Development**: http://localhost:8010 ready for REST API development
- **Background Tasks**: Celery workers ready for async task development
- **Message Queue**: RabbitMQ management UI at http://localhost:15672
- **Database**: PostgreSQL ready for model creation and migrations
- **Cache**: Redis integrated with Django for session/data caching

#### Credentials & Access
- **PostgreSQL**: powerbank_user/chargeghar5060@db:5432/powerbank_db
- **RabbitMQ**: powerbank/chargeghar5060@rabbitmq:5672 (+ Management UI)
- **Django Admin**: janak/5060
- **Redis**: redis:6379 (responding to ping)

#### Development Workflow
```bash
# Start complete PowerBank infrastructure
docker compose up -d

# Check service status
docker ps

# View service logs
docker logs powerbank_local-<service>-1

# Execute commands in containers
docker exec powerbank_local-api-1 uv run python manage.py migrate
docker exec powerbank_local-api-1 uv run python manage.py createsuperuser

# Test services
# - API: http://localhost:8010
# - RabbitMQ: http://localhost:15672
# - Redis: docker exec powerbank_local-redis-1 redis-cli ping
```

**Status**: Infrastructure verified and ready for PowerBank feature development! 🚀