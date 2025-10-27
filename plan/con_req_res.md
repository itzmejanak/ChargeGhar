# ChargeGhar Integration - API Request/Response Specifications

## 📡 API Endpoints

### Base URLs
- **Django Main App**: `https://main.chargeghar.com`
- **Java IoT System**: `https://api.chargeghar.com`

---

## 🔐 Authentication APIs

### 1. Admin Login
**Endpoint**: `POST /api/admin/login`  
**Purpose**: Obtain JWT tokens for API access

#### Request
```http
POST https://main.chargeghar.com/api/admin/login HTTP/1.1
Content-Type: application/json

{
  "email": "janak@powerbank.com",
  "password": "password123"
}
```

#### Response (Success - 200 OK)
```json
{
  "success": true,
  "message": "Admin login successful",
  "data": {
    "user_id": "1",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsImV4cCI6MTcyOTc4ODAwMH0.signature_here",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMSIsInR5cGUiOiJyZWZyZXNoIiwiZXhwIjoxNzMwMzkwMDAwfQ.refresh_signature",
    "user": {
      "id": "1",
      "email": "janak@powerbank.com",
      "username": "janak",
      "is_staff": true,
      "is_superuser": true
    }
  }
}
```

#### Response (Error - 401 Unauthorized)
```json
{
  "success": false,
  "message": "Invalid credentials",
  "error": "INVALID_CREDENTIALS"
}
```

#### Java Usage
```java
// Store tokens in singleton
AuthTokenManager.getInstance().setAccessToken(response.access_token);
AuthTokenManager.getInstance().setRefreshToken(response.refresh_token);
```

---

### 2. Token Refresh
**Endpoint**: `POST /api/admin/refresh`  
**Purpose**: Refresh expired access token

#### Request
```http
POST https://main.chargeghar.com/api/admin/refresh HTTP/1.1
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (Success - 200 OK)
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_token_here"
  }
}
```

---

## 📊 Data Synchronization APIs

### 3. Station Data Upload (Full Sync)
**Endpoint**: `POST /api/internal/stations/data`  
**Purpose**: Sync complete station, slot, and powerbank data from IoT device  
**Trigger**: Every device upload (20-minute cycle) or on-demand commands

#### Request Headers
```http
POST https://main.chargeghar.com/api/internal/stations/data HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Signature: base64_encoded_hmac_sha256_signature
X-Timestamp: 1698345600
```

#### Request Body (type=full)
```json
{
  "type": "full",
  "timestamp": 1698345600,
  "device": {
    "serial_number": "864601069946994",
    "imei": "864601069946994",
    "signal_strength": "85",
    "wifi_ssid": "ChargeGhar_Office",
    "last_heartbeat": "2025-10-27T14:30:00Z",
    "status": "ONLINE",
    "hardware_info": {
      "firmware_version": "2.1.5",
      "protocol_version": "0xA8"
    }
  },
  "station": {
    "serial_number": "864601069946994",
    "total_slots": 4,
    "pinboards": [
      {
        "index": 1,
        "io": 0,
        "temperature": 28,
        "soft_version": 21,
        "hard_version": 5
      }
    ]
  },
  "slots": [
    {
      "slot_number": 1,
      "status": "AVAILABLE",
      "battery_level": 0,
      "slot_metadata": {
        "micro_switch": "1",
        "solenoid_valve": "0",
        "lock_count": 0,
        "last_updated": "2025-10-27T14:30:00Z"
      }
    },
    {
      "slot_number": 2,
      "status": "OCCUPIED",
      "battery_level": 85,
      "power_bank_serial": "123456789",
      "slot_metadata": {
        "micro_switch": "1",
        "solenoid_valve": "0",
        "lock_count": 3,
        "last_updated": "2025-10-27T14:30:00Z"
      }
    },
    {
      "slot_number": 3,
      "status": "ERROR",
      "battery_level": 0,
      "slot_metadata": {
        "error_code": "0x04",
        "error_message": "Spring cannot eject powerbank",
        "micro_switch": "0",
        "solenoid_valve": "1",
        "last_updated": "2025-10-27T14:30:00Z"
      }
    },
    {
      "slot_number": 4,
      "status": "AVAILABLE",
      "battery_level": 0,
      "slot_metadata": {
        "micro_switch": "1",
        "solenoid_valve": "0",
        "lock_count": 0,
        "last_updated": "2025-10-27T14:30:00Z"
      }
    }
  ],
  "power_banks": [
    {
      "serial_number": "123456789",
      "status": "AVAILABLE",
      "battery_level": 85,
      "current_slot": 2,
      "hardware_info": {
        "temperature": 32,
        "voltage": 5000,
        "current": 1500,
        "soft_version": 10,
        "hard_version": 128,
        "micro_switch": "1",
        "solenoid_valve": "0",
        "area_code": 1
      }
    }
  ]
}
```

