# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
from django.shortcuts import render
from web.decorators import log_execution_time

logger = logging.getLogger('webapp')

@log_execution_time
def index_view(request):
    logger.info("Rendering index view for user '%s' [%s]", request.user.username, request.user.id)
    
    # Log index page access (handles both authenticated and anonymous users)
    logger.info('index_view: Index page accessed by user %s [%s]',
               request.user.username if request.user.is_authenticated else 'Anonymous', 
               request.user.id if request.user.is_authenticated else 'None',
               extra={'function': 'index_view', 'action': 'page_view', 'page': 'index', 
                     'user_authenticated': request.user.is_authenticated,
                     'function_args': {'request_method': request.method}})
    
    content = "Hello from django!"
    return render(request, 'index.html', context={'content': content})
