# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import time
import logging
from functools import wraps
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Collection, CollectionItem

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


def owner_required(model_name):
    """
    Decorator that checks if the user is the owner of a Collection or CollectionItem.
    
    Args:
        model_name (str): Either 'collection' or 'item' to specify which model to check
    
    Usage:
        @owner_required('collection')
        def my_view(request, hash):
            # hash parameter must be present for the collection
            
        @owner_required('item')
        def my_view(request, hash):
            # hash parameter must be present for the item
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Extract hash from kwargs or args
            hash_value = kwargs.get('hash')
            if not hash_value and len(args) > 0:
                hash_value = args[0]
            
            if not hash_value:
                raise PermissionDenied("Hash parameter required")
            
            if model_name == 'collection':
                obj = get_object_or_404(Collection, hash=hash_value)
                if obj.created_by != request.user:
                    raise PermissionDenied("You don't have permission to access this collection.")
                    
            elif model_name == 'item':
                obj = get_object_or_404(CollectionItem, hash=hash_value)
                if obj.collection.created_by != request.user:
                    raise PermissionDenied("You don't have permission to access this item.")
                    
            else:
                raise ValueError(f"Invalid model_name: {model_name}. Must be 'collection' or 'item'.")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator