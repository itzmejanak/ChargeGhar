# 🔋 PowerBank Charging Station Backend

**A comprehensive Django REST API for Nepal's shared charging station network**

---

## 📋 Table of Contents

- [🎯 Project Overview](#-project-overview)
- [📚 Documentation](#-documentation)
- [🚀 Quick Start](#-quick-start)
- [🛠️ Development Setup](#️-development-setup)
- [🐳 Docker Setup](#-docker-setup)
- [⚙️ Configuration](#️-configuration)
- [🔧 Advanced Features](#-advanced-features)
- [📖 Additional Resources](#-additional-resources)

---

## 🎯 Project Overview

We're building a **smart charging station network** for Nepal that allows users to rent power banks via mobile app by scanning QR codes at physical kiosks. Users can return power banks to any station in the network, making it convenient and flexible.

### Key Features
- 📱 **Mobile App Integration**: QR code scanning, real-time station status
- 💳 **Multi-Payment Support**: Khalti, eSewa, Stripe integration
- 🎯 **Points & Rewards**: Gamification with referral system
- 📊 **Admin Dashboard**: Comprehensive management interface
- 🔔 **Real-time Notifications**: FCM push notifications and in-app alerts
- 🏆 **Social Features**: Leaderboards and achievements
- 🌐 **IoT Integration**: MQTT communication with hardware stations

---

## 📚 Documentation

### Core Documentation
- **[📋 Features TOC](Features%20TOC.md)** - Complete API specification with all endpoints and features
- **[🗄️ Database Schema](PowerBank_ER_Diagram.md)** - Entity Relationship Diagram and database design
- **[👨‍💻 Development Guide](DEVELOPMENT_GUIDE.md)** - Comprehensive development workflow and best practices
- **[🔄 Async Workflow Guide](ASYNC_WORKFLOW_GUIDE.md)** - Celery, Redis, and RabbitMQ integration guide

### Quick Reference
- **High Priority Features**: User management, Station network, Rental system, Payment integration, Notifications, Admin dashboard
- **Low Priority Features**: Social features, Promotions, Content management
- **Tech Stack**: Django 5.2, DRF, PostgreSQL, Redis, RabbitMQ, Celery, JWT Authentication

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.12+**
- **uv** package manager - [Installation Guide](https://github.com/astral-sh/uv#installation)
- **Docker & Docker Compose** (optional, for containerized setup)

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/itzmejanak/ChargeGhar.git
cd powerbank-backend

# Install dependencies
uv sync --all-extras --dev

# Setup environment
cp .env.example .env

# Run migrations
make migrate

# Start the server
make run.server.local
```

🎉 **Your API is now running at http://localhost:8000**

---

## 🛠️ Development Setup

### Local Development (Recommended for Development)

#### Step 1: Clone and Install
```bash
# Clone the repository
cd powerbank-backend

# Install dependencies with uv
uv sync --all-extras --dev
```

#### Step 2: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional for basic setup)
# Key variables to update for production:
# - POSTGRES_PASSWORD
# - DJANGO_SECRET_KEY  
# - RABBITMQ_DEFAULT_PASS
```

#### Step 3: Database Setup
```bash
# Run database migrations
make migrate

# Create superuser (optional)
make createsuperuser
```

#### Step 4: Start Development Services
```bash
# Terminal 1: Start Django server
make run.server.local

# Terminal 2: Start Celery worker (for background tasks)
make run.celery.local
```

### Development URLs
- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

---

## 🐳 Docker Setup

### Quick Docker Start
```bash
# Clone repository
git clone <repository-url>
cd powerbank-backend

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d
```

### Docker Services
- **API**: http://localhost:8010
- **RabbitMQ Dashboard**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Docker Commands
```bash
# View logs
make logs

# View only errors
make logs.errors

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

---

## ⚙️ Configuration

### Environment Variables

#### 🔒 Security (Change for Production)
```bash
POSTGRES_PASSWORD=your-super-secret-postgres-password
DJANGO_SECRET_KEY=your-super-secret-django-key
RABBITMQ_DEFAULT_PASS=your-super-secret-rabbitmq-password
```

#### 🌐 Application Settings
```bash
HOST=localhost
ENVIRONMENT=local
DJANGO_DEBUG=true
TIME_ZONE=Asia/Kathmandu
LANGUAGE_CODE=en-us
```

#### 🔗 Service URLs
```bash
DATABASE_URL=postgres://user:pass@host:port/db
REDIS_URL=redis://host:port/0
RABBITMQ_URL=amqp://user:pass@host:port/
```

#### 📊 External Services
```bash
# Sentry (Error Tracking)
USE_SENTRY=false
SENTRY_DSN=your-sentry-dsn

# AWS S3 (File Storage)
USE_S3_FOR_MEDIA=false
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_ACCESS_KEY_ID=your-access-key

# Cloudinary (Media Upload)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
```

---

## 🔧 Advanced Features

### Built-in Integrations
- **🔐 JWT Authentication**: Secure token-based authentication
- **📊 OpenAPI Documentation**: Auto-generated API docs with DRF Spectacular
- **🔄 Background Tasks**: Celery with RabbitMQ and Redis
- **📈 Performance Monitoring**: Django Silk profiling
- **🛡️ Security**: Django Axes for brute force protection
- **🌐 CORS Support**: Cross-origin resource sharing
- **☁️ Cloud Storage**: AWS S3 and Cloudinary integration
- **📱 Push Notifications**: Firebase Cloud Messaging (FCM)
- **💳 Payment Gateways**: Khalti, eSewa, Stripe integration
- **🏗️ IoT Communication**: MQTT for hardware station control

### Development Tools
```bash
# Code formatting and linting
make format          # Format code with ruff
make lint           # Check code quality
make test           # Run test suite

# Database operations
make makemigrations # Create migrations
make migrate        # Apply migrations
make db.dump.all    # Backup database
```

---

## 📖 Additional Resources

### For Developers
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Complete development workflow
- **[Async Workflow Guide](ASYNC_WORKFLOW_GUIDE.md)** - Background task processing
- **[Database Schema](PowerBank_ER_Diagram.md)** - Complete ER diagram

### For Product Managers
- **[Features TOC](Features%20TOC.md)** - All API endpoints and features
- **API Documentation**: Available at `/api/schema/swagger-ui/` when server is running

### For DevOps Engineers
- **[Async Workflow Guide](ASYNC_WORKFLOW_GUIDE.md)** - Production deployment guide
- **Docker Compose**: Multi-service container orchestration
- **Monitoring**: Sentry integration for error tracking

### Architecture Overview
```
Mobile App ←→ Django REST API ←→ PostgreSQL
     ↓              ↓                ↓
   FCM Push    Celery Workers    Redis Cache
     ↓              ↓                ↓
Hardware IoT ←→ RabbitMQ Queue ←→ Background Tasks
```

### Support
- 📧 **Technical Issues**: Check the [Development Guide](DEVELOPMENT_GUIDE.md)
- 🐛 **Bug Reports**: Create an issue with detailed reproduction steps
- 💡 **Feature Requests**: Refer to [Features TOC](Features%20TOC.md) for planned features

---

**Happy Coding! 🚀**

*Building the future of mobile charging in Nepal, one power bank at a time.*
