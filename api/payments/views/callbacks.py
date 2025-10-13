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