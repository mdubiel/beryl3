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
    content = "Hello from django!"
    return render(request, 'index.html', context={'content': content})
