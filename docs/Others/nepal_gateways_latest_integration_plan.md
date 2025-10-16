# Nepal Gateways Latest Integration Plan - FINAL IMPLEMENTATION
## Complete Implementation Guide Based on Full Codebase Analysis

---

## 🎯 **EXECUTIVE SUMMARY**

After analyzing the complete codebase including the full `api/payments/views.py` file, this plan provides the **FINAL IMPLEMENTATION STRATEGY** for integrating nepal-gateways package with your ChargeGhar PowerBank rental system.

### **Key Findings from Views Analysis**
- **15 View Classes** identified in `views.py`
- **StripeWebhookView** exists and must be removed
- **TopupIntentCreateView** and **VerifyTopupView** need real gateway integration
- **KhaltiWebhookView** and **ESewaWebhookView** exist but need real implementation
- **Environment-based URLs** needed for callback configuration

---

## 📋 **PHASE-BY-PHASE IMPLEMENTATION PLAN**

### **PHASE 1: Environment & Dependencies Setup**
**Duration**: 1-2 hours | **Priority**: CRITICAL

#### 1.1 Update Dependencies
**File**: `pyproject.toml`
```toml
dependencies = [
    # ... existing dependencies ...
    "nepal-gateways>=1.0.0",  # ADD THIS LINE
]
```

#### 1.2 Update Environment Variables
**File**: `.env`
```bash
# REMOVE these Stripe configurations:
# STRIPE_PUBLIC_KEY=pk_test_51234567890abcdef
# STRIPE_SECRET_KEY=sk_test_51234567890abcdef  
# STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef
# STRIPE_BASE_URL=https://api.stripe.com/v1/

# ADD Nepal Gateways Configuration (Environment-based URLs)
# eSewa Configuration
ESEWA_PRODUCT_CODE=EPAYTEST
ESEWA_SECRET_KEY=8gBm/:&EnhH.1/q
ESEWA_SUCCESS_URL=https://${HOST}/api/payments/esewa/success
ESEWA_FAILURE_URL=https://${HOST}/api/payments/esewa/failure
ESEWA_MODE=sandbox

# Khalti Configuration  
KHALTI_LIVE_SECRET_KEY=test_secret_key_f59e8b7c18b4499bb7ba1c56c1e8e8e8
KHALTI_RETURN_URL=https://${HOST}/api/payments/khalti/callback
KHALTI_WEBSITE_URL=https://${HOST}
KHALTI_MODE=sandbox
```

#### 1.3 Update Django Configuration
**File**: `api/config/application.py`
```python
# REMOVE the commented Stripe configuration:
# '''STRIPE_PUBLIC_KEY = getenv("STRIPE_PUBLIC_KEY", "")
# STRIPE_SECRET_KEY = getenv("STRIPE_SECRET_KEY", "")'''

# ADD Nepal Gateways Configuration
NEPAL_GATEWAYS_CONFIG = {
    'esewa': {
        'product_code': getenv('ESEWA_PRODUCT_CODE', 'EPAYTEST'),
        'secret_key': getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q'),
        'success_url': getenv('ESEWA_SUCCESS_URL'),
        'failure_url': getenv('ESEWA_FAILURE_URL'),
        'mode': getenv('ESEWA_MODE', 'sandbox'),
    },
    'khalti': {
        'live_secret_key': getenv('KHALTI_LIVE_SECRET_KEY'),
        'return_url_config': getenv('KHALTI_RETURN_URL'),
        'website_url_config': getenv('KHALTI_WEBSITE_URL'),
        'mode': getenv('KHALTI_MODE', 'sandbox'),
    }
}
```

---

### **PHASE 2: Create Nepal Gateway Service**
**Duration**: 3-4 hours | **Priority**: CRITICAL

#### 2.1 Create Gateway Service Wrapper
**File**: `api/payments/services/nepal_gateway.py` (NEW FILE)

