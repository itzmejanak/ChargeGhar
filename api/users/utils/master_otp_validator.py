"""Master OTP validator for development/testing"""
from api.system.services import AppConfigService


def is_master_otp_enabled() -> bool:
    """Check if master OTP is enabled"""
    config_service = AppConfigService()
    return config_service.get_config_cached('MASTER_OTP_ENABLED', 'false').lower() == 'true'


def get_master_otp_numbers() -> list:
    """Get list of master OTP numbers"""
    config_service = AppConfigService()
    numbers_str = config_service.get_config_cached('MASTER_OTP_NUMBERS', '')
    return [n.strip() for n in numbers_str.split(',') if n.strip()]


def get_master_otp() -> str:
    """Get master OTP value"""
    config_service = AppConfigService()
    return config_service.get_config_cached('MASTER_OTP', '')


def is_master_number(identifier: str) -> bool:
    """Check if identifier is in master OTP numbers list"""
    if not is_master_otp_enabled():
        return False
    return identifier in get_master_otp_numbers()


def validate_master_otp(identifier: str, otp: str) -> bool:
    """Validate master OTP - requires BOTH identifier in list AND OTP match"""
    if not is_master_otp_enabled():
        return False
    return is_master_number(identifier) and otp == get_master_otp()
