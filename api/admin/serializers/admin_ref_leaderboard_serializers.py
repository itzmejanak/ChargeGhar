
from __future__ import annotations
from rest_framework import serializers


# ============================================================
# Referral Management Serializers
# ============================================================

class ReferralAnalyticsFiltersSerializer(serializers.Serializer):
    """Serializer for referral analytics filters"""
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )


class UserReferralsFiltersSerializer(serializers.Serializer):
    """Serializer for user referrals filters"""
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


# ============================================================
# Leaderboard Serializers
# ============================================================

class LeaderboardFiltersSerializer(serializers.Serializer):
    """Serializer for leaderboard filters"""
    category = serializers.ChoiceField(
        choices=['overall', 'rentals', 'points', 'referrals', 'timely_returns'],
        required=False,
        default='overall',
        help_text="Leaderboard category"
    )
    period = serializers.ChoiceField(
        choices=['all_time', 'monthly', 'weekly'],
        required=False,
        default='all_time',
        help_text="Time period"
    )
    limit = serializers.IntegerField(
        required=False,
        min_value=10,
        max_value=500,
        default=100,
        help_text="Number of entries to return"
    )
