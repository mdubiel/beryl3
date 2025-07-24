# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from web.views import index, landing, user, collection, collection_hx, items, items_hx, public, sys


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
    
    # User favorites
    path('favorites/', user.favorites_view, name='favorites_list'),

    # HX actions
    path('collections/<str:hash>/update-visibility/', collection_hx.update_collection_visibility, name='collection_update_visibility'),
    path('items/<str:hash>/update-status/', items_hx.update_item_status, name='item_update_status'),
    path('items/<str:hash>/toggle-favorite/', items_hx.toggle_item_favorite, name='item_toggle_favorite'),
    path('items/<str:hash>/change-type/', items_hx.change_item_type, name='item_change_type'),
    path('items/<str:hash>/add-attribute/', items_hx.item_add_attribute, name='item_add_attribute'),
    path('items/<str:hash>/edit-attribute/<str:attribute_name>/', items_hx.item_edit_attribute, name='item_edit_attribute'),
    path('items/<str:hash>/save-attribute/', items_hx.item_save_attribute, name='item_save_attribute'),
    path('items/<str:hash>/remove-attribute/<str:attribute_name>/', items_hx.item_remove_attribute, name='item_remove_attribute'),
    
    # Item link management
    path('items/<str:hash>/add-link/', items_hx.item_add_link, name='item_add_link'),
    path('items/<str:hash>/edit-link/<int:link_id>/', items_hx.item_edit_link, name='item_edit_link'),
    path('items/<str:hash>/save-link/', items_hx.item_save_link, name='item_save_link'),
    path('items/<str:hash>/remove-link/<int:link_id>/', items_hx.item_remove_link, name='item_remove_link'),

    # Item move/copy operations
    path('items/<str:item_hash>/move/', items.move_item_to_collection, name='move_item'),
    path('items/<str:item_hash>/copy/', items.copy_item_to_collection, name='copy_item'),
    path('items/<str:item_hash>/collections/', items.get_user_collections_for_move_copy, name='get_collections_for_move_copy'),

    path('item/<str:hash>/book/authenticated/', public.book_item_authenticated, name='book_item_authenticated'),
    path('item/<str:hash>/book/guest/', public.book_item_guest, name='book_item_guest'),
    path('item/<str:hash>/book/release/<str:token>/', public.unreserve_guest_item, name='unreserve_guest_item'),

    # System administration
    path('sys/', sys.sys_dashboard, name='sys_dashboard'),
    path('sys/users/', sys.sys_users, name='sys_users'),
    path('sys/users/<int:user_id>/profile/', sys.sys_user_profile, name='sys_user_profile'),
    path('sys/activity/', sys.sys_activity, name='sys_activity'),
    path('sys/metrics/', sys.sys_metrics, name='sys_metrics'),
    path('sys/metrics/prometheus/', sys.sys_prometheus_metrics, name='sys_prometheus_metrics'),
    path('sys/backup/', sys.sys_backup, name='sys_backup'),
    path('sys/settings/', sys.sys_settings, name='sys_settings'),
    path('sys/media/', sys.sys_media_browser, name='sys_media_browser'),
    path('sys/media/upload/', sys.sys_media_upload, name='sys_media_upload'),
    path('sys/media/delete/<str:media_file_hash>/', sys.sys_media_delete, name='sys_media_delete'),
    path('sys/media/cleanup-abandoned/', sys.sys_media_cleanup_abandoned, name='sys_media_cleanup_abandoned'),
    path('sys/media/verify-all/', sys.sys_media_verify_all, name='sys_media_verify_all'),
    
    # System HTMX endpoints
    path('sys/users/<int:user_id>/toggle-active/', sys.sys_user_toggle_active, name='sys_user_toggle_active'),
    path('sys/users/<int:user_id>/reset-password/', sys.sys_user_reset_password, name='sys_user_reset_password'),
    path('sys/users/<int:user_id>/unlock-account/', sys.sys_user_unlock_account, name='sys_user_unlock_account'),
    path('sys/users/<int:user_id>/verify-email/', sys.sys_user_force_email_verification, name='sys_user_verify_email'),
    path('sys/activity/cleanup/', sys.sys_activity_cleanup, name='sys_activity_cleanup'),
    
    # Item type management
    path('sys/item-types/', sys.sys_item_types, name='sys_item_types'),
    path('sys/item-types/<int:item_type_id>/', sys.sys_item_type_detail, name='sys_item_type_detail'),
    path('sys/item-types/create/', sys.sys_item_type_create, name='sys_item_type_create'),
    path('sys/item-types/<int:item_type_id>/update/', sys.sys_item_type_update, name='sys_item_type_update'),
    path('sys/item-types/<int:item_type_id>/delete/', sys.sys_item_type_delete, name='sys_item_type_delete'),
    
    # Item attribute management
    path('sys/item-types/<int:item_type_id>/attributes/create/', sys.sys_item_attribute_create, name='sys_item_attribute_create'),
    path('sys/attributes/<int:attribute_id>/update/', sys.sys_item_attribute_update, name='sys_item_attribute_update'),
    path('sys/attributes/<int:attribute_id>/delete/', sys.sys_item_attribute_delete, name='sys_item_attribute_delete'),
    
    # Link pattern management
    path('sys/link-patterns/', sys.sys_link_patterns, name='sys_link_patterns'),
    path('sys/link-patterns/<int:link_pattern_id>/', sys.sys_link_pattern_detail, name='sys_link_pattern_detail'),
    path('sys/link-patterns/create/', sys.sys_link_pattern_create, name='sys_link_pattern_create'),
    path('sys/link-patterns/<int:link_pattern_id>/update/', sys.sys_link_pattern_update, name='sys_link_pattern_update'),
    path('sys/link-patterns/<int:link_pattern_id>/delete/', sys.sys_link_pattern_delete, name='sys_link_pattern_delete'),
    
    # HTMX endpoints
    path('sys/validate-lucide-icon/', sys.sys_validate_lucide_icon, name='sys_validate_lucide_icon'),
    path('sys/lucide-icon-search/', sys.sys_lucide_icon_search, name='sys_lucide_icon_search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)