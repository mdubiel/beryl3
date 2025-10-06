# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
import os
from PIL import Image
from io import BytesIO

from .models import Collection, CollectionItem, MediaFile, ItemType

class CollectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing an existing collection, filter attributes to only those used in the collection
        if self.instance and self.instance.pk:
            from web.models import CollectionItemAttributeValue, ItemAttribute

            # Get all attributes used in this collection's items
            used_attribute_ids = CollectionItemAttributeValue.objects.filter(
                item__collection=self.instance
            ).values_list('item_attribute_id', flat=True).distinct()

            # Filter the grouping_attribute and sort_attribute querysets
            if used_attribute_ids:
                used_attributes = ItemAttribute.objects.filter(id__in=used_attribute_ids)
                self.fields['grouping_attribute'].queryset = used_attributes
                self.fields['sort_attribute'].queryset = used_attributes
            else:
                # No attributes used, show empty queryset
                self.fields['grouping_attribute'].queryset = ItemAttribute.objects.none()
                self.fields['sort_attribute'].queryset = ItemAttribute.objects.none()

    class Meta:
        model = Collection
        fields = ['name', 'description', 'image_url', 'group_by', 'grouping_attribute', 'sort_by', 'sort_attribute']

        labels = {
            'name': 'Collection Name',
            'image_url': 'Cover Image URL (Optional)',
            'group_by': 'Group By',
            'grouping_attribute': 'Group By Attribute',
            'sort_by': 'Sort By',
            'sort_attribute': 'Sort By Attribute',
        }
        help_texts = {
            'name': 'Give your new collection a unique and descriptive name.',
            'group_by': 'Group items by type, status, or attribute',
            'grouping_attribute': 'Select which attribute to use for grouping (when Group By = Attribute)',
            'sort_by': 'Sort items within groups',
            'sort_attribute': 'Select which attribute to sort by (when Sort By = Attribute)',
        }

class CollectionItemForm(forms.ModelForm):
    item_type = forms.ModelChoiceField(
        queryset=ItemType.objects.all(),
        required=False,
        empty_label="(No Type)",
        label="Item Type (Optional)"
    )

    link_url = forms.URLField(
        required=False,
        label="Link URL (Optional)",
        help_text="Add a related link for this item"
    )

    class Meta:
        model = CollectionItem
        fields = ['name', 'item_type', 'status', 'description', 'image_url']

        labels = {
            'name': 'Item Name',
            'image_url': 'Image URL (Optional)',
        }


class ImageUploadForm(forms.Form):
    """
    Form for uploading images via file upload or URL download
    """
    UPLOAD_METHODS = (
        ('file', 'Upload File'),
        ('url', 'Download from URL'),
    )
    
    upload_method = forms.ChoiceField(
        choices=UPLOAD_METHODS,
        widget=forms.RadioSelect,
        initial='file',
        label='Upload Method'
    )
    
    # File upload field
    image_file = forms.ImageField(
        required=False,
        label='Select Image File',
        help_text='Select an image file from your device (JPEG, PNG, WebP). Max size: 5MB',
        widget=forms.ClearableFileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/jpeg,image/png,image/webp'
        })
    )
    
    # URL download field
    image_url = forms.URLField(
        required=False,
        label='Image URL',
        help_text='Enter a URL to download an image from the internet',
        widget=forms.URLInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'https://example.com/image.jpg'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        upload_method = cleaned_data.get('upload_method')
        image_file = cleaned_data.get('image_file')
        image_url = cleaned_data.get('image_url')
        
        if upload_method == 'file' and not image_file:
            raise ValidationError('Please select an image file to upload.')
        
        # Validate file size (5MB limit)
        if upload_method == 'file' and image_file:
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if image_file.size > max_size:
                raise ValidationError(f'Image file is too large. Maximum size is 5MB. Your file is {image_file.size / (1024*1024):.1f}MB.')
        
        if upload_method == 'url' and not image_url:
            raise ValidationError('Please enter a URL to download an image.')
        
        # Validate URL if provided
        if upload_method == 'url' and image_url:
            try:
                # Basic URL validation
                url_validator = URLValidator()
                url_validator(image_url)
                
                # Check if URL is accessible (optional - can be resource intensive)
                response = requests.head(image_url, timeout=10)
                if response.status_code != 200:
                    raise ValidationError(f'Cannot access URL: {image_url} (HTTP {response.status_code})')
                
                # Check if it's an image
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    raise ValidationError('URL does not point to an image file.')
                    
            except requests.RequestException:
                raise ValidationError('Cannot access the provided URL. Please check the URL and try again.')
        
        return cleaned_data
    
    def save_media_file(self, user, media_type=MediaFile.MediaType.OTHER):
        """
        Create a MediaFile instance from the form data
        """
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import uuid
        
        cleaned_data = self.cleaned_data
        upload_method = cleaned_data['upload_method']
        
        if upload_method == 'file':
            # Handle file upload
            image_file = cleaned_data['image_file']
            original_filename = image_file.name
            
            # Generate unique filename
            file_extension = os.path.splitext(original_filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Determine storage path based on media type
            if media_type == MediaFile.MediaType.COLLECTION_HEADER:
                file_path = f"collections/{unique_filename}"
            elif media_type == MediaFile.MediaType.COLLECTION_ITEM:
                file_path = f"items/{unique_filename}"
            else:
                file_path = f"uploads/{unique_filename}"
            
            # Save file to storage
            saved_path = default_storage.save(file_path, image_file)
            
            # Get image dimensions
            try:
                image = Image.open(image_file)
                width, height = image.size
            except Exception:
                width, height = None, None
            
            # Create MediaFile record
            media_file = MediaFile.objects.create(
                name=f"Uploaded: {original_filename}",
                file_path=saved_path,
                original_filename=original_filename,
                file_size=image_file.size,
                content_type=image_file.content_type,
                media_type=media_type,
                width=width,
                height=height,
                created_by=user
            )
            
        elif upload_method == 'url':
            # Handle URL download
            image_url = cleaned_data['image_url']
            
            try:
                # Download the image
                response = requests.get(image_url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Get original filename from URL
                original_filename = os.path.basename(image_url.split('?')[0])
                if not original_filename or '.' not in original_filename:
                    # Generate filename from content type
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    extension = content_type.split('/')[-1]
                    original_filename = f"downloaded_image.{extension}"
                
                # Generate unique filename
                file_extension = os.path.splitext(original_filename)[1].lower()
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                
                # Determine storage path based on media type
                if media_type == MediaFile.MediaType.COLLECTION_HEADER:
                    file_path = f"collections/{unique_filename}"
                elif media_type == MediaFile.MediaType.COLLECTION_ITEM:
                    file_path = f"items/{unique_filename}"
                else:
                    file_path = f"downloads/{unique_filename}"
                
                # Read image content and save to storage
                image_content = response.content
                saved_path = default_storage.save(file_path, ContentFile(image_content))
                
                # Get image dimensions
                try:
                    image = Image.open(BytesIO(image_content))
                    width, height = image.size
                except Exception:
                    width, height = None, None
                
                # Create MediaFile record
                media_file = MediaFile.objects.create(
                    name=f"Downloaded: {original_filename}",
                    file_path=saved_path,
                    original_filename=original_filename,
                    file_size=len(image_content),
                    content_type=response.headers.get('content-type', 'image/jpeg'),
                    media_type=media_type,
                    width=width,
                    height=height,
                    created_by=user,
                    metadata={'source_url': image_url}
                )
                
            except requests.RequestException as e:
                raise ValidationError(f'Failed to download image: {str(e)}')
        
        return media_file