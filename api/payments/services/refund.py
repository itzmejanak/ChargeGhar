from __future__ import annotations

from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from api.common.services.base import CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.payments.models import Refund, Transaction

class RefundService(CRUDService):
    """Service for refund operations"""
    model = Refund

    @transaction.atomic
    def request_refund(self, user, transaction_id: str, reason: str) -> Refund:
        """Request refund for a transaction"""
        try:
            # Input validation
            if not transaction_id:
                raise ServiceException(
                    detail="Transaction ID is required",
                    code="transaction_id_required"
                )

            if not reason or len(reason.strip()) < 10:
                raise ServiceException(
                    detail="Please provide a valid reason (minimum 10 characters)",
                    code="invalid_reason"
                )

            # Find and validate transaction
            try:
                transaction_obj = Transaction.objects.select_related('user').get(transaction_id=transaction_id)
            except Transaction.DoesNotExist:
                raise ServiceException(
                    detail=f"Transaction with ID {transaction_id} not found",
                    code="transaction_not_found"
                )

            # Security check: verify ownership
            if transaction_obj.user_id != user.id:
                raise ServiceException(
                    detail="You are not authorized to request refund for this transaction",
                    code="unauthorized_transaction"
                )

            # Business logic validation
            if transaction_obj.status != 'SUCCESS':
                raise ServiceException(
                    detail="Only successful transactions can be refunded",
                    code="invalid_transaction_status"
                )

            # Check for existing refund request
            existing_refund = Refund.objects.filter(transaction=transaction_obj).first()
            if existing_refund:
                raise ServiceException(
                    detail=f"A refund request already exists for this transaction (Status: {existing_refund.status})",
                    code="refund_already_exists"
                )

            # Create refund request
            refund = Refund.objects.create(
                transaction=transaction_obj,
                requested_by=user,
                amount=transaction_obj.amount,
                reason=reason.strip(),
                status='REQUESTED'
            )

            # Schedule admin notification
            try:
                from api.notifications.tasks import send_refund_request_notification
                send_refund_request_notification.delay(refund.id)
            except Exception as notification_error:
                self.log_warning(f"Failed to send refund notification: {str(notification_error)}")
                # Continue processing as notification is not critical

            self.log_info(f"Refund requested: {transaction_obj.transaction_id} by {user.username}")
            return refund

        except ServiceException:
            # Re-raise service exceptions as they already have proper formatting
            raise
        except ValidationError as e:
            raise ServiceException(detail=str(e), code="validation_error")
        except Exception as e:
            self.log_error(f"Unexpected error in refund request: {str(e)}")
            raise ServiceException(
                detail="An unexpected error occurred while processing your refund request",
                code="internal_error"
            )

    def get_user_refunds(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user's refund requests"""
        try:
            queryset = Refund.objects.filter(requested_by=user).select_related('transaction')
            return paginate_queryset(queryset, page, page_size)
        except Exception as e:
            self.handle_service_error(e, "Failed to get user refunds")

    @transaction.atomic
    def approve_refund(self, refund_id: str, admin_user) -> Refund:
        """Approve a refund request"""
        try:
            # Find and validate refund
            try:
                refund = Refund.objects.select_related('transaction', 'transaction__payment_method').get(id=refund_id)
            except Refund.DoesNotExist:
                raise ServiceException(
                    detail=f"Refund with ID {refund_id} not found",
                    code="refund_not_found"
                )

            # Validate refund status
            if refund.status != 'REQUESTED':
                raise ServiceException(
                    detail=f"Cannot approve refund with status '{refund.status}'",
                    code="invalid_refund_status"
                )

            # Verify transaction exists and is valid for refund
            transaction = refund.transaction
            if not transaction:
                raise ServiceException(
                    detail="Transaction not found for this refund request",
                    code="transaction_not_found"
                )

            if transaction.status != 'SUCCESS':
                raise ServiceException(
                    detail="Only successful transactions can be refunded",
                    code="invalid_transaction_status"
                )

            # For gateway payments, verify the payment method and gateway reference
            if transaction.payment_method_type == 'GATEWAY':
                if not transaction.payment_method:
                    raise ServiceException(
                        detail="Payment method information missing for this transaction",
                        code="payment_method_missing"
                    )

                if not transaction.gateway_reference:
                    raise ServiceException(
                        detail="Gateway reference missing for this transaction",
                        code="gateway_reference_missing"
                    )

                # Additional gateway-specific validation
                gateway = transaction.payment_method.gateway
                if gateway not in ['khalti', 'esewa']:
                    raise ServiceException(
                        detail=f"Unsupported payment gateway: {gateway}",
                        code="unsupported_gateway"
                    )

                # Verify gateway configuration exists
                if not transaction.payment_method.configuration:
                    raise ServiceException(
                        detail=f"Payment gateway configuration missing",
                        code="gateway_config_missing"
                    )

            # Update refund status
            refund.status = 'APPROVED'
            refund.approved_by = admin_user
            refund.save(update_fields=['status', 'approved_by', 'updated_at'])

            # Schedule refund processing
            try:
                from api.payments.tasks import process_pending_refunds
                process_pending_refunds.delay()
            except Exception as task_error:
                self.log_warning(f"Failed to schedule refund processing: {str(task_error)}")

            # Notify user
            try:
                from api.notifications.tasks import send_refund_approved_notification
                send_refund_approved_notification.delay(refund.id)
            except Exception as notification_error:
                self.log_warning(f"Failed to send approval notification: {str(notification_error)}")

            self.log_info(f"Refund approved: {refund_id} by admin {admin_user.username}")
            return refund

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error approving refund: {str(e)}")
            raise ServiceException(
                detail="An unexpected error occurred while approving the refund",
                code="internal_error"
            )

    def get_pending_refunds(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get all pending refund requests for admin review"""
        try:
            queryset = Refund.objects.filter(status='REQUESTED').select_related(
                'transaction', 'requested_by'
            ).order_by('-requested_at')

            # Apply pagination
            return self.paginate_queryset(queryset, page, page_size)

        except Exception as e:
            self.log_error(f"Error getting pending refunds: {str(e)}")
            return self.handle_service_error(e)

    @transaction.atomic
    def reject_refund(self, refund_id: str, admin_user, rejection_reason: str) -> Refund:
        """Reject a refund request"""
        try:
            # Input validation
            if not rejection_reason or len(rejection_reason.strip()) < 5:
                raise ServiceException(
                    detail="Please provide a valid rejection reason",
                    code="invalid_rejection_reason"
                )

            # Find and validate refund
            try:
                refund = Refund.objects.select_related('transaction').get(id=refund_id)
            except Refund.DoesNotExist:
                raise ServiceException(
                    detail=f"Refund with ID {refund_id} not found",
                    code="refund_not_found"
                )

            # Validate refund status
            if refund.status != 'REQUESTED':
                raise ServiceException(
                    detail=f"Cannot reject refund with status '{refund.status}'",
                    code="invalid_refund_status"
                )

            # Update refund status
            refund.status = 'REJECTED'
            refund.approved_by = admin_user  # Using the same field to track who handled it
            refund.admin_notes = rejection_reason.strip()
            refund.save(update_fields=['status', 'approved_by', 'admin_notes', 'updated_at'])

            # Notify user
            try:
                from api.notifications.tasks import send_refund_rejected_notification
                send_refund_rejected_notification.delay(refund.id)
            except Exception as notification_error:
                self.log_warning(f"Failed to send rejection notification: {str(notification_error)}")

            self.log_info(f"Refund rejected: {refund_id} by admin {admin_user.username}")
            return refund

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error rejecting refund: {str(e)}")
            raise ServiceException(
                detail="An unexpected error occurred while rejecting the refund",
                code="internal_error"
            )