#### Field Mapping (Device → Request)
| Device Field | JSON Field | Example | Notes |
|--------------|------------|---------|-------|
| `rentboxSN` | `device.serial_number` | "864601069946994" | Station identifier |
| Redis heartbeat | `device.last_heartbeat` | ISO 8601 | Last communication |
| Redis activity | `device.status` | "ONLINE" | Computed status |
| `signal` param | `device.signal_strength` | "85" | Signal % |
| `ssid` param | `device.wifi_ssid` | "ChargeGhar_Office" | WiFi network |
| `Pinboard.index` | `slots[].slot_number` | 1 | Slot index |
| `Powerbank.status` | `slots[].status` | "OCCUPIED" | Mapped from 0x01 |
| `Powerbank.power` | `slots[].battery_level` | 85 | 0-100% |
| `Powerbank.snAsString` | `power_banks[].serial_number` | "123456789" | PowerBank SN |
| `Powerbank.temp` | `hardware_info.temperature` | 32 | Celsius |
| `Powerbank.voltage` | `hardware_info.voltage` | 5000 | Millivolts |
| `Powerbank.current` | `hardware_info.current` | 1500 | Milliamps |

#### Status Code Mapping
| Device Status | Slot Status | PowerBank Status | Description |
|---------------|-------------|------------------|-------------|
| `0x00` | `AVAILABLE` | N/A | Empty slot |
| `0x01` | `OCCUPIED` | `AVAILABLE` | Normal powerbank present |
| `0x02` | `ERROR` | `MAINTENANCE` | Charging error |
| `0x04` | `ERROR` | `MAINTENANCE` | Spring stuck |
| `0x05` | `ERROR` | `DAMAGED` | Forced release |
| `0x06` | `ERROR` | `DAMAGED` | No communication |

#### Response (Success - 200 OK)
```json
{
  "success": true,
  "message": "Station data updated successfully",
  "data": {
    "station_id": "uuid-here",
    "slots_updated": 4,
    "powerbanks_updated": 1,
    "timestamp": "2025-10-27T14:30:05Z"
  }
}
```

#### Response (Error - 400 Bad Request)
```json
{
  "success": false,
  "message": "Invalid data format",
  "errors": {
    "slots[2].status": "Invalid status code 'INVALID'"
  }
}
```

#### Response (Error - 403 Forbidden)
```json
{
  "success": false,
  "message": "Signature verification failed",
  "error": "INVALID_SIGNATURE"
}
```

---

### 4. PowerBank Return Event
**Endpoint**: `POST /api/internal/stations/data`  
**Purpose**: Notify Django app of powerbank return event  
**Trigger**: Device detects powerbank insertion

#### Request Body (type=returned)
```json
{
  "type": "returned",
  "timestamp": 1698345600,
  "device": {
    "serial_number": "864601069946994",
    "last_heartbeat": "2025-10-27T15:45:00Z"
  },
  "return_event": {
    "power_bank_serial": "123456789",
    "slot_number": 3,
    "battery_level": 45,
    "returned_at": "2025-10-27T15:45:00Z",
    "condition": "NORMAL",
    "hardware_info": {
      "temperature": 28,
      "voltage": 4800,
      "current": 0
    }
  },
  "rental_info": {
    "rental_code": "RNT12345",
    "user_id": "user-uuid-here",
    "started_at": "2025-10-27T12:00:00Z",
    "duration_minutes": 225
  }
}
```

#### Response (Success - 200 OK)
```json
{
  "success": true,
  "message": "Return processed successfully",
  "data": {
    "rental_id": "rental-uuid",
    "rental_status": "COMPLETED",
    "charges": {
      "base_amount": 50.00,
      "overdue_amount": 0.00,
      "total_paid": 50.00
    },
    "power_bank_status": "AVAILABLE"
  }
}
```