```python
from __future__ import annotations

import logging
from typing import Dict, Any, Optional, Union
from decimal import Decimal
from django.conf import settings
from nepal_gateways import (
    EsewaClient, KhaltiClient, 
    ConfigurationError, InitiationError, 
    VerificationError, InvalidSignatureError
)
from api.common.services.base import ServiceException

logger = logging.getLogger(__name__)

class NepalGatewayService:
    """Service wrapper for nepal-gateways package"""
    
    def __init__(self):
        self.config = getattr(settings, 'NEPAL_GATEWAYS_CONFIG', {})
        self._esewa_client = None
        self._khalti_client = None
    
    @property
    def esewa_client(self) -> EsewaClient:
        """Get or create eSewa client"""
        if self._esewa_client is None:
            try:
                esewa_config = self.config.get('esewa', {})
                self._esewa_client = EsewaClient(config=esewa_config)
            except ConfigurationError as e:
                logger.error(f"eSewa configuration error: {e}")
                raise ServiceException(
                    detail=f"eSewa gateway configuration error: {e}",
                    code="esewa_config_error"
                )
        return self._esewa_client
    
    @property
    def khalti_client(self) -> KhaltiClient:
        """Get or create Khalti client"""
        if self._khalti_client is None:
            try:
                khalti_config = self.config.get('khalti', {})
                self._khalti_client = KhaltiClient(config=khalti_config)
            except ConfigurationError as e:
                logger.error(f"Khalti configuration error: {e}")
                raise ServiceException(
                    detail=f"Khalti gateway configuration error: {e}",
                    code="khalti_config_error"
                )
        return self._khalti_client
    
    def convert_amount_for_gateway(self, amount: Decimal, gateway: str) -> Union[float, int]:
        """Convert amount to gateway-specific format"""
        if gateway == 'esewa':
            return float(amount)  # eSewa accepts NPR as float
        elif gateway == 'khalti':
            return int(amount * 100)  # Khalti requires paisa (NPR * 100)
        else:
            raise ServiceException(
                detail=f"Unknown gateway for amount conversion: {gateway}",
                code="unknown_gateway"
            )
    
    def convert_amount_from_gateway(self, amount: Union[float, int], gateway: str) -> Decimal:
        """Convert amount from gateway-specific format to Decimal"""
        if gateway == 'esewa':
            return Decimal(str(amount))  # eSewa returns NPR
        elif gateway == 'khalti':
            return Decimal(str(amount)) / 100  # Khalti returns paisa
        else:
            raise ServiceException(
                detail=f"Unknown gateway for amount conversion: {gateway}",
                code="unknown_gateway"
            )
    
    def initiate_esewa_payment(
        self, 
        amount: Decimal, 
        order_id: str,
        tax_amount: Decimal = Decimal('0'),
        product_service_charge: Decimal = Decimal('0'),
        product_delivery_charge: Decimal = Decimal('0')
    ) -> Dict[str, Any]:
        """Initiate eSewa payment"""
        try:
            init_response = self.esewa_client.initiate_payment(
                amount=float(amount),
                order_id=order_id,
                tax_amount=float(tax_amount),
                product_service_charge=float(product_service_charge),
                product_delivery_charge=float(product_delivery_charge)
            )
            
            return {
                'success': True,
                'redirect_required': init_response.is_redirect_required,
                'redirect_url': init_response.redirect_url,
                'redirect_method': init_response.redirect_method,  # POST
                'form_fields': init_response.form_fields,
                'payment_instructions': init_response.payment_instructions or {}
            }
            
        except InitiationError as e:
            logger.error(f"eSewa payment initiation failed: {e}")
            raise ServiceException(
                detail=f"eSewa payment initiation failed: {e}",
                code="esewa_initiation_error"
            )
    
    def verify_esewa_payment(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify eSewa payment"""
        try:
            verification = self.esewa_client.verify_payment(
                transaction_data_from_callback=transaction_data
            )
            
            return {
                'success': verification.is_successful,
                'order_id': verification.order_id,
                'transaction_id': verification.transaction_id,
                'status_code': verification.status_code,
                'amount': self.convert_amount_from_gateway(verification.verified_amount, 'esewa'),
                'gateway_response': verification.raw_response
            }
            
        except InvalidSignatureError as e:
            logger.error(f"eSewa signature validation failed: {e}")
            raise ServiceException(
                detail="eSewa payment signature validation failed",
                code="esewa_invalid_signature"
            )
        except VerificationError as e:
            logger.error(f"eSewa payment verification failed: {e}")
            raise ServiceException(
                detail=f"eSewa payment verification failed: {e}",
                code="esewa_verification_error"
            )
    
    def initiate_khalti_payment(
        self,
        amount: Decimal,
        order_id: str,
        description: str,
        customer_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Initiate Khalti payment"""
        try:
            khalti_amount_paisa = self.convert_amount_for_gateway(amount, 'khalti')
            
            init_response = self.khalti_client.initiate_payment(
                amount=khalti_amount_paisa,
                order_id=order_id,
                description=description,
                customer_info=customer_info or {}
            )
            
            return {
                'success': True,
                'redirect_required': init_response.is_redirect_required,
                'redirect_url': init_response.redirect_url,
                'redirect_method': init_response.redirect_method,  # GET
                'form_fields': init_response.form_fields,  # None for Khalti
                'payment_instructions': init_response.payment_instructions
            }
            
        except InitiationError as e:
            logger.error(f"Khalti payment initiation failed: {e}")
            raise ServiceException(
                detail=f"Khalti payment initiation failed: {e}",
                code="khalti_initiation_error"
            )
    
    def verify_khalti_payment(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Khalti payment"""
        try:
            verification = self.khalti_client.verify_payment(
                transaction_data_from_callback=transaction_data
            )
            
            return {
                'success': verification.is_successful,
                'order_id': verification.order_id,  # PIDX for Khalti
                'transaction_id': verification.transaction_id,
                'status_code': verification.status_code,
                'amount': self.convert_amount_from_gateway(verification.verified_amount, 'khalti'),
                'gateway_response': verification.raw_response
            }
            
        except VerificationError as e:
            logger.error(f"Khalti payment verification failed: {e}")
            raise ServiceException(
                detail=f"Khalti payment verification failed: {e}",
                code="khalti_verification_error"
            )
```

