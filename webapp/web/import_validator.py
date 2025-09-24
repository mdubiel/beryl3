"""
Import File Validation Module
=============================

Validates JSON/YAML import files against the Beryl3 import schema.
Provides comprehensive error reporting and data validation.
"""

import json
import yaml
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse

import jsonschema
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator

from .import_schema import IMPORT_SCHEMA


class ImportValidationError(Exception):
    """Custom exception for import validation errors"""
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class ImportValidator:
    """
    Validates import files and provides detailed error reporting
    """
    
    def __init__(self):
        self.url_validator = URLValidator()
        self.email_validator = EmailValidator()
        
    def load_file_content(self, file_content: str, file_extension: str) -> Dict[str, Any]:
        """
        Load and parse JSON or YAML content
        
        Args:
            file_content: Raw file content as string
            file_extension: File extension ('json' or 'yaml'/'yml')
            
        Returns:
            Parsed data dictionary
            
        Raises:
            ImportValidationError: If parsing fails
        """
        try:
            if file_extension.lower() in ['yaml', 'yml']:
                data = yaml.safe_load(file_content)
            elif file_extension.lower() == 'json':
                data = json.loads(file_content)
            else:
                raise ImportValidationError(f"Unsupported file format: {file_extension}")
                
            if not isinstance(data, dict):
                raise ImportValidationError("Import file must contain a JSON/YAML object at root level")
                
            return data
            
        except yaml.YAMLError as e:
            raise ImportValidationError(f"YAML parsing error: {str(e)}")
        except json.JSONDecodeError as e:
            raise ImportValidationError(f"JSON parsing error: {str(e)}")
        except Exception as e:
            raise ImportValidationError(f"File parsing error: {str(e)}")
    
    def validate_schema(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate data against the import schema
        
        Args:
            data: Parsed import data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Validate against JSON schema
            jsonschema.validate(data, IMPORT_SCHEMA)
        except jsonschema.ValidationError as e:
            errors.append({
                'type': 'schema_error',
                'path': list(e.absolute_path),
                'message': e.message,
                'invalid_value': e.instance
            })
        except jsonschema.SchemaError as e:
            errors.append({
                'type': 'schema_definition_error',
                'message': f"Schema definition error: {e.message}"
            })
            
        return errors
    
    def validate_business_rules(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate business logic and data consistency
        
        Args:
            data: Parsed import data
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check collections
        collections = data.get('collections', [])
        for col_idx, collection in enumerate(collections):
            col_path = f"collections[{col_idx}]"
            
            # Validate collection images
            images = collection.get('images', [])
            self._validate_images(images, f"{col_path}.images", errors)
            
            # Validate items
            items = collection.get('items', [])
            for item_idx, item in enumerate(items):
                item_path = f"{col_path}.items[{item_idx}]"
                
                # Validate item images
                item_images = item.get('images', [])
                self._validate_images(item_images, f"{item_path}.images", errors)
                
                # Validate links
                links = item.get('links', [])
                self._validate_links(links, f"{item_path}.links", errors)
                
                # Validate reservation data
                if item.get('status') == 'RESERVED':
                    reservation = item.get('reservation')
                    if not reservation:
                        errors.append({
                            'type': 'business_rule_error',
                            'path': item_path,
                            'message': 'Items with RESERVED status must include reservation details'
                        })
                    else:
                        self._validate_reservation(reservation, f"{item_path}.reservation", errors)
        
        # Validate item types
        item_types = data.get('item_types', [])
        for it_idx, item_type in enumerate(item_types):
            it_path = f"item_types[{it_idx}]"
            self._validate_item_type(item_type, it_path, errors)
        
        return errors
    
    def _validate_images(self, images: List[Dict], path: str, errors: List[Dict]):
        """Validate image array"""
        default_count = 0
        orders = []
        
        for img_idx, image in enumerate(images):
            img_path = f"{path}[{img_idx}]"
            
            # Validate URL
            url = image.get('url')
            if url:
                try:
                    self.url_validator(url)
                except ValidationError:
                    errors.append({
                        'type': 'validation_error',
                        'path': f"{img_path}.url",
                        'message': f'Invalid URL: {url}'
                    })
            
            # Check default image count
            if image.get('is_default', False):
                default_count += 1
                
            # Check order values
            order = image.get('order', 0)
            if order in orders:
                errors.append({
                    'type': 'validation_error',
                    'path': f"{img_path}.order",
                    'message': f'Duplicate order value: {order}'
                })
            orders.append(order)
        
        # Only one default image allowed
        if default_count > 1:
            errors.append({
                'type': 'business_rule_error',
                'path': path,
                'message': f'Only one image can be marked as default, found {default_count}'
            })
    
    def _validate_links(self, links: List[Dict], path: str, errors: List[Dict]):
        """Validate links array"""
        for link_idx, link in enumerate(links):
            link_path = f"{path}[{link_idx}]"
            
            # Validate URL
            url = link.get('url')
            if url:
                try:
                    self.url_validator(url)
                except ValidationError:
                    errors.append({
                        'type': 'validation_error',
                        'path': f"{link_path}.url",
                        'message': f'Invalid URL: {url}'
                    })
    
    def _validate_reservation(self, reservation: Dict, path: str, errors: List[Dict]):
        """Validate reservation details"""
        email = reservation.get('reserved_by_email')
        if email:
            try:
                self.email_validator(email)
            except ValidationError:
                errors.append({
                    'type': 'validation_error',
                    'path': f"{path}.reserved_by_email",
                    'message': f'Invalid email address: {email}'
                })
        
        # Validate date format
        date_str = reservation.get('reserved_date')
        if date_str:
            try:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                errors.append({
                    'type': 'validation_error',
                    'path': f"{path}.reserved_date",
                    'message': f'Invalid date format: {date_str}. Use ISO 8601 format.'
                })
    
    def _validate_item_type(self, item_type: Dict, path: str, errors: List[Dict]):
        """Validate item type definition"""
        attributes = item_type.get('attributes', [])
        orders = []
        names = []
        
        for attr_idx, attr in enumerate(attributes):
            attr_path = f"{path}.attributes[{attr_idx}]"
            
            # Check for duplicate names
            name = attr.get('name', '').lower()
            if name in names:
                errors.append({
                    'type': 'validation_error',
                    'path': f"{attr_path}.name",
                    'message': f'Duplicate attribute name: {name}'
                })
            names.append(name)
            
            # Check order values
            order = attr.get('order')
            if order and order in orders:
                errors.append({
                    'type': 'validation_error',
                    'path': f"{attr_path}.order",
                    'message': f'Duplicate order value: {order}'
                })
            if order:
                orders.append(order)
            
            # Validate choices for CHOICE type
            if attr.get('attribute_type') == 'CHOICE':
                choices = attr.get('choices')
                if not choices:
                    errors.append({
                        'type': 'validation_error',
                        'path': f"{attr_path}.choices",
                        'message': 'CHOICE type attributes must include choices array'
                    })
                else:
                    try:
                        json.loads(choices)
                    except json.JSONDecodeError:
                        errors.append({
                            'type': 'validation_error',
                            'path': f"{attr_path}.choices",
                            'message': 'Choices must be valid JSON array'
                        })
    
    def validate_import_file(self, file_content: str, file_extension: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Complete validation of an import file
        
        Args:
            file_content: Raw file content
            file_extension: File extension
            
        Returns:
            Tuple of (parsed_data, errors)
        """
        errors = []
        
        try:
            # Parse file content
            data = self.load_file_content(file_content, file_extension)
            
            # Schema validation
            schema_errors = self.validate_schema(data)
            errors.extend(schema_errors)
            
            # Business rules validation (only if schema is valid)
            if not schema_errors:
                business_errors = self.validate_business_rules(data)
                errors.extend(business_errors)
            
            return data, errors
            
        except ImportValidationError as e:
            errors.append({
                'type': 'parsing_error',
                'message': e.message
            })
            return {}, errors
    
    def generate_validation_report(self, errors: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable validation report
        
        Args:
            errors: List of validation errors
            
        Returns:
            Formatted error report
        """
        if not errors:
            return "✅ Import file validation passed successfully!"
        
        report = f"❌ Import file validation failed with {len(errors)} error(s):\n\n"
        
        for i, error in enumerate(errors, 1):
            error_type = error.get('type', 'unknown')
            message = error.get('message', 'Unknown error')
            path = error.get('path')
            
            report += f"{i}. {error_type.upper().replace('_', ' ')}\n"
            if path:
                if isinstance(path, list):
                    path_str = '.'.join(map(str, path))
                else:
                    path_str = str(path)
                report += f"   Location: {path_str}\n"
            report += f"   Message: {message}\n"
            
            if 'invalid_value' in error:
                report += f"   Invalid Value: {error['invalid_value']}\n"
            
            report += "\n"
        
        return report