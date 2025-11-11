
from __future__ import annotations
from rest_framework import serializers


# ============================================================
# Points Management Serializers
# ============================================================

class AdjustUserPointsSerializer(serializers.Serializer):
    """Serializer for adjusting user points"""
    user_id = serializers.IntegerField(
        required=True,
        help_text="User ID to adjust points for"
    )
    points = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Number of points to adjust"
    )
    adjustment_type = serializers.ChoiceField(
        choices=['ADD', 'DEDUCT'],
        required=True,
        help_text="Type of adjustment (ADD or DEDUCT)"
    )
    reason = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Reason for the adjustment"
    )
    
    def validate_reason(self, value):
        """Validate reason is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Reason cannot be empty")
        return value.strip()


class PointsAnalyticsFiltersSerializer(serializers.Serializer):
    """Serializer for points analytics filters"""
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering (ISO format)"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering (ISO format)"
    )


class PointsHistoryFiltersSerializer(serializers.Serializer):
    """Serializer for points history filters"""
    transaction_type = serializers.ChoiceField(
        choices=['EARNED', 'SPENT', 'ADJUSTMENT'],
        required=False,
        help_text="Filter by transaction type"
    )
    source = serializers.ChoiceField(
        choices=[
            'SIGNUP', 'REFERRAL_INVITER', 'REFERRAL_INVITEE', 
            'TOPUP', 'RENTAL_COMPLETE', 'TIMELY_RETURN', 
            'COUPON', 'RENTAL_PAYMENT', 'ADMIN_ADJUSTMENT'
        ],
        required=False,
        help_text="Filter by source"
    )
    search = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Search by user ID, username, email, or transaction description"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    page = serializers.IntegerField(
        required=False,
        min_value=1,
        default=1,
        help_text="Page number"
    )
    page_size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=20,
        help_text="Items per page"
    )



