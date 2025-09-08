from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from celery import Task
from django.conf import settings


logger = logging.getLogger(__name__)


class BaseTask(Task):
    """
    Base task class with common functionality
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        self.logger.info(f"Task {self.name} succeeded", extra={
            'task_id': task_id,
            'result': retval
        })
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        self.logger.error(f"Task {self.name} failed", extra={
            'task_id': task_id,
            'exception': str(exc),
            'traceback': str(einfo)
        })
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        self.logger.warning(f"Task {self.name} retrying", extra={
            'task_id': task_id,
            'exception': str(exc),
            'retry_count': self.request.retries
        })


class NotificationTask(BaseTask):
    """
    Base class for notification tasks
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    
    def send_notification(self, user_id: str, message: str, data: Optional[Dict[str, Any]] = None):
        """Override in subclasses to implement specific notification logic"""
        raise NotImplementedError("Subclasses must implement send_notification method")


class PaymentTask(BaseTask):
    """
    Base class for payment-related tasks
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 5, 'countdown': 30}
    
    def process_payment(self, payment_data: Dict[str, Any]):
        """Override in subclasses to implement specific payment logic"""
        raise NotImplementedError("Subclasses must implement process_payment method")


class AnalyticsTask(BaseTask):
    """
    Base class for analytics and reporting tasks
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2, 'countdown': 300}  # 5 minutes
    
    def generate_report(self, report_type: str, filters: Optional[Dict[str, Any]] = None):
        """Override in subclasses to implement specific analytics logic"""
        raise NotImplementedError("Subclasses must implement generate_report method")