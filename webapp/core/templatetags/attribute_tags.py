"""Template tags and filters for attribute display."""

from django import template
from collections import OrderedDict

register = template.Library()


@register.filter
def group_attributes(attributes):
    """
    Group attributes by attribute name.

    Takes a list of attribute dictionaries from get_display_attributes() and groups
    them by attribute name, combining multiple values of the same attribute.

    Input format (from get_display_attributes()):
    [
        {'attribute': ItemAttribute, 'value': 'Terry Pratchett', 'is_multiple': True, ...},
        {'attribute': ItemAttribute (same), 'value': 'Neil Gaiman', 'is_multiple': True, ...},
        {'attribute': ItemAttribute2, 'value': 'Fantasy', 'is_multiple': True, ...},
    ]

    Output format:
    [
        {
            'attribute': ItemAttribute,
            'values': [
                {'value': 'Terry Pratchett', 'display_value': 'Terry Pratchett', 'attr_value_hash': ...},
                {'value': 'Neil Gaiman', 'display_value': 'Neil Gaiman', 'attr_value_hash': ...},
            ],
            'is_multiple': True,
        },
        {
            'attribute': ItemAttribute2,
            'values': [
                {'value': 'Fantasy', 'display_value': 'Fantasy', 'attr_value_hash': ...},
            ],
            'is_multiple': True,
        },
    ]
    """
    if not attributes:
        return []

    # Use OrderedDict to preserve the order of first appearance
    grouped = OrderedDict()

    for attr_data in attributes:
        attr = attr_data['attribute']
        attr_id = attr.id

        if attr_id not in grouped:
            # First occurrence of this attribute
            grouped[attr_id] = {
                'attribute': attr,
                'values': [],
                'is_multiple': attr_data.get('is_multiple', False),
            }

        # Add this value to the group
        grouped[attr_id]['values'].append({
            'value': attr_data['value'],
            'display_value': attr_data.get('display_value', attr_data['value']),
            'attr_value_hash': attr_data.get('attr_value_hash'),
        })

        # If any instance is marked as multiple, mark the whole group as multiple
        if attr_data.get('is_multiple', False):
            grouped[attr_id]['is_multiple'] = True

    return list(grouped.values())
