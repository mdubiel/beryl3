"""
Views for marketing email management
"""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from web.models import UserProfile
from web.services.resend_service import handle_marketing_unsubscribe

logger = logging.getLogger("webapp")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def marketing_unsubscribe(request, token):
    """
    Handle marketing email unsubscribe via secure token
    
    GET: Show unsubscribe confirmation page
    POST: Process unsubscribe request
    """
    try:
        profile = get_object_or_404(UserProfile, unsubscribe_token=token)
    except UserProfile.DoesNotExist:
        return render(request, 'marketing/unsubscribe_error.html', {
            'error': 'Invalid or expired unsubscribe link.'
        })
    
    if request.method == 'GET':
        # Show confirmation page
        return render(request, 'marketing/unsubscribe_confirm.html', {
            'profile': profile,
            'user': profile.user,
            'token': token
        })
    
    elif request.method == 'POST':
        # Process unsubscribe
        success = handle_marketing_unsubscribe(token)
        
        if success:
            logger.info(f"Successfully unsubscribed user {profile.user.email} via marketing link")
            return render(request, 'marketing/unsubscribe_success.html', {
                'user': profile.user
            })
        else:
            return render(request, 'marketing/unsubscribe_error.html', {
                'error': 'There was a problem processing your unsubscribe request. Please try again.'
            })


@require_http_methods(["GET"])
def marketing_preferences(request):
    """
    Show marketing preferences for logged-in users
    Redirects to login if not authenticated
    """
    if not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
    
    return render(request, 'marketing/preferences.html', {
        'profile': profile,
        'unsubscribe_url': profile.get_unsubscribe_url()
    })