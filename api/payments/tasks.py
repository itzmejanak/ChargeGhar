from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from typing import Dict, Any

from api.common.tasks.base import BaseTask, PaymentTask
from api.payments.models import Transaction, PaymentIntent, Refund, Wallet


class PaymentWebhookHandler(PaymentTask):
    """Handler for payment webhook processing"""

    def _handle_payment_completed(
        self, payload: Dict[str, Any], gateway: str
    ) -> Dict[str, Any]:
        """Handle successful payment"""
        try:
            # Extract intent ID from payload (gateway-specific)
            intent_id = self._extract_intent_id(payload, gateway)

            # Find payment intent
            intent = PaymentIntent.objects.get(intent_id=intent_id)

            if intent.status == "COMPLETED":
                return {"status": "already_processed"}

            # Process the payment using the payment service
            from api.payments.services import PaymentIntentService

            service = PaymentIntentService()

            gateway_reference = payload.get("transaction_id") or payload.get("reference")
            result = service.verify_topup_payment(intent_id, gateway_reference)

            return {"status": "processed", "result": result}

        except PaymentIntent.DoesNotExist:
            self.logger.error(f"Payment intent not found: {intent_id}")
            return {"status": "error", "reason": "intent_not_found"}
        except Exception as e:
            self.logger.error(f"Failed to handle payment completion: {str(e)}")
            raise

    def _handle_payment_failed(
        self, payload: Dict[str, Any], gateway: str
    ) -> Dict[str, Any]:
        """Handle failed payment"""
        try:
            intent_id = self._extract_intent_id(payload, gateway)

            intent = PaymentIntent.objects.get(intent_id=intent_id)
            intent.status = "FAILED"
            intent.intent_metadata["failure_reason"] = payload.get(
                "failure_reason", "Payment failed"
            )
            intent.save(update_fields=["status", "intent_metadata"])

            return {"status": "marked_failed"}

        except PaymentIntent.DoesNotExist:
            self.logger.error(f"Payment intent not found: {intent_id}")
            return {"status": "error", "reason": "intent_not_found"}
        except Exception as e:
            self.logger.error(f"Failed to handle payment failure: {str(e)}")
            raise

    def _extract_intent_id(self, payload: Dict[str, Any], gateway: str) -> str:
        """Extract intent ID from gateway payload"""
        if gateway == "khalti":
            return payload.get("merchant_reference") or payload.get("order_id")
        elif gateway == "esewa":
            return payload.get("product_code") or payload.get("reference")
        else:
            raise ValueError(f"Unknown gateway: {gateway}")


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


@shared_task(base=BaseTask, bind=True)
def generate_payment_analytics(self, date_range: tuple = None):
    """Generate payment analytics report"""
    try:
        if date_range:
            from datetime import datetime

            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])
        else:
            # Default to last 30 days
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=30)

        # Get transaction statistics
        transactions = Transaction.objects.filter(
            created_at__range=(start_date, end_date)
        )

        analytics = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_transactions": transactions.count(),
            "successful_transactions": transactions.filter(status="SUCCESS").count(),
            "failed_transactions": transactions.filter(status="FAILED").count(),
            "total_revenue": transactions.filter(status="SUCCESS").aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0"),
            "transaction_types": {},
            "payment_methods": {},
            "daily_breakdown": [],
        }

        # Transaction type breakdown
        for tx_type, _ in Transaction.TRANSACTION_TYPE_CHOICES:
            count = transactions.filter(transaction_type=tx_type).count()
            revenue = transactions.filter(
                transaction_type=tx_type, status="SUCCESS"
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            analytics["transaction_types"][tx_type] = {
                "count": count,
                "revenue": float(revenue),
            }

        # Payment method breakdown
        for method_type, _ in Transaction.PAYMENT_METHOD_TYPE_CHOICES:
            count = transactions.filter(payment_method_type=method_type).count()
            analytics["payment_methods"][method_type] = count

        # Cache analytics
        from django.core.cache import cache

        cache_key = f"payment_analytics:{start_date.date()}:{end_date.date()}"
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour

        self.logger.info(
            f"Payment analytics generated for {start_date.date()} to {end_date.date()}"
        )
        return analytics

    except Exception as e:
        self.logger.error(f"Failed to generate payment analytics: {str(e)}")
        raise