from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.db.models import Model

from api.common.services.base import CRUDService, ServiceException
from api.payments.models import Wallet, WalletTransaction, Transaction


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