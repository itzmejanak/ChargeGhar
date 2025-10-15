from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING
from drf_spectacular.utils import extend_schema
from rest_framework import status, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.serializers import BaseResponseSerializer
from api.payments.services import PaymentIntentService

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

# Callback serializers
class CallbackSerializer(serializers.Serializer):
    """Base callback serializer"""
    pass

class PaymentVerificationSerializer(serializers.Serializer):
    """Payment verification request serializer"""
    gateway = serializers.CharField()
    intent_id = serializers.CharField()
    callback_data = serializers.JSONField()


@router.register(r"payments/esewa/success", name="payment-esewa-success")
@extend_schema(
    tags=["Payments"],
    summary="eSewa Success Callback",
    responses={200: BaseResponseSerializer}
)
class ESewaSuccessCallbackView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    serializer_class = CallbackSerializer
    
    def get(self, request: Request) -> Response:
        """Handle eSewa success callback - Process payment and return response"""
        try:
            # eSewa sends Base64 encoded JSON in 'data' query parameter
            data = request.GET.get('data')
            if not data:
                return self.error_response(
                    message="Missing callback data",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract intent_id from base64 data
            try:
                decoded_json = json.loads(base64.b64decode(data))
                intent_id = decoded_json.get('transaction_uuid')
                if not intent_id:
                    return self.error_response(
                        message="Invalid callback data",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as decode_error:
                return self.error_response(
                    message="Invalid data format",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Process payment server-side using PaymentIntentService
            service = PaymentIntentService()
            try:
                result = service.verify_topup_payment(intent_id, {'data': data})
                
                if result.get('status') == 'SUCCESS':
                    return self.success_response(
                        data={
                            'intent_id': intent_id,
                            'gateway': 'esewa',
                            'status': 'SUCCESS',
                            'result': result
                        },
                        message="Payment verified successfully"
                    )
                else:
                    return self.error_response(
                        message="Payment verification failed",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    
            except Exception as verify_error:
                self.log_error(f"eSewa payment verification failed: {str(verify_error)}")
                return self.error_response(
                    message="Verification error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/esewa/failure", name="payment-esewa-failure")
@extend_schema(
    tags=["Payments"],
    summary="eSewa Failure Callback",
    responses={200: BaseResponseSerializer}
)
class ESewaFailureCallbackView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    serializer_class = CallbackSerializer
    
    def get(self, request: Request) -> Response:
        """Handle eSewa failure callback - Process failure and return response"""
        try:
            # eSewa may send error details in query parameters
            error_message = request.GET.get('message', 'Payment cancelled or failed')
            data = request.GET.get('data')  # eSewa might send data even on failure
            
            # If there's data, try to extract intent_id for better error handling
            intent_id = None
            if data:
                try:
                    decoded_json = json.loads(base64.b64decode(data))
                    intent_id = decoded_json.get('transaction_uuid')
                except Exception:
                    pass  # If decoding fails, continue without intent_id
            
            # Mark payment intent as failed if we have intent_id
            if intent_id:
                try:
                    from api.payments.models import PaymentIntent
                    intent = PaymentIntent.objects.get(intent_id=intent_id, status='PENDING')
                    intent.status = 'FAILED'
                    intent.intent_metadata['failure_reason'] = error_message
                    intent.save(update_fields=['status', 'intent_metadata'])
                    self.log_info(f"Payment intent {intent_id} marked as failed")
                except Exception as e:
                    self.log_error(f"Failed to update payment intent {intent_id}: {str(e)}")
                
                return self.error_response(
                    data={
                        'intent_id': intent_id,
                        'gateway': 'esewa',
                        'status': 'FAILED'
                    },
                    message=error_message,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            else:
                return self.error_response(
                    data={'gateway': 'esewa', 'status': 'FAILED'},
                    message=error_message,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            return self.error_response(
                message="Payment processing error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"payments/khalti/callback", name="payment-khalti-callback")
@extend_schema(
    tags=["Payments"],
    summary="Khalti Callback",
    responses={200: BaseResponseSerializer}
)
class KhaltiCallbackView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    serializer_class = CallbackSerializer
    
    def get(self, request: Request) -> Response:
        """Handle Khalti return callback - Process payment and return response"""
        try:
            # Khalti sends query parameters: pidx, status, txnId, etc.
            pidx = request.GET.get('pidx')
            status_param = request.GET.get('status')
            txn_id = request.GET.get('txnId')
            
            if not pidx:
                return self.error_response(
                    message="Invalid Khalti callback",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # For Khalti, pidx IS the intent_id in our system
            intent_id = pidx
            
            # Process payment server-side using PaymentIntentService
            service = PaymentIntentService()
            try:
                callback_data = {
                    'pidx': pidx,
                    'status': status_param,
                    'txnId': txn_id
                }
                
                result = service.verify_topup_payment(intent_id, callback_data)
                
                if result.get('status') == 'SUCCESS':
                    return self.success_response(
                        data={
                            'intent_id': intent_id,
                            'gateway': 'khalti',
                            'status': 'SUCCESS',
                            'result': result
                        },
                        message="Payment verified successfully"
                    )
                else:
                    return self.error_response(
                        message="Payment verification failed",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    
            except Exception as verify_error:
                self.log_error(f"Khalti payment verification failed: {str(verify_error)}")
                return self.error_response(
                    message="Verification error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )