"""
Beryl3 Data Import Schema Definition
====================================

This module defines the JSON/YAML schema for comprehensive data imports.
Supports Collections, Items, Links, Images, and all associated metadata.
"""

# JSON Schema for Beryl3 Import Format
IMPORT_SCHEMA = {
    "type": "object",
    "required": ["version", "collections"],
    "properties": {
        "version": {
            "type": "string",
            "enum": ["1.0"],
            "description": "Import format version"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Import title/name"},
                "description": {"type": "string", "description": "Import description"},
                "source": {"type": "string", "description": "Source of the data"},
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string", "description": "Original creator"},
                "import_notes": {"type": "string", "description": "Notes about this import"}
            }
        },
        "options": {
            "type": "object",
            "properties": {
                "download_images": {
                    "type": "boolean", 
                    "default": False,
                    "description": "Whether to download images from web URLs"
                },
                "skip_existing": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Skip items that already exist (by name)"
                },
                "default_visibility": {
                    "type": "string",
                    "enum": ["PRIVATE", "UNLISTED", "PUBLIC"],
                    "default": "PRIVATE",
                    "description": "Default visibility for imported collections"
                }
            }
        },
        "collections": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "maxLength": 255},
                    "description": {"type": "string"},
                    "visibility": {
                        "type": "string",
                        "enum": ["PRIVATE", "UNLISTED", "PUBLIC"],
                        "default": "PRIVATE"
                    },
                    "image_url": {
                        "type": "string", 
                        "format": "uri",
                        "description": "URL of collection main image"
                    },
                    "images": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "required": ["url"],
                            "properties": {
                                "url": {"type": "string", "format": "uri"},
                                "is_default": {"type": "boolean", "default": False},
                                "order": {"type": "integer", "minimum": 0, "maximum": 2},
                                "filename": {"type": "string", "description": "Suggested filename"},
                                "alt_text": {"type": "string", "description": "Alt text for image"}
                            }
                        }
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string", "maxLength": 255},
                                "description": {"type": "string"},
                                "status": {
                                    "type": "string",
                                    "enum": [
                                        "IN_COLLECTION", "PREVIOUSLY_OWNED", 
                                        "LENT_OUT", "RESERVED", "ORDERED", "WANTED"
                                    ],
                                    "default": "IN_COLLECTION"
                                },
                                "is_favorite": {"type": "boolean", "default": False},
                                "item_type": {
                                    "type": "string",
                                    "description": "Name of ItemType (will be created if not exists)"
                                },
                                "attributes": {
                                    "type": "object",
                                    "description": "Key-value pairs for item attributes",
                                    "additionalProperties": {"type": "string"}
                                },
                                "image_url": {
                                    "type": "string", 
                                    "format": "uri",
                                    "description": "URL of item main image"
                                },
                                "images": {
                                    "type": "array",
                                    "maxItems": 3,
                                    "items": {
                                        "type": "object",
                                        "required": ["url"],
                                        "properties": {
                                            "url": {"type": "string", "format": "uri"},
                                            "is_default": {"type": "boolean", "default": False},
                                            "order": {"type": "integer", "minimum": 0, "maximum": 2},
                                            "filename": {"type": "string"},
                                            "alt_text": {"type": "string"}
                                        }
                                    }
                                },
                                "links": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["url"],
                                        "properties": {
                                            "url": {"type": "string", "format": "uri"},
                                            "display_name": {"type": "string"},
                                            "order": {"type": "integer", "minimum": 0}
                                        }
                                    }
                                },
                                "reservation": {
                                    "type": "object",
                                    "description": "Reservation details if status is RESERVED",
                                    "properties": {
                                        "reserved_by_name": {"type": "string"},
                                        "reserved_by_email": {"type": "string", "format": "email"},
                                        "reserved_date": {"type": "string", "format": "date-time"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "item_types": {
            "type": "array",
            "description": "Optional item type definitions to create before import",
            "items": {
                "type": "object",
                "required": ["name", "display_name"],
                "properties": {
                    "name": {"type": "string", "maxLength": 100},
                    "display_name": {"type": "string", "maxLength": 100},
                    "description": {"type": "string"},
                    "icon": {"type": "string", "maxLength": 50},
                    "attributes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "display_name", "attribute_type"],
                            "properties": {
                                "name": {"type": "string"},
                                "display_name": {"type": "string"},
                                "attribute_type": {
                                    "type": "string",
                                    "enum": ["TEXT", "NUMBER", "DATE", "BOOLEAN", "CHOICE", "URL"]
                                },
                                "required": {"type": "boolean", "default": False},
                                "order": {"type": "integer", "minimum": 1},
                                "choices": {
                                    "type": "string",
                                    "description": "JSON array of choices for CHOICE type"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Example import file structure
EXAMPLE_IMPORT_DATA = {
    "version": "1.0",
    "metadata": {
        "title": "My Collection Import",
        "description": "Import of my personal collections",
        "source": "manual_export",
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "john.doe@example.com",
        "import_notes": "Migrating from old system"
    },
    "options": {
        "download_images": True,
        "skip_existing": True,
        "default_visibility": "PRIVATE"
    },
    "item_types": [
        {
            "name": "vinyl_record",
            "display_name": "Vinyl Record",
            "description": "Music vinyl records",
            "icon": "disc",
            "attributes": [
                {"name": "artist", "display_name": "Artist", "attribute_type": "TEXT", "required": True, "order": 1},
                {"name": "album", "display_name": "Album", "attribute_type": "TEXT", "required": True, "order": 2},
                {"name": "year", "display_name": "Year", "attribute_type": "NUMBER", "required": False, "order": 3},
                {"name": "condition", "display_name": "Condition", "attribute_type": "CHOICE", "required": False, "order": 4,
                 "choices": "[\"Mint\", \"Near Mint\", \"Very Good\", \"Good\", \"Fair\", \"Poor\"]"}
            ]
        }
    ],
    "collections": [
        {
            "name": "My Vinyl Collection",
            "description": "Personal collection of **vinyl records** with *detailed* tracking.",
            "visibility": "UNLISTED",
            "image_url": "https://example.com/collection-cover.jpg",
            "images": [
                {
                    "url": "https://example.com/collection-cover.jpg",
                    "is_default": True,
                    "order": 0,
                    "filename": "collection-cover.jpg",
                    "alt_text": "My vinyl collection cover"
                }
            ],
            "items": [
                {
                    "name": "Abbey Road",
                    "description": "Classic Beatles album from **1969**.",
                    "status": "IN_COLLECTION",
                    "is_favorite": True,
                    "item_type": "vinyl_record",
                    "attributes": {
                        "artist": "The Beatles",
                        "album": "Abbey Road",
                        "year": "1969",
                        "condition": "Near Mint"
                    },
                    "image_url": "https://example.com/abbey-road-cover.jpg",
                    "images": [
                        {
                            "url": "https://example.com/abbey-road-cover.jpg",
                            "is_default": True,
                            "order": 0,
                            "alt_text": "Abbey Road album cover"
                        }
                    ],
                    "links": [
                        {
                            "url": "https://www.discogs.com/The-Beatles-Abbey-Road/release/123456",
                            "display_name": "Discogs Page",
                            "order": 0
                        },
                        {
                            "url": "https://en.wikipedia.org/wiki/Abbey_Road",
                            "display_name": "Wikipedia",
                            "order": 1
                        }
                    ]
                },
                {
                    "name": "Dark Side of the Moon",
                    "description": "Progressive rock masterpiece by Pink Floyd.",
                    "status": "WANTED",
                    "is_favorite": True,
                    "item_type": "vinyl_record",
                    "attributes": {
                        "artist": "Pink Floyd",
                        "album": "The Dark Side of the Moon",
                        "year": "1973",
                        "condition": "Mint"
                    },
                    "links": [
                        {
                            "url": "https://www.discogs.com/Pink-Floyd-The-Dark-Side-Of-The-Moon/master/10362",
                            "display_name": "Discogs"
                        }
                    ]
                }
            ]
        }
    ]
}