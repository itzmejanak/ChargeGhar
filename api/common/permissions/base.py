from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only to the owner
        return obj.user == request.user


class IsProfileComplete(BasePermission):
    """
    Permission to check if user profile is complete
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has completed profile
        try:
            profile = request.user.profile
            return profile.is_profile_complete
        except AttributeError:
            return False


class IsKYCVerified(BasePermission):
    """
    Permission to check if user KYC is verified
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user KYC is approved
        try:
            kyc = request.user.kyc
            return kyc.status == 'APPROVED'
        except AttributeError:
            return False


class HasNoPendingDues(BasePermission):
    """
    Permission to check if user has no pending rental dues
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check for pending rental dues
        from api.rentals.models import Rental
        
        pending_dues = Rental.objects.filter(
            user=request.user,
            payment_status='PENDING',
            status__in=['OVERDUE', 'COMPLETED']
        ).exists()
        
        return not pending_dues


class IsActiveUser(BasePermission):
    """
    Permission to check if user account is active
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.status == 'ACTIVE'


class IsAdminUser(BasePermission):
    """
    Permission for admin users only
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsSuperAdminUser(BasePermission):
    """
    Permission for super admin users only
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.user and request.user.is_authenticated and request.user.is_superuser


class CanRentPowerBank(BasePermission):
    """
    Combined permission for power bank rental eligibility
    """
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check all rental prerequisites
        permissions = [
            IsActiveUser(),
            IsProfileComplete(),
            IsKYCVerified(),
            HasNoPendingDues(),
        ]
        
        for permission in permissions:
            if not permission.has_permission(request, view):
                return False
        
        return True