#### 2.2 Update Services __init__.py
**File**: `api/payments/services/__init__.py`

```python
"""
Payment Services Package

This package contains all payment-related service classes split by functionality.
"""

from .wallet import WalletService
from .payment_calculation import PaymentCalculationService
from .payment_intent import PaymentIntentService
from .rental_payment import RentalPaymentService
from .refund import RefundService
from .transaction import TransactionService
from .nepal_gateway import NepalGatewayService  # ADD THIS LINE

__all__ = [
    'WalletService',
    'PaymentCalculationService',
    'PaymentIntentService',
    'RentalPaymentService',
    'RefundService',
    'TransactionService',
    'NepalGatewayService',  # ADD THIS LINE
]
```

---

### **PHASE 3: Update PaymentIntentService**
**Duration**: 2-3 hours | **Priority**: CRITICAL

#### 3.1 Update PaymentIntentService
**File**: `api/payments/services/payment_intent.py`

**REPLACE** the existing `_generate_payment_url()` method (lines 67-72) with:

```python
def _initiate_gateway_payment(self, intent: PaymentIntent, payment_method: PaymentMethod, gateway_service: NepalGatewayService) -> Dict[str, Any]:
    """Initiate payment with actual gateway"""
    try:
        if payment_method.gateway == 'esewa':
            return gateway_service.initiate_esewa_payment(
                amount=intent.amount,
                order_id=intent.intent_id,
                tax_amount=Decimal('0'),
                product_service_charge=Decimal('0'),
                product_delivery_charge=Decimal('0')
            )
        elif payment_method.gateway == 'khalti':
            return gateway_service.initiate_khalti_payment(
                amount=intent.amount,  # Will be converted to paisa internally
                order_id=intent.intent_id,
                description=f"Wallet top-up - NPR {intent.amount}",
                customer_info={
                    'name': getattr(intent.user, 'username', 'User'),
                    'email': getattr(intent.user, 'email', '')
                }
            )
        else:
            raise ServiceException(
                detail=f"Unsupported gateway: {payment_method.gateway}",
                code="unsupported_gateway"
            )
    except Exception as e:
        self.log_error(f"Gateway payment initiation failed: {str(e)}")
        raise
```

**UPDATE** the `create_topup_intent()` method to use real gateway integration:

```python
# ADD import at the top
from api.payments.services.nepal_gateway import NepalGatewayService

# REPLACE the gateway URL generation section with:
# Generate payment URL using nepal-gateways
gateway_service = NepalGatewayService()
gateway_result = self._initiate_gateway_payment(intent, payment_method, gateway_service)

intent.gateway_url = gateway_result.get('redirect_url')
intent.intent_metadata.update({
    'gateway_result': gateway_result,
    'gateway': payment_method.gateway
})
intent.save(update_fields=['gateway_url', 'intent_metadata'])
```

**UPDATE** the `_verify_with_gateway()` method:

