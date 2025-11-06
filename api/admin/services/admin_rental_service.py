"""
Admin Rental Service
============================================================

This module contains service classes for admin rental issue management operations.

Created: 2025-11-06
"""

from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from api.common.services.base import BaseService, ServiceException
from api.rentals.models import RentalIssue

User = get_user_model()


class AdminRentalService(BaseService):
    """Service for admin rental issue management"""
    
    def get_rental_issues(
        self,
        status: str = None,
        issue_type: str = None,
        search: str = None,
        ordering: str = '-reported_at'
    ):
        """
        Get list of rental issues with filtering
        
        Args:
            status: Filter by status (REPORTED, RESOLVED)
            issue_type: Filter by issue type
            search: Search in description or rental code
            ordering: Order by field
            
        Returns:
            Queryset of rental issues
        """
        queryset = RentalIssue.objects.select_related(
            'rental__user',
            'rental__power_bank',
            'rental__station',
            'rental__return_station'
        )
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
        
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(rental__rental_code__icontains=search)
            )
        
        # Apply ordering
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_rental_issue(self, issue_id: str) -> RentalIssue:
        """
        Get specific rental issue by ID
        
        Args:
            issue_id: Issue ID
            
        Returns:
            RentalIssue instance
            
        Raises:
            ServiceException: If issue not found
        """
        try:
            return RentalIssue.objects.select_related(
                'rental__user',
                'rental__power_bank',
                'rental__station',
                'rental__return_station'
            ).get(id=issue_id)
        except RentalIssue.DoesNotExist:
            raise ServiceException(
                detail="Rental issue not found",
                code="rental_issue_not_found"
            )
    
    @transaction.atomic
    def update_rental_issue_status(
        self,
        issue_id: str,
        status: str,
        admin_user: User,
        notes: str = None,
        request=None
    ) -> RentalIssue:
        """
        Update rental issue status
        
        Args:
            issue_id: Issue ID
            status: New status (REPORTED, RESOLVED)
            admin_user: Admin user making the update
            notes: Optional admin notes
            request: HTTP request for audit logging
            
        Returns:
            Updated RentalIssue instance
            
        Raises:
            ServiceException: If validation fails
        """
        issue = self.get_rental_issue(issue_id)
        
        # Validate status
        valid_statuses = ['REPORTED', 'RESOLVED']
        if status not in valid_statuses:
            raise ServiceException(
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                code="invalid_status"
            )
        
        # Update status
        old_status = issue.status
        issue.status = status
        
        # Set resolved_at if resolved
        if status == 'RESOLVED' and old_status != 'RESOLVED':
            issue.resolved_at = timezone.now()
        
        issue.save(update_fields=['status', 'resolved_at', 'updated_at'])
        
        # Log admin action
        self._log_admin_action(
            admin_user=admin_user,
            action_type='UPDATE_RENTAL_ISSUE_STATUS',
            target_model='RentalIssue',
            target_id=str(issue.id),
            changes={
                'old_status': old_status,
                'new_status': status,
                'rental_code': issue.rental.rental_code,
                'notes': notes
            },
            description=f"Updated rental issue {issue.id} status from {old_status} to {status}",
            request=request
        )
        
        self.log_info(f"Rental issue {issue.id} status updated: {old_status} -> {status}")
        
        # Send notification to user if resolved
        if status == 'RESOLVED':
            self._send_issue_resolved_notification(issue)
        
        return issue
    
    @transaction.atomic
    def delete_rental_issue(
        self,
        issue_id: str,
        admin_user: User,
        request=None
    ) -> Dict[str, str]:
        """
        Delete rental issue (soft delete by marking as resolved)
        
        Args:
            issue_id: Issue ID
            admin_user: Admin user making the deletion
            request: HTTP request for audit logging
            
        Returns:
            Success message dict
            
        Raises:
            ServiceException: If validation fails
        """
        issue = self.get_rental_issue(issue_id)
        
        # Soft delete by marking as resolved
        if issue.status != 'RESOLVED':
            issue.status = 'RESOLVED'
            issue.resolved_at = timezone.now()
            issue.save(update_fields=['status', 'resolved_at', 'updated_at'])
        
        # Log admin action
        self._log_admin_action(
            admin_user=admin_user,
            action_type='DELETE_RENTAL_ISSUE',
            target_model='RentalIssue',
            target_id=str(issue.id),
            changes={
                'rental_code': issue.rental.rental_code,
                'issue_type': issue.issue_type
            },
            description=f"Deleted rental issue {issue.id}",
            request=request
        )
        
        self.log_info(f"Rental issue {issue.id} deleted")
        
        return {"message": "Rental issue deleted successfully"}
    
    def _send_issue_resolved_notification(self, issue: RentalIssue):
        """Send notification to user when issue is resolved"""
        try:
            from api.notifications.services import notify
            
            notify(
                issue.rental.user,
                'rental_issue_resolved',
                rental_code=issue.rental.rental_code,
                issue_type=issue.issue_type,
                rental_id=str(issue.rental.id),
                issue_id=str(issue.id)
            )
        except Exception as e:
            self.log_warning(f"Failed to send issue resolved notification: {str(e)}")
    
    def _log_admin_action(
        self,
        admin_user: User,
        action_type: str,
        target_model: str,
        target_id: str,
        changes: dict,
        description: str,
        request=None
    ):
        """Log admin action to audit trail"""
        try:
            from api.admin.models import AdminActionLog
            
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type=action_type,
                target_model=target_model,
                target_id=target_id,
                changes=changes,
                description=description,
                ip_address=self._get_client_ip(request) if request else '',
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
            )
        except Exception as e:
            self.log_error(f"Failed to log admin action: {str(e)}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
