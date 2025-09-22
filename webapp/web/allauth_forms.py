# -*- coding: utf-8 -*-

from django import forms
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """
    Custom signup form that includes marketing email preference
    """
    receive_marketing_emails = forms.BooleanField(
        required=False,
        initial=False,  # Opt-out by default as requested
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