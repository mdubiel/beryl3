# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """
    Custom signup form that includes marketing email preference
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value based on environment configuration
        self.fields['receive_marketing_emails'].initial = getattr(settings, 'MARKETING_EMAIL_DEFAULT_OPT_IN', True)
    
    receive_marketing_emails = forms.BooleanField(
        required=False,
        label='Marketing Emails',
        help_text='I would like to receive promotional emails and product updates',
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        })
    )

    def save(self, request):
        """
        Save the user and create profile with marketing preference
        """
        user = super().save(request)
        
        # Create or update user profile with marketing preference
        from web.models_user_profile import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.receive_marketing_emails = self.cleaned_data.get('receive_marketing_emails', False)
        profile.save()
        
        return user