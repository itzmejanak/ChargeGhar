# 🚀 PowerBank Django Production Deployment Guide

## 📋 Summary: Docker-Only Deployment (Recommended)

**Answer to your question:** **YES, Docker CLI is enough!**
- ✅ No Python installation needed
- ✅ No PostgreSQL installation needed
- ✅ No Redis/RabbitMQ installation needed
- ✅ Everything runs in containers

---

## 🎯 Deployment Strategy

### **Why Docker-Only Approach:**
1. **Your project is Docker-ready** - Multi-stage Dockerfile with uv dependency management
2. **Zero dependency management** - All dependencies packaged in containers
3. **Production consistency** - Same environment as local testing
4. **Easy maintenance** - Single command deployment and updates
5. **Resource efficient** - Proper resource limits and health checks

---

## 📦 What You Need on Server

**Requirements:**
- Server: Ubuntu (any recent version)
- Docker + Docker Compose (already installed for your Java app)
- At least 2GB RAM available
- 10GB free storage

---

## 🔧 Step-by-Step Deployment

### **Phase 1: Server Preparation (One-time)**

Since Docker is already installed for your Java/IoT application:

```bash
# 1. Connect to server
ssh root@213.210.21.113

# 2. Verify Docker is working
docker --version
docker-compose --version

# 3. Optional: Run setup script to ensure everything is ready
curl -O https://raw.githubusercontent.com/itzmejanak/ChargeGhar/main/deploy-server-setup.sh
chmod +x deploy-server-setup.sh
./deploy-server-setup.sh
```

### **Phase 2: Application Deployment**

```bash
# 1. Download and run deployment script
curl -O https://raw.githubusercontent.com/itzmejanak/ChargeGhar/main/deploy-production.sh
chmod +x deploy-production.sh
chmod +x load-fixtures.sh
./deploy-production.sh
./load-fixtures.sh
```

**That's it!** Your PowerBank Django application will be running at:
- **Django API:** http://213.210.21.113:8010
- **Health Check:** http://213.210.21.113:8010/api/app/health/
- **Admin Panel:** http://213.210.21.113:8010/admin/

---

## 🔄 Updates & Maintenance

### **Deploy New Version:**
```bash
cd /opt/powerbank
./deploy-production.sh
```

### **View Logs:**
```bash
cd /opt/powerbank
docker-compose -f docker-compose.prod.yml logs -f
```

### **View Specific Service Logs:**
```bash
# API logs
docker-compose -f docker-compose.prod.yml logs -f powerbank_api

# Database logs
docker-compose -f docker-compose.prod.yml logs -f powerbank_db

# Celery logs
docker-compose -f docker-compose.prod.yml logs -f powerbank_celery
```

### **Stop Application:**
```bash
cd /opt/powerbank
docker-compose -f docker-compose.prod.yml down
```

### **Restart Application:**
```bash
cd /opt/powerbank
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring Commands

```bash
# Check container status
docker-compose -f /opt/powerbank/docker-compose.prod.yml ps

# Check resource usage
docker stats

# Check application health
curl http://localhost:8010/api/app/health/

# View real-time logs
docker-compose -f /opt/powerbank/docker-compose.prod.yml logs -f powerbank_api
```

---

## 🌐 Domain Setup (Tomorrow)

When you get your domain:

1. **Update DNS:** Point domain to `213.210.21.113`
2. **Setup Nginx reverse proxy** (optional for SSL on port 80)
3. **Configure SSL certificate** with Let's Encrypt
4. **Update ALLOWED_HOSTS** in .env file

---

## 🚨 Troubleshooting

### **Common Issues:**

1. **Port 8010 in use:**
   ```bash
   netstat -tulpn | grep :8010
   # Kill process if needed
   ```

2. **Database connection issues:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs powerbank_db
   ```

3. **Migration failures:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec powerbank_api make migrate
   ```

4. **Container fails to start:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs powerbank_api
   ```

5. **Memory issues:**
   ```bash
   docker stats
   # Check if containers need more memory
   ```

---

## 🔐 Security Considerations

- ✅ Containers run as non-root user
- ✅ Production environment variables
- ✅ Resource limits configured
- ✅ Health checks implemented
- 📋 **TODO:** Setup firewall rules (only 22, 8010, 8080, 80, 443)
- 📋 **TODO:** SSL certificate when domain is ready
- 📋 **TODO:** Database backups automation

---

## 🏗️ Architecture Overview

Your PowerBank application includes:

- **Django API** (Port 8010) - Main application with REST API
- **PostgreSQL** - Primary database with PgBouncer connection pooling
- **Redis** - Caching and session storage
- **RabbitMQ** - Message queuing for Celery tasks
- **Celery** - Background task processing

### **Resource Allocation:**
- API: 1GB RAM limit
- Database: 512MB RAM limit
- Redis: 128MB RAM limit
- RabbitMQ: 256MB RAM limit
- Celery: 512MB RAM limit

---

## 📱 API Endpoints

Once deployed, your API will be available at:

```
GET  /api/app/health/          - Health check
POST /api/auth/login/          - User login
POST /api/auth/register/       - User registration
GET  /api/stations/            - List power stations
POST /api/rentals/             - Create rental
GET  /api/payments/            - Payment history
```

---

## ✅ Deployment Checklist

- [ ] Server access confirmed (SSH working)
- [ ] Docker installation verified
- [ ] Repository access confirmed
- [ ] Environment variables configured
- [ ] Test deployment process
- [ ] Verify application health
- [ ] Test API endpoints
- [ ] Plan domain configuration

---

## 🔧 Environment Variables

Key variables in your `.env` file:

```bash
# Application
ENVIRONMENT=production
API_PORT=8010
HOST=213.210.21.113

# Database
POSTGRES_DB=powerbank_db
POSTGRES_USER=powerbank_user
POSTGRES_HOST=powerbank_db

# Security (CHANGE THESE!)
DJANGO_SECRET_KEY=your-production-secret-key
POSTGRES_PASSWORD=your-production-db-password
RABBITMQ_DEFAULT_PASS=your-production-rabbitmq-password
```

---

**🎯 Next Action:** Run the deployment script to get your PowerBank Django API live in minutes!

**Note:** This runs alongside your existing Java/IoT application on the same server without conflicts.