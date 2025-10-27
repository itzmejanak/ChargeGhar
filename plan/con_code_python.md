# ChargeGhar Integration - Django/Python Implementation

## 📦 Project Structure
```
main_chargeghar/
├── api/
│   ├── stations/
│   │   ├── views/
│   │   │   ├── __init__.py              [MODIFY] - Add internal routes
│   │   │   ├── internal_views.py        [NEW] - IoT system integration endpoints
│   │   │   └── ...existing views...
│   │   ├── services/
│   │   │   ├── __init__.py              [MODIFY] - Add internal services
│   │   │   ├── utils/
│   │   │   │   └── sign_chargeghar_main.py  [NEW] - Signature utilities
│   │   │   ├── station_sync_service.py  [NEW] - Data synchronization logic
│   │   │   └── ...existing services...
│   │   ├── serializers.py
│   │   ├── models.py
│   │   └── urls.py                      
│   ├── rentals/
│   │   └── ...existing rental logic...
│   └── users/
│       └── ...existing user logic...
└── main_app/
    ├── settings.py                      [MODIFY] - Add IoT integration settings
    └── middleware.py                    [NEW] - Signature validation middleware
```

---

## 🔐 1. Signature Utility

**File**: `api/stations/services/utils/sign_chargeghar_main.py`

```python
"""
Signature generation and validation for IoT system integration
Uses HMAC-SHA256 algorithm matching Java implementation
"""

import hmac
import hashlib
import base64
import time
from typing import Tuple
from django.conf import settings


class SignChargeGharMain:
    """
    HMAC-SHA256 signature utilities for ChargeGhar IoT integration
    """
    
    def __init__(self, secret_key: str = None):
        """
        Initialize with secret key
        
        Args:
            secret_key: Shared secret for HMAC. If None, uses Django settings
        """
        self.secret_key = secret_key or settings.IOT_SYSTEM_SIGNATURE_SECRET
        
        if not self.secret_key:
            raise ValueError("Signature secret key not configured in settings")
    
    def generate_signature(self, payload: str, timestamp: int) -> str:
        """
        Generate HMAC-SHA256 signature for request
        
        Args:
            payload: JSON request body as string
            timestamp: Unix timestamp in seconds
            
        Returns:
            Base64 encoded signature string
        """
        message = f"{payload}{timestamp}"
        
        signature = hmac.new(
            key=self.secret_key.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def validate_signature(
        self, 
        payload: str, 
        timestamp: int, 
        received_signature: str,
        time_tolerance: int = 300  # 5 minutes
    ) -> Tuple[bool, str]:
        """
        Validate signature from request
        
        Args:
            payload: JSON request body as string
            timestamp: Timestamp from request header
            received_signature: Signature from X-Signature header
            time_tolerance: Maximum age of request in seconds (default 300s = 5min)
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check timestamp freshness
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)
        
        if time_diff > time_tolerance:
            return False, f"Request timestamp too old ({time_diff}s > {time_tolerance}s allowed)"
        
        # Compute expected signature
        try:
            expected_signature = self.generate_signature(payload, timestamp)
        except Exception as e:
            return False, f"Signature generation error: {str(e)}"
        
        # Compare signatures (timing-safe comparison)
        if not hmac.compare_digest(expected_signature, received_signature):
            return False, "Signature mismatch"
        
        return True, ""
    
    @staticmethod
    def get_current_timestamp() -> int:
        """Get current Unix timestamp in seconds"""
        return int(time.time())


# Singleton instance
_signature_util = None


def get_signature_util() -> SignChargeGharMain:
    """Get singleton signature utility instance"""
    global _signature_util
    if _signature_util is None:
        _signature_util = SignChargeGharMain()
    return _signature_util
```

---

## 🛡️ 2. Signature Validation Middleware

**File**: `main_app/middleware.py`

