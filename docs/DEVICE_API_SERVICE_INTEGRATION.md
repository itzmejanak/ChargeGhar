# Device API Service Integration Guide

**Simple & Compact Guide for Django Integration**  
**Date:** November 5, 2025

---

## 📋 What This Does (In Simple Terms)

Your **Java Spring API** (`api.chargeghar.com`) already handles all device communication via MQTT. This Python service just **calls those Java endpoints** from Django. Think of it as a **bridge** - Django asks the service, service calls Java, Java talks to devices.

```
Django App → device_api_service.py → Java API → MQTT → Device Hardware
```

**No MQTT code needed in Django!** Java handles everything. You just make HTTP requests.

---

## 🎯 The 5 Endpoints You'll Use

| What You Want | Call This Method | Java Endpoint |
|---------------|------------------|---------------|
| Send raw command to device | `send_command()` | `GET /send` |
| Check device status | `check_device()` | `GET /check` |
| Check all slots (including empty) | `check_all_devices()` | `GET /check_all` |
| Pop a powerbank | `popup_powerbank()` | `GET /popup_random` |
| Register new device | `create_device()` | `POST /device/create` |

---

## ⚙️ Step 1: Configuration Setup

### A. Django Settings (Add to `application.py`)

```python
# Device API Configuration (Java Spring API)
DEVICE_API = {
    'BASE_URL': 'https://api.chargeghar.com',    
    'CONNECT_TIMEOUT': 10,  # Wait 10 seconds to connect
    'READ_TIMEOUT': 30,     # Wait 30 seconds for response (device commands take time)
    'MAX_RETRIES': 2,       # Retry failed requests 2 times
    
    # Authentication (for inter-system communication)
    'AUTH_ENABLED': True,   # Set False for local testing
    'AUTH_USERNAME': 'system_user',  # Java admin user
    'AUTH_PASSWORD': 'your_secure_password',  # Java admin password
    'AUTH_LOGIN_ENDPOINT': '/api/auth/login',  # Java login endpoint
}
```

**What this means:**
- `BASE_URL`: Where your Java Spring API is running
- `CONNECT_TIMEOUT`: How long to wait for connection (10 seconds is good)
- `READ_TIMEOUT`: How long to wait for device response (30s because MQTT can be slow)
- `MAX_RETRIES`: Auto-retry on server errors (500, 503, etc.)
- `AUTH_ENABLED`: Enable/disable JWT authentication (disable for local dev)
- `AUTH_USERNAME`: Username for Java API admin account
- `AUTH_PASSWORD`: Password for Java API authentication
- `AUTH_LOGIN_ENDPOINT`: Java endpoint to get JWT token

### B. Environment Variables (Optional - for production)

Create `.env` file:
```bash
# Java API Configuration
DEVICE_API_BASE_URL=https://api.chargeghar.com
DEVICE_API_CONNECT_TIMEOUT=10
DEVICE_API_READ_TIMEOUT=30
DEVICE_API_MAX_RETRIES=2

# Authentication for inter-system communication
DEVICE_API_AUTH_ENABLED=True
DEVICE_API_AUTH_USERNAME=system_user
DEVICE_API_AUTH_PASSWORD=your_secure_password_here
DEVICE_API_AUTH_LOGIN_ENDPOINT=/api/auth/login
```

Then in `settings.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DEVICE_API = {
    'BASE_URL': os.getenv('DEVICE_API_BASE_URL', 'https://api.chargeghar.com'),
    'CONNECT_TIMEOUT': int(os.getenv('DEVICE_API_CONNECT_TIMEOUT', '10')),
    'READ_TIMEOUT': int(os.getenv('DEVICE_API_READ_TIMEOUT', '30')),
    'MAX_RETRIES': int(os.getenv('DEVICE_API_MAX_RETRIES', '2')),
    
    # Authentication
    'AUTH_ENABLED': os.getenv('DEVICE_API_AUTH_ENABLED', 'False').lower() == 'true',
    'AUTH_USERNAME': os.getenv('DEVICE_API_AUTH_USERNAME', 'system_user'),
    'AUTH_PASSWORD': os.getenv('DEVICE_API_AUTH_PASSWORD', ''),
    'AUTH_LOGIN_ENDPOINT': os.getenv('DEVICE_API_AUTH_LOGIN_ENDPOINT', '/api/auth/login'),
}
```

