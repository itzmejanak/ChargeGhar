from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from typing import Dict, Any

from api.common.tasks.base import BaseTask, PaymentTask
from api.payments.models import (
    Transaction, PaymentIntent, PaymentWebhook, Refund, Wallet
)


@shared_task(base=PaymentTask, bind=True)
def process_payment_webhook(self, webhook_data: Dict[str, Any]):
    """Process payment gateway webhook"""
    try:
        # Create webhook record
        webhook = PaymentWebhook.objects.create(
            gateway=webhook_data['gateway'],
            event_type=webhook_data['event_type'],
            payload=webhook_data['payload'],
            status='RECEIVED'
        )
        
        # Process based on gateway and event type
        if webhook_data['gateway'] == 'khalti':
            result = self._process_khalti_webhook(webhook_data)
        elif webhook_data['gateway'] == 'esewa':
            result = self._process_esewa_webhook(webhook_data)
        elif webhook_data['gateway'] == 'stripe':
            result = self._process_stripe_webhook(webhook_data)
        else:
            raise ValueError(f"Unsupported gateway: {webhook_data['gateway']}")
        
        # Update webhook status
        webhook.status = 'PROCESSED'
        webhook.processing_result = str(result)
        webhook.processed_at = timezone.now()
        webhook.save(update_fields=['status', 'processing_result', 'processed_at'])
        
        self.logger.info(f"Webhook processed: {webhook_data['gateway']} - {webhook_data['event_type']}")
        return result
        
    except Exception as e:
        # Mark webhook as failed
        if 'webhook' in locals():
            webhook.status = 'FAILED'
            webhook.processing_result = str(e)
            webhook.processed_at = timezone.now()
            webhook.save(update_fields=['status', 'processing_result', 'processed_at'])
        
        self.logger.error(f"Failed to process webhook: {str(e)}")
        raise
    
    def _process_khalti_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Khalti webhook"""
        payload = webhook_data['payload']
        event_type = webhook_data['event_type']
        
        if event_type == 'payment.completed':
            return self._handle_payment_completed(payload, 'khalti')
        elif event_type == 'payment.failed':
            return self._handle_payment_failed(payload, 'khalti')
        else:
            self.logger.warning(f"Unhandled Khalti event: {event_type}")
            return {'status': 'ignored', 'reason': 'unhandled_event'}
    
    def _process_esewa_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process eSewa webhook"""
        payload = webhook_data['payload']
        event_type = webhook_data['event_type']
        
        if event_type == 'payment_success':
            return self._handle_payment_completed(payload, 'esewa')
        elif event_type == 'payment_failure':
            return self._handle_payment_failed(payload, 'esewa')
        else:
            self.logger.warning(f"Unhandled eSewa event: {event_type}")
            return {'status': 'ignored', 'reason': 'unhandled_event'}
    
    def _process_stripe_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe webhook"""
        payload = webhook_data['payload']
        event_type = webhook_data['event_type']
        
        if event_type == 'payment_intent.succeeded':
            return self._handle_payment_completed(payload, 'stripe')
        elif event_type == 'payment_intent.payment_failed':
            return self._handle_payment_failed(payload, 'stripe')
        else:
            self.logger.warning(f"Unhandled Stripe event: {event_type}")
            return {'status': 'ignored', 'reason': 'unhandled_event'}
    
    def _handle_payment_completed(self, payload: Dict[str, Any], gateway: str) -> Dict[str, Any]:
        """Handle successful payment"""
        try:
            # Extract intent ID from payload (gateway-specific)
            intent_id = self._extract_intent_id(payload, gateway)
            
            # Find payment intent
            intent = PaymentIntent.objects.get(intent_id=intent_id)
            
            if intent.status == 'COMPLETED':
                return {'status': 'already_processed'}
            
            # Process the payment using the payment service
            from api.payments.services import PaymentIntentService
            service = PaymentIntentService()
            
            gateway_reference = payload.get('transaction_id') or payload.get('reference')
            result = service.verify_topup_payment(intent_id, gateway_reference)
            
            return {'status': 'processed', 'result': result}
            
        except PaymentIntent.DoesNotExist:
            self.logger.error(f"Payment intent not found: {intent_id}")
            return {'status': 'error', 'reason': 'intent_not_found'}
        except Exception as e:
            self.logger.error(f"Failed to handle payment completion: {str(e)}")
            raise
    
    def _handle_payment_failed(self, payload: Dict[str, Any], gateway: str) -> Dict[str, Any]:
        """Handle failed payment"""
        try:
            intent_id = self._extract_intent_id(payload, gateway)
            
            intent = PaymentIntent.objects.get(intent_id=intent_id)
            intent.status = 'FAILED'
            intent.intent_metadata['failure_reason'] = payload.get('failure_reason', 'Payment failed')
            intent.save(update_fields=['status', 'intent_metadata'])
            
            return {'status': 'marked_failed'}
            
        except PaymentIntent.DoesNotExist:
            self.logger.error(f"Payment intent not found: {intent_id}")
            return {'status': 'error', 'reason': 'intent_not_found'}
        except Exception as e:
            self.logger.error(f"Failed to handle payment failure: {str(e)}")
            raise
    
    def _extract_intent_id(self, payload: Dict[str, Any], gateway: str) -> str:
        """Extract intent ID from gateway payload"""
        if gateway == 'khalti':
            return payload.get('merchant_reference') or payload.get('order_id')
        elif gateway == 'esewa':
            return payload.get('product_code') or payload.get('reference')
        elif gateway == 'stripe':
            return payload.get('metadata', {}).get('intent_id')
        else:
            raise ValueError(f"Unknown gateway: {gateway}")


@shared_task(base=BaseTask, bind=True)
def expire_payment_intents(self):
    """Mark expired payment intents as failed"""
    try:
        expired_intents = PaymentIntent.objects.filter(
            status='PENDING',
            expires_at__lt=timezone.now()
        )
        
        expired_count = 0
        for intent in expired_intents:
            intent.status = 'CANCELLED'
            intent.intent_metadata['expiry_reason'] = 'Expired due to timeout'
            intent.save(update_fields=['status', 'intent_metadata'])
            expired_count += 1
        
        self.logger.info(f"Expired {expired_count} payment intents")
        return {'expired_count': expired_count}
        
    except Exception as e:
        self.logger.error(f"Failed to expire payment intents: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def reconcile_transactions(self, date_str: str = None):
    """Reconcile transactions with gateway records"""
    try:
        if date_str:
            from datetime import datetime
            target_date = datetime.fromisoformat(date_str).date()
        else:
            target_date = timezone.now().date()
        
        # Get transactions for the date
        transactions = Transaction.objects.filter(
            created_at__date=target_date,
            status='SUCCESS',
            payment_method_type='GATEWAY'
        )
        
        reconciliation_results = []
        
        for transaction in transactions:
            # Mock reconciliation - in real implementation, 
            # you would call gateway APIs to verify transaction status
            gateway_status = self._check_gateway_status(transaction)
            
            if gateway_status != transaction.status:
                # Mark for manual review
                transaction.gateway_response['reconciliation_flag'] = True
                transaction.gateway_response['gateway_status'] = gateway_status
                transaction.save(update_fields=['gateway_response'])
                
                reconciliation_results.append({
                    'transaction_id': transaction.transaction_id,
                    'local_status': transaction.status,
                    'gateway_status': gateway_status,
                    'action': 'flagged_for_review'
                })
        
        self.logger.info(f"Reconciled {transactions.count()} transactions for {target_date}")
        return {
            'date': str(target_date),
            'total_transactions': transactions.count(),
            'discrepancies': len(reconciliation_results),
            'results': reconciliation_results
        }
        
    except Exception as e:
        self.logger.error(f"Failed to reconcile transactions: {str(e)}")
        raise
    
    def _check_gateway_status(self, transaction: Transaction) -> str:
        """Check transaction status with gateway"""
        # Mock implementation - replace with actual gateway API calls
        return 'SUCCESS'


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
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'total_transactions': transactions.count(),
            'successful_transactions': transactions.filter(status='SUCCESS').count(),
            'failed_transactions': transactions.filter(status='FAILED').count(),
            'total_revenue': transactions.filter(status='SUCCESS').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0'),
            'transaction_types': {},
            'payment_methods': {},
            'daily_breakdown': []
        }
        
        # Transaction type breakdown
        for tx_type, _ in Transaction.TRANSACTION_TYPE_CHOICES:
            count = transactions.filter(transaction_type=tx_type).count()
            revenue = transactions.filter(
                transaction_type=tx_type, 
                status='SUCCESS'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            analytics['transaction_types'][tx_type] = {
                'count': count,
                'revenue': float(revenue)
            }
        
        # Payment method breakdown
        for method_type, _ in Transaction.PAYMENT_METHOD_TYPE_CHOICES:
            count = transactions.filter(payment_method_type=method_type).count()
            analytics['payment_methods'][method_type] = count
        
        # Cache analytics
        from django.core.cache import cache
        cache_key = f"payment_analytics:{start_date.date()}:{end_date.date()}"
        cache.set(cache_key, analytics, timeout=3600)  # 1 hour
        
        self.logger.info(f"Payment analytics generated for {start_date.date()} to {end_date.date()}")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate payment analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def process_pending_refunds(self):
    """Process pending refund requests"""
    try:
        pending_refunds = Refund.objects.filter(status='APPROVED')
        
        processed_count = 0
        failed_count = 0
        
        for refund in pending_refunds:
            try:
                # Process refund with gateway
                success = self._process_gateway_refund(refund)
                
                if success:
                    refund.status = 'PROCESSED'
                    refund.processed_at = timezone.now()
                    refund.gateway_reference = f"REF_{refund.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Add refund amount back to wallet
                    from api.payments.services import WalletService
                    wallet_service = WalletService()
                    wallet_service.add_balance(
                        refund.requested_by,
                        refund.amount,
                        f"Refund for transaction {refund.transaction.transaction_id}"
                    )
                    
                    processed_count += 1
                else:
                    failed_count += 1
                
                refund.save(update_fields=['status', 'processed_at', 'gateway_reference'])
                
            except Exception as e:
                self.logger.error(f"Failed to process refund {refund.id}: {str(e)}")
                failed_count += 1
        
        self.logger.info(f"Processed {processed_count} refunds, {failed_count} failed")
        return {
            'processed_count': processed_count,
            'failed_count': failed_count
        }
        
    except Exception as e:
        self.logger.error(f"Failed to process pending refunds: {str(e)}")
        raise
    
def _process_gateway_refund(self, refund: Refund) -> bool:
    """Process refund with payment gateway"""
    try:
        transaction = refund.transaction
        
        # Skip gateway verification if payment was from wallet or points
        if transaction.payment_method_type in ['WALLET', 'POINTS']:
            self.logger.info(f"Refund {refund.id} is for wallet/points payment, no gateway verification needed")
            return True
            
        # Get gateway reference
        gateway_reference = transaction.gateway_reference
        
        if not gateway_reference:
            self.logger.error(f"No gateway reference found for transaction {transaction.transaction_id}")
            return False
            
        # Determine gateway from reference or transaction metadata
        # This is a simplified approach since payment_method table is missing
        gateway = None
        if gateway_reference.startswith('khalti_'):
            gateway = 'khalti'
        elif gateway_reference.startswith('esewa_'):
            gateway = 'esewa'
        elif gateway_reference.startswith('stripe_'):
            gateway = 'stripe'
        else:
            # Try to extract from transaction metadata if available
            if hasattr(transaction, 'metadata') and transaction.metadata and 'gateway' in transaction.metadata:
                gateway = transaction.metadata.get('gateway')
        
        if not gateway:
            self.logger.error(f"Could not determine gateway for transaction {transaction.transaction_id}")
            return False
            
        # Process based on gateway type
        if gateway == 'khalti':
            return self._process_khalti_refund(transaction, refund)
        elif gateway == 'esewa':
            return self._process_esewa_refund(transaction, refund)
        elif gateway == 'stripe':
            return self._process_stripe_refund(transaction, refund)
        else:
            self.logger.error(f"Unsupported gateway: {gateway}")
            return False
            
    except Exception as e:
        self.logger.error(f"Error processing gateway refund: {str(e)}")
        return False
        
def _process_khalti_refund(self, transaction, refund):
    """Process refund through Khalti gateway"""
    try:
        import requests
        import os
        
        # Get Khalti configuration from environment variables instead of payment_method
        secret_key = os.environ.get('KHALTI_SECRET_KEY')
        if not secret_key:
            self.logger.error("Khalti secret key not found in environment variables")
            return False
            
        # Verify transaction exists and is refundable in Khalti
        if not transaction.gateway_reference:
            self.logger.error("No Khalti reference to refund")
            return False
            
        self.logger.info(f"Processing Khalti refund for transaction {transaction.transaction_id}")
        
        # Make API call to Khalti refund endpoint
        khalti_response = requests.post(
            "https://khalti.com/api/v2/refund/",
            headers={"Authorization": f"Key {secret_key}"},
            json={
                "transaction_id": transaction.gateway_reference, 
                "amount": float(refund.amount),
                "refund_id": str(refund.id)
            }
        )
        
        if khalti_response.status_code == 200:
            response_data = khalti_response.json()
            # Store the response for reference
            refund.gateway_response = response_data
            refund.save(update_fields=['gateway_response'])
            return True
        else:
            self.logger.error(f"Khalti refund failed: {khalti_response.text}")
            refund.gateway_response = {"error": khalti_response.text}
            refund.save(update_fields=['gateway_response'])
            return False
        
    except Exception as e:
        self.logger.error(f"Khalti refund error: {str(e)}")
        return False
        
def _process_esewa_refund(self, transaction, refund):
    """Process refund through eSewa gateway"""
    try:
        import requests
        
        # Get eSewa configuration
        config = transaction.payment_method.configuration
        if not config or 'merchant_id' not in config or 'secret_key' not in config:
            self.logger.error("eSewa configuration missing")
            return False
            
        # Verify transaction exists and is refundable in eSewa
        if not transaction.gateway_reference:
            self.logger.error("No eSewa reference to refund")
            return False
            
        self.logger.info(f"Processing eSewa refund for transaction {transaction.transaction_id}")
        
        # Make API call to eSewa refund endpoint
        esewa_response = requests.post(
            "https://esewa.com.np/api/refund/",
            headers={
                "Authorization": f"Bearer {config['secret_key']}",
                "merchantId": config['merchant_id']
            },
            json={
                "transactionId": transaction.gateway_reference,
                "amount": float(refund.amount),
                "refundId": str(refund.id)
            }
        )
        
        if esewa_response.status_code == 200:
            response_data = esewa_response.json()
            # Store the response for reference
            refund.gateway_response = response_data
            refund.save(update_fields=['gateway_response'])
            return True
        else:
            self.logger.error(f"eSewa refund failed: {esewa_response.text}")
            refund.gateway_response = {"error": esewa_response.text}
            refund.save(update_fields=['gateway_response'])
            return False
        
    except Exception as e:
        self.logger.error(f"eSewa refund error: {str(e)}")
        return False
        
def _process_stripe_refund(self, transaction, refund):
    """Process refund through Stripe gateway"""
    try:
        # Get Stripe configuration
        config = transaction.payment_method.configuration
        if not config or 'secret_key' not in config:
            self.logger.error("Stripe configuration missing")
            return False
            
        # Verify transaction exists and is refundable in Stripe
        if not transaction.gateway_reference:
            self.logger.error("No Stripe charge ID to refund")
            return False
            
        self.logger.info(f"Processing Stripe refund for transaction {transaction.transaction_id}")
        
        # Use Stripe SDK to process refund
        import stripe
        stripe.api_key = config['secret_key']
        
        try:
            refund_response = stripe.Refund.create(
                charge=transaction.gateway_reference,
                amount=int(refund.amount * 100),  # Stripe uses cents
                metadata={"refund_id": str(refund.id)}
            )
            
            # Store the response for reference
            refund.gateway_response = {
                "id": refund_response.id,
                "status": refund_response.status,
                "amount": refund_response.amount / 100  # Convert back to dollars
            }
            refund.save(update_fields=['gateway_response'])
            
            return refund_response.status == 'succeeded'
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe API error: {str(e)}")
            refund.gateway_response = {"error": str(e)}
            refund.save(update_fields=['gateway_response'])
            return False
        
    except Exception as e:
        self.logger.error(f"Stripe refund error: {str(e)}")
        return False


@shared_task(base=BaseTask, bind=True)
def cleanup_old_payment_data(self):
    """Clean up old payment data"""
    try:
        # Clean up old completed payment intents (older than 3 months)
        three_months_ago = timezone.now() - timezone.timedelta(days=90)
        
        old_intents = PaymentIntent.objects.filter(
            status__in=['COMPLETED', 'FAILED', 'CANCELLED'],
            created_at__lt=three_months_ago
        )
        
        deleted_intents = old_intents.delete()[0]
        
        # Clean up old webhook records (older than 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        
        old_webhooks = PaymentWebhook.objects.filter(
            created_at__lt=six_months_ago
        )
        
        deleted_webhooks = old_webhooks.delete()[0]
        
        self.logger.info(f"Cleaned up {deleted_intents} payment intents and {deleted_webhooks} webhooks")
        return {
            'deleted_intents': deleted_intents,
            'deleted_webhooks': deleted_webhooks
        }
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup old payment data: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def sync_wallet_balances(self):
    """Sync and verify wallet balances"""
    try:
        wallets = Wallet.objects.all()
        
        discrepancies = []
        
        for wallet in wallets:
            # Calculate balance from wallet transactions
            from api.payments.models import WalletTransaction
            
            credits = WalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            debits = WalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='DEBIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            calculated_balance = credits - debits
            
            if calculated_balance != wallet.balance:
                discrepancies.append({
                    'wallet_id': str(wallet.id),
                    'user_id': str(wallet.user.id),
                    'stored_balance': float(wallet.balance),
                    'calculated_balance': float(calculated_balance),
                    'difference': float(wallet.balance - calculated_balance)
                })
        
        if discrepancies:
            # Send alert to admin
            from api.notifications.tasks import send_wallet_discrepancy_alert
            send_wallet_discrepancy_alert.delay(discrepancies)
        
        self.logger.info(f"Wallet balance sync completed. {len(discrepancies)} discrepancies found")
        return {
            'total_wallets': wallets.count(),
            'discrepancies_count': len(discrepancies),
            'discrepancies': discrepancies
        }
        
    except Exception as e:
        self.logger.error(f"Failed to sync wallet balances: {str(e)}")
        raise