```python
"""
Middleware for validating IoT system request signatures
"""

import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from api.stations.services.utils.sign_chargeghar_main import get_signature_util


class IoTSignatureValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate HMAC signatures on internal IoT API endpoints
    """
    
    # Endpoints that require signature validation
    PROTECTED_PATHS = [
        '/api/internal/stations/data',
    ]
    
    def process_request(self, request):
        """
        Validate signature before processing request
        """
        # Check if this endpoint requires validation
        if not any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            return None
        
        # Get signature and timestamp from headers
        signature = request.META.get('HTTP_X_SIGNATURE')
        timestamp_str = request.META.get('HTTP_X_TIMESTAMP')
        
        if not signature or not timestamp_str:
            return JsonResponse({
                'success': False,
                'message': 'Missing signature or timestamp headers',
                'error': 'MISSING_HEADERS'
            }, status=403)
        
        # Parse timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid timestamp format',
                'error': 'INVALID_TIMESTAMP'
            }, status=400)
        
        # Get request body
        try:
            if request.content_type == 'application/json':
                payload = request.body.decode('utf-8')
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Content-Type must be application/json',
                    'error': 'INVALID_CONTENT_TYPE'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error reading request body: {str(e)}',
                'error': 'BODY_READ_ERROR'
            }, status=400)
        
        # Validate signature
        signature_util = get_signature_util()
        is_valid, error_message = signature_util.validate_signature(
            payload=payload,
            timestamp=timestamp,
            received_signature=signature
        )
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'message': f'Signature validation failed: {error_message}',
                'error': 'INVALID_SIGNATURE'
            }, status=403)
        
        # Signature valid, continue processing
        return None
```

---

## 📡 3. Internal API Views

**File**: `api/stations/views/internal_views.py`

```python
"""
Internal API views for IoT system integration
Endpoints for receiving device data from Java IoT management system
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.utils import timezone
import logging

from api.stations.services.station_sync_service import StationSyncService

logger = logging.getLogger(__name__)


class StationDataInternalView(APIView):
    """
    Internal endpoint for receiving station data from IoT system
    
    POST /api/internal/stations/data
    
    Handles two types of data:
    - type=full: Complete station synchronization (device upload)
    - type=returned: PowerBank return event notification
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        """
        Process incoming station data from IoT system
        """
        try:
            data = request.data
            data_type = data.get('type')
            
            logger.info(f"Received IoT data sync request: type={data_type}")
            logger.debug(f"Request data: {data}")
            
            if data_type == 'full':
                return self._handle_full_sync(data)
            elif data_type == 'returned':
                return self._handle_return_event(data)
            else:
                return Response({
                    'success': False,
                    'message': f'Invalid data type: {data_type}',
                    'error': 'INVALID_TYPE'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Error processing IoT data: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Internal server error: {str(e)}',
                'error': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_full_sync(self, data):
        """
        Handle full station synchronization
        Updates Station, StationSlot, and PowerBank records
        """
        try:
            service = StationSyncService()
            
            with transaction.atomic():
                result = service.sync_station_data(data)
            
            logger.info(f"Station sync successful: {result}")
            
            return Response({
                'success': True,
                'message': 'Station data updated successfully',
                'data': result
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            logger.warning(f"Validation error in full sync: {str(e)}")
            return Response({
                'success': False,
                'message': str(e),
                'error': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in full sync: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'error': 'SYNC_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_return_event(self, data):
        """
        Handle PowerBank return event notification
        Updates Rental status and PowerBank location
        """
        try:
            service = StationSyncService()
            
            with transaction.atomic():
                result = service.process_return_event(data)
            
            logger.info(f"Return event processed: {result}")
            
            return Response({
                'success': True,
                'message': 'Return processed successfully',
                'data': result
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            logger.warning(f"Validation error in return event: {str(e)}")
            return Response({
                'success': False,
                'message': str(e),
                'error': 'VALIDATION_ERROR'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing return: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Return processing failed: {str(e)}',
                'error': 'RETURN_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 🔧 4. Station Sync Service

**File**: `api/stations/services/station_sync_service.py`

```python
"""
Service for synchronizing station data from IoT system
Handles station, slot, and powerbank updates
"""

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from typing import Dict, Any
import logging

from api.stations.models import Station, StationSlot, PowerBank
from api.rentals.models import Rental

logger = logging.getLogger(__name__)


