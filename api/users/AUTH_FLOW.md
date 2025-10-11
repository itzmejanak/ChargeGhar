# 🚀 OTP Authentication Flow
---

## 🧩 STEP 1: Request OTP for Registration

```bash
curl -X POST http://localhost:8010/api/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "purpose": "REGISTER"
  }' | jq .
```

---

## 🗝️ STEP 2: Extract OTP from Redis

```bash
docker-compose exec api python manage.py shell -c "
from django.core.cache import cache
otp = cache.get('otp:REGISTER:test@example.com')
print(f'🔑 OTP for test@example.com: {otp}')
"
```

---

## ✅ STEP 3: Verify Registration OTP

```bash
curl -X POST http://localhost:8010/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "otp": "962393",
    "purpose": "REGISTER"
  }' | jq .
```

---

## 👤 STEP 4: Register User

```bash
curl -X POST http://localhost:8010/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "username": "testuser",
    "verification_token": "a005c090-7de9-41ce-89dd-d71911ce36ea"
  }' | jq .
```

---

## 🔐 STEP 5: Request OTP for Login

```bash

```

---

## 🗝️ STEP 6: Extract Login OTP from Redis

```bash
docker-compose exec api python manage.py shell -c "
from django.core.cache import cache
otp = cache.get('otp:LOGIN:test@example.com')
print(f'🔑 Login OTP for test@example.com: {otp}')
"
```

---

## ✅ STEP 7: Verify Login OTP

```bash
curl -X POST http://localhost:8010/api/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "otp": "011860",
    "purpose": "LOGIN"
  }' | jq .
```

---

## 🔓 STEP 8: Complete Login

```bash
curl -X POST http://localhost:8010/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com",
    "verification_token": "c926ef6d-2315-4943-9043-4aa590eb065c"
  }' | jq .
```

---

## 👤 STEP 9: Verify Authenticated User (Using Access Token)

```bash
curl -X GET http://localhost:8010/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" | jq .
```

---

## 🛠️ STEP 10: Create Temporary Admin Access

```bash
docker-compose exec api python manage.py shell -c "
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.get(username='janak')
admin_user.set_password('admin123')
admin_user.save()

print('🔑 Django Admin Access Created:')
print('URL: http://localhost:8010/admin/')
print('Username: janak')
print('Password: admin123')
"
```

---

## 🎫 STEP 11: Generate Admin Access Token (For Swagger UI)

```bash
docker-compose exec api python manage.py shell -c "
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
admin_user = User.objects.get(username='janak')
refresh = RefreshToken.for_user(admin_user)
print('🎫 Admin Access Token:')
print(str(refresh.access_token))
"
```

---