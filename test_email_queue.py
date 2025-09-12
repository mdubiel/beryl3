#!/usr/bin/env python
"""
Test script to debug the email queue view error
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
sys.path.insert(0, '/home/mdubiel/projects/beryl3/webapp')

django.setup()

# Now we can import Django modules
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.contrib.auth.models import Group
from web.views.sys import sys_email_queue

User = get_user_model()

def test_email_queue_view():
    """Test the sys_email_queue view"""
    print("Testing sys_email_queue view...")
    
    try:
        # Create a mock request
        request = HttpRequest()
        request.method = 'GET'
        
        # Get the admin user
        admin_user = User.objects.filter(email='admin@example.com', is_superuser=True).first()
        if not admin_user:
            print("ERROR: No admin user found")
            return
            
        request.user = admin_user
        
        # Call the view
        print("Calling sys_email_queue view...")
        response = sys_email_queue(request)
        
        print(f"View executed successfully! Status code: {response.status_code}")
        
        if hasattr(response, 'context_data'):
            print("Context data:", response.context_data.keys())
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email_queue_view()