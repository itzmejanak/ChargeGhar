from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class ProfileIncompleteException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Profile must be completed before accessing this feature"
    default_code = "profile_incomplete"


class KYCNotVerifiedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "KYC verification required before accessing this feature"
    default_code = "kyc_not_verified"


class InsufficientBalanceException(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Insufficient wallet balance"
    default_code = "insufficient_balance"


class PendingDuesException(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Please clear pending dues before proceeding"
    default_code = "pending_dues"


class StationOfflineException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Station is currently offline"
    default_code = "station_offline"


class NoAvailableSlotsException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "No available slots at this station"
    default_code = "no_available_slots"


class ActiveRentalExistsException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "You already have an active rental"
    default_code = "active_rental_exists"


class PaymentFailedException(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Payment processing failed"
    default_code = "payment_failed"


class InvalidOTPException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or expired OTP"
    default_code = "invalid_otp"


class RateLimitExceededException(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Rate limit exceeded. Please try again later"
    default_code = "rate_limit_exceeded"


class StationMaintenanceException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Station is under maintenance"
    default_code = "station_maintenance"


class InvalidReferralCodeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid referral code"
    default_code = "invalid_referral_code"


class CouponExpiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Coupon has expired"
    default_code = "coupon_expired"


class CouponAlreadyUsedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Coupon has already been used"
    default_code = "coupon_already_used"