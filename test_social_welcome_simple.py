"""
Simple test for social auth welcome message
"""

print("🧪 Testing Social Auth Welcome Message")
print("=" * 50)

# Import required modules
from django.contrib.auth import get_user_model
from api.users.services import AuthService
from api.users.tasks import send_social_auth_welcome_message
from api.notifications.models import Notification, NotificationTemplate
from api.notifications.services import notify

User = get_user_model()

# Test 1: Check if template exists
print("\n1️⃣ Checking notification template...")
try:
    template = NotificationTemplate.objects.get(slug='social_auth_welcome')
    print(f"✅ Template found: {template.name}")
    print(f"   Type: {template.notification_type}")
    print(f"   Active: {template.is_active}")
except NotificationTemplate.DoesNotExist:
    print("❌ Template 'social_auth_welcome' not found")
    exit(1)

# Test 2: Create a test user
print("\n2️⃣ Creating test social user...")
social_data = {
    'email': 'test_welcome@example.com',
    'name': 'Test Welcome User',
    'picture': 'https://example.com/avatar.jpg',
    'id': '123456789',
    'sub': '123456789'
}

# Clean up existing user
User.objects.filter(email=social_data['email']).delete()
print("   Cleaned up existing test user")

# Create user via service
auth_service = AuthService()
user = auth_service.create_social_user(social_data, 'google')
print(f"✅ User created: {user.username} ({user.email})")

# Test 3: Test welcome message task directly
print("\n3️⃣ Testing welcome message task...")
# Clear existing notifications
Notification.objects.filter(user=user).delete()

# Call task directly
result = send_social_auth_welcome_message(user.id, 'google')
print(f"✅ Task result: {result}")

# Check notifications
notifications = Notification.objects.filter(user=user)
print(f"✅ Notifications created: {notifications.count()}")

for notif in notifications:
    print(f"   Title: {notif.title}")
    print(f"   Message: {notif.message}")
    print(f"   Type: {notif.notification_type}")

# Test 4: Test notify function directly
print("\n4️⃣ Testing notify function...")
Notification.objects.filter(user=user).delete()

notification = notify(
    user,
    'social_auth_welcome',
    async_send=False,
    provider='Google',
    signup_method='social'
)

print(f"✅ Notification created via notify(): {notification.id}")
print(f"   Title: {notification.title}")
print(f"   Message: {notification.message}")

print("\n🎉 All tests completed successfully!")