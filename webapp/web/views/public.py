# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.http import Http404
from django.shortcuts import get_object_or_404, render

from web.models import Collection


def public_collection_view(request, hash):
    """
    Displays a collection to the public if its visibility is set to
    'PUBLIC' or 'UNLISTED'.
    """
    collection = get_object_or_404(Collection, hash=hash)

    # Only allow access if the collection is not private.
    if collection.visibility == Collection.Visibility.PRIVATE:
        # We raise Http404 to avoid leaking the existence of private collections.
        raise Http404("Collection not found or is private.")

    context = {
        "collection": collection,
        "items": collection.items.all().order_by("name"),
    }
    return render(request, "public/collection_public_detail.html", context)