### C. Install Required Package

```bash
pip install requests
```

Add to `requirements.txt`:
```
requests>=2.31.0
```

---

## 💻 Step 2: The Service Code

Create file: `yourapp/services/device_api_service.py`

```python
"""
Device API Service - HTTP Client for Java Spring API
Simple bridge to call device control endpoints with JWT authentication
"""
import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DeviceAPIService:
    """
    Calls Java API endpoints to control devices with JWT authentication
    
    Features:
    - Auto-login to get JWT token
    - Token caching and auto-refresh
    - Automatic retry on 401 (re-authenticate)
    
    Simple usage:
        service = DeviceAPIService()
        result = service.check_device("CG001")
        if result['success']:
            print(result['data'])  # List of powerbanks
    """
    
    def __init__(self):
        """Initialize with settings from Django config"""
        config = settings.DEVICE_API
        self.base_url = config['BASE_URL']
        self.timeout = (config['CONNECT_TIMEOUT'], config['READ_TIMEOUT'])
        self.max_retries = config['MAX_RETRIES']
        
        # Authentication settings
        self.auth_enabled = config.get('AUTH_ENABLED', False)
        self.auth_username = config.get('AUTH_USERNAME', '')
        self.auth_password = config.get('AUTH_PASSWORD', '')
        self.auth_login_endpoint = config.get('AUTH_LOGIN_ENDPOINT', '/api/auth/login')
        
        # Token management
        self.jwt_token = None
        self.token_expires_at = None
        
        self.session = requests.Session()
        
        logger.info(f"Device API Service initialized: {self.base_url}")
        logger.info(f"Authentication: {'Enabled' if self.auth_enabled else 'Disabled'}")
    
    # ==========================================
    # AUTHENTICATION METHODS
    # ==========================================
    
    def _login(self) -> bool:
        """
        Login to Java API and get JWT token
        
        Returns:
            True if login successful, False otherwise
        """
        if not self.auth_enabled:
            return True  # No auth needed
        
        login_url = f"{self.base_url}{self.auth_login_endpoint}"
        
        try:
            logger.info(f"🔐 Logging in to Java API: {login_url}")
            
            # Java AuthController expects this format
            login_data = {
                'username': self.auth_username,
                'password': self.auth_password
            }
            
            response = self.session.post(
                login_url,
                json=login_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Java LoginResponse format:
                # {
                #   "success": true,
                #   "token": "eyJhbGc...",
                #   "user": {...}
                # }
                
                if result.get('success'):
                    self.jwt_token = result.get('token')
                    
                    # Token expires in 24 hours (from Java JwtUtil)
                    # Refresh 1 hour before expiry
                    self.token_expires_at = datetime.now() + timedelta(hours=23)
                    
                    logger.info(f"✅ Login successful! Token expires at: {self.token_expires_at}")
                    return True
                else:
                    logger.error(f"❌ Login failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Login HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.exception(f"💥 Login error: {str(e)}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if JWT token is still valid"""
        if not self.auth_enabled:
            return True  # No auth needed
        
        if not self.jwt_token:
            return False
        
        if not self.token_expires_at:
            return False
        
        # Check if token expired
        return datetime.now() < self.token_expires_at
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid JWT token
        Login if needed
        """
        if not self.auth_enabled:
            return True
        
        if self._is_token_valid():
            return True
        
        # Token expired or not available, login again
        logger.info("🔄 Token expired or not available, logging in...")
        return self._login()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for requests
        
        Returns:
            Headers dict with Authorization if auth enabled
        """
        headers = {}
        
        if self.auth_enabled and self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        return headers
    
    # ==========================================
    # PRIVATE METHOD - Makes actual HTTP request
    # ==========================================
    
    def _make_request(
        self, 
        method: str,           # 'GET' or 'POST'
        endpoint: str,         # '/check', '/send', etc.
        params: Optional[Dict] = None,   # Query parameters
        json_data: Optional[Dict] = None,  # Request body (for POST)
        retry_count: int = 0,
        retry_auth: bool = True  # Retry on 401 (re-authenticate)
    ) -> Dict[str, Any]:
        """
        Makes HTTP request to Java API and handles response
        
        Returns:
            {
                'success': True/False,
                'data': <response data>,
                'message': 'ok' or error message,
                'code': HTTP status code
            }
        """
        # Ensure we have valid JWT token
        if not self._ensure_authenticated():
            return {
                'success': False,
                'data': None,
                'message': 'Authentication failed',
                'code': 401
            }
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        
        try:
            logger.info(f"📡 Calling: {method} {url}")
            if params:
                logger.debug(f"   Params: {params}")
            if self.auth_enabled:
                logger.debug(f"   Auth: Bearer token (length: {len(self.jwt_token) if self.jwt_token else 0})")
            
            # Make HTTP request
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=self.timeout
            )
            
            # ============================================
            # HANDLE 401 - Token expired or invalid
            # ============================================
            
            if response.status_code == 401 and retry_auth:
                logger.warning("⚠️  401 Unauthorized - Token may be expired, re-authenticating...")
                
                # Clear token and login again
                self.jwt_token = None
                self.token_expires_at = None
                
                if self._login():
                    logger.info("🔄 Re-authenticated, retrying request...")
                    # Retry request with new token (but don't retry auth again)
                    return self._make_request(method, endpoint, params, json_data, retry_count, retry_auth=False)
                else:
                    return {
                        'success': False,
                        'data': None,
                        'message': 'Authentication failed after retry',
                        'code': 401
                    }
            
            # ============================================
            # RESPONSE HANDLING (Based on Java HttpResult)
            # ============================================
            
            # Java returns this format:
            # {
            #   "code": 200,      <- Internal status (200=success, 500=error)
            #   "msg": "ok",      <- Message
            #   "data": {...},    <- Actual response data
            #   "time": 1234567890
            # }
            
            if response.status_code == 200:
                result = response.json()
                
                # Check internal code from Java
                internal_code = result.get('code', 200)
                
                if internal_code == 200:
                    # SUCCESS CASE
                    logger.info(f"✅ Success: {url}")
                    return {
                        'success': True,
                        'data': result.get('data'),
                        'message': result.get('msg', 'ok'),
                        'code': 200
                    }
                else:
                    # ERROR CASE (Java returned error)
                    error_msg = result.get('msg', 'Unknown error')
                    logger.error(f"❌ Java API error: {error_msg} (code: {internal_code})")
                    return {
                        'success': False,
                        'data': None,
                        'message': error_msg,
                        'code': internal_code
                    }
            
            # HTTP ERROR (not 200)
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('msg', response.text)
                    error_msg = f"{error_msg}: {error_detail}"
                except:
                    error_msg = f"{error_msg}: {response.text[:100]}"
                
                logger.error(f"❌ HTTP error: {error_msg}")
                
                # RETRY LOGIC for server errors (500, 502, 503)
                if response.status_code >= 500 and retry_count < self.max_retries:
                    retry_count += 1
                    logger.warning(f"🔄 Retrying... (attempt {retry_count}/{self.max_retries})")
                    return self._make_request(method, endpoint, params, json_data, retry_count, retry_auth)
                
                return {
                    'success': False,
                    'data': None,
                    'message': error_msg,
                    'code': response.status_code
                }
        
        # ============================================
        # ERROR HANDLING
        # ============================================
        
        except requests.Timeout:
            # Request took too long
            error_msg = f"Timeout after {self.timeout[1]} seconds"
            logger.error(f"⏱️  {error_msg}")
            
            # Retry on timeout
            if retry_count < self.max_retries:
                retry_count += 1
                logger.warning(f"🔄 Retrying... (attempt {retry_count}/{self.max_retries})")
                return self._make_request(method, endpoint, params, json_data, retry_count, retry_auth)
            
            return {
                'success': False,
                'data': None,
                'message': error_msg,
                'code': 504  # Gateway Timeout
            }
        
        except requests.ConnectionError:
            # Cannot connect to Java API
            error_msg = f"Cannot connect to {self.base_url}"
            logger.error(f"🔌 {error_msg}")
            return {
                'success': False,
                'data': None,
                'message': error_msg,
                'code': 503  # Service Unavailable
            }
        
        except Exception as e:
            # Any other error
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"💥 {error_msg}")
            return {
                'success': False,
                'data': None,
                'message': error_msg,
                'code': 500  # Internal Server Error
            }
    
    # ==========================================
    # PUBLIC METHODS - Call these from your code
    # ==========================================
    
    def send_command(self, device_name: str, command: str) -> Dict[str, Any]:
        """
        Send raw MQTT command to device
        
        Args:
            device_name: Device ID (e.g., "CG001")
            command: JSON command string (e.g., '{"cmd":"check"}')
        
        Returns:
            {
                'success': True/False,
                'data': None,  # No data returned for send
                'message': 'ok' or error message,
                'code': 200 or error code
            }
        
        Example:
            result = service.send_command("CG001", '{"cmd":"check"}')
            if result['success']:
                print("Command sent!")
        
        Request Format (Query Parameters):
            GET /send?deviceName=CG001&data={"cmd":"check"}
        """
        return self._make_request(
            method='GET',
            endpoint='/send',
            params={
                'deviceName': device_name,
                'data': command
            }
        )
    
    def check_device(self, device_name: str) -> Dict[str, Any]:
        """
        Check device powerbank status (non-empty slots only)
        
        Args:
            device_name: Device ID (e.g., "CG001")
        
        Returns:
            {
                'success': True/False,
                'data': [  # List of powerbanks in device
                    {
                        'index': 1,              # Slot number
                        'status': 1,             # 1=normal, 2=error, etc.
                        'snAsString': '12345678', # Powerbank serial number
                        'power': 85,             # Battery % (0-100)
                        'temp': 25,              # Temperature
                        'voltage': 4200,         # Voltage in mV
                        'current': 500,          # Current in mA
                        'area': 1,               # Area code
                        'message': 'OK'          # Status message
                    }
                ],
                'message': 'ok',
                'code': 200
            }
        
        Example:
            result = service.check_device("CG001")
            if result['success']:
                for powerbank in result['data']:
                    print(f"Slot {powerbank['index']}: {powerbank['power']}%")
        
        Request Format (Query Parameters):
            GET /check?deviceName=CG001
        
        Common Errors:
            - "Device is Offline": Device not connected to MQTT
            - "Request Time Out": Device didn't respond in 10 seconds
        """
        return self._make_request(
            method='GET',
            endpoint='/check',
            params={'deviceName': device_name}
        )
    
    def check_all_devices(self, device_name: str) -> Dict[str, Any]:
        """
        Check ALL slots in device (includes empty slots)
        
        Args:
            device_name: Device ID
        
        Returns:
            Same format as check_device() but includes empty slots
            (slots with status=0 mean no powerbank present)
        
        Example:
            result = service.check_all_devices("CG001")
            if result['success']:
                total_slots = len(result['data'])
                empty_slots = sum(1 for p in result['data'] if p['status'] == 0)
                print(f"Total: {total_slots}, Empty: {empty_slots}")
        
        Request Format (Query Parameters):
            GET /check_all?deviceName=CG001
        """
        return self._make_request(
            method='GET',
            endpoint='/check_all',
            params={'deviceName': device_name}
        )
    
    def popup_powerbank(
        self, 
        device_name: str, 
        min_power: int = 20
    ) -> Dict[str, Any]:
        """
        Pop (eject) a powerbank from device
        
        Args:
            device_name: Device ID
            min_power: Minimum battery % required (default: 20)
        
        Returns:
            {
                'success': True/False,
                'data': '12345678',  # Serial number of popped powerbank
                'message': 'ok',
                'code': 200
            }
        
        Example:
            # Pop powerbank with at least 50% battery
            result = service.popup_powerbank("CG001", min_power=50)
            if result['success']:
                sn = result['data']
                print(f"Popped powerbank: {sn}")
        
        Request Format (Query Parameters):
            GET /popup_random?deviceName=CG001&minPower=20
        
        Common Errors:
            - "Device is Offline": Device not connected
            - "NO Powerbank": No powerbank meets criteria (battery < minPower)
            - "Popup Error:...": Hardware failure (motor/spring issue)
            - "Request Time Out": Device didn't respond in 15 seconds
        
        How it works:
            1. Checks all powerbanks in device
            2. Filters: status=1 (normal) AND battery >= minPower
            3. Randomly picks one
            4. Sends popup command to device
            5. Returns powerbank serial number
        """
        return self._make_request(
            method='GET',
            endpoint='/popup_random',
            params={
                'deviceName': device_name,
                'minPower': min_power
            }
        )
    
    def create_device(
        self, 
        device_name: str, 
        imei: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register new device with EMQX and database
        
        Args:
            device_name: Unique device ID (e.g., "CG001")
            imei: Device IMEI number (optional)
        
        Returns:
            {
                'success': True/False,
                'data': {
                    'deviceName': 'CG001',
                    'password': 'A8kL3mP9xQ2vW7nZ',  # Auto-generated
                    'username': 'powerbank&CG001',
                    'host': 'nf0e7f22.ala.dedicated.aws.emqxcloud.com',
                    'port': 1883,
                    'imei': '123456789012345',
                    'emqxRegistered': True,
                    'message': 'Device created successfully...'
                },
                'message': 'ok',
                'code': 200
            }
        
        Example:
            result = service.create_device("CG001", imei="123456789012345")
            if result['success']:
                credentials = result['data']
                print(f"Device registered!")
                print(f"Username: {credentials['username']}")
                print(f"Password: {credentials['password']}")
                # Give these credentials to ESP32 device
        
        Request Format (Query Parameters):
            POST /device/create?deviceName=CG001&imei=123456789012345
        
        Important Notes:
            - Password is auto-generated (16 characters)
            - If device exists, password is updated
            - Username format: "powerbank&{deviceName}"
            - Use credentials to configure ESP32 device
        """
        params = {'deviceName': device_name}
        if imei:
            params['imei'] = imei
        
        return self._make_request(
            method='POST',
            endpoint='/device/create',
            params=params
        )


# ==========================================
# SINGLETON - Use this to get service instance
# ==========================================

_service_instance = None

def get_device_api_service() -> DeviceAPIService:
    """
    Get singleton instance of DeviceAPIService
    
    Usage in your Django views/code:
        from yourapp.services.device_api_service import get_device_api_service
        
        service = get_device_api_service()
        result = service.check_device("CG001")
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = DeviceAPIService()
    return _service_instance
```

