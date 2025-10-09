from __future__ import annotations

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api.payments.models import (
    Transaction, Wallet, WalletTransaction, PaymentIntent, 
    PaymentWebhook, Refund, PaymentMethod
)


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ['transaction_id', 'user', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'gateway_reference']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Wallet)
class WalletAdmin(ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'is_active', 'updated_at']
    list_filter = ['is_active', 'currency']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__username', 'description']
    readonly_fields = ['created_at']


@admin.register(PaymentIntent)
class PaymentIntentAdmin(ModelAdmin):
    list_display = ['intent_id', 'user', 'intent_type', 'amount', 'status', 'created_at']
    list_filter = ['intent_type', 'status', 'created_at']
    search_fields = ['user__username', 'intent_id']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(ModelAdmin):
    list_display = ['gateway', 'event_type', 'status', 'received_at', 'processed_at']
    list_filter = ['gateway', 'status', 'received_at']
    search_fields = ['gateway', 'event_type']
    readonly_fields = ['received_at', 'processed_at']


@admin.register(Refund)
class RefundAdmin(ModelAdmin):
    list_display = ['transaction', 'amount', 'status', 'requested_by', 'requested_at']
    list_filter = ['status', 'requested_at']
    search_fields = ['transaction__transaction_id', 'requested_by__username', 'reason']
    readonly_fields = ['requested_at', 'processed_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(ModelAdmin):
    list_display = ['name', 'gateway', 'is_active', 'min_amount', 'max_amount']
    list_filter = ['is_active', 'gateway']
    search_fields = ['name', 'gateway']
    readonly_fields = ['created_at', 'updated_at']