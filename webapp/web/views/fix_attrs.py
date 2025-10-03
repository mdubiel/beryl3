"""
View to fix production attributes via web interface
"""

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from web.models import Collection, CollectionItem, ItemType, ItemAttribute
from django.contrib.auth import get_user_model
import re
import json

@staff_member_required
@csrf_exempt
@require_POST
def fix_production_attributes(request):
    """
    Fix production attributes stored in descriptions
    """
    
    try:
        User = get_user_model()
        user = User.objects.get(username="mdubiel")
        
        # Polish to English mapping
        polish_to_english = {
            "Seria": "series",
            "Autor": "author", 
            "Wydawca": "publisher",
            "Wolumen": "volume",
            "Przeczytane": "read_status",
            "Numer zestawu": "set_number",
            "Ilość części": "piece_count"
        }

        # Get item types
        book_type = ItemType.objects.filter(name="book").first()
        lego_type = ItemType.objects.filter(name="lego_set").first()
        comic_type = ItemType.objects.filter(name="comic").first()

        results = {
            "user_found": user.username,
            "item_types": {
                "book": book_type is not None,
                "lego": lego_type is not None,
                "comic": comic_type is not None
            },
            "attributes_created": [],
            "items_fixed": []
        }

        # Create missing attributes for book type
        if book_type:
            for english_name in ["series", "volume", "read_status"]:
                attr, created = ItemAttribute.objects.get_or_create(
                    name=english_name,
                    item_type=book_type,
                    defaults={
                        "display_name": english_name.replace("_", " ").title(),
                        "attribute_type": "BOOLEAN" if english_name == "read_status" else "TEXT",
                        "required": False,
                        "order": 10
                    }
                )
                results["attributes_created"].append({
                    "name": english_name,
                    "created": created
                })

        # Process items
        items = CollectionItem.objects.filter(created_by=user)
        results["total_items"] = items.count()

        fixed_count = 0
        for item in items:
            if not item.description:
                continue
                
            # Check if description contains Polish attributes
            has_polish_attrs = any(polish_name in item.description for polish_name in polish_to_english.keys())
            if not has_polish_attrs:
                continue
                
            # Parse attributes from description
            parsed_attrs = {}
            remaining_description = item.description
            
            for polish_name, english_name in polish_to_english.items():
                pattern = rf"{re.escape(polish_name)}:\s*([^\n]+)"
                match = re.search(pattern, item.description)
                if match:
                    value = match.group(1).strip()
                    parsed_attrs[english_name] = value
                    remaining_description = re.sub(pattern + r"\n?", "", remaining_description)
            
            if parsed_attrs:
                # Determine correct item type
                old_item_type = item.item_type.name if item.item_type else "none"
                
                if "set_number" in parsed_attrs or "piece_count" in parsed_attrs:
                    new_item_type = lego_type or item.item_type
                elif "series" in parsed_attrs and "volume" in parsed_attrs:
                    new_item_type = comic_type or book_type or item.item_type
                else:
                    new_item_type = book_type or item.item_type
                
                # Update item
                item.attributes = parsed_attrs
                item.item_type = new_item_type
                item.description = remaining_description.strip()
                item.save()
                
                fixed_count += 1
                if fixed_count <= 20:  # Log first 20
                    results["items_fixed"].append({
                        "name": item.name,
                        "attributes": parsed_attrs,
                        "old_type": old_item_type,
                        "new_type": new_item_type.name if new_item_type else "none"
                    })

        results["total_fixed"] = fixed_count
        results["status"] = "success"
        
        return JsonResponse(results)
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e)
        })