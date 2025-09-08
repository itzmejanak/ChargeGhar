from __future__ import annotations

import random
import string
import uuid
from typing import Any, Dict, Optional
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework import status


def generate_random_code(length: int = 6, include_letters: bool = True, include_numbers: bool = True) -> str:
    """Generate random alphanumeric code"""
    chars = ""
    if include_letters:
        chars += string.ascii_uppercase
    if include_numbers:
        chars += string.digits
    
    if not chars:
        raise ValueError("At least one character type must be included")
    
    return ''.join(random.choices(chars, k=length))


def generate_unique_code(prefix: str = "", length: int = 8) -> str:
    """Generate unique code with optional prefix"""
    code = generate_random_code(length)
    return f"{prefix}{code}" if prefix else code


def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_random_code(6)
    return f"TXN{timestamp}{random_part}"


def generate_rental_code() -> str:
    """Generate unique rental code"""
    return generate_random_code(8, include_letters=True, include_numbers=True)


def calculate_points_from_amount(amount: Decimal, points_per_unit: int = 10, unit_amount: Decimal = Decimal('100')) -> int:
    """Calculate points based on amount (default: 10 points per NPR 100)"""
    if amount <= 0:
        return 0
    return int((amount / unit_amount) * points_per_unit)


def convert_points_to_amount(points: int, points_per_unit: int = 10, unit_amount: Decimal = Decimal('1')) -> Decimal:
    """Convert points to monetary amount (default: 10 points = NPR 1)"""
    if points <= 0:
        return Decimal('0')
    return Decimal(points / points_per_unit) * unit_amount


def paginate_queryset(queryset, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """Paginate queryset and return pagination info"""
    # Ensure queryset is ordered to avoid pagination warnings
    if not queryset.ordered:
        queryset = queryset.order_by('id')
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return {
        'results': page_obj.object_list,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    }


def create_success_response(data: Any = None, message: str = "Success", status_code: int = status.HTTP_200_OK) -> Response:
    """Create standardized success response"""
    response_data = {
        'success': True,
        'message': message,
    }
    if data is not None:
        response_data['data'] = data
    
    return Response(response_data, status=status_code)


def create_error_response(message: str = "Error", errors: Optional[Dict[str, Any]] = None, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """Create standardized error response"""
    response_data = {
        'success': False,
        'message': message,
    }
    if errors:
        response_data['errors'] = errors
    
    return Response(response_data, status=status_code)


def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation for Nepal"""
    # Remove any spaces or special characters
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Nepal mobile numbers are typically 10 digits starting with 98
    if len(clean_phone) == 10 and clean_phone.startswith('98'):
        return True
    
    # International format +977-98XXXXXXXX
    if len(clean_phone) == 13 and clean_phone.startswith('97798'):
        return True
    
    return False


def format_currency(amount: Decimal, currency: str = "NPR") -> str:
    """Format currency amount"""
    return f"{currency} {amount:,.2f}"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data like phone numbers, emails"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def get_client_ip(request) -> str:
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'