from __future__ import annotations

import uuid
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import (
    generate_transaction_id, 
    convert_points_to_amount,
    calculate_points_from_amount,
    paginate_queryset
)
from api.payments.models import (
    Transaction, Wallet, WalletTransaction, PaymentIntent,
    PaymentMethod, Refund
)
from api.rentals.models import RentalPackage
from api.users.models import UserPoints


class WalletService(CRUDService):
    """Service for wallet operations"""
    model = Wallet
    
    def get_or_create_wallet(self, user) -> Wallet:
        """Get or create user wallet"""
        try:
            wallet, created = Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('0'), 'currency': 'NPR'}
            )
            return wallet
        except Exception as e:
            self.handle_service_error(e, "Failed to get or create wallet")
    
    @transaction.atomic
    def add_balance(self, user, amount: Decimal, description: str, transaction_obj: Transaction = None) -> WalletTransaction:
        """Add balance to user wallet"""
        try:
            wallet = self.get_or_create_wallet(user)
            
            balance_before = wallet.balance
            wallet.balance += amount
            wallet.save(update_fields=['balance', 'updated_at'])
            
            # Create wallet transaction record
            wallet_transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction=transaction_obj,
                transaction_type='CREDIT',
                amount=amount,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description
            )
            
            self.log_info(f"Balance added to wallet: {user.username} +{amount}")
            return wallet_transaction
            
        except Exception as e:
            self.handle_service_error(e, "Failed to add wallet balance")
    
    @transaction.atomic
    def deduct_balance(self, user, amount: Decimal, description: str, transaction_obj: Transaction = None) -> WalletTransaction:
        """Deduct balance from user wallet"""
        try:
            wallet = self.get_or_create_wallet(user)
            
            if wallet.balance < amount:
                raise ServiceException(
                    detail="Insufficient wallet balance",
                    code="insufficient_balance"
                )
            
            balance_before = wallet.balance
            wallet.balance -= amount
            wallet.save(update_fields=['balance', 'updated_at'])
            
            # Create wallet transaction record
            wallet_transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction=transaction_obj,
                transaction_type='DEBIT',
                amount=amount,
                balance_before=balance_before,
                balance_after=wallet.balance,
                description=description
            )
            
            self.log_info(f"Balance deducted from wallet: {user.username} -{amount}")
            return wallet_transaction
            
        except Exception as e:
            self.handle_service_error(e, "Failed to deduct wallet balance")
    
    def get_wallet_balance(self, user) -> Decimal:
        """Get user wallet balance"""
        try:
            wallet = self.get_or_create_wallet(user)
            return wallet.balance
        except Exception as e:
            self.handle_service_error(e, "Failed to get wallet balance")