---

## 🔒 Signature Generation

### Algorithm
```
signature = HMAC-SHA256(
    key=SIGNATURE_SECRET,
    message=JSON_BODY + TIMESTAMP
)
encoded_signature = Base64.encode(signature)
```

### Example (Pseudocode)
```java
// Java
String payload = jsonBody + timestamp;
SecretKeySpec key = new SecretKeySpec(SECRET_KEY.getBytes(), "HmacSHA256");
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(key);
byte[] rawHmac = mac.doFinal(payload.getBytes());
String signature = Base64.getEncoder().encodeToString(rawHmac);
```

```python
# Python
import hmac
import hashlib
import base64

payload = json_body + str(timestamp)
signature = hmac.new(
    SECRET_KEY.encode(),
    payload.encode(),
    hashlib.sha256
).digest()
encoded_signature = base64.b64encode(signature).decode()
```

### Validation Rules
1. **Timestamp Check**: Request must be within 5 minutes of server time
2. **Signature Match**: Computed signature must match `X-Signature` header
3. **Idempotency**: Reject duplicate timestamps from same device (optional)

---

## 📋 Status Reference Tables

### Device Online Status
| Redis Key | TTL | Used For |
|-----------|-----|----------|
| `device_heartbeat:{deviceName}` | 5 min | Real-time online check |
| `device_activity:{deviceName}` | 25 min | Extended activity window |
| `clientConect:{deviceName}` | 1 day | Device registration |

### Station Status Values
| Status | Meaning | Trigger |
|--------|---------|---------|
| `ONLINE` | Active and responding | Heartbeat within 2 min |
| `OFFLINE` | Not responding | No activity for 25+ min |
| `MAINTENANCE` | Under repair | Manual admin action |

### Slot Status Values
| Status | Meaning | Device Status Code |
|--------|---------|-------------------|
| `AVAILABLE` | Empty, ready for powerbank | 0x00 |
| `OCCUPIED` | Has powerbank (normal) | 0x01 |
| `MAINTENANCE` | Under repair | Admin set |
| `ERROR` | Hardware malfunction | 0x02-0x06 |

### PowerBank Status Values
| Status | Meaning | Context |
|--------|---------|---------|
| `AVAILABLE` | In station, ready to rent | status=0x01, not rented |
| `RENTED` | Currently rented by user | Active rental exists |
| `MAINTENANCE` | Under repair | Error codes or admin set |
| `DAMAGED` | Damaged, unusable | Forced release or comm loss |

---

## 🔄 Retry Strategy

### Java Connector Retry Logic
```
Attempt 1: Immediate
    ↓ (if fails)
Attempt 2: Wait 2 seconds
    ↓ (if fails)
Attempt 3: Wait 4 seconds
    ↓ (if fails)
Log error, store for manual retry
```

### HTTP Status Code Handling
| Code | Action |
|------|--------|
| 200 | Success, clear retry counter |
| 400 | Bad request, log and skip (no retry) |
| 401 | Refresh token and retry once |
| 403 | Signature error, log and alert admin |
| 429 | Rate limited, wait 60s and retry |
| 500 | Server error, retry with backoff |
| 502/503 | Service unavailable, retry 3x |

---

## 📊 Data Format Examples

### Empty Station (All Slots Available)
```json
{
  "type": "full",
  "station": {
    "serial_number": "864601069946994",
    "total_slots": 4
  },
  "slots": [
    {"slot_number": 1, "status": "AVAILABLE", "battery_level": 0},
    {"slot_number": 2, "status": "AVAILABLE", "battery_level": 0},
    {"slot_number": 3, "status": "AVAILABLE", "battery_level": 0},
    {"slot_number": 4, "status": "AVAILABLE", "battery_level": 0}
  ],
  "power_banks": []
}
```

