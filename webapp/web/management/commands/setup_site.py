# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup site configuration from environment variables'

    def handle(self, *args, **options):
        site_domain = os.environ.get('SITE_DOMAIN', 'localhost:8000')
        site_name = os.environ.get('SITE_NAME', 'Beryl3')
        
        try:
            site = Site.objects.get(pk=settings.SITE_ID)
            site.domain = site_domain
            site.name = site_name
            site.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Site updated: {site_name} ({site_domain})')
            )
        except Site.DoesNotExist:
            site = Site.objects.create(
                pk=settings.SITE_ID,
                domain=site_domain,
                name=site_name
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Site created: {site_name} ({site_domain})')
            )
        
        self.stdout.write(f'   Domain: {site.domain}')
        self.stdout.write(f'   Name: {site.name}')
        self.stdout.write(f'   ID: {site.pk}')