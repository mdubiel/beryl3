# -*- coding: utf-8 -*-

from django import forms
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    """
    Custom signup form that includes marketing email preference
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marketing consent must be disabled by default (GDPR compliance)
        self.fields['receive_marketing_emails'].initial = False
    
    receive_marketing_emails = forms.BooleanField(
        required=False,
        label='Marketing Emails',
        help_text='I would like to receive promotional emails and product updates',
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        })
    )
    
    accept_policies = forms.BooleanField(
        required=True,
        label='Terms and Policies',
        help_text='I have read and understand the <a href="/terms/" target="_blank" class="link link-primary">Site Policies</a> and <a href="/privacy/" target="_blank" class="link link-primary">Privacy Policy</a>',
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary'
        })
    )

    def clean(self):
        """
        Validate the form
        """
        cleaned_data = super().clean()
        return cleaned_data

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