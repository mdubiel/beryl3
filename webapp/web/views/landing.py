# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
import string
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from web.decorators import log_execution_time

logger = logging.getLogger('webapp')

@log_execution_time
def landing_view(request, landing):
    """Handles rendering of landing pages based on the provided landing ID."""
    logger.info("Landing view accessed with landing ID: '%s'", landing)
    if landing is None:
        logger.error("Landing ID is required but was not provided.")
        return HttpResponse("Landing ID is required", status=400)

    allowed_chars = set(string.ascii_letters + string.digits + '_-')
    if not set(landing).issubset(allowed_chars):
        logger.error("Invalid characters in landing ID: '%s'", landing)
        return HttpResponse("Invalid Landing ID format.", status=400)

    # Define the template path
    template_name = f'landings/{landing}/index.html'

    # Check if the template can be found by Django's loader
    try:
        loader.get_template(template_name)
    except TemplateDoesNotExist as exc:
        # If the loader cannot find it after checking all template dirs, raise Http404
        logger.error("Landing page template not found for ID: '%s'", landing)
        raise Http404("Landing page not found.") from exc

    # If the check passes, proceed with rendering the page.
    logger.info("Rendering landing page for ID: '%s'", landing)
    return render(request, template_name)
