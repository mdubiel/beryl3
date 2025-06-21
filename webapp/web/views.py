import string
from django.http import HttpResponse
from django.shortcuts import redirect, render

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate # Import login, logout, and authenticate functions
from django.contrib import messages # For displaying messages to the user
from django.contrib.auth.forms import AuthenticationForm # Django's built-in login form
from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist


def index_view(request):
    content = "Hello from django!"
    #messages.success(request, 'This is a test success message! If you can see this, it works.')
    #messages.error(request, 'This is a test error message.')
    return render(request, 'index.html', context={'content': content})

def landing_view(request, landing):
    
    # Initial Validation
    if landing is None:
        return HttpResponse("Landing ID is required", status=400)

    allowed_chars = set(string.ascii_letters + string.digits + '_-')
    if not set(landing).issubset(allowed_chars):
        return HttpResponse("Invalid Landing ID format.", status=400)
    
    # Define the template path
    template_name = f'landings/{landing}/index.html'
    
    # Check if the template can be found by Django's loader
    try:
        loader.get_template(template_name)
    except TemplateDoesNotExist:
        # If the loader cannot find it after checking all template dirs, raise Http404
        raise Http404("Landing page not found.")
    
    # If the check passes, proceed with rendering the page.
    return render(request, template_name)
