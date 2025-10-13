# Usage Analyzer - Complete Test Guide

## ✅ What Can Be Detected

### 1. **Classes**
The analyzer can find:
- ✅ Class instantiation: `MyClass()`
- ✅ Class inheritance: `class Child(MyClass)`
- ✅ Type annotations: `user: UserClass`
- ✅ Import statements: `from app.models import User`
- ✅ isinstance checks: `isinstance(obj, MyClass)`
- ✅ Class references in strings

### 2. **Methods (Class Methods)**
The analyzer can find:
- ✅ Method calls: `obj.method_name()`
- ✅ Method references: `self.method_name`
- ✅ Decorator usage: `@method_name`
- ✅ Method in strings (for serializers, etc.)

### 3. **Functions (Standalone)**
The analyzer can find:
- ✅ Direct function calls: `function_name()`
- ✅ Function references: `callback=function_name`
- ✅ Import statements
- ✅ Decorator usage

### 4. **Celery Tasks** (Special Detection)
The analyzer can find:
- ✅ `.delay()` calls: `task_name.delay(args)`
- ✅ `.apply_async()` calls: `task_name.apply_async()`
- ✅ `.s()` signatures: `task_name.s(args)`
- ✅ `.si()` immutable signatures
- ✅ String references: `send_task('app.tasks.task_name')`

### 5. **Variables & Constants**
The analyzer can find:
- ✅ Variable usage
- ✅ Constant references
- ✅ Configuration values

---

## 🧪 Test Commands

### Test 1: Find Class Usages
```bash
# First, see what classes are available
python ./tools/umain.py --app users --file models.py --list

# Then find usages of a class (example: User)
python ./tools/umain.py --app users --file models.py --usage User --verbose
```

**What it finds:**
- Where `User` class is imported
- Where `User()` is instantiated
- Where it's used in type hints
- Where it's inherited from
- Where it's used in isinstance checks

---

### Test 2: Find Method Usages (Class Methods)
```bash
# List methods in a class
python ./tools/umain.py --app users --file services.py --list

# Find usages of a specific method
python ./tools/umain.py --app users --file services.py --usage create_user --verbose
```

**What it finds:**
- Method calls: `service.create_user()`
- String references in URLs or serializers

---

### Test 3: Find Function Usages (Celery Tasks)
```bash
# List all functions/tasks
python ./tools/umain.py --app users --file tasks.py --list

# Find usages of a Celery task
python ./tools/umain.py --app users --file tasks.py --usage cleanup_expired_audit_logs --verbose
```

**What it finds:**
- Import statements
- `.delay()` calls for async execution
- `.apply_async()` calls with options
- String references in `send_task()`
- Direct function calls

---

### Test 4: Find Usages with Export
```bash
# Export results to a file for later review
python ./tools/umain.py --app users --file tasks.py --usage send_profile_completion_reminder --export task_usages.txt --verbose
```

---

### Test 5: Search Multiple Functions
```bash
# Find usages of different tasks
python ./tools/umain.py --app users --file tasks.py --usage update_user_last_activity
python ./tools/umain.py --app users --file tasks.py --usage deactivate_inactive_users
python ./tools/umain.py --app users --file tasks.py --usage send_kyc_verification_reminder
```

---

## 📊 Understanding the Output

### Usage Types You'll See:

1. **import** - Element is imported
   ```python
   from users.tasks import cleanup_expired_audit_logs
   ```

2. **function_call** - Direct function call
   ```python
   result = cleanup_expired_audit_logs()
   ```

3. **celery_delay** - Async Celery task execution
   ```python
   cleanup_expired_audit_logs.delay()
   ```

4. **celery_apply_async** - Async with options
   ```python
   cleanup_expired_audit_logs.apply_async(countdown=60)
   ```

5. **celery_signature** - Task signature
   ```python
   sig = cleanup_expired_audit_logs.s()
   ```

6. **string_reference** - Referenced in strings
   ```python
   send_task('users.tasks.cleanup_expired_audit_logs')
   ```

7. **instantiation** - Class object creation
   ```python
   user = User()
   ```

8. **inheritance** - Class inheritance
   ```python
   class CustomUser(User):
   ```

9. **method_call** - Method invoked on object
   ```python
   service.create_user()
   ```

10. **reference** - Name referenced (not called)
    ```python
    callback = cleanup_expired_audit_logs
    ```

---

## 🎯 Expected Results for Your Project

Based on your output, here's what should work:

### For `cleanup_expired_audit_logs`:
```bash
python ./tools/umain.py --app users --file tasks.py --usage cleanup_expired_audit_logs
```

**Should find usages like:**
- Celery beat schedule in `settings.py` or `celery.py`
- Manual task calls in views or other services
- Import statements in other files
- References in management commands
- String-based task invocations

### For `update_user_last_activity`:
```bash
python ./tools/umain.py --app users --file tasks.py --usage update_user_last_activity
```

**Should find usages like:**
- Called from signals (post_login, post_save)
- Called from middleware
- Called from views on user actions
- Scheduled in Celery beat

### For `send_profile_completion_reminder`:
```bash
python ./tools/umain.py --app users --file tasks.py --usage send_profile_completion_reminder
```

**Should find usages like:**
- Called from other tasks
- Scheduled jobs
- Admin actions
- Management commands

---

## 🔍 Debugging Tips

### If No Usages Found:

1. **Verify the element exists:**
   ```bash
   python ./tools/umain.py --app users --file tasks.py --list
   ```

2. **Use verbose mode:**
   ```bash
   python ./tools/umain.py --app users --file tasks.py --usage task_name --verbose
   ```

3. **Check search paths:**
   ```bash
   python ./tools/umain.py --debug --list-apps
   ```

4. **Try searching for a class you know is used:**
   ```bash
   python ./tools/umain.py --app users --file models.py --usage User --verbose
   ```

### Common Scenarios:

**Task might be registered but not called yet:**
- The task exists but hasn't been used in code yet
- It's only registered with Celery beat
- Check `celery.py` or `settings.py` for schedule definitions

**Task called via string name:**
- Some tasks are invoked using `send_task('app.tasks.task_name')`
- The analyzer now detects these string references

**Task called from management commands:**
- Check in `management/commands/` directory
- These should be detected

---

## 📈 Best Practices

1. **Start with classes** - They're easier to track
2. **Check imports first** - If no imports found, it's not used
3. **Use verbose mode** - Shows more context
4. **Export results** - Keep records of dependencies
5. **Search from project root** - More reliable path detection

---

## 🚀 Quick Verification Commands

```bash
# 1. List all apps
python ./tools/umain.py --list-apps

# 2. See all files in users app
python ./tools/umain.py --app users --list-files

# 3. Analyze tasks.py
python ./tools/umain.py --app users --file tasks.py --list

# 4. Find usages of first task
python ./tools/umain.py --app users --file tasks.py --usage cleanup_expired_audit_logs --verbose

# 5. Check project stats
python ./tools/umain.py --stats

# 6. Try finding a model class
python ./tools/umain.py --app users --file models.py --list
python ./tools/umain.py --app users --file models.py --usage User --verbose
```

Run these commands in sequence to verify everything works! 🎉