---

## 🚀 Step 3: How to Use It

### Example 1: Check Device Status

```python
from yourapp.services.device_api_service import get_device_api_service

# Get service
service = get_device_api_service()

# Check device
result = service.check_device("CG001")

# Handle response
if result['success']:
    powerbanks = result['data']
    
    print(f"Found {len(powerbanks)} powerbanks:")
    for pb in powerbanks:
        print(f"  Slot {pb['index']}: {pb['power']}% battery")
else:
    print(f"Error: {result['message']}")
```

### Example 2: Pop Powerbank

```python
from yourapp.services.device_api_service import get_device_api_service

service = get_device_api_service()

# Pop powerbank with at least 30% battery
result = service.popup_powerbank("CG001", min_power=30)

if result['success']:
    sn = result['data']
    print(f"✅ Popped powerbank: {sn}")
else:
    error = result['message']
    if "Device is Offline" in error:
        print("❌ Device is not connected")
    elif "NO Powerbank" in error:
        print("❌ No powerbank available with 30%+ battery")
    else:
        print(f"❌ Error: {error}")
```

### Example 3: Create New Device

```python
from yourapp.services.device_api_service import get_device_api_service

service = get_device_api_service()

result = service.create_device("CG001", imei="123456789012345")

if result['success']:
    credentials = result['data']
    
    print("✅ Device registered successfully!")
    print(f"Username: {credentials['username']}")
    print(f"Password: {credentials['password']}")
    print(f"MQTT Host: {credentials['host']}:{credentials['port']}")
    
    # TODO: Configure ESP32 device with these credentials
else:
    print(f"❌ Failed: {result['message']}")
```