class StationSyncService:
    """
    Service for processing station data from IoT system
    """
    
    # Status mapping from IoT system to Django models
    SLOT_STATUS_MAP = {
        'AVAILABLE': 'AVAILABLE',
        'OCCUPIED': 'OCCUPIED',
        'ERROR': 'ERROR',
        'MAINTENANCE': 'MAINTENANCE'
    }
    
    POWERBANK_STATUS_MAP = {
        'AVAILABLE': 'AVAILABLE',
        'RENTED': 'RENTED',
        'MAINTENANCE': 'MAINTENANCE',
        'DAMAGED': 'DAMAGED'
    }
    
    STATION_STATUS_MAP = {
        'ONLINE': 'ONLINE',
        'OFFLINE': 'OFFLINE',
        'MAINTENANCE': 'MAINTENANCE'
    }
    
    def sync_station_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync complete station data (full sync)
        
        Args:
            data: Full data payload from IoT system
            
        Returns:
            Summary of sync operation
        """
        device_data = data.get('device', {})
        station_data = data.get('station', {})
        slots_data = data.get('slots', [])
        powerbanks_data = data.get('power_banks', [])
        
        serial_number = device_data.get('serial_number')
        if not serial_number:
            raise ValueError("Missing device serial_number")
        
        # Update or create Station
        station = self._sync_station(device_data, station_data)
        
        # Update StationSlots
        slots_updated = self._sync_slots(station, slots_data)
        
        # Update PowerBanks
        powerbanks_updated = self._sync_powerbanks(station, powerbanks_data)
        
        return {
            'station_id': str(station.id),
            'station_serial': station.serial_number,
            'slots_updated': slots_updated,
            'powerbanks_updated': powerbanks_updated,
            'timestamp': timezone.now().isoformat()
        }
    
    def _sync_station(self, device_data: Dict, station_data: Dict) -> Station:
        """
        Update or create Station record
        """
        serial_number = device_data.get('serial_number')
        imei = device_data.get('imei', serial_number)
        
        # Parse last_heartbeat
        last_heartbeat_str = device_data.get('last_heartbeat')
        last_heartbeat = None
        if last_heartbeat_str:
            last_heartbeat = parse_datetime(last_heartbeat_str)
        
        # Get or create station
        station, created = Station.objects.get_or_create(
            serial_number=serial_number,
            defaults={
                'imei': imei,
                'station_name': f'Station {serial_number[-4:]}',  # Default name
                'latitude': 0.0,  # Will be set manually in admin
                'longitude': 0.0,
                'address': 'Pending',
                'total_slots': station_data.get('total_slots', 0),
                'status': self.STATION_STATUS_MAP.get(device_data.get('status', 'OFFLINE'), 'OFFLINE'),
                'hardware_info': device_data.get('hardware_info', {}),
                'last_heartbeat': last_heartbeat or timezone.now()
            }
        )
        
        if not created:
            # Update existing station
            station.imei = imei
            station.total_slots = station_data.get('total_slots', station.total_slots)
            station.status = self.STATION_STATUS_MAP.get(device_data.get('status', 'OFFLINE'), 'OFFLINE')
            station.hardware_info = device_data.get('hardware_info', {})
            station.last_heartbeat = last_heartbeat or timezone.now()
            station.save()
            
            logger.info(f"Updated station {serial_number}")
        else:
            logger.info(f"Created new station {serial_number}")
        
        return station
    
    def _sync_slots(self, station: Station, slots_data: list) -> int:
        """
        Update or create StationSlot records
        
        Returns:
            Number of slots updated
        """
        slots_updated = 0
        
        for slot_info in slots_data:
            slot_number = slot_info.get('slot_number')
            if not slot_number:
                logger.warning(f"Slot data missing slot_number: {slot_info}")
                continue
            
            slot_status = self.SLOT_STATUS_MAP.get(
                slot_info.get('status', 'AVAILABLE'),
                'AVAILABLE'
            )
            
            battery_level = slot_info.get('battery_level', 0)
            slot_metadata = slot_info.get('slot_metadata', {})
            
            # Get or create slot
            slot, created = StationSlot.objects.get_or_create(
                station=station,
                slot_number=slot_number,
                defaults={
                    'status': slot_status,
                    'battery_level': battery_level,
                    'slot_metadata': slot_metadata
                }
            )
            
            if not created:
                # Update existing slot
                slot.status = slot_status
                slot.battery_level = battery_level
                slot.slot_metadata = slot_metadata
                slot.save()
            
            slots_updated += 1
        
        logger.info(f"Updated {slots_updated} slots for station {station.serial_number}")
        return slots_updated
    
    def _sync_powerbanks(self, station: Station, powerbanks_data: list) -> int:
        """
        Update or create PowerBank records
        
        Returns:
            Number of powerbanks updated
        """
        powerbanks_updated = 0
        
        for pb_info in powerbanks_data:
            pb_serial = pb_info.get('serial_number')
            if not pb_serial:
                logger.warning(f"PowerBank data missing serial_number: {pb_info}")
                continue
            
            pb_status = self.POWERBANK_STATUS_MAP.get(
                pb_info.get('status', 'AVAILABLE'),
                'AVAILABLE'
            )
            
            battery_level = pb_info.get('battery_level', 0)
            current_slot_number = pb_info.get('current_slot')
            hardware_info = pb_info.get('hardware_info', {})
            
            # Find current slot
            current_slot = None
            if current_slot_number:
                try:
                    current_slot = StationSlot.objects.get(
                        station=station,
                        slot_number=current_slot_number
                    )
                except StationSlot.DoesNotExist:
                    logger.warning(f"Slot {current_slot_number} not found for station {station.serial_number}")
            
            # Get or create powerbank
            powerbank, created = PowerBank.objects.get_or_create(
                serial_number=pb_serial,
                defaults={
                    'model': 'Standard',  # Will be set based on capacity mapping
                    'capacity_mah': 10000,  # Default, should be mapped from SN
                    'status': pb_status,
                    'battery_level': battery_level,
                    'hardware_info': hardware_info,
                    'current_station': station,
                    'current_slot': current_slot
                }
            )
            
            if not created:
                # Update existing powerbank
                powerbank.status = pb_status
                powerbank.battery_level = battery_level
                powerbank.hardware_info = hardware_info
                powerbank.current_station = station
                powerbank.current_slot = current_slot
                powerbank.save()
            
            powerbanks_updated += 1
        
        logger.info(f"Updated {powerbanks_updated} powerbanks for station {station.serial_number}")
        return powerbanks_updated
    
    def process_return_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PowerBank return event
        
        Args:
            data: Return event payload from IoT system
            
        Returns:
            Summary of return processing
        """
        device_data = data.get('device', {})
        return_event = data.get('return_event', {})
        
        station_serial = device_data.get('serial_number')
        pb_serial = return_event.get('power_bank_serial')
        slot_number = return_event.get('slot_number')
        battery_level = return_event.get('battery_level', 0)
        
        if not all([station_serial, pb_serial, slot_number]):
            raise ValueError("Missing required fields for return event")
        
        # Find station
        try:
            station = Station.objects.get(serial_number=station_serial)
        except Station.DoesNotExist:
            raise ValueError(f"Station {station_serial} not found")
        
        # Find powerbank
        try:
            powerbank = PowerBank.objects.get(serial_number=pb_serial)
        except PowerBank.DoesNotExist:
            raise ValueError(f"PowerBank {pb_serial} not found")
        
        # Find slot
        try:
            slot = StationSlot.objects.get(station=station, slot_number=slot_number)
        except StationSlot.DoesNotExist:
            raise ValueError(f"Slot {slot_number} not found at station {station_serial}")
        
        # Find active rental for this powerbank
        active_rental = Rental.objects.filter(
            power_bank=powerbank,
            status='ACTIVE'
        ).first()
        
        if not active_rental:
            logger.warning(f"No active rental found for powerbank {pb_serial}")
            # Still update powerbank location
            powerbank.current_station = station
            powerbank.current_slot = slot
            powerbank.battery_level = battery_level
            powerbank.status = 'AVAILABLE'
            powerbank.save()
            
            slot.status = 'OCCUPIED'
            slot.battery_level = battery_level
            slot.save()
            
            return {
                'message': 'PowerBank location updated, no active rental found',
                'power_bank_serial': pb_serial,
                'station_serial': station_serial,
                'slot_number': slot_number
            }
        
        # Process rental return
        from api.rentals.services.rental_service import RentalService
        rental_service = RentalService()
        
        # TODO: Call rental service to complete rental
        # This would normally calculate charges, update payment status, etc.
        # For now, just mark as completed
        
        active_rental.status = 'COMPLETED'
        active_rental.ended_at = timezone.now()
        active_rental.return_station = station
        
        # Check if returned on time
        if active_rental.ended_at <= active_rental.due_at:
            active_rental.is_returned_on_time = True
        
        active_rental.save()
        
        # Update powerbank
        powerbank.current_station = station
        powerbank.current_slot = slot
        powerbank.battery_level = battery_level
        powerbank.status = 'AVAILABLE'
        powerbank.save()
        
        # Update slot
        slot.status = 'OCCUPIED'
        slot.battery_level = battery_level
        slot.save()
        
        logger.info(f"Rental {active_rental.rental_code} completed successfully")
        
        return {
            'rental_id': str(active_rental.id),
            'rental_code': active_rental.rental_code,
            'rental_status': active_rental.status,
            'returned_on_time': active_rental.is_returned_on_time,
            'power_bank_status': powerbank.status,
            'station_serial': station_serial,
            'slot_number': slot_number
        }
