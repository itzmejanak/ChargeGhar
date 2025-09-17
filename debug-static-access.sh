#!/bin/bash

echo "🔍 Debugging Static Files Access"
echo "================================"

# Find API container
API_CONTAINER=$(docker ps --format "{{.Names}}" | grep "powerbank.*api" | head -1)
echo "Using container: $API_CONTAINER"

# Check if static files exist in container
echo ""
echo "📁 Static files in container:"
docker exec -i "$API_CONTAINER" ls -la /application/staticfiles/admin/css/ | head -5

# Check Django settings
echo ""
echo "⚙️ Django static settings:"
docker exec -i "$API_CONTAINER" python manage.py shell -c "
from django.conf import settings
print(f'STATIC_URL: {settings.STATIC_URL}')
print(f'STATIC_ROOT: {settings.STATIC_ROOT}')
print(f'DEBUG: {settings.DEBUG}')
"

# Test direct container access
echo ""
echo "🧪 Testing direct container access:"
echo "Container IP access:"
curl -I http://localhost:8010/static/admin/css/base.css 2>/dev/null | head -1 || echo "Failed"

echo ""
echo "Domain access:"
curl -I https://main.chargeghar.com/static/admin/css/base.css 2>/dev/null | head -1 || echo "Failed"

# Check if there's a reverse proxy
echo ""
echo "🔍 Checking for reverse proxy or load balancer..."
curl -I https://main.chargeghar.com/ 2>/dev/null | grep -i server || echo "No server header found"