---

## 📊 Response Format Reference

### Success Response
```python
{
    'success': True,
    'data': <actual data>,  # Varies by endpoint
    'message': 'ok',
    'code': 200
}
```

### Error Response
```python
{
    'success': False,
    'data': None,
    'message': 'Error description',
    'code': 500  # or other error code
}
```

### Powerbank Data Structure (from check/check_all)
```python
{
    'index': 1,              # Slot number (1-based)
    'status': 1,             # 0=empty, 1=normal, 2+=error
    'snAsString': '12345678', # Serial number
    'power': 85,             # Battery % (0-100)
    'temp': 25,              # Temperature °C
    'voltage': 4200,         # Voltage mV
    'current': 500,          # Current mA
    'area': 1,               # Area code
    'message': 'OK',         # Status message
    'softVersion': 10,       # Software version
    'hardVersion': 12        # Hardware version
}
```

---

## 🔍 Request Formats by Endpoint

### 1. Send Command
**Java Endpoint:** `GET /send`  
**Parameters:** Query params  
```
deviceName=CG001&data={"cmd":"check"}
```

### 2. Check Device
**Java Endpoint:** `GET /check`  
**Parameters:** Query params  
```
deviceName=CG001
```

### 3. Check All
**Java Endpoint:** `GET /check_all`  
**Parameters:** Query params  
```
deviceName=CG001
```

