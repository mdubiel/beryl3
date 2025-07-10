# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
from threading import local

_thread_locals = local()

# This filter will be attached to a logger handler.
# It adds custom attributes to the log record.
class RequestUserInfoFilter(logging.Filter):
    def filter(self, record):
        # Attach the user and request path to the log record
        record.user = getattr(_thread_locals, 'user', 'Anonymous')
        record.path = getattr(_thread_locals, 'path', 'N/A')
        return True

# This middleware will run on every request.
# It captures the user and path and stores them in a "thread local" variable,
# making them available to the logging filter.
class RequestUserInfoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user and path before the view is processed
        _thread_locals.user = request.user if request.user.is_authenticated else 'Anonymous'
        _thread_locals.path = request.path

        response = self.get_response(request)

        # Clean up after the request is done
        del _thread_locals.user
        del _thread_locals.path

        return response