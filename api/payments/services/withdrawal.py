from __future__ import annotations

import uuid
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum

from api.common.services.base import CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset, generate_transaction_id
from api.payments.models import WithdrawalRequest, WithdrawalLimit, PaymentMethod
from api.payments.services.wallet import WalletService

class WithdrawalService(CRUDService):
    """Service for withdrawal operations"""
    model = WithdrawalRequest

    def __init__(self):
        super().__init__()
        from api.system.services import AppConfigService
        self.config_service = AppConfigService()
        self.wallet_service = WalletService()

    @transaction.atomic
    def request_withdrawal(self, user, amount: Decimal, withdrawal_method: str, account_details: Dict[str, Any]) -> WithdrawalRequest:
        """Request withdrawal with comprehensive validation"""
        try:
            # Input validation
            if not amount or amount <= 0:
                raise ServiceException(
                    detail="Amount must be greater than 0",
                    code="invalid_amount"
                )

            if not account_details:
                raise ServiceException(
                    detail="Account details are required",
                    code="account_details_required"
                )

            # Check if withdrawals are enabled
            withdrawal_enabled = self.config_service.get_config_cached('WITHDRAWAL_ENABLED', 'true').lower() == 'true'
            if not withdrawal_enabled:
                raise ServiceException(
                    detail="Withdrawal functionality is currently disabled",
                    code="withdrawals_disabled"
                )

            # Validate withdrawal method and get corresponding payment method
            try:
                payment_method = PaymentMethod.objects.get(gateway=withdrawal_method, is_active=True)
            except PaymentMethod.DoesNotExist:
                raise ServiceException(
                    detail=f"Withdrawal method '{withdrawal_method}' is not available",
                    code="invalid_withdrawal_method"
                )

            # Validate minimum amount
            min_amount = Decimal(self.config_service.get_config_cached('WITHDRAWAL_MIN_AMOUNT', '100'))
            if amount < min_amount:
                raise ServiceException(
                    detail=f"Minimum withdrawal amount is NPR {min_amount}",
                    code="amount_below_minimum"
                )

            # Validate withdrawal limits
            self.validate_withdrawal_limits(user, amount)

            # Check wallet balance
            wallet_balance = self.wallet_service.get_wallet_balance(user)
            if isinstance(wallet_balance, dict):
                balance = wallet_balance.get('balance', 0)
            else:
                balance = wallet_balance

            if balance < amount:
                raise ServiceException(
                    detail=f"Insufficient wallet balance. Available: NPR {balance}",
                    code="insufficient_balance"
                )

            # Calculate processing fee
            processing_fee = self.calculate_withdrawal_fee(amount)
            net_amount = amount - processing_fee

            # Validate account details based on withdrawal method
            self._validate_account_details(withdrawal_method, account_details)

            # Create withdrawal request
            withdrawal = WithdrawalRequest.objects.create(
                user=user,
                amount=amount,
                processing_fee=processing_fee,
                net_amount=net_amount,
                payment_method=payment_method,
                account_details=account_details,
                status='REQUESTED',
                internal_reference=f"WD{generate_transaction_id()[-10:]}"
            )

            # Deduct amount from wallet (hold the funds)
            self.wallet_service.deduct_balance(
                user=user,
                amount=amount,
                description=f"Withdrawal request - {withdrawal.internal_reference}"
            )

            # Update withdrawal limits
            self._update_withdrawal_limits(user, amount)

            # Send notification
            try:
                from api.notifications.services import notify
                notify(
                    user,
                    'withdrawal_requested',
                    async_send=True,
                    amount=float(amount),
                    processing_fee=float(processing_fee),
                    net_amount=float(net_amount),
                    withdrawal_reference=withdrawal.internal_reference
                )
            except Exception as notification_error:
                self.log_warning(f"Failed to send withdrawal notification: {str(notification_error)}")

            self.log_info(f"Withdrawal requested: {withdrawal.internal_reference} by user {user.username}")
            return withdrawal

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.handle_service_error(e, "Failed to request withdrawal")

    def get_user_withdrawals(self, user, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get user withdrawal history with pagination"""
        try:
            queryset = WithdrawalRequest.objects.filter(user=user).select_related('payment_method').order_by('-requested_at')
            return paginate_queryset(queryset, page, page_size)
        except Exception as e:
            self.handle_service_error(e, "Failed to get user withdrawals")

    @transaction.atomic
    def approve_withdrawal(self, withdrawal_id: str, admin_user, admin_notes: Optional[str] = None) -> WithdrawalRequest:
        """Approve withdrawal request"""
        try:
            # Find and validate withdrawal
            try:
                withdrawal = WithdrawalRequest.objects.select_related('user', 'payment_method').get(id=withdrawal_id)
            except WithdrawalRequest.DoesNotExist:
                raise ServiceException(
                    detail=f"Withdrawal with ID {withdrawal_id} not found",
                    code="withdrawal_not_found"
                )

            # Validate withdrawal status
            if withdrawal.status != 'REQUESTED':
                raise ServiceException(
                    detail=f"Cannot approve withdrawal with status '{withdrawal.status}'",
                    code="invalid_withdrawal_status"
                )

            # Update withdrawal status
            withdrawal.status = 'APPROVED'
            withdrawal.processed_by = admin_user
            withdrawal.processed_at = timezone.now()
            
            if admin_notes:
                withdrawal.admin_notes = admin_notes.strip()

            withdrawal.save(update_fields=['status', 'processed_by', 'processed_at', 'admin_notes', 'updated_at'])

            # Process the actual withdrawal payment
            self._process_withdrawal_payment(withdrawal)

            # Mark as completed
            withdrawal.status = 'COMPLETED'
            withdrawal.save(update_fields=['status', 'updated_at'])

            # Notify user
            try:
                from api.notifications.services import notify
                notify(
                    withdrawal.user,
                    'withdrawal_approved',
                    async_send=True,
                    amount=float(withdrawal.amount),
                    net_amount=float(withdrawal.net_amount),
                    withdrawal_reference=withdrawal.internal_reference,
                    admin_notes=admin_notes or ''
                )
            except Exception as notification_error:
                self.log_warning(f"Failed to send approval notification: {str(notification_error)}")

            self.log_info(f"Withdrawal approved: {withdrawal_id} by admin {admin_user.username}")
            return withdrawal

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error approving withdrawal: {str(e)}")
            raise ServiceException(
                detail="An unexpected error occurred while approving the withdrawal",
                code="internal_error"
            )

    @transaction.atomic
    def reject_withdrawal(self, withdrawal_id: str, admin_user, rejection_reason: str) -> WithdrawalRequest:
        """Reject withdrawal request"""
        try:
            # Input validation
            if not rejection_reason or len(rejection_reason.strip()) < 5:
                raise ServiceException(
                    detail="Please provide a valid rejection reason (minimum 5 characters)",
                    code="invalid_rejection_reason"
                )

            # Find and validate withdrawal
            try:
                withdrawal = WithdrawalRequest.objects.select_related('user').get(id=withdrawal_id)
            except WithdrawalRequest.DoesNotExist:
                raise ServiceException(
                    detail=f"Withdrawal with ID {withdrawal_id} not found",
                    code="withdrawal_not_found"
                )

            # Validate withdrawal status
            if withdrawal.status != 'REQUESTED':
                raise ServiceException(
                    detail=f"Cannot reject withdrawal with status '{withdrawal.status}'",
                    code="invalid_withdrawal_status"
                )

            # Update withdrawal status
            withdrawal.status = 'REJECTED'
            withdrawal.processed_by = admin_user
            withdrawal.admin_notes = rejection_reason.strip()
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=['status', 'processed_by', 'admin_notes', 'processed_at', 'updated_at'])

            # Refund the amount back to wallet
            self.wallet_service.add_balance(
                user=withdrawal.user,
                amount=withdrawal.amount,
                description=f"Withdrawal rejected - {withdrawal.internal_reference}"
            )

            # Reverse withdrawal limits
            self._reverse_withdrawal_limits(withdrawal.user, withdrawal.amount)

            # Notify user
            try:
                from api.notifications.services import notify
                notify(
                    withdrawal.user,
                    'withdrawal_rejected',
                    async_send=True,
                    amount=float(withdrawal.amount),
                    withdrawal_reference=withdrawal.internal_reference,
                    rejection_reason=rejection_reason
                )
            except Exception as notification_error:
                self.log_warning(f"Failed to send rejection notification: {str(notification_error)}")

            self.log_info(f"Withdrawal rejected: {withdrawal_id} by admin {admin_user.username}")
            return withdrawal

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error rejecting withdrawal: {str(e)}")
            raise ServiceException(
                detail="An unexpected error occurred while rejecting the withdrawal",
                code="internal_error"
            )

    @transaction.atomic
    def cancel_withdrawal(self, withdrawal_id: str, user) -> WithdrawalRequest:
        """Cancel user's own withdrawal request"""
        try:
            # Find and validate withdrawal
            try:
                withdrawal = WithdrawalRequest.objects.get(id=withdrawal_id, user=user)
            except WithdrawalRequest.DoesNotExist:
                raise ServiceException(
                    detail="Withdrawal request not found",
                    code="withdrawal_not_found"
                )

            # Validate withdrawal status
            if withdrawal.status != 'REQUESTED':
                raise ServiceException(
                    detail=f"Cannot cancel withdrawal with status '{withdrawal.status}'",
                    code="invalid_withdrawal_status"
                )

            # Update withdrawal status
            withdrawal.status = 'CANCELLED'
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=['status', 'processed_at', 'updated_at'])

            # Refund the amount back to wallet
            self.wallet_service.add_balance(
                user=user,
                amount=withdrawal.amount,
                description=f"Withdrawal cancelled - {withdrawal.internal_reference}"
            )

            # Reverse withdrawal limits
            self._reverse_withdrawal_limits(user, withdrawal.amount)

            self.log_info(f"Withdrawal cancelled: {withdrawal_id} by user {user.username}")
            return withdrawal

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.handle_service_error(e, "Failed to cancel withdrawal")

    def calculate_withdrawal_fee(self, amount: Decimal) -> Decimal:
        """Calculate withdrawal processing fee"""
        try:
            fee_percentage = Decimal(self.config_service.get_config_cached('WITHDRAWAL_PROCESSING_FEE_PERCENTAGE', '2.0'))
            fee_fixed = Decimal(self.config_service.get_config_cached('WITHDRAWAL_PROCESSING_FEE_FIXED', '10'))
            
            percentage_fee = (amount * fee_percentage) / 100
            total_fee = percentage_fee + fee_fixed
            
            return total_fee
        except Exception as e:
            self.log_error(f"Error calculating withdrawal fee: {str(e)}")
            return Decimal('10')  # Default fee

    def validate_withdrawal_limits(self, user, amount: Decimal) -> None:
        """Validate daily and monthly withdrawal limits"""
        try:
            # Get limits from config
            daily_limit = Decimal(self.config_service.get_config_cached('WITHDRAWAL_MAX_DAILY_LIMIT', '10000'))
            monthly_limit = Decimal(self.config_service.get_config_cached('WITHDRAWAL_MAX_MONTHLY_LIMIT', '50000'))

            # Get or create withdrawal limit record
            withdrawal_limit, created = WithdrawalLimit.objects.get_or_create(
                user=user,
                defaults={
                    'daily_withdrawn': Decimal('0'),
                    'monthly_withdrawn': Decimal('0'),
                    'last_daily_reset': date.today(),
                    'last_monthly_reset': date.today()
                }
            )

            # Reset daily limit if needed
            if withdrawal_limit.last_daily_reset < date.today():
                withdrawal_limit.daily_withdrawn = Decimal('0')
                withdrawal_limit.last_daily_reset = date.today()

            # Reset monthly limit if needed
            current_month_start = date.today().replace(day=1)
            if withdrawal_limit.last_monthly_reset < current_month_start:
                withdrawal_limit.monthly_withdrawn = Decimal('0')
                withdrawal_limit.last_monthly_reset = date.today()

            withdrawal_limit.save()

            # Check daily limit
            if withdrawal_limit.daily_withdrawn + amount > daily_limit:
                remaining_daily = daily_limit - withdrawal_limit.daily_withdrawn
                raise ServiceException(
                    detail=f"Daily withdrawal limit exceeded. Remaining: NPR {remaining_daily}",
                    code="daily_limit_exceeded"
                )

            # Check monthly limit
            if withdrawal_limit.monthly_withdrawn + amount > monthly_limit:
                remaining_monthly = monthly_limit - withdrawal_limit.monthly_withdrawn
                raise ServiceException(
                    detail=f"Monthly withdrawal limit exceeded. Remaining: NPR {remaining_monthly}",
                    code="monthly_limit_exceeded"
                )

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error validating withdrawal limits: {str(e)}")
            raise ServiceException(
                detail="Failed to validate withdrawal limits",
                code="limit_validation_error"
            )

    def _validate_account_details(self, withdrawal_method: str, account_details: Dict[str, Any]) -> None:
        """Validate account details based on withdrawal method"""
        try:
            method = withdrawal_method.lower()
            
            if method == 'bank':
                required_fields = ['bank_name', 'account_number', 'account_holder_name']
                for field in required_fields:
                    if not account_details.get(field) or not account_details.get(field).strip():
                        raise ServiceException(
                            detail=f"Bank {field.replace('_', ' ')} is required",
                            code="missing_bank_details"
                        )
            
            elif method in ['esewa', 'khalti']:
                if not account_details.get('phone_number'):
                    raise ServiceException(
                        detail=f"{method.title()} phone number is required",
                        code="missing_phone_number"
                    )
                
                # Validate phone number format (basic validation)
                phone = account_details['phone_number'].strip()
                if not phone.startswith('98') or len(phone) != 10 or not phone.isdigit():
                    raise ServiceException(
                        detail="Please provide a valid Nepali phone number (98XXXXXXXX)",
                        code="invalid_phone_format"
                    )
            
            else:
                raise ServiceException(
                    detail=f"Unsupported withdrawal method: {method}",
                    code="unsupported_withdrawal_method"
                )

        except ServiceException:
            # Re-raise service exceptions
            raise
        except Exception as e:
            self.log_error(f"Error validating account details: {str(e)}")
            raise ServiceException(
                detail="Failed to validate account details",
                code="account_validation_error"
            )

    def _update_withdrawal_limits(self, user, amount: Decimal) -> None:
        """Update user withdrawal limits"""
        try:
            withdrawal_limit, created = WithdrawalLimit.objects.get_or_create(
                user=user,
                defaults={
                    'daily_withdrawn': amount,
                    'monthly_withdrawn': amount,
                    'last_daily_reset': date.today(),
                    'last_monthly_reset': date.today()
                }
            )

            if not created:
                withdrawal_limit.daily_withdrawn += amount
                withdrawal_limit.monthly_withdrawn += amount
                withdrawal_limit.save(update_fields=['daily_withdrawn', 'monthly_withdrawn', 'updated_at'])

        except Exception as e:
            self.log_error(f"Error updating withdrawal limits: {str(e)}")

    def _reverse_withdrawal_limits(self, user, amount: Decimal) -> None:
        """Reverse withdrawal limits when withdrawal is rejected/cancelled"""
        try:
            withdrawal_limit = WithdrawalLimit.objects.get(user=user)
            withdrawal_limit.daily_withdrawn = max(Decimal('0'), withdrawal_limit.daily_withdrawn - amount)
            withdrawal_limit.monthly_withdrawn = max(Decimal('0'), withdrawal_limit.monthly_withdrawn - amount)
            withdrawal_limit.save(update_fields=['daily_withdrawn', 'monthly_withdrawn', 'updated_at'])

        except WithdrawalLimit.DoesNotExist:
            self.log_warning(f"Withdrawal limit not found for user {user.username}")
        except Exception as e:
            self.log_error(f"Error reversing withdrawal limits: {str(e)}")

    def _process_withdrawal_payment(self, withdrawal: WithdrawalRequest) -> None:
        """Process the actual withdrawal payment (placeholder for gateway integration)"""
        try:
            # This is where you would integrate with actual payment gateways
            # For now, we'll just log the action
            
            method = withdrawal.account_details.get('method', '').lower()
            
            if method == 'bank':
                # Process bank transfer
                account_number = withdrawal.account_details.get('account_number', 'N/A')
                bank_name = withdrawal.account_details.get('bank_name', 'N/A')
                self.log_info(f"Processing bank transfer: NPR {withdrawal.net_amount} to {bank_name} account {account_number}")
                
            elif method in ['esewa', 'khalti']:
                # Process digital wallet transfer
                phone_number = withdrawal.account_details.get('phone_number', 'N/A')
                self.log_info(f"Processing {method.title()} transfer: NPR {withdrawal.net_amount} to {phone_number}")
                
            # Set gateway reference (in real implementation, this would come from the gateway)
            withdrawal.gateway_reference = f"{method.upper()}_{withdrawal.internal_reference}"
            withdrawal.save(update_fields=['gateway_reference', 'updated_at'])
            
            self.log_info(f"Withdrawal payment processed: {withdrawal.internal_reference}")
            
        except Exception as e:
            self.log_error(f"Failed to process withdrawal payment: {str(e)}")
            raise ServiceException(
                detail="Failed to process withdrawal payment",
                code="payment_processing_failed"
            )

    def get_withdrawals(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all withdrawals with filters (admin view)"""
        try:
            queryset = WithdrawalRequest.objects.select_related(
                'user', 'payment_method', 'processed_by'
            )
            
            # Apply filters if provided
            if filters:
                # Status filter
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                # Payment method filter
                if filters.get('payment_method'):
                    queryset = queryset.filter(payment_method__name__icontains=filters['payment_method'])
                
                # Date range filters
                if filters.get('start_date'):
                    queryset = queryset.filter(requested_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(requested_at__lte=filters['end_date'])
                
                # Search filter
                if filters.get('search'):
                    search_term = filters['search']
                    queryset = queryset.filter(
                        Q(internal_reference__icontains=search_term) |
                        Q(user__username__icontains=search_term) |
                        Q(user__email__icontains=search_term)
                    )
            
            # Order by latest first
            queryset = queryset.order_by('-requested_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20

            return paginate_queryset(queryset, page, page_size)

        except Exception as e:
            self.log_error(f"Error getting withdrawals: {str(e)}")
            return self.handle_service_error(e, "Failed to get withdrawals")

    def get_pending_withdrawals(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all pending withdrawal requests for admin review"""
        try:
            queryset = WithdrawalRequest.objects.filter(status='REQUESTED').select_related(
                'user', 'payment_method'
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
                        Q(internal_reference__icontains=search_term) |
                        Q(user__username__icontains=search_term) |
                        Q(user__email__icontains=search_term)
                    )
            
            # Order by latest first
            queryset = queryset.order_by('-requested_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20

            return paginate_queryset(queryset, page, page_size)

        except Exception as e:
            self.log_error(f"Error getting pending withdrawals: {str(e)}")
            return self.handle_service_error(e, "Failed to get pending withdrawals")

    def get_withdrawal_by_id(self, withdrawal_id: str) -> WithdrawalRequest:
        """Get withdrawal by ID with related data"""
        try:
            return WithdrawalRequest.objects.select_related(
                'user', 'payment_method', 'processed_by'
            ).get(id=withdrawal_id)
        except WithdrawalRequest.DoesNotExist:
            raise ServiceException(
                detail=f"Withdrawal with ID {withdrawal_id} not found",
                code="withdrawal_not_found"
            )

    def get_withdrawals_by_status(self, status: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get withdrawals by status"""
        try:
            queryset = WithdrawalRequest.objects.filter(status=status).select_related(
                'user', 'payment_method', 'processed_by'
            ).order_by('-requested_at')

            return paginate_queryset(queryset, page, page_size)
        except Exception as e:
            self.handle_service_error(e, f"Failed to get withdrawals with status {status}")