### 4. Popup Powerbank
**Java Endpoint:** `GET /popup_random`  
**Parameters:** Query params  
```
deviceName=CG001&minPower=30
```

### 5. Create Device
**Java Endpoint:** `POST /device/create`  
**Parameters:** Query params  
```
deviceName=CG001&imei=123456789012345
```

---

## ❗ Common Errors & Solutions

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| `Device is Offline` | Device not connected to MQTT | Check device power and internet |
| `NO Powerbank` | No powerbank meets criteria | Lower minPower or restock device |
| `Request Time Out` | Device didn't respond | Check device is responsive |
| `Popup Error:0x...` | Hardware failure | Check device motor/spring |
| `Cannot connect to...` | Java API is down | Check Java server is running |
| `Timeout after 30 seconds` | Request took too long | Check network/Java API health |
| `HTTP 500: ...` | Java server error | Check Java API logs |

---

## 🎯 Key Points to Remember

1. **Authentication Flow**: Service auto-logs in on first request and caches JWT token

2. **Token Management**: Token valid for 24 hours, auto-refreshes on 401 error

3. **No MQTT in Django**: Java API handles all MQTT. You just make HTTP calls.

4. **Response Format**: Always check `result['success']` first, then access `result['data']`

5. **Timeouts**: Device commands take 10-15 seconds. Don't use short timeouts.

