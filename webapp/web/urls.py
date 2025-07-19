# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from web.views import index, landing, user, collection, collection_hx, items, items_hx, public


urlpatterns = [
    # this is main page
    path('', index.index_view, name='index'),

    # Landing pages, which will be used for marketing purposes
    # <str:landing> is a placeholder for the landing page identifier
    # It will be verified, and files from directory will be served
    # If the landing page does not exist, a 404 error will be raised
    path('landing/<str:landing>', landing.landing_view, name='landing'),
    # User dashboard view
    path('dashboard/', user.dashboard_view, name='dashboard'),

    # Collection
    path('collections/', collection.collection_list_view, name='collection_list'),
    path('collections/new/', collection.collection_create, name='collection_create'),
    path('collections/<str:hash>/', collection.collection_detail_view, name='collection_detail'),
    path('collections/<str:hash>/edit/', collection.collection_update_view, name='collection_update'),
    path('collections/<str:hash>/delete/', collection.collection_delete_view, name='collection_delete'),
    

    # Public view for sharable collections
    path('share/collections/<str:hash>/', public.public_collection_view, name='public_collection_view'),

    # Item
    path('collections/<str:collection_hash>/add-item/', items.collection_item_create_view, name='item_create'),
    path('items/<str:hash>/', items.collection_item_detail_view, name='item_detail'),
    path('items/<str:hash>/edit/', items.collection_item_update_view, name='item_update'),
    path('items/<str:hash>/delete/', items.collection_item_delete_view, name='item_delete'),

    # Recent activity
    path('activity/', user.recent_activity_view, name='recent_activity_list'),

    # HX actions
    path('collections/<str:hash>/update-visibility/', collection_hx.update_collection_visibility, name='collection_update_visibility'),
    path('items/<str:hash>/update-status/', items_hx.update_item_status, name='item_update_status'),
    path('items/<str:hash>/toggle-favorite/', items_hx.toggle_item_favorite, name='item_toggle_favorite'),
    path('items/<str:hash>/change-type/', items_hx.change_item_type, name='item_change_type'),
    path('items/<str:hash>/add-attribute/', items_hx.item_add_attribute, name='item_add_attribute'),
    path('items/<str:hash>/edit-attribute/<str:attribute_name>/', items_hx.item_edit_attribute, name='item_edit_attribute'),
    path('items/<str:hash>/save-attribute/', items_hx.item_save_attribute, name='item_save_attribute'),
    path('items/<str:hash>/remove-attribute/<str:attribute_name>/', items_hx.item_remove_attribute, name='item_remove_attribute'),

    path('item/<str:hash>/book/authenticated/', public.book_item_authenticated, name='book_item_authenticated'),
    path('item/<str:hash>/book/guest/', public.book_item_guest, name='book_item_guest'),
    path('item/<str:hash>/book/release/<str:token>/', public.unreserve_guest_item, name='unreserve_guest_item'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)