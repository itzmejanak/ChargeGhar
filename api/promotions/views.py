from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import cached_response, log_api_call
from api.common.services.base import ServiceException
from api.promotions import serializers
from api.promotions.models import Coupon, CouponUsage
from api.promotions.services import CouponService, PromotionAnalyticsService
from api.users.permissions import IsStaffPermission

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

logger = logging.getLogger(__name__)


# ===============================
# PUBLIC PROMOTION ENDPOINTS
# ===============================

@router.register(r"promotions/coupons/apply", name="promotion-coupons-apply")
class CouponApplyView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Apply Coupon Code",
        description="Apply coupon code and receive points",
        operation_id="apply_coupon_code",
        responses={200: serializers.CouponApplyResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Apply coupon code - REAL-TIME (no caching for financial operations)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            coupon_service = CouponService()
            result = coupon_service.apply_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            return result
        
        return self.handle_service_operation(
            operation,
            "Coupon applied successfully",
            "Failed to apply coupon"
        )


@router.register(r"promotions/coupons/validate", name="promotion-coupons-validate")
class CouponValidateView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Validate Coupon Code",
        description="Check if coupon code is valid and can be used",
        operation_id="validate_coupon_code",
        responses={200: serializers.CouponValidationResponseSerializer}
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Validate coupon code - REAL-TIME (always check current status)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            coupon_service = CouponService()
            result = coupon_service.validate_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            return result
        
        return self.handle_service_operation(
            operation,
            "Coupon validation completed",
            "Failed to validate coupon"
        )


@router.register(r"promotions/coupons/my", name="promotion-coupons-my")
class MyCouponsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.UserCouponHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="My Coupon History",
        description="Returns user's coupon usage history",
        operation_id="get_my_coupon_history",
        responses={200: serializers.MyCouponsResponseSerializer}
    )
    @log_api_call()
    def get(self, request: Request) -> Response:
        """Get user's coupon history - REAL-TIME (user-specific data)"""
        def operation():
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            coupon_service = CouponService()
            result = coupon_service.get_user_coupon_history(
                user=request.user,
                page=page,
                page_size=page_size
            )
            
            # Use MVP list serializer for performance
            serializer = serializers.UserCouponHistorySerializer(result['results'], many=True)
            
            return {
                'results': serializer.data,
                'pagination': result['pagination']
            }
        
        return self.handle_service_operation(
            operation,
            "Coupon history retrieved successfully",
            "Failed to retrieve coupon history"
        )


@router.register(r"promotions/coupons/active", name="promotion-coupons-active")
class ActiveCouponsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponPublicSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Active Coupons",
        description="Returns list of currently active and valid coupons",
        operation_id="get_active_coupons",
        responses={200: serializers.ActiveCouponsResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=900)  # Cache for 15 minutes - coupons don't change frequently
    def get(self, request: Request) -> Response:
        """Get active coupons - CACHED for performance"""
        def operation():
            coupon_service = CouponService()
            coupons = coupon_service.get_active_coupons()
            
            # Use MVP public serializer for performance
            serializer = serializers.CouponPublicSerializer(coupons, many=True)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Active coupons retrieved successfully",
            "Failed to retrieve active coupons"
        )


# ===============================
# ADMIN COUPON MANAGEMENT ENDPOINTS
# ===============================

