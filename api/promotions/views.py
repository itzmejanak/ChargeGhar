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
class CouponApplyView(GenericAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Apply Coupon Code",
        description="Apply coupon code and receive points",
        operation_id="apply_coupon_code"
    )
    
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            coupon_service = CouponService()
            result = coupon_service.apply_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            return Response(result, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"promotions/coupons/validate", name="promotion-coupons-validate")
class CouponValidateView(GenericAPIView):
    serializer_class = serializers.CouponApplySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Validate Coupon Code",
        description="Check if coupon code is valid and can be used",
        operation_id="validate_coupon_code"
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            coupon_service = CouponService()
            result = coupon_service.validate_coupon(
                coupon_code=serializer.validated_data['coupon_code'],
                user=request.user
            )
            
            response_serializer = serializers.CouponValidationSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@router.register(r"promotions/coupons/my", name="promotion-coupons-my")
class MyCouponsView(GenericAPIView):
    serializer_class = serializers.UserCouponHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Promotions"],
        summary="My Coupon History",
        description="Returns user's coupon usage history",
        operation_id="get_my_coupon_history"
    )
    def get(self, request: Request) -> Response:
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            coupon_service = CouponService()
            result = coupon_service.get_user_coupon_history(
                user=request.user,
                page=page,
                page_size=page_size
            )
            
            # Serialize the results
            serializer = self.get_serializer(result['results'], many=True)
            
            return Response({
                'results': serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get user coupon history: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve coupon history'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"promotions/coupons/active", name="promotion-coupons-active")
class ActiveCouponsView(GenericAPIView):
    serializer_class = serializers.CouponPublicSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=["Promotions"],
        summary="Active Coupons",
        description="Returns list of currently active and valid coupons",
        operation_id="get_active_coupons"
    )
    def get(self, request: Request) -> Response:
        try:
            coupon_service = CouponService()
            coupons = coupon_service.get_active_coupons()
            
            serializer = self.get_serializer(coupons, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get active coupons: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve active coupons'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===============================
# ADMIN COUPON MANAGEMENT ENDPOINTS
# ===============================

@router.register(r"admin/promotions/coupons", name="admin-coupons")
@extend_schema_view(
    list=extend_schema(
        tags=["Admin - Promotions"], 
        summary="List All Coupons (Admin)",
        description="Returns paginated list of all coupons with filtering (Staff only)",
        operation_id="list_admin_coupons"
    ),
    create=extend_schema(
        tags=["Admin - Promotions"], 
        summary="Create Coupon (Admin)",
        description="Creates new coupon (Staff only)",
        operation_id="create_admin_coupon"
    ),
    retrieve=extend_schema(
        tags=["Admin - Promotions"], 
        summary="Get Coupon Details (Admin)",
        description="Retrieves specific coupon details (Staff only)",
        operation_id="get_admin_coupon_details"
    ),
    update=extend_schema(
        tags=["Admin - Promotions"], 
        summary="Update Coupon (Admin)",
        description="Updates coupon information (Staff only)",
        operation_id="update_admin_coupon"
    ),
    partial_update=extend_schema(
        tags=["Admin - Promotions"], 
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
        tags=["Admin - Promotions"],
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
        tags=["Admin - Promotions"],
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
class AdminPromotionAnalyticsView(GenericAPIView):
    serializer_class = serializers.CouponAnalyticsSerializer
    permission_classes = [IsStaffPermission]
    
    @extend_schema(
        tags=["Admin"],
        summary="Promotion Analytics (Admin)",
        description="Get comprehensive promotion analytics (Staff only)",
        operation_id="get_promotion_analytics"
    )
    def get(self, request: Request) -> Response:
        try:
            analytics_service = PromotionAnalyticsService()
            analytics = analytics_service.get_coupon_analytics()
            
            serializer = self.get_serializer(analytics)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to get promotion analytics: {str(e)}")
            return Response(
                {'detail': 'Failed to retrieve analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@router.register(r"admin/promotions/coupons/filter", name="admin-coupons-filter")
class AdminCouponFilterView(GenericAPIView):
    serializer_class = serializers.CouponFilterSerializer
    permission_classes = [IsStaffPermission]
    
    @extend_schema(
        tags=["Admin"],
        summary="Filter Coupons (Admin)",
        description="Get filtered and paginated list of coupons (Staff only)",
        operation_id="filter_admin_coupons"
    )
    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            coupon_service = CouponService()
            result = coupon_service.get_coupons_list(serializer.validated_data)
            
            # Serialize the results
            coupon_serializer = serializers.CouponSerializer(result['results'], many=True)
            
            return Response({
                'results': coupon_serializer.data,
                'pagination': {
                    'count': result['pagination']['total_count'],
                    'page': result['pagination']['current_page'],
                    'page_size': result['pagination']['page_size'],
                    'total_pages': result['pagination']['total_pages'],
                    'has_next': result['pagination']['has_next'],
                    'has_previous': result['pagination']['has_previous']
                }
            }, status=status.HTTP_200_OK)
            
        except ServiceException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to filter coupons: {str(e)}")
            return Response(
                {'detail': 'Failed to filter coupons'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
