
# Template Views for Frontend Integration
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from api.payments.services.wallet import WalletService

def payment_test_view(request):
    """
    Render the payment test template with user context and access token
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Return a simple login message for now
        from django.http import HttpResponse
        return HttpResponse("""
        <html>
        <head><title>Login Required</title></head>
        <body>
            <h2>🔐 Authentication Required</h2>
            <p>Please log in to access the payment interface.</p>
            <p><a href="/admin/">Go to Admin Login</a></p>
            <p>Or use the API with JWT token for testing.</p>
        </body>
        </html>
        """)
    
    # Generate access token for the authenticated user
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    
    # Get user's wallet balance if available
    wallet_balance = None
    try:
        wallet_service = WalletService()
        wallet_balance = wallet_service.get_balance(request.user)
    except Exception as e:
        # If wallet service fails, just continue without balance
        pass
    
    context = {
        'user': request.user,
        'access_token': access_token,
        'wallet_balance': wallet_balance,
    }
    
    return render(request, 'stripe_test.html', context)