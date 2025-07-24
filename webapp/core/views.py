"""
Core app views for utility functions and showcases.
"""

from django.shortcuts import render
from django.http import HttpResponse
from .pixelcube import create_showcase, generate_pixelcube_image, SIZE_MAPPINGS
import io


def pixelcube_showcase(request):
    """Display a showcase of pixel cube images."""
    showcase_data = create_showcase()
    
    context = {
        'showcase_data': showcase_data,
        'sizes': SIZE_MAPPINGS,
        'patterns': ['solid', 'mixed', 'gradient', 'random'],
    }
    
    return render(request, 'core/pixelcube_showcase.html', context)


def pixelcube_image_view(request):
    """
    Generate and serve a pixel cube image directly.
    
    Query parameters:
    - size: xs, s, m, l, xl (default: m)
    - color: hex color without # (default: random)
    - pattern: solid, mixed, gradient, random (default: random)
    - format: PNG, JPEG, WEBP (default: PNG)
    - cubes: specific number of cubes (default: random 1-10)
    - min_cubes: minimum cubes if cubes not specified (default: 1)
    - max_cubes: maximum cubes if cubes not specified (default: 10)
    - background: transparent, palette, or hex color (default: transparent)
    """
    # Get parameters
    size = request.GET.get('size', 'm')
    color = request.GET.get('color')
    pattern = request.GET.get('pattern', 'random')
    img_format = request.GET.get('format', 'PNG').upper()
    
    # New parameters
    cube_count = request.GET.get('cubes')
    min_cubes = int(request.GET.get('min_cubes', 1))
    max_cubes = int(request.GET.get('max_cubes', 10))
    background = request.GET.get('background', 'transparent')
    
    # Add # to color if provided
    if color and not color.startswith('#'):
        color = f'#{color}'
    
    # Handle cube count
    if cube_count:
        try:
            cube_count = int(cube_count)
        except ValueError:
            cube_count = None
    
    # Handle background color
    if background and background != 'transparent' and background != 'palette':
        if not background.startswith('#'):
            background = f'#{background}'
    
    try:
        # Generate image
        image = generate_pixelcube_image(
            size=size, 
            color=color, 
            pattern=pattern, 
            format=img_format,
            cube_count=cube_count,
            min_cubes=min_cubes,
            max_cubes=max_cubes,
            background=background
        )
        
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=img_format)
        buffer.seek(0)
        
        # Set content type
        content_types = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg', 
            'WEBP': 'image/webp'
        }
        content_type = content_types.get(img_format, 'image/png')
        
        # Return image response
        response = HttpResponse(buffer.getvalue(), content_type=content_type)
        response['Cache-Control'] = 'public, max-age=1800'  # Cache for 30 minutes (less due to randomness)
        return response
        
    except Exception as e:
        # Return error response
        return HttpResponse(f'Error generating image: {str(e)}', status=400)
