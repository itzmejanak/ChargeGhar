# 🚀 **Common App - Quick Reference**

## **🏗️ Must-Use Components**

### **Views Pattern (ALWAYS)**
```python
@router.register(r"endpoint", name="endpoint")
@extend_schema(responses={200: BaseResponseSerializer})
class MyView(GenericAPIView, BaseAPIView):  # ✅ Always BaseAPIView
    def get(self, request):
        def operation():
            return data
        return self.handle_service_operation(operation, "Success", "Failed")
```

### **Serializers (MVP Pattern)**
```python
# List - minimal fields
class ModelListSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'status']  # Only essentials

# Standard - with computed fields  
class ModelSerializer(serializers.ModelSerializer):
    computed = serializers.SerializerMethodField()

# Detail - full data
class ModelDetailSerializer(serializers.ModelSerializer):
    relations = RelatedSerializer(read_only=True)
```

### **Services**
```python
class MyService(CRUDService):  # or BaseService
    model = MyModel
    
    def my_operation(self):
        try:
            return result
        except Exception as e:
            self.handle_service_error(e, "Operation failed")
```

---

## **📦 Available Components**

### **Models**
- `BaseModel` - UUID + timestamps (inherit from this)
- `Country` - Countries with dial codes
- `MediaUpload` - File uploads with cloud storage
- `LateFeeConfiguration` - Late fee settings

### **Mixins (in BaseAPIView)**
- `StandardResponseMixin` - `success_response()`, `error_response()`
- `ServiceHandlerMixin` - `handle_service_operation()`
- `PaginationMixin` - `paginate_response()`
- `FilterMixin` - `apply_date_filters()`, `apply_status_filter()`

### **Services**
- `MediaUploadService` - File uploads
- `CountryService` - Country operations  
- `AppDataService` - App init data
- `CloudStorageFactory` - Cloudinary/S3

### **Permissions**
- `IsProfileComplete`, `IsKYCVerified`, `HasNoPendingDues`
- `CanRentPowerBank` - Combined rental eligibility
- `IsOwnerOrReadOnly`, `IsAdminUser`

### **Decorators**
- `@cached_response(timeout=300)` - Cache responses
- `@rate_limit(max_requests=5)` - Rate limiting
- `@log_api_call()` - API logging
- `@require_complete_profile` - Profile check

### **Utilities**
```python
from api.common.utils.helpers import (
    generate_random_code, generate_transaction_id,
    paginate_queryset, calculate_distance,
    validate_phone_number, mask_sensitive_data,
    format_currency, calculate_points_from_amount
)
```

### **Exceptions**
```python
from api.common.exceptions.custom import (
    ProfileIncompleteException, KYCNotVerifiedException,
    InsufficientBalanceException, StationOfflineException,
    PaymentFailedException, InvalidOTPException
)
```

### **Tasks (Celery)**
- `BaseTask` - Base with logging
- `NotificationTask` - For notifications
- `PaymentTask` - For payments
- `AnalyticsTask` - For reports

---

## **⚡ Quick Rules**

### **✅ ALWAYS DO**
- Inherit from `BaseAPIView`
- Use `BaseResponseSerializer` in Swagger
- Use `handle_service_operation()` for error handling
- Create separate List/Detail serializers
- Real-time data for financial info (no caching)
- Use `paginate_response()` for lists

### **❌ NEVER DO**
- Cache financial data (wallet, payments)
- Return custom formats that don't match serializer
- Skip `BaseAPIView` inheritance
- Use heavy serializers for lists
- Mix business logic in views

### **🎯 MVP Focus**
1. **Minimal fields** in list responses
2. **Real-time** critical data (wallet, payments)
3. **Consistent** response format
4. **Proper** pagination
5. **Performance** optimized queries

---

## **📋 Checklist for New Views**

- [ ] Inherits from `GenericAPIView, BaseAPIView`
- [ ] Uses `@extend_schema(responses={200: BaseResponseSerializer})`
- [ ] Has proper serializer_class
- [ ] Uses `handle_service_operation()`
- [ ] Has MVP-focused serializers (List/Detail)
- [ ] Real-time data for critical info
- [ ] Proper pagination for lists
- [ ] Business logic in services

**Follow this guide for consistent, scalable MVP code! 🚀**