```python
def _verify_with_gateway(self, intent: PaymentIntent, gateway_reference: str, gateway_service: NepalGatewayService) -> Dict[str, Any]:
    """Verify payment with actual gateway"""
    try:
        gateway = intent.intent_metadata.get('gateway')
        if not gateway:
            raise ServiceException(
                detail="Gateway information not found in payment intent",
                code="gateway_info_missing"
            )
        
        if gateway == 'esewa':
            # For eSewa, gateway_reference should contain the callback data
            if isinstance(gateway_reference, str):
                transaction_data = {'data': gateway_reference}
            else:
                transaction_data = gateway_reference
            return gateway_service.verify_esewa_payment(transaction_data)
            
        elif gateway == 'khalti':
            # For Khalti, gateway_reference should contain query parameters
            if isinstance(gateway_reference, str):
                transaction_data = {'pidx': gateway_reference}
            else:
                transaction_data = gateway_reference
            return gateway_service.verify_khalti_payment(transaction_data)
        else:
            raise ServiceException(
                detail=f"Unsupported gateway for verification: {gateway}",
                code="unsupported_gateway_verification"
            )
    except Exception as e:
        self.log_error(f"Gateway payment verification failed: {str(e)}")
        raise
```

---

### **PHASE 4: Update Views Layer**
**Duration**: 2-3 hours | **Priority**: HIGH

#### 4.1 Remove StripeWebhookView
**File**: `api/payments/views.py`

**REMOVE** the entire `StripeWebhookView` class (lines 587-620):

```python
# DELETE THIS ENTIRE CLASS:
@router.register(r"payments/webhooks/stripe", name="payment-webhook-stripe")
@extend_schema(
    tags=["Payments"],
    summary="Stripe Webhook",
    description="Handle Stripe payment gateway webhooks"
)
class StripeWebhookView(GenericAPIView):
    # ... DELETE ALL OF THIS
```

#### 4.2 Update TopupIntentCreateView
**File**: `api/payments/views.py`

The `TopupIntentCreateView` (lines 201-238) is already correctly structured and will work with the updated `PaymentIntentService`. No changes needed.

#### 4.3 Update VerifyTopupView  
**File**: `api/payments/views.py`

The `VerifyTopupView` (lines 239-274) is already correctly structured and will work with the updated `PaymentIntentService`. No changes needed.

#### 4.4 Create Callback Views
**File**: `api/payments/views/callbacks.py` (NEW FILE)

```python
from __future__ import annotations

from typing import TYPE_CHECKING
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import redirect
from django.http import HttpResponse
from api.common.routers import CustomViewRouter
from api.payments.services import PaymentIntentService

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

@router.register(r"payments/esewa/success", name="payment-esewa-success")
class ESewaSuccessCallbackView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        """Handle eSewa success callback"""
        try:
            # eSewa sends Base64 encoded JSON in 'data' query parameter
            data = request.GET.get('data')
            if not data:
                return HttpResponse("Invalid eSewa callback - missing data parameter", status=400)
            
            # For web redirect - extract intent_id and redirect to frontend
            return redirect(f"https://{request.get_host()}/payment/success?gateway=esewa&data={data}")
            
        except Exception as e:
            return redirect(f"https://{request.get_host()}/payment/error?message={str(e)}")

@router.register(r"payments/esewa/failure", name="payment-esewa-failure")
class ESewaFailureCallbackView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        """Handle eSewa failure callback"""
        try:
            error_message = request.GET.get('message', 'eSewa payment failed')
            return redirect(f"https://{request.get_host()}/payment/failure?gateway=esewa&message={error_message}")
        except Exception as e:
            return redirect(f"https://{request.get_host()}/payment/error?message={str(e)}")

@router.register(r"payments/khalti/callback", name="payment-khalti-callback")
class KhaltiCallbackView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request: Request) -> Response:
        """Handle Khalti return callback"""
        try:
            # Khalti sends query parameters: pidx, status, txnId, etc.
            pidx = request.GET.get('pidx')
            status_param = request.GET.get('status')
            
            if not pidx:
                return redirect(f"https://{request.get_host()}/payment/error?message=Invalid Khalti callback")
            
            # For web redirect - pass parameters to frontend
            return redirect(f"https://{request.get_host()}/payment/success?gateway=khalti&pidx={pidx}&status={status_param}")
            
        except Exception as e:
            return redirect(f"https://{request.get_host()}/payment/error?message={str(e)}")

# API endpoint for mobile apps to verify payments
@router.register(r"payments/verify-callback", name="payment-verify-callback")
class VerifyCallbackView(GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request: Request) -> Response:
        """API endpoint for mobile apps to verify payment status"""
        try:
            gateway = request.data.get('gateway')
            intent_id = request.data.get('intent_id')
            callback_data = request.data.get('callback_data', {})
            
            if not gateway or not intent_id:
                return Response(
                    {'error': 'Gateway and intent_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = PaymentIntentService()
            result = service.verify_topup_payment(
                intent_id=intent_id,
                gateway_reference=callback_data
            )
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f'Payment verification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

#### 4.5 Update URLs Configuration
**File**: `api/payments/urls.py`

```python
from __future__ import annotations

