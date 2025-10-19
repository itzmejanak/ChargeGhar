# OpenAPI Operation ID Collision Fix

## Problem
DRF Spectacular generates operation IDs automatically. When you have list and detail endpoints with same HTTP method (e.g., GET), they collide:
- `GET /api/admin/users` → `api_admin_users_retrieve`
- `GET /api/admin/users/{id}` → `api_admin_users_retrieve` ❌ COLLISION

## Solution Pattern
Move `@extend_schema` from class level to method level with explicit `operation_id`:

**❌ WRONG (causes collision):**
```python
@extend_schema(tags=["Admin"], summary="User Detail")
class AdminUserDetailView(GenericAPIView):
    def get(self, request, user_id):
        pass
```

**✅ CORRECT (no collision):**
```python
class AdminUserDetailView(GenericAPIView):
    @extend_schema(
        operation_id="admin_user_detail_retrieve",
        tags=["Admin"],
        summary="Get User Detail"
    )
    def get(self, request, user_id):
        pass
```

## Naming Convention
For detail views with multiple methods:
- `{app}_{resource}_detail_retrieve` - GET method
- `{app}_{resource}_detail_update` - PUT method
- `{app}_{resource}_detail_delete` - DELETE method

Examples:
- `admin_content_faq_detail_retrieve`
- `admin_content_banner_detail_update`
- `admin_user_detail_retrieve`

## When to Apply
Apply this pattern whenever you have:
1. List endpoint: `GET /resource`
2. Detail endpoint: `GET /resource/{id}` 
3. Both in same router path prefix

## Quick Check
If you see warnings like:
```
Warning: operationId "api_admin_users_retrieve" has collisions
```
Move `@extend_schema` to method level with unique `operation_id`.