class PaymentCalculationService(BaseService):
    """Service for payment calculations"""
    
    def calculate_payment_options(self, user, scenario: str, **kwargs) -> Dict[str, Any]:
        """Calculate payment options for different scenarios"""
        try:
            # Extract package_id or rental_id from kwargs
            package_id = kwargs.get('package_id')
            rental_id = kwargs.get('rental_id')
            amount = kwargs.get('amount')

            # Determine amount based on scenario
            if scenario == 'wallet_topup':
                if not amount:
                    raise ServiceException(
                        detail="Amount required for wallet topup",
                        code="amount_required"
                    )
            elif scenario == 'pre_payment':
                if not package_id:
                    raise ServiceException(
                        detail="Package ID required for pre-payment",
                        code="package_required"
                    )
                # Get amount from package price
                from api.rentals.models import RentalPackage
                package = RentalPackage.objects.get(id=package_id, is_active=True)
                amount = package.price
            elif scenario == 'settle_dues':
                if not rental_id:
                    raise ServiceException(
                        detail="Rental ID required for settling dues",
                        code="rental_required"
                    )
                # Calculate amount based on rental dues
                from api.rentals.models import Rental
                rental = Rental.objects.get(id=rental_id, user=user)
                # Calculate dues including overdue amounts
                if rental.package.payment_model == 'POSTPAID':
                    # Calculate actual usage cost
                    if rental.ended_at and rental.started_at:
                        usage_duration = rental.ended_at - rental.started_at
                        usage_minutes = int(usage_duration.total_seconds() / 60)
                        package_rate_per_minute = rental.package.price / rental.package.duration_minutes
                        amount = Decimal(str(usage_minutes)) * package_rate_per_minute

                        # Add overdue charges if applicable
                        if rental.ended_at > rental.due_at:
                            from api.common.utils.helpers import calculate_overdue_minutes, calculate_late_fee_amount
                            overdue_minutes = calculate_overdue_minutes(rental)
                            if overdue_minutes > 0:
                                late_fee = calculate_late_fee_amount(package_rate_per_minute, overdue_minutes)
                                amount += late_fee
                        else:
                            # Use package price as fallback
                            amount = rental.package.price
                    else:
                        # Use package price if duration not available
                        amount = rental.package.price
                else:
                    # Use package price for prepaid models with dues
                    amount = rental.overdue_amount
            else:
                raise ServiceException(
                    detail="Invalid scenario",
                    code="invalid_scenario"
                )

            # Get user's current points and wallet balance
            user_points = self._get_user_points(user)
            wallet_balance = self._get_wallet_balance(user)

            # Convert points to monetary value (10 points = NPR 1)
            points_value = convert_points_to_amount(user_points)

            # Calculate payment breakdown
            payment_breakdown = self._calculate_payment_breakdown(
                amount, user_points, wallet_balance, points_value
            )

            # Check if user has sufficient funds
            total_available = points_value + wallet_balance
            is_sufficient = total_available >= amount
            shortfall = max(Decimal('0'), amount - total_available)

            # Suggest top-up amount if needed
            suggested_topup = None
            if not is_sufficient:
                # Round up to nearest 100 for convenience
                suggested_topup = ((shortfall // 100) + 1) * 100

            return {
                'scenario': scenario,
                'total_amount': amount,
                'user_balances': {
                    'points': user_points,
                    'wallet': wallet_balance,
                    'points_to_npr_rate': 10.0  # 10 points = NPR 1
                },
                'payment_breakdown': {
                    'points_used': payment_breakdown['points_to_use'],
                    'points_amount': payment_breakdown['points_amount'],
                    'wallet_used': payment_breakdown['wallet_amount'],
                    'remaining_balance': {
                        'points': user_points - payment_breakdown['points_to_use'],
                        'wallet': wallet_balance - payment_breakdown['wallet_amount']
                    }
                },
                'is_sufficient': is_sufficient,
                'shortfall': shortfall,
                'suggested_topup': suggested_topup
            }

        except Exception as e:
            self.handle_service_error(e, "Failed to calculate payment options")
    
    def _get_user_points(self, user) -> int:
        """Get user's current points"""
        try:
            return user.points.current_points
        except UserPoints.DoesNotExist:
            return 0
    
    def _get_wallet_balance(self, user) -> Decimal:
        """Get user's wallet balance"""
        try:
            return user.wallet.balance
        except:
            return Decimal('0')
    
    def _calculate_payment_breakdown(self, amount: Decimal, user_points: int, wallet_balance: Decimal, points_value: Decimal) -> Dict[str, Any]:
        """Calculate how payment will be split between points and wallet"""
        # Use points first, then wallet
        points_to_use = 0
        points_amount = Decimal('0')
        wallet_amount = Decimal('0')
        
        if points_value >= amount:
            # Points are sufficient
            points_amount = amount
            points_to_use = int(amount * 10)  # Convert back to points (NPR 1 = 10 points)
        else:
            # Use all points, then wallet
            points_amount = points_value
            points_to_use = user_points
            wallet_amount = amount - points_value
        
        return {
            'points_to_use': points_to_use,
            'points_amount': points_amount,
            'wallet_amount': wallet_amount,
            'total_amount': points_amount + wallet_amount
        }


class PaymentIntentService(CRUDService):
    """Service for payment intents"""
    model = PaymentIntent
    
    @transaction.atomic
    def create_topup_intent(self, user, amount: Decimal, payment_method_id: str) -> PaymentIntent:
        """Create payment intent for wallet top-up"""
        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
            
            # Validate amount against payment method limits
            if amount < payment_method.min_amount:
                raise ServiceException(
                    detail=f"Minimum amount is {payment_method.min_amount}",
                    code="amount_too_low"
                )
            
            if payment_method.max_amount and amount > payment_method.max_amount:
                raise ServiceException(
                    detail=f"Maximum amount is {payment_method.max_amount}",
                    code="amount_too_high"
                )
            
            # Create payment intent
            intent = PaymentIntent.objects.create(
                user=user,
                payment_method=payment_method,
                intent_id=str(uuid.uuid4()),
                intent_type='WALLET_TOPUP',
                amount=amount,
                currency='NPR',
                expires_at=timezone.now() + timezone.timedelta(minutes=30),
                intent_metadata={
                    'user_id': str(user.id),
                    'payment_method': payment_method.gateway
                }
            )
            
            # Generate payment URL (integrate with actual payment gateway)
            gateway_url = self._generate_payment_url(intent, payment_method)
            intent.gateway_url = gateway_url
            intent.save(update_fields=['gateway_url'])
            
            self.log_info(f"Top-up intent created: {intent.intent_id} for user {user.username}")
            return intent
            
        except PaymentMethod.DoesNotExist:
            raise ServiceException(
                detail="Invalid payment method",
                code="invalid_payment_method"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to create top-up intent")
    
    def _generate_payment_url(self, intent: PaymentIntent, payment_method: PaymentMethod) -> str:
        """Generate payment URL for gateway"""
        # This would integrate with actual payment gateways
        # For now, return a placeholder URL
        base_url = "https://api.example.com/payment"
        return f"{base_url}/{payment_method.gateway}/{intent.intent_id}"
    
    @transaction.atomic
    def verify_topup_payment(self, intent_id: str, gateway_reference: str = None) -> Dict[str, Any]:
        """Verify top-up payment and update wallet"""
        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id)
            
            if intent.status != 'PENDING':
                raise ServiceException(
                    detail="Payment intent is not pending",
                    code="invalid_intent_status"
                )
            
            if timezone.now() > intent.expires_at:
                raise ServiceException(
                    detail="Payment intent has expired",
                    code="intent_expired"
                )
            
            # Verify payment with gateway (mock verification for now)
            payment_verified = self._verify_with_gateway(intent, gateway_reference)
            
            if payment_verified:
                # Create transaction record
                transaction_obj = Transaction.objects.create(
                    user=intent.user,
                    payment_method=intent.payment_method,
                    transaction_id=generate_transaction_id(),
                    transaction_type='TOPUP',
                    amount=intent.amount,
                    status='SUCCESS',
                    payment_method_type='GATEWAY',
                    gateway_reference=gateway_reference
                )
                
                # Add balance to wallet
                wallet_service = WalletService()
                wallet_service.add_balance(
                    intent.user,
                    intent.amount,
                    f"Wallet top-up via {intent.payment_method.name}",
                    transaction_obj
                )
                
                # Award points for top-up
                from api.points.tasks import award_topup_points_task
                award_topup_points_task.delay(intent.user.id, float(intent.amount))
                
                # Update intent status
                intent.status = 'COMPLETED'
                intent.completed_at = timezone.now()
                intent.save(update_fields=['status', 'completed_at'])
                
                self.log_info(f"Top-up verified and processed: {intent.intent_id}")
                
                return {
                    'status': 'SUCCESS',
                    'transaction_id': transaction_obj.transaction_id,
                    'amount': intent.amount,
                    'new_balance': intent.user.wallet.balance
                }
            else:
                # Mark as failed
                intent.status = 'FAILED'
                intent.save(update_fields=['status'])
                
                raise ServiceException(
                    detail="Payment verification failed",
                    code="payment_verification_failed"
                )
                
        except PaymentIntent.DoesNotExist:
            raise ServiceException(
                detail="Payment intent not found",
                code="intent_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to verify top-up payment")
    
    def _verify_with_gateway(self, intent: PaymentIntent, gateway_reference: str) -> bool:
        """Verify payment with actual gateway"""
        # This would integrate with actual payment gateway APIs
        # For now, return True for successful verification
        return True
    
    def get_payment_status(self, intent_id: str) -> Dict[str, Any]:
        """Get payment status"""
        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id)
            
            return {
                'intent_id': intent_id,
                'status': intent.status,
                'amount': intent.amount,
                'currency': intent.currency,
                'gateway_reference': intent.intent_metadata.get('gateway_reference'),
                'completed_at': intent.completed_at,
                'failure_reason': intent.intent_metadata.get('failure_reason')
            }
            
        except PaymentIntent.DoesNotExist:
            raise ServiceException(
                detail="Payment intent not found",
                code="intent_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get payment status")
    
    @transaction.atomic
    def cancel_payment_intent(self, intent_id: str, user) -> Dict[str, Any]:
        """Cancel a pending payment intent"""
        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id, user=user)
            
            if intent.status != 'PENDING':
                raise ServiceException(
                    detail="Only pending payment intents can be cancelled",
                    code="invalid_intent_status"
                )
            
            # Update intent status
            intent.status = 'CANCELLED'
            intent.intent_metadata['cancelled_at'] = timezone.now().isoformat()
            intent.intent_metadata['cancelled_by'] = 'user'
            intent.save(update_fields=['status', 'intent_metadata'])
            
            self.log_info(f"Payment intent cancelled: {intent_id} by user {user.username}")
            
            return {
                'status': 'CANCELLED',
                'intent_id': intent_id,
                'message': 'Payment intent cancelled successfully'
            }
            
        except PaymentIntent.DoesNotExist:
            raise ServiceException(
                detail="Payment intent not found",
                code="intent_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to cancel payment intent")


