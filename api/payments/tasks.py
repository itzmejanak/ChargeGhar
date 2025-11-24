from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from typing import Dict, Any

from api.common.tasks.base import BaseTask, PaymentTask
from api.payments.models import Transaction, PaymentIntent, Refund, Wallet

@shared_task(base=BaseTask, bind=True)
def expire_payment_intents(self):
    """Mark expired payment intents as failed"""
    try:
        expired_intents = PaymentIntent.objects.filter(
            status="PENDING", expires_at__lt=timezone.now()
        )

        expired_count = 0
        for intent in expired_intents:
            intent.status = "CANCELLED"
            intent.intent_metadata["expiry_reason"] = "Expired due to timeout"
            intent.save(update_fields=["status", "intent_metadata"])
            expired_count += 1

        self.logger.info(f"Expired {expired_count} payment intents")
        return {"expired_count": expired_count}

    except Exception as e:
        self.logger.error(f"Failed to expire payment intents: {str(e)}")
        raise