@router.register(r"admin/promotions/coupons", name="admin-coupons")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin"], 
        summary="List All Coupons (Admin)",
        description="Returns paginated list of all coupons with filtering (Staff only)",
        operation_id="list_admin_coupons"
    ),
    create=extend_schema(
        tags=["Admin"], 
        summary="Create Coupon (Admin)",
        description="Creates new coupon (Staff only)",
        operation_id="create_admin_coupon"
    ),
    retrieve=extend_schema(
        tags=["Admin"], 
        summary="Get Coupon Details (Admin)",
        description="Retrieves specific coupon details (Staff only)",
        operation_id="get_admin_coupon_details"
    ),
    update=extend_schema(
        tags=["Admin"], 
        summary="Update Coupon (Admin)",
        description="Updates coupon information (Staff only)",
        operation_id="update_admin_coupon"
    ),
    partial_update=extend_schema(
        tags=["Admin"], 
        summary="Partial Update Coupon (Admin)",
        description="Partially updates coupon information (Staff only)",
        operation_id="partial_update_admin_coupon"
    )
)
class AdminCouponViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    """Admin-only coupon management ViewSet"""
    queryset = Coupon.objects.all().order_by('-created_at')
    permission_classes = (IsStaffPermission,)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CouponCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.CouponUpdateSerializer
        return serializers.CouponSerializer
    
    def get_queryset(self):
        """Apply filters to queryset"""
        queryset = super().get_queryset()
        
        # Apply filters from query parameters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(code__icontains=search) | Q(name__icontains=search)
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            coupon_service = CouponService()
            coupon = coupon_service.create_coupon(
                code=serializer.validated_data['code'],
                name=serializer.validated_data['name'],
                points_value=serializer.validated_data['points_value'],
                max_uses_per_user=serializer.validated_data['max_uses_per_user'],
                valid_from=serializer.validated_data['valid_from'],
                valid_until=serializer.validated_data['valid_until'],
                admin_user=request.user
            )
            
            response_serializer = serializers.CouponSerializer(coupon)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='bulk-create')
    @extend_schema(
        tags=["Admin"],
        summary="Bulk Create Coupons (Admin)",
        description="Creates multiple coupons at once (Staff only)",
        operation_id="bulk_create_admin_coupons",
        request=serializers.BulkCouponCreateSerializer
    )
    def bulk_create(self, request):
        serializer = serializers.BulkCouponCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            coupon_service = CouponService()
            coupons = coupon_service.bulk_create_coupons(
                name_prefix=serializer.validated_data['name_prefix'],
                points_value=serializer.validated_data['points_value'],
                max_uses_per_user=serializer.validated_data['max_uses_per_user'],
                valid_from=serializer.validated_data['valid_from'],
                valid_until=serializer.validated_data['valid_until'],
                quantity=serializer.validated_data['quantity'],
                code_length=serializer.validated_data['code_length'],
                admin_user=request.user
            )
            
            return Response({
                'message': f'Successfully created {len(coupons)} coupons',
                'quantity': len(coupons),
                'codes': [coupon.code for coupon in coupons[:10]]  # Show first 10 codes
            }, status=status.HTTP_201_CREATED)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'], url_path='performance')
    @extend_schema(
        tags=["Admin"],
        summary="Coupon Performance (Admin)",
        description="Get performance metrics for a specific coupon (Staff only)",
        operation_id="get_admin_coupon_performance",
        parameters=[
            {
                'name': 'id',
                'in': 'path',
                'description': 'Coupon ID',
                'required': True,
                'schema': {'type': 'string'}
            }
        ]
    )
    def performance(self, request, pk=None):
        try:
            analytics_service = PromotionAnalyticsService()
            performance_data = analytics_service.get_coupon_performance(pk)
            
            return Response(performance_data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"admin/promotions/analytics", name="admin-promotion-analytics")
class AdminPromotionAnalyticsView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponAnalyticsSerializer
    permission_classes = [IsStaffPermission]
    
    @extend_schema(
        tags=["Admin"],
        summary="Promotion Analytics (Admin)",
        description="Get comprehensive promotion analytics (Staff only)",
        operation_id="get_promotion_analytics",
        responses={200: serializers.CouponAnalyticsResponseSerializer}
    )
    @log_api_call()
    @cached_response(timeout=3600)  # Cache for 1 hour - analytics change slowly
    def get(self, request: Request) -> Response:
        """Get promotion analytics - CACHED for performance"""
        def operation():
            analytics_service = PromotionAnalyticsService()
            analytics = analytics_service.get_coupon_analytics()
            
            serializer = serializers.CouponAnalyticsSerializer(analytics)
            return serializer.data
        
        return self.handle_service_operation(
            operation,
            "Promotion analytics retrieved successfully",
            "Failed to retrieve analytics"
        )


@router.register(r"admin/promotions/coupons/filter", name="admin-coupons-filter")
class AdminCouponFilterView(GenericAPIView, BaseAPIView):
    serializer_class = serializers.CouponFilterSerializer
    permission_classes = [IsStaffPermission]
    
    @extend_schema(
        tags=["Admin"],
        summary="Filter Coupons (Admin)",
        description="Get filtered and paginated list of coupons (Staff only)",
        operation_id="filter_admin_coupons"
    )
    @log_api_call()
    def post(self, request: Request) -> Response:
        """Filter coupons with pagination (Admin only)"""
        def operation():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            coupon_service = CouponService()
            result = coupon_service.get_coupons_list(serializer.validated_data)
            
            # Serialize the results
            coupon_serializer = serializers.CouponSerializer(result['results'], many=True)
            
            return {
                'results': coupon_serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            }
        
        return self.handle_service_operation(
            operation,
            "Coupons filtered successfully",
            "Failed to filter coupons"
        )
