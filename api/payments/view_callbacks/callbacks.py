from __future__ import annotations

import base64
import json
import logging
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
from django.shortcuts import redirect

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()


# ----------------------------------------------------------------------
# Base serializers
# ----------------------------------------------------------------------

class CallbackSerializer(serializers.Serializer):
    """Base callback serializer"""
    pass


class PaymentVerificationSerializer(serializers.Serializer):
    """Payment verification request serializer"""
    gateway = serializers.CharField()
    intent_id = serializers.CharField()
    callback_data = serializers.JSONField()


# ----------------------------------------------------------------------
# eSewa SUCCESS CALLBACK
# ----------------------------------------------------------------------

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
            data = request.GET.get('data')
            if not data:
                return self.error_response(
                    message="Missing callback data",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            try:
                decoded_json = json.loads(base64.b64decode(data))
                intent_id = decoded_json.get('transaction_uuid')
                if not intent_id:
                    return self.error_response(
                        message="Invalid callback data",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            except Exception:
                return self.error_response(
                    message="Invalid data format",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

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
                logger = logging.getLogger(__name__)
                logger.error(f"eSewa payment verification failed: {str(verify_error)}")

                from api.payments.models import PaymentIntent
                try:
                    intent = PaymentIntent.objects.get(intent_id=intent_id)

                    if intent.status == 'COMPLETED':
                        return self.success_response(
                            data={
                                'intent_id': intent_id,
                                'gateway': 'esewa',
                                'status': 'ALREADY_PROCESSED',
                                'message': 'Payment was already successfully processed'
                            },
                            message="Payment already processed successfully"
                        )
                    elif intent.status == 'FAILED':
                        return self.error_response(
                            data={
                                'intent_id': intent_id,
                                'gateway': 'esewa',
                                'status': 'FAILED'
                            },
                            message="Payment verification failed",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except PaymentIntent.DoesNotExist:
                    pass

                return self.error_response(
                    message="Verification error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# eSewa FAILURE CALLBACK
# ----------------------------------------------------------------------

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
        try:
            error_message = request.GET.get('message', 'Payment cancelled or failed')
            data = request.GET.get('data')

            intent_id = None
            if data:
                try:
                    decoded_json = json.loads(base64.b64decode(data))
                    intent_id = decoded_json.get('transaction_uuid')
                except Exception:
                    pass

            if intent_id:
                try:
                    from api.payments.models import PaymentIntent
                    intent = PaymentIntent.objects.get(intent_id=intent_id, status='PENDING')
                    intent.status = 'FAILED'
                    intent.intent_metadata['failure_reason'] = error_message
                    intent.save(update_fields=['status', 'intent_metadata'])
                    logger = logging.getLogger(__name__)
                    logger.info(f"Payment intent {intent_id} marked as failed")
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to update payment intent {intent_id}: {str(e)}")

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

        except Exception:
            return self.error_response(
                message="Payment processing error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# KHALTI CALLBACK
# ----------------------------------------------------------------------

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
        try:
            pidx = request.GET.get('pidx')
            status_param = request.GET.get('status')
            txn_id = request.GET.get('txnId')
            purchase_order_id = request.GET.get('purchase_order_id')

            if not pidx or not purchase_order_id:
                return self.error_response(
                    message="Invalid Khalti callback - missing required parameters",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            intent_id = purchase_order_id
            service = PaymentIntentService()

            try:
                callback_data = {
                    'pidx': pidx,
                    'status': status_param,
                    'txnId': txn_id,
                    'transaction_id': request.GET.get('transaction_id'),
                    'tidx': request.GET.get('tidx'),
                    'amount': request.GET.get('amount'),
                    'total_amount': request.GET.get('total_amount'),
                    'mobile': request.GET.get('mobile'),
                    'purchase_order_id': purchase_order_id,
                    'purchase_order_name': request.GET.get('purchase_order_name')
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
                logger = logging.getLogger(__name__)
                logger.error(f"Khalti payment verification failed: {str(verify_error)}")

                from api.payments.models import PaymentIntent
                try:
                    intent = PaymentIntent.objects.get(intent_id=intent_id)

                    if intent.status == 'COMPLETED':
                        return self.success_response(
                            data={
                                'intent_id': intent_id,
                                'gateway': 'khalti',
                                'status': 'ALREADY_PROCESSED',
                                'message': 'Payment was already successfully processed'
                            },
                            message="Payment already processed successfully"
                        )
                    elif intent.status == 'FAILED':
                        return self.error_response(
                            data={
                                'intent_id': intent_id,
                                'gateway': 'khalti',
                                'status': 'FAILED'
                            },
                            message="Payment verification failed",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except PaymentIntent.DoesNotExist:
                    pass

                return self.error_response(
                    message="Verification error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# STRIPE CALLBACKS (✅ Fixed)
# ----------------------------------------------------------------------

@router.register(r"stripe/success", name="payment-stripe-success")
@extend_schema(
    tags=["Payments"],
    summary="Stripe Success Callback",
    responses={200: BaseResponseSerializer}
)
class StripeSuccessCallbackView(GenericAPIView, BaseAPIView):
    """Handle Stripe success callback."""
    permission_classes = [AllowAny]
    serializer_class = CallbackSerializer

    def get(self, request: Request) -> Response:
        try:
            session_id = request.GET.get("session_id")
            if not session_id:
                return self.error_response(
                    message="Missing session_id in callback",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            service = PaymentIntentService()
            try:
                result = service.verify_topup_payment(
                    intent_id=session_id,
                    callback_data={"session_id": session_id, "gateway": "stripe"}
                )

                if result.get("status") == "SUCCESS":
                    return self.success_response(
                        data={
                            "intent_id": session_id,
                            "gateway": "stripe",
                            "status": "SUCCESS",
                            "result": result
                        },
                        message="Stripe payment verified successfully"
                    )
                else:
                    return self.error_response(
                        message="Stripe payment verification failed",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            except Exception as verify_error:
                logger = logging.getLogger(__name__)
                logger.error(f"Stripe payment verification failed: {verify_error}")

                from api.payments.models import PaymentIntent
                try:
                    intent = PaymentIntent.objects.get(intent_id=session_id)
                    if intent.status == "COMPLETED":
                        return self.success_response(
                            data={
                                "intent_id": session_id,
                                "gateway": "stripe",
                                "status": "ALREADY_PROCESSED",
                            },
                            message="Payment already processed successfully"
                        )
                    elif intent.status == "FAILED":
                        return self.error_response(
                            message="Payment failed",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
                except PaymentIntent.DoesNotExist:
                    pass

                return self.error_response(
                    message="Stripe verification error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return self.error_response(
                message=f"Stripe callback error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"stripe/cancel", name="payment-stripe-cancel")
@extend_schema(
    tags=["Payments"],
    summary="Stripe Cancel Callback",
    responses={200: BaseResponseSerializer}
)
class StripeCancelCallbackView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]
    serializer_class = CallbackSerializer

    def get(self, request: Request) -> Response:
        try:
            session_id = request.GET.get("session_id")
            error_message = "Stripe checkout cancelled by user"

            if session_id:
                from api.payments.models import PaymentIntent
                try:
                    intent = PaymentIntent.objects.get(intent_id=session_id)
                    intent.status = "FAILED"
                    intent.intent_metadata["failure_reason"] = error_message
                    intent.save(update_fields=["status", "intent_metadata"])
                except PaymentIntent.DoesNotExist:
                    pass

            return self.error_response(
                data={
                    "intent_id": session_id,
                    "gateway": "stripe",
                    "status": "FAILED"
                },
                message=error_message,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Stripe cancel callback error: {str(e)}")

            return self.error_response(
                message="Stripe cancel processing error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# GENERIC SUCCESS REDIRECT (✅ Fixed)
# ----------------------------------------------------------------------

@router.register(r"success", name="payment-generic-success")
@extend_schema(
    tags=["Payments"],
    summary="Redirect generic success to Stripe success",
    responses={200: BaseResponseSerializer}
)
class GenericSuccessRedirectView(GenericAPIView, BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id")
        return redirect(f"/payments/stripe/success/?session_id={session_id}")
