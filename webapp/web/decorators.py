# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import time
import logging
from functools import wraps

def log_execution_time(func):
    """
    This decorator logs the execution time of a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # The first argument to a view is always the request
        request = args[0]
        logger = logging.getLogger('performance')
        # Start the timer
        start_time = time.perf_counter()
        
        # Execute the original view function
        response = func(*args, **kwargs)
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        log_data = {
            "function": f"{func.__module__}.{func.__name__}",
            "user": request.user.username if request.user.is_authenticated else "Anonymous",
            "duration_ms": round(duration_ms, 2)
        }
        logger.info(log_data)
        return response
    return wrapper