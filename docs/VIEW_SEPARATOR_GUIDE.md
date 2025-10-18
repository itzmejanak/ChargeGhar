# View Separator Tool - Quick Reference

## 📋 Overview
Single comprehensive Python script for safely separating Django REST Framework views into multiple focused modules.

## 🚀 Features
1. **dump** - Extract view classes, generate editable JSON plan
2. **dryrun** - Validate plan and preview changes (no modifications)
3. **execute** - Perform separation with automatic backups

## 📝 Usage

### Step 1: Extract & Generate Plan
```bash
python view_separator.py dump <views_file> <app_name>

# Example:
python view_separator.py dump api/users/views.py users
```

**Output:** `<app_name>_plan.json` with:
- Available view classes
- Auto-suggested module organization
- Editable configuration

### Step 2: Edit JSON Plan
Edit the generated JSON file to organize classes into 3-5 modules:

```json
{
  "modules": [
    {
      "name": "auth_views",
      "description": "Authentication views",
      "router_name": "auth_router",
      "view_classes": ["LoginView", "RegisterView", ...]
    },
    {
      "name": "profile_views",
      "description": "User profile views", 
      "router_name": "profile_router",
      "view_classes": ["UserProfileView", ...]
    }
  ]
}
```

**Constraints:**
- Minimum 3 modules
- Maximum 5 modules
- Each module needs unique name and router_name
- All view classes must be assigned to a module

### Step 3: Dry Run (Preview)
```bash
python view_separator.py dryrun <plan_file>

# Example:
python view_separator.py dryrun users_plan.json
```

**Preview shows:**
- Directory structure
- File operations
- Class distribution
- Statistics

### Step 4: Execute Separation
```bash
python view_separator.py execute <plan_file>

# Example:
python view_separator.py execute users_plan.json
```

**Actions performed:**
1. ✓ Validate plan
2. ✓ Create backup in `backups/views_backup_<timestamp>/`
3. ✓ Generate module files with proper imports
4. ✓ Create `__init__.py` with router aggregation
5. ✓ Rename original to `views_legacy.py`
6. ✓ Validate Python syntax
7. ✓ Report success/failure

## 🔄 Rollback

If something goes wrong:
```bash
# The execute command provides rollback instructions
# Example:
rm -rf api/users/views && \
mv api/users/views_legacy.py api/users/views.py
```

## ✅ Verification

After separation, verify:

```bash
# 1. Check imports
python -c "from api.users.views import router; print(f'Routes: {len(router._paths)}')"

# 2. Test API endpoint
curl http://localhost:8010/api/auth/me -H "Authorization: Bearer <token>"

# 3. Check for errors
docker compose logs api --tail 100 | grep -i error

# 4. Generate schema
docker compose exec api python manage.py spectacular --file openapi.yaml
```

## 📊 What Gets Extracted

✓ Class definitions with decorators
✓ Multi-line decorators (`@extend_schema`)
✓ Router registrations (`@router.register`)
✓ Method decorators (`@rate_limit`, `@log_api_call`)
✓ All class methods
✓ Docstrings and comments

## 🎯 Generated File Structure

```
api/<app>/views/
├── __init__.py              # Router aggregation
├── <module1>_views.py       # Module 1 views
├── <module2>_views.py       # Module 2 views
└── <module3>_views.py       # Module 3 views
```

Each module file includes:
- Auto-generated imports (DRF, common, app-specific)
- Module-specific router instance
- View classes with decorators
- TYPE_CHECKING for Request type hints

## 🔧 Router Aggregation Pattern

The `__init__.py` merges all module routers:

```python
from api.common.routers import CustomViewRouter
from .auth_views import auth_router
from .profile_views import profile_router

router = CustomViewRouter()

# Merge all routers
for sub_router in [auth_router, profile_router]:
    router._paths.extend(sub_router._paths)
    router._drf_router.registry.extend(sub_router._drf_router.registry)

__all__ = ['router']
```

## 🐛 Troubleshooting

### "Too few/many modules" error
- Edit JSON to have 3-5 modules exactly

### "Missing view classes" error
- All classes from `available_classes` must be assigned to modules

### Syntax errors after execution
- Check backup in `backups/views_backup_<timestamp>/`
- Use rollback command
- Report issue (may be decorator extraction bug)

### Import errors
- Verify `__init__.py` was created
- Check router aggregation pattern
- Restart Django server: `docker compose restart api`

## 📦 Apps Separated

- ✅ **users** (19 classes → 3 modules)
  - auth_views (9 classes)
  - social_auth_views (5 classes)
  - profile_views (5 classes)

## 🎓 Best Practices

1. **Always run dryrun first** - Preview changes before executing
2. **Organize by functionality** - Group related views (auth, profile, admin, etc.)
3. **Keep backups** - Don't delete backup directories immediately
4. **Test thoroughly** - Verify imports, endpoints, and schema generation
5. **Consistent naming** - Use `<category>_views.py` and `<category>_router` pattern

## 🚨 Common Patterns

### Authentication Module
```python
# auth_views.py
- LoginView
- RegisterView
- OTPRequestView
- OTPVerifyView
- LogoutView
- TokenRefreshView
```

### Profile Module
```python
# profile_views.py
- UserProfileView
- UserKYCView
- WalletView
- SettingsView
```

### Admin Module
```python
# admin_views.py
- UserViewSet (admin CRUD)
- AnalyticsView
- ReportView
```

## 📄 Files Generated

- `<app>_plan.json` - Editable separation plan
- `api/<app>/views/__init__.py` - Router aggregation
- `api/<app>/views/<module>_views.py` - Module files
- `api/<app>/views_legacy.py` - Original file (renamed)
- `backups/views_backup_<timestamp>/` - Backup directory

## 💡 Tips

- Start with largest apps (most view classes)
- Use URL patterns to guide module organization
- Keep related views together (e.g., all OTP views in auth)
- Review auto-suggestions in JSON plan
- Test one app before doing all apps