```

---

## ⚙️ 6. Django Settings

**File**: `main_app/config/application.py and .env and logging.py`

```python
# ========================================
# IoT System Integration Settings
# ========================================

# Shared secret for request signature validation (MUST match Java config)
IOT_SYSTEM_SIGNATURE_SECRET = env.str(
    'IOT_SYSTEM_SIGNATURE_SECRET',
    default='your-strong-secret-key-min-32-chars-here-change-me'
)

# IP whitelist for IoT system (optional but recommended)
IOT_SYSTEM_ALLOWED_IPS = env.list(
    'IOT_SYSTEM_ALLOWED_IPS',
    default=['127.0.0.1']  # Add api.chargeghar.com IP
)

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Add IoT signature validation middleware
    'main_app.middleware.IoTSignatureValidationMiddleware',  # NEW
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/iot_integration.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'api.stations.views.internal_views': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'api.stations.services.station_sync_service': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

---

## 🧪 7. Testing Code

**File**: `api/stations/tests/test_signature.py`

```python
"""
Unit tests for signature generation and validation
"""

from django.test import TestCase
from api.stations.services.utils.sign_chargeghar_main import SignChargeGharMain


class SignatureTestCase(TestCase):
    """
    Test signature utilities
    """
    
    def setUp(self):
        self.secret_key = "test-secret-key"
        self.sign_util = SignChargeGharMain(secret_key=self.secret_key)
    
    def test_signature_generation(self):
        """Test that signature generation is consistent"""
        payload = '{"test":"data"}'
        timestamp = 1698345600
        
        sig1 = self.sign_util.generate_signature(payload, timestamp)
        sig2 = self.sign_util.generate_signature(payload, timestamp)
        
        self.assertEqual(sig1, sig2)
        self.assertIsInstance(sig1, str)
        self.assertGreater(len(sig1), 0)
    
    def test_signature_validation_success(self):
        """Test that valid signature passes validation"""
        payload = '{"test":"data"}'
        timestamp = int(self.sign_util.get_current_timestamp())
        
        signature = self.sign_util.generate_signature(payload, timestamp)
        is_valid, error = self.sign_util.validate_signature(
            payload, timestamp, signature, time_tolerance=10
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_signature_validation_invalid_signature(self):
        """Test that invalid signature fails validation"""
        payload = '{"test":"data"}'
        timestamp = int(self.sign_util.get_current_timestamp())
        
        is_valid, error = self.sign_util.validate_signature(
            payload, timestamp, "invalid-signature", time_tolerance=10
        )
        
        self.assertFalse(is_valid)
        self.assertIn("mismatch", error.lower())
    
    def test_signature_validation_expired_timestamp(self):
        """Test that old timestamp fails validation"""
        payload = '{"test":"data"}'
        timestamp = 1609459200  # Jan 1, 2021 (very old)
        
        signature = self.sign_util.generate_signature(payload, timestamp)
        is_valid, error = self.sign_util.validate_signature(
            payload, timestamp, signature, time_tolerance=300
        )
        
        self.assertFalse(is_valid)
        self.assertIn("too old", error.lower())
    
    def test_signature_validation_different_payload(self):
        """Test that different payload fails validation"""
        payload1 = '{"test":"data1"}'
        payload2 = '{"test":"data2"}'
        timestamp = int(self.sign_util.get_current_timestamp())
        
        signature = self.sign_util.generate_signature(payload1, timestamp)
        is_valid, error = self.sign_util.validate_signature(
            payload2, timestamp, signature, time_tolerance=10
        )
        
        self.assertFalse(is_valid)
        self.assertIn("mismatch", error.lower())
```

