"""
Country operations and search
"""
from __future__ import annotations

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call
from api.system.services import CountryService
from api.system.serializers import CountryListSerializer
from api.common.services.base import ServiceException

country_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@country_router.register(r"app/countries", name="countries")
class CountryListView(ListAPIView):
    """Get list of countries with dialing codes"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["App"],
        summary="Get Country Codes",
        description="Returns a list of countries with dialing codes (e.g., +977 for Nepal).",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        service = CountryService()
        return service.get_active_countries()



@country_router.register(r"app/countries/search", name="countries-search")
class CountrySearchView(GenericAPIView, BaseAPIView):
    """Search countries by name or code"""
    serializer_class = CountryListSerializer
    permission_classes = [AllowAny]
    
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Search countries by query parameter"""
        def operation():
            query = request.query_params.get('q', '')
            if not query:
                raise ServiceException(
                    "Search query 'q' parameter is required", 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            service = CountryService()
            countries = service.search_countries(query)
            serializer = self.get_serializer(countries, many=True)
            
            return {
                'results': serializer.data,
                'count': len(serializer.data)
            }
        
        return self.handle_service_operation(
            operation,
            "Countries searched successfully",
            "Failed to search countries"
        )