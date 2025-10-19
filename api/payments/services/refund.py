from __future__ import annotations

from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

from api.common.services.base import CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.payments.models import Refund, Transaction, PaymentMethod

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
    def approve_refund(self, refund_id: str, admin_user, admin_notes: Optional[str] = None) -> Refund:
        """Approve a refund request"""
        try:
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
                    detail=f"Cannot approve refund with status '{refund.status}'",
                    code="invalid_refund_status"
                )

            # Verify transaction exists and is valid for refund
            transaction_obj = refund.transaction
            if not transaction_obj:
                raise ServiceException(
                    detail="Transaction not found for this refund request",
                    code="transaction_not_found"
                )

            if transaction_obj.status != 'SUCCESS':
                raise ServiceException(
                    detail="Only successful transactions can be refunded",
                    code="invalid_transaction_status"
                )

            # For gateway payments, verify gateway reference exists
            if transaction_obj.payment_method_type == 'GATEWAY':
                if not transaction_obj.gateway_reference:
                    raise ServiceException(
                        detail="Gateway reference missing for this transaction",
                        code="gateway_reference_missing"
                    )

            # Update refund status
            refund.status = 'APPROVED'
            refund.approved_by = admin_user
            refund.processed_at = timezone.now()
            
            if admin_notes:
                refund.admin_notes = admin_notes.strip()

            refund.save(update_fields=['status', 'approved_by', 'processed_at', 'admin_notes', 'updated_at'])

            # Process the actual refund (add money back to wallet)
            self._process_refund_payment(refund)

            # Update transaction status
            transaction_obj.status = 'REFUNDED'
            transaction_obj.save(update_fields=['status', 'updated_at'])

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

    def get_pending_refunds(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all pending refund requests for admin review"""
        try:
            queryset = Refund.objects.filter(status='REQUESTED').select_related(
                'transaction', 'requested_by'
            )
            
            # Apply filters if provided
            if filters:
                if filters.get('start_date'):
                    queryset = queryset.filter(requested_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(requested_at__lte=filters['end_date'])
                
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(transaction__transaction_id__icontains=search_term) |
                        Q(requested_by__username__icontains=search_term) |
                        Q(requested_by__email__icontains=search_term)
                    )
            
            # Order by latest first
            queryset = queryset.order_by('-requested_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20

            return paginate_queryset(queryset, page, page_size)

        except Exception as e:
            self.log_error(f"Error getting pending refunds: {str(e)}")
            return self.handle_service_error(e, "Failed to get pending refunds")

    @transaction.atomic
    def reject_refund(self, refund_id: str, admin_user, rejection_reason: str) -> Refund:
        """Reject a refund request"""
        try:
            # Input validation
            if not rejection_reason or len(rejection_reason.strip()) < 5:
                raise ServiceException(
                    detail="Please provide a valid rejection reason (minimum 5 characters)",
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
            refund.processed_at = timezone.now()
            refund.save(update_fields=['status', 'approved_by', 'admin_notes', 'processed_at', 'updated_at'])

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

    def _process_refund_payment(self, refund: Refund) -> None:
        """Process the actual refund payment to user's wallet"""
        try:
            from api.payments.services.wallet import WalletService
            wallet_service = WalletService()
            
            wallet_service.add_balance(
                user=refund.requested_by,
                amount=refund.amount,
                description=f"Refund for transaction {refund.transaction.transaction_id}"
            )
            
            self.log_info(f"Refund payment processed: {refund.amount} added to {refund.requested_by.username}'s wallet")
            
        except Exception as e:
            self.log_error(f"Failed to process refund payment: {str(e)}")
            raise ServiceException(
                detail="Failed to process refund payment to wallet",
                code="refund_payment_failed"
            )

    def get_refund_by_id(self, refund_id: str) -> Refund:
        """Get refund by ID with related data"""
        try:
            return Refund.objects.select_related(
                'transaction', 'requested_by', 'approved_by'
            ).get(id=refund_id)
        except Refund.DoesNotExist:
            raise ServiceException(
                detail=f"Refund with ID {refund_id} not found",
                code="refund_not_found"
            )

    def get_refunds_by_status(self, status: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get refunds by status"""
        try:
            queryset = Refund.objects.filter(status=status).select_related(
                'transaction', 'requested_by', 'approved_by'
            ).order_by('-requested_at')

            return paginate_queryset(queryset, page, page_size)
        except Exception as e:
            self.handle_service_error(e, f"Failed to get refunds with status {status}")