from django.urls import path, include
from api.payments.views import router
from api.payments.views.callbacks import router as callback_router  # ADD THIS

urlpatterns = [
    path("", include(router.urls)),
    path("", include(callback_router.urls)),  # ADD THIS
]
```

---

### **PHASE 5: Clean Up Stripe References**
**Duration**: 1-2 hours | **Priority**: MEDIUM

#### 5.1 Clean Tasks Layer
**File**: `api/payments/tasks.py`

**REMOVE** these functions and references:
- `_process_stripe_webhook()` function
- `_process_stripe_refund()` function  
- Stripe case in `_extract_intent_id()` (lines 130-139)

**UPDATE** `_extract_intent_id()` method:
```python
def _extract_intent_id(self, payload: Dict[str, Any], gateway: str) -> str:
    """Extract intent ID from gateway payload"""
    if gateway == 'khalti':
        return payload.get('merchant_reference') or payload.get('order_id')
    elif gateway == 'esewa':
        return payload.get('product_code') or payload.get('reference')
    else:
        raise ValueError(f"Unknown gateway: {gateway}")
```

#### 5.2 Clean Services Layer
**File**: `api/payments/services/refund.py`

**UPDATE** gateway validation (around line 155):
```python
# Additional gateway-specific validation
gateway = transaction.payment_method.gateway
if gateway not in ['khalti', 'esewa']:  # REMOVE 'stripe'
    raise ServiceException(
        detail=f"Unsupported payment gateway: {gateway}",
        code="unsupported_gateway"
    )
```

#### 5.3 Clean Models Layer
**File**: `api/payments/models.py`

**UPDATE** comment (line 152):
```python
gateway = models.CharField(max_length=255)  # khalti, esewa
```

---

### **PHASE 6: Database Migration**
**Duration**: 1 hour | **Priority**: MEDIUM

#### 6.1 Database Migration Script
**File**: `docs/database_migration.sql`

```sql
-- Remove Stripe payment methods
DELETE FROM payment_methods WHERE gateway = 'stripe';

-- Clean up any Stripe webhook records
DELETE FROM payment_webhooks WHERE gateway = 'stripe';

-- Update eSewa payment method (if exists)
UPDATE payment_methods 
SET configuration = jsonb_build_object(
    'use_env_config', true,
    'env_prefix', 'ESEWA'
)
WHERE gateway = 'esewa';

-- Update Khalti payment method (if exists)
UPDATE payment_methods 
SET configuration = jsonb_build_object(
    'use_env_config', true,
    'env_prefix', 'KHALTI'
)
WHERE gateway = 'khalti';

-- Insert default payment methods if they don't exist
INSERT INTO payment_methods (id, name, gateway, is_active, min_amount, max_amount, supported_currencies, configuration, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'eSewa',
    'esewa',
    true,
    50.00,
    50000.00,
    '["NPR"]'::jsonb,
    jsonb_build_object('use_env_config', true, 'env_prefix', 'ESEWA'),
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM payment_methods WHERE gateway = 'esewa');

INSERT INTO payment_methods (id, name, gateway, is_active, min_amount, max_amount, supported_currencies, configuration, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'Khalti',
    'khalti',
    true,
    10.00,
    100000.00,
    '["NPR"]'::jsonb,
    jsonb_build_object('use_env_config', true, 'env_prefix', 'KHALTI'),
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM payment_methods WHERE gateway = 'khalti');
```

---

## 🧪 **TESTING STRATEGY**

### **Phase 1: Configuration Testing**
```bash
# Test environment setup
python manage.py shell
>>> from django.conf import settings
>>> settings.NEPAL_GATEWAYS_CONFIG
>>> # Should show eSewa and Khalti configurations

