"""
App-related functionality
"""
import logging

from api.common.routers import CustomViewRouter

app_router = CustomViewRouter()
logger = logging.getLogger(__name__)