**File**: `api/stations/tests/test_station_sync.py`

```python
"""
Integration tests for station synchronization
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from api.stations.models import Station, StationSlot, PowerBank
import json
import time

User = get_user_model()


class StationSyncTestCase(TestCase):
    """
    Test station data synchronization endpoint
    """
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.admin_user)
    
    def test_full_station_sync(self):
        """Test full station synchronization"""
        # Prepare test data
        payload = {
            "type": "full",
            "timestamp": int(time.time()),
            "device": {
                "serial_number": "TEST12345",
                "imei": "TEST12345",
                "signal_strength": "85",
                "wifi_ssid": "TestNetwork",
                "last_heartbeat": "2025-10-27T14:30:00Z",
                "status": "ONLINE",
                "hardware_info": {
                    "firmware_version": "2.1.5"
                }
            },
            "station": {
                "serial_number": "TEST12345",
                "total_slots": 2
            },
            "slots": [
                {
                    "slot_number": 1,
                    "status": "AVAILABLE",
                    "battery_level": 0,
                    "slot_metadata": {}
                },
                {
                    "slot_number": 2,
                    "status": "OCCUPIED",
                    "battery_level": 85,
                    "power_bank_serial": "PB12345",
                    "slot_metadata": {}
                }
            ],
            "power_banks": [
                {
                    "serial_number": "PB12345",
                    "status": "AVAILABLE",
                    "battery_level": 85,
                    "current_slot": 2,
                    "hardware_info": {
                        "temperature": 30,
                        "voltage": 5000
                    }
                }
            ]
        }
        
        # Send request (Note: Signature validation will be skipped in tests)
        response = self.client.post(
            '/api/internal/stations/data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify database records
        station = Station.objects.get(serial_number="TEST12345")
        self.assertEqual(station.status, 'ONLINE')
        self.assertEqual(station.total_slots, 2)
        
        slots = StationSlot.objects.filter(station=station)
        self.assertEqual(slots.count(), 2)
        
        powerbanks = PowerBank.objects.filter(serial_number="PB12345")
        self.assertEqual(powerbanks.count(), 1)
        self.assertEqual(powerbanks.first().battery_level, 85)
```

