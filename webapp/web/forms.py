# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from django import forms

from .models import Collection, CollectionItem

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description', 'image_url']

        labels = {
            'name': 'Collection Name',
            'image_url': 'Cover Image URL (Optional)',
        }
        help_texts = {
            'name': 'Give your new collection a unique and descriptive name.',
        }

class CollectionItemForm(forms.ModelForm):
    class Meta:
        model = CollectionItem
        fields = ['name', 'status', 'description', 'image_url']

        labels = {
            'name': 'Item Name',
            'image_url': 'Image URL (Optional)',
        }