6. **Retries**: Service auto-retries 2 times on 5xx errors. You don't need to retry.

7. **Error Handling**: Always check `result['success']` and handle `result['message']`

8. **Device Names**: Use consistent device naming (e.g., "CG001", "CG002")

9. **Configuration**: Update `DEVICE_API['BASE_URL']` and credentials for production

10. **Security**: Keep `AUTH_PASSWORD` in `.env`, never commit to git

---

## 🔐 Authentication Flow Diagram

```
First Request:
  Django Service → Check token valid? → NO
                → Login to Java API (POST /api/auth/login)
                → Receive JWT token
                → Cache token (expires in 24h)
                → Make actual request with Bearer token
                → Return response

Subsequent Requests:
  Django Service → Check token valid? → YES
                → Make request with Bearer token
                → Return response

Token Expired (401):
  Django Service → Make request
                → Receive 401 Unauthorized
                → Auto re-login
                → Retry request with new token
                → Return response
```

---

## ✅ Testing Your Setup

### Test 1: Basic Connection
```python
# Test if Java API is reachable and authentication works
from yourapp.services.device_api_service import get_device_api_service

service = get_device_api_service()
print(f"Java API URL: {service.base_url}")
print(f"Auth Enabled: {service.auth_enabled}")

# This will auto-login on first request
result = service.check_device("TEST001")
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")

if service.jwt_token:
    print(f"✅ Authenticated! Token: {service.jwt_token[:20]}...")
```

