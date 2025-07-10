# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.contrib import admin
from .models import Collection, CollectionItem, RecentActivity

# Let's create a base class for our models to inherit from.
# This avoids repeating common settings for all our models.
class BerylModelAdmin(admin.ModelAdmin):
    """
    A base ModelAdmin for models inheriting from BerylModel.
    Handles read-only audit fields and automatic user assignment.
    """
    # Make the audit fields read-only in the admin detail view.
    readonly_fields = ('created', 'updated', 'created_by', 'hash')

    def save_model(self, request, obj, form, change):
        """
        When creating a new object, set the created_by user to the
        currently logged-in admin user.
        """
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class CollectionItemInline(admin.TabularInline):
    """
    An inline editor for CollectionItems within the Collection admin page.
    TabularInline provides a more compact, table-based layout.
    """
    model = CollectionItem
    fields = ('name', 'status', 'description', 'image_url')
    extra = 1
    show_change_link = True

@admin.register(Collection)
class CollectionAdmin(BerylModelAdmin):
    """
    Custom Admin configuration for the Collection model.
    """
    inlines = [CollectionItemInline]
    list_display = ('name', 'item_count', 'created', 'is_deleted')
    list_filter = ('created', 'is_deleted')
    search_fields = ('name', 'description', 'created_by__username')

    def item_count(self, obj):
        """A custom method to display the number of items in the collection."""
        return obj.items.count()
    
    item_count.short_description = 'Item Count'


@admin.register(CollectionItem)
class CollectionItemAdmin(BerylModelAdmin):
    """
    Custom Admin configuration for the CollectionItem model.
    """
    list_display = ('name', 'collection', 'status', 'created', 'is_bookable', 'is_deleted')
    list_filter = ('status', 'collection', 'is_deleted')
    search_fields = ('name', 'description', 'collection__name')
    fieldsets = (
        (None, {
            'fields': ('name', 'collection', 'status')
        }),
        ('Details', {
            'fields': ('description', 'image_url')
        }),
        ('Audit Information', {
            'fields': BerylModelAdmin.readonly_fields,
            'classes': ('collapse',)
        }),
    )

@admin.register(RecentActivity)
class RecentActivityAdmin(admin.ModelAdmin):
    """
    Admin configuration for the RecentActivity model.
    This interface is optimized for viewing and filtering immutable log data.
    """
    list_display = (
        'created',
        'created_by',
        'name',
        'target_repr'
    )

    list_filter = (
        ('created_by', admin.RelatedOnlyFieldListFilter),
        ('subject', admin.RelatedOnlyFieldListFilter),
        'name',
        'created'
    )
    search_fields = (
        'name',
        'target_repr',
        'created_by__username',
        'subject__username'
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields]
        return []

    fieldsets = (
        ('Event Details', {
            'fields': ('name', 'created_by', 'subject', 'created')
        }),
        ('Target Information', {
            'fields': ('target_repr', 'details')
        }),
    )