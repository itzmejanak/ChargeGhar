# ChargeGhar Integration Plan - System Architecture

## 🎯 Objective
Integrate IoT device management system (Java/Spring) with Django-based user application (main.chargeghar.com) to synchronize real-time device data, station status, and rental operations.

---

## 📊 System Overview

### Current Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                       EMQX MQTT Broker                          │
│         qd081a20.ala.dedicated.aws.emqxcloud.com:1883          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├──► Device → Server: /powerbank/{deviceName}/user/update
                 ├──► Device → Server: /powerbank/{deviceName}/user/heart
                 └──► Server → Device: /powerbank/{deviceName}/user/get
                 
┌─────────────────────────────────────────────────────────────────┐
│              Java IoT Management System (Current)                │
│                   api.chargeghar.com                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Device Communication (MQTT + HTTP)                     │  │
│  │  • Data Parsing (ReceiveUpload, Powerbank, Pinboard)     │  │
│  │  • Redis State Management                                 │  │
│  │  • Device Commands (check, popup_random, send)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                 │
                 │ NEW INTEGRATION ✨
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Django User Application (Target)                    │
│                 main.chargeghar.com                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • User Management & Authentication                       │  │
│  │  • Rental Operations (Start, Return, Extend)             │  │
│  │  • Station Management & Slot Tracking                    │  │
│  │  • PowerBank Inventory & Status                          │  │
│  │  • Payment Processing & History                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Architecture

### Authentication Flow
```
Java System (api.chargeghar.com)
    │
    ├─► POST /api/admin/login
    │   Headers: Content-Type: application/json
    │   Body: {"email": "janak@powerbank.com", "password": "password123"}
    │
    ├─◄ Response: Access Token + Refresh Token
    │   {
    │     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    │     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    │   }
    │
    └─► Store tokens in memory (singleton pattern)
        Use access_token for all subsequent API calls
        Refresh token when expired (401 response)
```

### Request Signature System
**Purpose**: Mutual authentication between Java IoT system and Django application

**Components**:
1. **Java Side**: `src/main/java/com.demo/tools/SignChargeGharMain.java`
2. **Django Side**: `api/stations/services/utils/sign_chargeghar_main.py`

**Signature Algorithm**:
```
HMAC-SHA256(payload + timestamp + secret_key) → Base64 Encoded
```

---

## 🏗️ Integration Components

### Java Side: New Connector Class
**Location**: `src/main/java/com.demo/connector/ChargeGharConnector.java`

**Responsibilities**:
1. Authenticate with Django API
2. Send device upload data
3. Send rental return data
4. Generate/validate request signatures
5. Handle token refresh & retry logic

### Django Side: New API Endpoints
**Location**: `api/stations/views/internal_views.py`

**Endpoints**:
- `POST /api/internal/stations/data` - Receive device data from IoT system

**Location**: `api/stations/services/utils/sign_chargeghar_main.py`
- Signature validation utility

---

## 📡 Data Flow Scenarios

### Scenario 1: Device Upload (Every 20 Minutes)
```
Device → EMQX → Java System → Django API
   │        │         │            │
   │        │         │            └─► Update Station Status
   │        │         │            └─► Update Slot Status
   │        │         │            └─► Update PowerBank Inventory
   │        │         │
   │        │         └─► Parse binary data (ReceiveUpload)
   │        └─► Topic: /powerbank/{deviceName}/user/update
   └─► HTTP POST /api/rentbox/upload/data
```

### Scenario 2: PowerBank Return
```
User Returns PowerBank → Device Detects → Java System → Django API
                            │                │              │
                            │                │              └─► Mark Rental as COMPLETED
                            │                │              └─► Calculate charges
                            │                │              └─► Update PowerBank location
                            │                │              └─► Free up slot
                            │                │
                            │                └─► Parse return event
                            └─► HTTP POST /api/rentbox/order/return
```

---

## 🗄️ Database Mapping

### Device Data → Django Models