### Fully Loaded Station
```json
{
  "type": "full",
  "station": {
    "serial_number": "864601069946994",
    "total_slots": 4
  },
  "slots": [
    {"slot_number": 1, "status": "OCCUPIED", "battery_level": 100, "power_bank_serial": "111111111"},
    {"slot_number": 2, "status": "OCCUPIED", "battery_level": 85, "power_bank_serial": "222222222"},
    {"slot_number": 3, "status": "OCCUPIED", "battery_level": 65, "power_bank_serial": "333333333"},
    {"slot_number": 4, "status": "OCCUPIED", "battery_level": 45, "power_bank_serial": "444444444"}
  ],
  "power_banks": [
    {"serial_number": "111111111", "status": "AVAILABLE", "battery_level": 100, "current_slot": 1},
    {"serial_number": "222222222", "status": "AVAILABLE", "battery_level": 85, "current_slot": 2},
    {"serial_number": "333333333", "status": "AVAILABLE", "battery_level": 65, "current_slot": 3},
    {"serial_number": "444444444", "status": "AVAILABLE", "battery_level": 45, "current_slot": 4}
  ]
}
```

### Station with Error Slot
```json
{
  "type": "full",
  "slots": [
    {"slot_number": 1, "status": "OCCUPIED", "battery_level": 100, "power_bank_serial": "111111111"},
    {"slot_number": 2, "status": "ERROR", "battery_level": 0, "slot_metadata": {"error_code": "0x04", "error_message": "Spring stuck"}},
    {"slot_number": 3, "status": "AVAILABLE", "battery_level": 0},
    {"slot_number": 4, "status": "AVAILABLE", "battery_level": 0}
  ]
}
```

---

## 🎯 Integration Milestones

### Milestone 1: Authentication Working
- ✅ Login succeeds, tokens returned
- ✅ Tokens stored in Java memory
- ✅ Subsequent requests use Bearer token

### Milestone 2: Signature Validation Working
- ✅ Java generates correct signature
- ✅ Django validates signature successfully
- ✅ Requests with invalid signature rejected (403)

### Milestone 3: Full Data Sync Working
- ✅ Device upload triggers sync
- ✅ Station record created/updated
- ✅ Slots created/updated (all 4)
- ✅ PowerBanks created/updated

### Milestone 4: Return Event Working
- ✅ Return detected by device
- ✅ Django receives return event
- ✅ Rental marked as COMPLETED
- ✅ Charges calculated correctly

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] Test login with valid credentials → 200 OK
- [ ] Test login with invalid credentials → 401 Unauthorized
- [ ] Test data sync with valid signature → 200 OK
- [ ] Test data sync with invalid signature → 403 Forbidden
- [ ] Test data sync with expired timestamp → 403 Forbidden
- [ ] Test full station sync (all slots empty)
- [ ] Test full station sync (all slots occupied)
- [ ] Test full station sync (mixed statuses)
- [ ] Test return event (normal return)
- [ ] Test return event (late return with charges)

### Automated Testing
- [ ] Unit test: Signature generation (Java)
- [ ] Unit test: Signature validation (Python)
- [ ] Integration test: End-to-end data sync
- [ ] Integration test: Return flow
- [ ] Load test: 100 devices uploading every 20 min
- [ ] Failure test: Django server down (retry logic)
- [ ] Failure test: Invalid token (refresh logic)

---

## 📝 Logging Requirements

### Java Side (api.chargeghar.com)
```
[2025-10-27 14:30:00] INFO  ChargeGharConnector - Authenticating with Django API
[2025-10-27 14:30:01] INFO  ChargeGharConnector - Authentication successful, token expires at 2025-10-27 15:30:01
[2025-10-27 14:30:05] INFO  ChargeGharConnector - Sending device data for station 864601069946994
[2025-10-27 14:30:05] DEBUG ChargeGharConnector - Payload: {"type":"full","device":{...}}
[2025-10-27 14:30:06] INFO  ChargeGharConnector - Data sync successful, response: 200 OK
```

### Django Side (main.chargeghar.com)
```
[2025-10-27 14:30:06] INFO  StationDataView - Received data sync request for station 864601069946994
[2025-10-27 14:30:06] DEBUG StationDataView - Signature validation: PASSED
[2025-10-27 14:30:06] INFO  StationDataView - Updated 4 slots, 1 powerbank
[2025-10-27 14:30:06] INFO  StationDataView - Response sent: 200 OK
```

---

## 🔗 Related Files
- **Plan**: `con_plan.md` - Overall architecture and strategy
- **Java Code**: `con_code_java.md` - Java implementation
- **Python Code**: `con_code_python.md` - Django implementation