class RentalPaymentService(BaseService):
    """Service for rental payments"""
    
    @transaction.atomic
    def process_rental_payment(self, user, rental, payment_breakdown: Dict[str, Any]) -> Transaction:
        """Process payment for rental"""
        try:
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                user=user,
                related_rental=rental,
                transaction_id=generate_transaction_id(),
                transaction_type='RENTAL',
                amount=payment_breakdown['total_amount'],
                status='SUCCESS',
                payment_method_type='COMBINATION' if payment_breakdown['points_to_use'] > 0 and payment_breakdown['wallet_amount'] > 0 else 'POINTS' if payment_breakdown['points_to_use'] > 0 else 'WALLET'
            )
            
            # Deduct points if used
            if payment_breakdown['points_to_use'] > 0:
                from api.points.services import PointsService
                points_service = PointsService()
                points_service.deduct_points(
                    user,
                    payment_breakdown['points_to_use'],
                    'RENTAL_PAYMENT',
                    f"Payment for rental {rental.rental_code}"
                )
            
            # Deduct wallet balance if used
            if payment_breakdown['wallet_amount'] > 0:
                wallet_service = WalletService()
                wallet_service.deduct_balance(
                    user,
                    payment_breakdown['wallet_amount'],
                    f"Payment for rental {rental.rental_code}",
                    transaction_obj
                )
            
            self.log_info(f"Rental payment processed: {rental.rental_code} for user {user.username}")
            return transaction_obj
            
        except Exception as e:
            self.handle_service_error(e, "Failed to process rental payment")
    
    @transaction.atomic
    def pay_rental_due(self, user, rental, payment_breakdown: Dict[str, Any]) -> Transaction:
        """Pay outstanding rental dues"""
        try:
            # Create transaction record
            total_amount = payment_breakdown['total_amount']
            payment_type = 'COMBINATION' if payment_breakdown['points_to_use'] > 0 and payment_breakdown['wallet_amount'] > 0 else 'POINTS' if payment_breakdown['points_to_use'] > 0 else 'WALLET'

            transaction_obj = Transaction.objects.create(
                user=user,
                related_rental=rental,
                transaction_id=generate_transaction_id(),
                transaction_type='RENTAL_DUE',
                amount=total_amount,
                status='SUCCESS',
                payment_method_type=payment_type
            )

            # Deduct points if used
            if payment_breakdown['points_to_use'] > 0:
                from api.points.services import PointsService
                points_service = PointsService()
                points_service.deduct_points(
                    user,
                    payment_breakdown['points_to_use'],
                    'DUE_PAYMENT',
                    f"Due payment for rental {rental.rental_code}"
                )

            # Deduct wallet if used
            if payment_breakdown['wallet_amount'] > 0:
                wallet_service = WalletService()
                wallet_service.deduct_balance(
                    user,
                    payment_breakdown['wallet_amount'],
                    f"Due payment for rental {rental.rental_code}",
                    transaction_obj
                )

            # Clear rental dues and overdue amounts
            rental.overdue_amount = Decimal('0')
            rental.payment_status = 'PAID'
            rental.save(update_fields=['overdue_amount', 'payment_status', 'updated_at'])

            self.log_info(f"Rental due paid: {rental.rental_code} for user {user.username} - amount: {total_amount}")
            return transaction_obj

        except Exception as e:
            self.handle_service_error(e, "Failed to pay rental due")


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
                if gateway not in ['khalti', 'esewa', 'stripe']:
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


class TransactionService(CRUDService):
    """Service for transaction operations"""
    model = Transaction
    
    def get_user_transactions(self, user, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get user's transaction history with filters"""
        try:
            queryset = Transaction.objects.filter(user=user).select_related('payment_method', 'related_rental')
            
            # Apply filters
            if filters:
                if filters.get('transaction_type'):
                    queryset = queryset.filter(transaction_type=filters['transaction_type'])
                
                if filters.get('status'):
                    queryset = queryset.filter(status=filters['status'])
                
                if filters.get('start_date'):
                    queryset = queryset.filter(created_at__gte=filters['start_date'])
                
                if filters.get('end_date'):
                    queryset = queryset.filter(created_at__lte=filters['end_date'])
            
            # Order by latest first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = filters.get('page', 1) if filters else 1
            page_size = filters.get('page_size', 20) if filters else 20
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get user transactions")