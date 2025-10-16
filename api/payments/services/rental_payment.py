from __future__ import annotations

from typing import Dict, Any
from decimal import Decimal
from django.db import transaction

from api.common.services.base import BaseService, ServiceException
from api.common.utils.helpers import generate_transaction_id
from api.payments.models import Transaction
from api.payments.services.wallet import WalletService


class RentalPaymentService(BaseService):
    """Service for rental payments"""

    @transaction.atomic
    def process_rental_payment(self, user, rental, payment_breakdown: Dict[str, Any]) -> Transaction:
        """Process payment for rental"""
        try:
            # Get values with defaults to handle missing keys
            points_amount = payment_breakdown.get('points_amount', Decimal('0'))
            wallet_amount = payment_breakdown.get('wallet_amount', Decimal('0'))
            points_to_use = payment_breakdown.get('points_to_use', 0)

            # Calculate total amount
            total_amount = points_amount + wallet_amount

            # Create transaction record
            transaction_obj = Transaction.objects.create(
                user=user,
                related_rental=rental,
                transaction_id=generate_transaction_id(),
                transaction_type='RENTAL',
                amount=total_amount,
                status='SUCCESS',
                payment_method_type='COMBINATION' if points_to_use > 0 and wallet_amount > 0 else 'POINTS' if points_to_use > 0 else 'WALLET'
            )

            # Get rental code or use a placeholder if rental is None
            rental_description = f"Payment for rental {rental.rental_code}" if rental else "Payment for new rental"

            # Deduct points if used
            if points_to_use > 0:
                from api.points.services import deduct_points
                deduct_points(
                    user,
                    points_to_use,
                    'RENTAL_PAYMENT',
                    rental_description,
                    async_send=False  # Immediate for payment processing
                )

            # Deduct wallet balance if used
            if wallet_amount > 0:
                wallet_service = WalletService()
                wallet_service.deduct_balance(
                    user,
                    wallet_amount,
                    rental_description,
                    transaction_obj
                )

            rental_code = rental.rental_code if rental else "new_rental"
            self.log_info(f"Rental payment processed: {rental_code} for user {user.username}")
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
                from api.points.services import deduct_points
                deduct_points(
                    user,
                    payment_breakdown['points_to_use'],
                    'DUE_PAYMENT',
                    f"Due payment for rental {rental.rental_code}",
                    async_send=False  # Immediate for payment processing
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