| Java Parsed Data | Django Model | Field | Notes |
|------------------|--------------|-------|-------|
| `rentboxSN` | `Station` | `serial_number` | Unique identifier |
| Device online status | `Station` | `status` | ONLINE/OFFLINE/MAINTENANCE |
| Last communication | `Station` | `last_heartbeat` | Timestamp |
| Powerbank count | `Station` | `total_slots` | Calculated from pinboards |
| `Pinboard.index` | `StationSlot` | `slot_number` | 1-based index |
| `Powerbank.status` | `StationSlot` | `status` | AVAILABLE/OCCUPIED/ERROR |
| `Powerbank.power` | `StationSlot` | `battery_level` | 0-100% |
| `Powerbank.snAsString` | `PowerBank` | `serial_number` | Unique SN |
| `Powerbank.power` | `PowerBank` | `battery_level` | Current charge |
| `Powerbank.status` | `PowerBank` | `status` | AVAILABLE/RENTED/MAINTENANCE |
| `Powerbank.temp` | `PowerBank` | `hardware_info.temperature` | JSON field |
| `Powerbank.voltage` | `PowerBank` | `hardware_info.voltage` | JSON field |
| `Powerbank.current` | `PowerBank` | `hardware_info.current` | JSON field |

---

## 🔄 Integration Points

### 1. Device Data Upload Hook
**Java Location**: `ApiController.rentboxOrderReturnEnd()` (line ~245)
**Action**: After parsing device data, call `ChargeGharConnector.sendDeviceData()`

### 2. PowerBank Return Hook
**Java Location**: `ApiController` - `/api/rentbox/order/return` endpoint
**Action**: After processing return, call `ChargeGharConnector.sendReturnedData()`

---

## ⚙️ Configuration Management

### Java Config File
**Location**: `src/main/resources/config.properties`

**New Entries**:
```properties
# ChargeGhar Main Django API
chargeghar.main.baseUrl=https://main.chargeghar.com
chargeghar.main.email=janak@powerbank.com
chargeghar.main.password=password123
chargeghar.main.signatureSecret=your-shared-secret-key-here

# API Endpoints
chargeghar.main.loginEndpoint=/api/admin/login
chargeghar.main.stationDataEndpoint=/api/internal/stations/data

# Timeouts & Retry
chargeghar.main.connectTimeout=10000
chargeghar.main.readTimeout=15000
chargeghar.main.maxRetries=3
```

### Django Settings
**Location**: `main_app/config/application.py and .env`

```python
# IoT System Integration
IOT_SYSTEM_SIGNATURE_SECRET = 'your-shared-secret-key-here'
IOT_SYSTEM_ALLOWED_IPS = ['api.chargeghar.com, 213.210.21.113']  # Whitelist
```

---

## 📋 Data Completeness Analysis

### ✅ Available Data from Device
- Station serial number (rentboxSN)
- Device online/offline status (via Redis timestamps)
- Pinboard count and configuration
- Powerbank count per station
- Individual powerbank details:
  - Serial number (SN)
  - Battery level (0-100%)
  - Status (empty, normal, charging error, stuck, etc.)
  - Temperature (°C)
  - Voltage (V)
  - Current (A)
  - Hardware/software versions
  - Micro switch & solenoid valve states
- Signal strength (from HTTP params)
- WiFi SSID (from HTTP params)
- IO configuration

### ⚠️ Missing Data (Need Alternative Sources)
| Missing Data | Alternative Source | Notes |
|--------------|-------------------|-------|
| Station GPS coordinates | Manual entry in Django admin | One-time setup |
| Station name | Manual entry | Business decision |
| Station address/landmark | Manual entry | Business decision |
| Rental session info | Django app tracks this | From user actions |
| Payment details | Django app handles | Razorpay integration |
| User information | Django User model | Registration/login |
| Rental pricing | Django RentalPackage | Business configuration |

### 🔍 Data Gaps to Address
1. **PowerBank Model/Capacity**: Not in device response
   - **Solution**: Add mapping table in Django (SN → Model/Capacity)
   
2. **Station Location**: Not in device data
   - **Solution**: Admin panel entry during station deployment
   
3. **Rental-to-PowerBank Association**: Device doesn't know about rentals
   - **Solution**: Django maintains this via `Rental.power_bank` foreign key
   
4. **Return Station Detection**: Need to identify which station received return
   - **Solution**: rentboxSN in return request identifies the station

---

## 🎯 Implementation Phases

### Phase 1: Foundation (Security & Auth)
1. Create `SignChargeGharMain.java` with HMAC signature generation
2. Create `sign_chargeghar_main.py` with signature validation
3. Add configuration properties for Django API
4. Implement token management (store, refresh, validate)

### Phase 2: Connector Class
1. Create `ChargeGharConnector.java` with HttpClient setup
2. Implement `connectChargeGharMain()` - authentication
3. Implement `generateSignature()` - request signing
4. Add retry logic and error handling

