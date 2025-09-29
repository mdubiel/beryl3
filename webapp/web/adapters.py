# -*- coding: utf-8 -*-

from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for controlling user registration based on feature flags.
    """
    
    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.
        Uses the ALLOW_USER_REGISTRATION feature flag to control registration.
        """
        return getattr(settings, 'ALLOW_USER_REGISTRATION', False)