---

## 🚀 8. Deployment Steps

### Environment Variables
```bash
# .env file and applyction.py
IOT_SYSTEM_SIGNATURE_SECRET=your-production-secret-key-here-min-32-chars
IOT_SYSTEM_ALLOWED_IPS=213.210.21.113,api.chargeghar.com
```

### Django Migrations
```bash
# No migrations needed if models already exist
# If you modified models:
python manage.py makemigrations
python manage.py migrate
```

### Create Admin User (if needed)
```bash
python manage.py createsuperuser
# Email: janak@powerbank.com
# Password: (set secure password)
```

### Test Locally
```bash
# Run development server
python manage.py runserver

# Test signature generation in Python shell
python manage.py shell
>>> from api.stations.services.utils.sign_chargeghar_main import SignChargeGharMain
>>> util = SignChargeGharMain("test-secret")
>>> util.generate_signature('{"test":"data"}', 1698345600)
```

### Deploy to Production
```bash
# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn main_app.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Or with Docker
docker-compose up -d --build
```

---

## 🔍 9. Monitoring & Debugging

### Check Logs
```bash
# View integration logs
tail -f logs/iot_integration.log

# Filter for specific station
tail -f logs/iot_integration.log | grep "864601069946994"

# Check for errors
tail -f logs/iot_integration.log | grep "ERROR"
```

### Django Admin
- Navigate to `/admin/stations/station/` to view synced stations
- Check `last_heartbeat` field for recent activity
- View `hardware_info` JSON for device details

### Manual API Test
```bash
# Get admin token first
curl -X POST "https://main.chargeghar.com/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"janak@powerbank.com","password":"yourpassword"}'

# Test station sync (requires valid signature)
# Use Python script to generate signature
python -c "
from api.stations.services.utils.sign_chargeghar_main import SignChargeGharMain
import time
payload = '{\"type\":\"full\",\"device\":{\"serial_number\":\"TEST123\"}}'
timestamp = int(time.time())
sig = SignChargeGharMain('your-secret').generate_signature(payload, timestamp)
print(f'Signature: {sig}')
print(f'Timestamp: {timestamp}')
"
```

---

## 📚 Related Files
- **Plan**: `con_plan.md` - System architecture
- **Java Code**: `con_code_java.md` - Java implementation
- **API Specs**: `con_req_res.md` - Request/response formats