### Phase 3: Data Transmission
1. Implement `sendDeviceData()` - full station sync
2. Implement `sendReturnedData()` - return event notification
3. Add data transformation logic (Java objects → JSON)

### Phase 4: Django Integration
1. Create `internal_views.py` with `/api/internal/stations/data` endpoint
2. Create service layer for data processing
3. Implement signature validation middleware
4. Add database update logic (Station, StationSlot, PowerBank)

### Phase 5: Testing & Validation
1. Unit tests for signature generation/validation
2. Integration tests for API communication
3. End-to-end testing with real device
4. Performance testing (handle 20-minute upload cycles)

### Phase 6: Monitoring & Maintenance
1. Add logging for all integration points
2. Set up alerts for failed synchronizations
3. Create admin dashboard for sync status
4. Document troubleshooting procedures

---

## 🚨 Error Handling Strategy

### Java Side
```
Try sending data
    ├─► Network Error → Retry with exponential backoff (max 3 attempts)
    ├─► 401 Unauthorized → Refresh token and retry
    ├─► 403 Forbidden → Log error, notify admin
    ├─► 500 Server Error → Retry after 30 seconds
    └─► Success (200) → Log success, clear retry counter
```

### Django Side
```
Receive request
    ├─► Validate signature → Reject if invalid (403)
    ├─► Parse JSON → Return 400 if malformed
    ├─► Process data → Wrap in transaction
    │   ├─► Update Station
    │   ├─► Update/Create StationSlots
    │   └─► Update/Create PowerBanks
    ├─► Database Error → Rollback, return 500
    └─► Success → Return 200 with confirmation
```

---

## 📊 Success Metrics

### Integration Health
- ✅ 95%+ successful data syncs
- ✅ <5 second average sync latency
- ✅ 0 data loss (retry until success)
- ✅ 100% signature validation success rate

### Data Consistency
- ✅ Station status matches device heartbeat
- ✅ Slot count matches physical device configuration
- ✅ PowerBank inventory matches device reports
- ✅ Battery levels within 5% tolerance

---

## 🔒 Security Considerations

### Authentication
- ✅ JWT tokens with expiration (60 minutes)
- ✅ Refresh token rotation
- ✅ Secure storage (memory only, no disk)

### Authorization
- ✅ Admin-level API access required
- ✅ IP whitelisting (optional but recommended)
- ✅ Rate limiting (100 requests/minute)

### Data Integrity
- ✅ HMAC signature on every request
- ✅ Timestamp validation (reject requests >5 min old)
- ✅ Idempotency keys for duplicate prevention

### Transport Security
- ✅ HTTPS only (TLS 1.2+)
- ✅ Certificate validation
- ✅ No sensitive data in logs

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] Update `config.properties` with production credentials
- [ ] Generate strong signature secret (32+ characters)
- [ ] Configure Django settings with secret and whitelist
- [ ] Test signature generation/validation locally
- [ ] Review all database migrations

### Deployment
- [ ] Deploy Java connector code to api.chargeghar.com
- [ ] Deploy Django endpoints to main.chargeghar.com
- [ ] Restart services in correct order (Django first, then Java)
- [ ] Verify authentication works (check logs)
- [ ] Monitor first device upload cycle

### Post-Deployment
- [ ] Monitor sync success rate (target 95%+)
- [ ] Check database for correct data
- [ ] Validate station status updates in real-time
- [ ] Test rental flow end-to-end
- [ ] Set up alerting for sync failures

---

## 🆘 Troubleshooting Guide

### Issue: Authentication Failed
- Check email/password in config.properties
- Verify Django admin user exists and is active
- Check Django logs for login attempts
- Ensure JWT_SECRET is configured correctly

### Issue: Signature Validation Failed
- Verify secret key matches on both sides
- Check timestamp synchronization (NTP)
- Log payload on both sides and compare
- Ensure no whitespace in payload

### Issue: Data Not Syncing
- Check Java logs for connector errors
- Verify Django endpoint is accessible
- Test endpoint with curl manually
- Check database permissions

### Issue: Duplicate Data
- Verify unique constraints in Django models
- Implement idempotency keys
- Check for race conditions in device uploads

---

## 📚 Related Documentation
- `con_code_java.md` - Java implementation code
- `con_code_python.md` - Django implementation code
- `con_req_res.md` - API request/response formats
- `STATUS_DETECTION_IMPROVEMENT.md` - Device status logic
- `TOPIC_FIX_SUMMARY.md` - MQTT topic configuration
