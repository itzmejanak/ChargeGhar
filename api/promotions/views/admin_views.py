"""
Admin coupon management - CRUD operations, analytics, and filtering
"""



import logging


from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, mixins
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


from api.common.routers import CustomViewRouter
from api.common.mixins import BaseAPIView
from api.common.decorators import log_api_call, cached_response
from api.promotions import serializers
from api.promotions.models import Coupon
from api.promotions.services import CouponService, PromotionAnalyticsService
from api.users.permissions import IsStaffPermission
from api.common.services.base import ServiceException

admin_router = CustomViewRouter()

logger = logging.getLogger(__name__)

@admin_router.register(r"admin/promotions/coupons", name="admin-coupons")
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



@admin_router.register(r"admin/promotions/analytics", name="admin-promotion-analytics")
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



@admin_router.register(r"admin/promotions/coupons/filter", name="admin-coupons-filter")
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