### Test 2: Authentication Flow
```python
from yourapp.services.device_api_service import get_device_api_service

service = get_device_api_service()

# Force login to test credentials
if service._login():
    print("✅ Login successful!")
    print(f"Token: {service.jwt_token[:30]}...")
    print(f"Expires: {service.token_expires_at}")
else:
    print("❌ Login failed! Check credentials in settings.py")
```

### Test 3: Full Flow
```python
from yourapp.services.device_api_service import get_device_api_service

service = get_device_api_service()

# Test each endpoint
print("1. Testing check_device...")
result = service.check_device("CG001")
print(f"   Result: {result['success']}")

print("2. Testing check_all_devices...")
result = service.check_all_devices("CG001")
print(f"   Result: {result['success']}")

print("3. Testing popup_powerbank...")
result = service.popup_powerbank("CG001", min_power=30)
print(f"   Result: {result['success']}")
```

---

## 🚨 Troubleshooting

### Issue 1: "Authentication failed"
**Cause:** Wrong username/password in settings

**Solution:**
```python
# Check your settings.py or .env
DEVICE_API = {
    'AUTH_USERNAME': 'correct_username',  # Check Java admin user
    'AUTH_PASSWORD': 'correct_password',  # Check Java admin password
}
```

### Issue 2: "401 Unauthorized" on every request
**Cause:** JWT token not being sent or invalid

**Solution:**
```python
# Check if token is being set
service = get_device_api_service()
print(f"Token: {service.jwt_token}")
print(f"Token valid: {service._is_token_valid()}")

# Check headers being sent
headers = service._get_auth_headers()
print(f"Headers: {headers}")
```

### Issue 3: Token expired errors
**Cause:** Service running for >24 hours with same token

**Solution:** Service auto-refreshes on 401, but you can manually clear:
```python
service = get_device_api_service()
service.jwt_token = None  # Force re-login on next request
```

---

**That's It!** You now have a complete, secure service with JWT authentication to control devices from Django. The service automatically:
- ✅ Logs in on first request
- ✅ Caches JWT token (24 hours)
- ✅ Auto-refreshes token on 401
- ✅ Handles retries and errors
- ✅ Secures inter-system communication

---

**Last Updated:** November 5, 2025  
**Version:** 1.0 - Compact Edition
