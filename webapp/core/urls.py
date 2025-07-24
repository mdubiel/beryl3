"""
Core app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('pixelcube/showcase/', views.pixelcube_showcase, name='pixelcube_showcase'),
    path('pixelcube/', views.pixelcube_image_view, name='pixelcube_image'),
]