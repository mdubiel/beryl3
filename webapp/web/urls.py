from django.urls import path
from web.views import index_view, landing_view

urlpatterns = [
  # this is main page
  path('', index_view, name='index'),
  
  # Landing pages, which will be used for marketing purposes
  # <str:landing> is a placeholder for the landing page identifier
  # It will be verified, and files from directory will be served
  # If the landing page does not exist, a 404 error will be raised
  path('landing/<str:landing>', landing_view, name='landing'),
  
]
