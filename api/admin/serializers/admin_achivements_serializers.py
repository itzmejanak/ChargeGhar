
from __future__ import annotations
from rest_framework import serializers


# ============================================================
# Achievement Management Serializers
# ============================================================

class CreateAchievementSerializer(serializers.Serializer):
    """Serializer for creating achievements"""
    name = serializers.CharField(
        required=True,
        max_length=100,
        help_text="Achievement name"
    )
    description = serializers.CharField(
        required=True,
        help_text="Achievement description"
    )
    criteria_type = serializers.ChoiceField(
        choices=['rental_count', 'timely_return_count', 'referral_count'],
        required=True,
        help_text="Type of criteria"
    )
    criteria_value = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Value to achieve"
    )
    reward_type = serializers.ChoiceField(
        choices=['points'],
        required=True,
        help_text="Type of reward"
    )
    reward_value = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Reward value"
    )
    
    def validate_name(self, value):
        """Validate achievement name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Achievement name cannot be empty")
        return value.strip()
    
    def validate_description(self, value):
        """Validate achievement description"""
        if not value or not value.strip():
            raise serializers.ValidationError("Achievement description cannot be empty")
        return value.strip()


class UpdateAchievementSerializer(serializers.Serializer):
    """Serializer for updating achievements"""
    name = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Achievement name"
    )
    description = serializers.CharField(
        required=False,
        help_text="Achievement description"
    )
    criteria_type = serializers.ChoiceField(
        choices=['rental_count', 'timely_return_count', 'referral_count'],
        required=False,
        help_text="Type of criteria"
    )
    criteria_value = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Value to achieve"
    )
    reward_type = serializers.ChoiceField(
        choices=['points'],
        required=False,
        help_text="Type of reward"
    )
    reward_value = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Reward value"
    )
    is_active = serializers.BooleanField(
        required=False,
        help_text="Active status"
    )


class AchievementFiltersSerializer(serializers.Serializer):
    """Serializer for achievement list filters"""
    criteria_type = serializers.ChoiceField(
        choices=['rental_count', 'timely_return_count', 'referral_count'],
        required=False,
        help_text="Filter by criteria type"
    )
    is_active = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Filter by active status (true=active only, false=inactive only, null/omit=all)"
    )
    search = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Search by name or description"
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