# Test service initialization
>>> from api.payments.services.nepal_gateway import NepalGatewayService
>>> service = NepalGatewayService()
>>> esewa_client = service.esewa_client  # Should not raise errors
>>> khalti_client = service.khalti_client  # Should not raise errors
```

### **Phase 2: Amount Conversion Testing**
```python
# Test amount conversion
from decimal import Decimal
service = NepalGatewayService()

# Test eSewa (NPR)
esewa_amount = service.convert_amount_for_gateway(Decimal('100.00'), 'esewa')
assert esewa_amount == 100.00 and isinstance(esewa_amount, float)

# Test Khalti (Paisa)
khalti_amount = service.convert_amount_for_gateway(Decimal('100.00'), 'khalti')
assert khalti_amount == 10000 and isinstance(khalti_amount, int)
```

### **Phase 3: Payment Flow Testing**
```bash
# Test payment intent creation
curl -X POST "http://localhost:8010/api/payments/wallet/topup-intent" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "100.00", "payment_method_id": "ESEWA_METHOD_ID"}'

# Expected: Should return redirect_url and form_fields for eSewa
# Expected: Should return redirect_url (no form_fields) for Khalti
```

---

## ✅ **IMPLEMENTATION CHECKLIST**

### **Phase 1: Environment & Dependencies** 
- [ ] Add `nepal-gateways>=1.0.0` to `pyproject.toml`
- [ ] Remove Stripe environment variables from `.env`
- [ ] Add Nepal Gateways environment variables to `.env`
- [ ] Add `NEPAL_GATEWAYS_CONFIG` to `api/config/application.py`

### **Phase 2: Service Integration**
- [ ] Create `api/payments/services/nepal_gateway.py`
- [ ] Update `api/payments/services/__init__.py`
- [ ] Update `api/payments/services/payment_intent.py`
- [ ] Test service initialization and amount conversion

### **Phase 3: Views Updates**
- [ ] Remove `StripeWebhookView` from `api/payments/views.py`
- [ ] Create `api/payments/views/callbacks.py`
- [ ] Update `api/payments/urls.py`
- [ ] Test callback endpoints

### **Phase 4: Cleanup**
- [ ] Clean Stripe references from `api/payments/tasks.py`
- [ ] Update gateway validation in `api/payments/services/refund.py`
- [ ] Update comments in `api/payments/models.py`
- [ ] Verify no Stripe references remain

### **Phase 5: Database**
- [ ] Run database migration script
- [ ] Verify PaymentMethod records
- [ ] Test payment method API endpoint

### **Phase 6: Final Testing**
- [ ] Test complete payment flow for eSewa
- [ ] Test complete payment flow for Khalti
- [ ] Test callback handling
- [ ] Test error scenarios
- [ ] Performance testing

---

## 🚨 **CRITICAL SUCCESS FACTORS**

### **1. Environment Variables Must Use Dynamic URLs**
```bash
# CORRECT
ESEWA_SUCCESS_URL=https://${HOST}/api/payments/esewa/success

# WRONG  
ESEWA_SUCCESS_URL=https://main.chargeghar.com/api/payments/esewa/success
```

### **2. Amount Conversion is Critical for Khalti**
```python
# Khalti REQUIRES paisa conversion
khalti_amount = int(amount * 100)  # NPR 100.00 → 10000 paisa
```

### **3. Callback Format Differences**
```python
# eSewa: {"data": "base64_encoded_json"}
# Khalti: {"pidx": "...", "status": "...", "txnId": "..."}
```

### **4. PaymentMethod Integration**
```python
# Must work with existing PaymentMethod.configuration field
# Support both environment-based and database-stored configs
```

---

## 🎯 **FINAL VERIFICATION**

After implementation, verify:

1. **✅ No Stripe References**: `grep -r "stripe\|Stripe" api/ --include="*.py"` returns no results
2. **✅ Real Gateway Integration**: Payment intents return actual gateway URLs
3. **✅ Amount Conversion**: Khalti amounts properly converted to paisa
4. **✅ Callback Handling**: Both eSewa and Khalti callbacks work
5. **✅ Environment Configuration**: URLs use `${HOST}` variable
6. **✅ Database Clean**: No Stripe payment methods exist

---

**This plan is now COMPLETE and IMPLEMENTATION READY with all gaps addressed and environment-based configuration properly implemented.**