# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from web.views import index, landing, user, collection, collection_hx, items, items_hx, public, sys, images, marketing, user_settings, fix_attrs, location


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
    path('collections/<str:hash>/manage-images/', images.collection_manage_images, name='collection_manage_images'),
    

    # Public view for sharable collections
    path('share/collections/<str:hash>/', public.public_collection_view, name='public_collection_view'),

    # Task 65: Lazy load item images for performance
    path('api/items/<str:item_hash>/image/', public.lazy_load_item_image, name='lazy_load_item_image'),

    # Task 64: Public user profile
    path('u/<str:username>/', public.public_user_profile, name='public_user_profile'),

    # Item
    path('collections/<str:collection_hash>/add-item/', items.collection_item_create_view, name='item_create'),
    # HTMX endpoint for item creation - must come before items/<str:hash>/ to avoid matching
    path('items/get-type-attributes/', items_hx.get_type_attributes_for_create, name='get_type_attributes_for_create'),
    path('items/<str:hash>/', items.collection_item_detail_view, name='item_detail'),
    path('items/<str:hash>/edit/', items.collection_item_update_view, name='item_update'),
    path('items/<str:hash>/delete/', items.collection_item_delete_view, name='item_delete'),
    path('items/<str:hash>/manage-images/', images.item_manage_images, name='item_manage_images'),

    # Recent activity
    path('activity/', user.recent_activity_view, name='recent_activity_list'),
    
    # User favorites
    path('favorites/', user.favorites_view, name='favorites_list'),

    # User account settings
    path('user/settings/', user_settings.user_settings_view, name='user_settings'),

    # Task 50: Location management
    path('locations/', location.location_list_view, name='location_list'),
    path('locations/new/', location.location_create_view, name='location_create'),
    path('locations/autocomplete/', location.location_autocomplete_view, name='location_autocomplete'),
    path('locations/quick-create/', location.location_quick_create_view, name='location_quick_create'),
    path('locations/<str:hash>/', location.location_items_view, name='location_items'),
    path('locations/<str:hash>/edit/', location.location_update_view, name='location_update'),
    path('locations/<str:hash>/delete/', location.location_delete_view, name='location_delete'),

    # HX actions
    path('collections/<str:hash>/update-visibility/', collection_hx.update_collection_visibility, name='collection_update_visibility'),
    path('items/<str:hash>/update-status/', items_hx.update_item_status, name='item_update_status'),
    path('items/<str:hash>/toggle-favorite/', items_hx.toggle_item_favorite, name='item_toggle_favorite'),
    path('items/<str:hash>/change-type/', items_hx.change_item_type, name='item_change_type'),
    path('items/<str:hash>/add-attribute/', items_hx.item_add_attribute, name='item_add_attribute'),
    path('items/<str:hash>/get-attribute-input/', items_hx.item_get_attribute_input, name='item_get_attribute_input'),
    path('items/<str:hash>/autocomplete-attribute-value/', items_hx.item_autocomplete_attribute_value, name='item_autocomplete_attribute_value'),
    path('items/<str:hash>/edit-attribute-value/<str:attr_value_hash>/', items_hx.item_edit_attribute_value, name='item_edit_attribute_value'),
    path('items/<str:hash>/save-attribute/', items_hx.item_save_attribute, name='item_save_attribute'),
    path('items/<str:hash>/remove-attribute-value/<str:attr_value_hash>/', items_hx.item_remove_attribute_value, name='item_remove_attribute_value'),
    path('items/<str:hash>/toggle-boolean-attribute/<str:attr_value_hash>/', items_hx.item_toggle_boolean_attribute, name='item_toggle_boolean_attribute'),

    # Item link management
    path('items/<str:hash>/add-link/', items_hx.item_add_link, name='item_add_link'),
    path('items/<str:hash>/edit-link/<int:link_id>/', items_hx.item_edit_link, name='item_edit_link'),
    path('items/<str:hash>/save-link/', items_hx.item_save_link, name='item_save_link'),
    path('items/<str:hash>/remove-link/<int:link_id>/', items_hx.item_remove_link, name='item_remove_link'),

    # Task 50: Personal information (Your ID and Location) management
    path('items/<str:hash>/edit-your-id/', items_hx.item_edit_your_id, name='item_edit_your_id'),
    path('items/<str:hash>/edit-location/', items_hx.item_edit_location, name='item_edit_location'),
    path('items/<str:hash>/edit-your-id-inline/', items_hx.item_edit_your_id_inline, name='item_edit_your_id_inline'),
    path('items/<str:hash>/edit-location-inline/', items_hx.item_edit_location_inline, name='item_edit_location_inline'),
    path('items/<str:hash>/reload-personal-info/', items_hx.item_reload_personal_info, name='item_reload_personal_info'),
    path('items/<str:hash>/save-personal-info/', items_hx.item_save_personal_info, name='item_save_personal_info'),
    
    # Image management HTMX endpoints
    path('images/<str:hash>/set-default/', images.set_default_image, name='set_default_image'),
    path('images/<str:hash>/delete/', images.delete_image, name='delete_image'),
    path('images/<str:hash>/switch/', images.switch_image, name='switch_image'),
    path('<str:hash>/reorder-images/', images.reorder_images, name='reorder_images'),

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
    path('sys/metrics/', sys.sys_metrics, name='sys_metrics'),
    path('sys/metrics/prometheus/', sys.sys_prometheus_metrics, name='sys_prometheus_metrics'),
    path('sys/email-queue/', sys.sys_email_queue, name='sys_email_queue'),
    path('sys/email-queue/process/', sys.sys_email_queue_process, name='sys_email_queue_process'),
    path('sys/email-queue/cleanup/', sys.sys_email_queue_cleanup, name='sys_email_queue_cleanup'),
    path('sys/marketing-consent/', sys.sys_marketing_consent, name='sys_marketing_consent'),
    path('sys/marketing-consent/sync-user/<int:user_id>/', sys.sys_marketing_consent_sync_user, name='sys_marketing_consent_sync_user'),
    path('sys/marketing-consent/bulk-sync/', sys.sys_marketing_consent_bulk_sync, name='sys_marketing_consent_bulk_sync'),
    path('sys/marketing-consent/remove-user/<int:user_id>/', sys.sys_marketing_consent_remove_user, name='sys_marketing_consent_remove_user'),
    path('sys/marketing-consent/bulk-remove-opted-out/', sys.sys_marketing_consent_bulk_remove_opted_out, name='sys_marketing_consent_bulk_remove_opted_out'),
    path('sys/marketing-consent/full-sync/', sys.sys_marketing_consent_full_sync, name='sys_marketing_consent_full_sync'),
    path('sys/import/', sys.sys_import_data, name='sys_import_data'),
    path('sys/import/confirm/', sys.sys_import_data_confirm, name='sys_import_data_confirm'),
    path('sys/import/result/', sys.sys_import_result, name='sys_import_result'),
    path('sys/fix-attributes/', fix_attrs.fix_production_attributes, name='sys_fix_attributes'),
    
    # Content moderation
    path('sys/content-moderation/', sys.content_moderation_dashboard, name='sys_content_moderation_dashboard'),
    path('sys/content-moderation/flagged/', sys.flagged_images, name='sys_flagged_images'),
    path('sys/content-moderation/violations/', sys.user_violations, name='sys_user_violations'),
    path('sys/content-moderation/settings/', sys.content_moderation_settings, name='sys_content_moderation_settings'),
    path('sys/content-moderation/review/<int:file_id>/', sys.review_content, name='sys_review_content'),
    path('sys/content-moderation/batch-analyze/', sys.batch_analyze_images, name='sys_batch_analyze_images'),
    path('sys/content-moderation/approve/<int:file_id>/', sys.approve_flagged_image, name='sys_approve_flagged_image'),
    path('sys/content-moderation/reject/<int:file_id>/', sys.reject_flagged_image, name='sys_reject_flagged_image'),
    path('sys/users/<int:user_id>/detail/', sys.user_detail, name='sys_user_detail'),
    path('sys/users/<int:user_id>/content/', sys.user_content, name='sys_user_content'),
    
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
    
    # Marketing email management
    path('unsubscribe/<str:token>/', marketing.marketing_unsubscribe, name='marketing_unsubscribe'),
    
    # Legal pages
    path('terms/', index.terms_view, name='terms'),
    path('privacy/', index.privacy_view, name='privacy'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)