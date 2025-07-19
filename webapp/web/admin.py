# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django.contrib import admin

from .models import Collection, CollectionItem, RecentActivity, ItemType, ItemAttribute

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


class ItemAttributeInline(admin.TabularInline):
    """
    Inline editor for ItemAttributes within the ItemType admin page.
    """
    model = ItemAttribute
    fields = ('name', 'display_name', 'attribute_type', 'required', 'skip_validation', 'order', 'choices', 'help_text')
    extra = 1
    ordering = ('order', 'display_name')


class CollectionItemInline(admin.TabularInline):
    """
    An inline editor for CollectionItems within the Collection admin page.
    TabularInline provides a more compact, table-based layout.
    """
    model = CollectionItem
    fields = ('name', 'item_type', 'status', 'description', 'image_url', 'is_favorite')
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


@admin.register(ItemType)
class ItemTypeAdmin(BerylModelAdmin):
    """
    Custom Admin configuration for the ItemType model.
    """
    inlines = [ItemAttributeInline]
    list_display = ('display_name', 'name', 'icon', 'created', 'is_deleted')
    list_filter = ('created', 'is_deleted')
    search_fields = ('name', 'display_name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'icon')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Audit Information', {
            'fields': BerylModelAdmin.readonly_fields,
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemAttribute)
class ItemAttributeAdmin(BerylModelAdmin):
    """
    Custom Admin configuration for the ItemAttribute model.
    """
    list_display = ('display_name', 'item_type', 'attribute_type', 'required', 'skip_validation', 'order', 'is_deleted')
    list_filter = ('attribute_type', 'required', 'skip_validation', 'item_type', 'is_deleted')
    search_fields = ('name', 'display_name', 'item_type__name', 'item_type__display_name')
    fieldsets = (
        (None, {
            'fields': ('item_type', 'name', 'display_name', 'attribute_type')
        }),
        ('Constraints', {
            'fields': ('required', 'skip_validation', 'order')
        }),
        ('Additional Settings', {
            'fields': ('choices', 'help_text')
        }),
        ('Audit Information', {
            'fields': BerylModelAdmin.readonly_fields,
            'classes': ('collapse',)
        }),
    )


@admin.register(CollectionItem)
class CollectionItemAdmin(BerylModelAdmin):
    """
    Custom Admin configuration for the CollectionItem model.
    """
    list_display = ('name', 'collection', 'item_type', 'status', 'is_favorite', 'created', 'is_bookable', 'is_deleted')
    list_filter = ('status', 'item_type', 'is_favorite', 'collection', 'is_deleted')
    search_fields = ('name', 'description', 'collection__name', 'item_type__display_name')
    fieldsets = (
        (None, {
            'fields': ('name', 'collection', 'item_type', 'status', 'is_favorite')
        }),
        ('Details', {
            'fields': ('description', 'image_url', 'attributes')
        }),
        ('Reservation Details', {
            'fields': ('reserved_date', 'reserved_by_name', 'reserved_by_email'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': BerylModelAdmin.readonly_fields,
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Customize the form to show a nice attributes widget
        """
        form = super().get_form(request, obj, **kwargs)
        if 'attributes' in form.base_fields:
            form.base_fields['attributes'].widget.attrs.update({
                'style': 'width: 100%; height: 200px;',
                'placeholder': 'JSON format: {"attribute_name": "value", ...}'
            })
        return form

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