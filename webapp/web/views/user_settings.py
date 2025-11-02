"""
User account settings views
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from web.models_user_profile import UserProfile

logger = logging.getLogger("webapp")
User = get_user_model()


@login_required
def user_settings_view(request):
    """
    User account settings page where users can update their profile information
    """
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Process form submission
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        nickname = request.POST.get('nickname', '').strip()
        use_nickname = request.POST.get('use_nickname') == 'on'
        receive_marketing_emails = request.POST.get('receive_marketing_emails') == 'on'
        
        try:
            # Update user information
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save(update_fields=['first_name', 'last_name'])

            # Update profile preferences
            old_marketing_preference = profile.receive_marketing_emails
            profile.nickname = nickname if nickname else None
            profile.use_nickname = use_nickname
            profile.receive_marketing_emails = receive_marketing_emails

            # Validate before saving (will call model's clean method and validators)
            profile.full_clean()
            profile.save(update_fields=['nickname', 'use_nickname', 'receive_marketing_emails'])

            # Sync with Resend if preference changed
            if old_marketing_preference != receive_marketing_emails:
                from web.services.resend_service import sync_user_marketing_subscription
                try:
                    sync_user_marketing_subscription(request.user)
                    logger.info(f"User {request.user.email} updated marketing preference to {receive_marketing_emails}")
                except Exception as e:
                    logger.error(f"Failed to sync marketing preference for user {request.user.email}: {str(e)}")

            messages.success(request, 'Your account settings have been updated successfully.')
            return redirect('user_settings')

        except ValidationError as e:
            # Handle validation errors
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(f"{field.replace('_', ' ').title()}: {error.message}")
            else:
                error_messages = e.messages

            for msg in error_messages:
                messages.error(request, msg)
            logger.warning(f"Validation error updating settings for {request.user.email}: {error_messages}")

        except IntegrityError as e:
            # Handle unique constraint violations
            if 'nickname' in str(e):
                messages.error(request, 'This nickname is already taken. Please choose a different one.')
            else:
                messages.error(request, 'An error occurred while saving your settings. Please try again.')
            logger.error(f"Integrity error updating settings for {request.user.email}: {str(e)}")
    
    context = {
        'user': request.user,
        'profile': profile,
    }
    
    return render(request, 'user/settings.html', context)