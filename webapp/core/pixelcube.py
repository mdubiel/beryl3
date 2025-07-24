"""
Pixel Cube Image Generator - Core Library

Generates pixelized isometric cube images with retro gaming aesthetics.
Similar to Minecraft blocks but with random colors and patterns.
"""

import io
import random
import math
from PIL import Image, ImageDraw
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import base64

# Gaming/Computer color palette (16-bit era inspired)
GAMING_PALETTE = [
    # Bright primaries
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
    # Darker variants
    '#CC0000', '#00CC00', '#0000CC', '#CCCC00', '#CC00CC', '#00CCCC',
    # Earth tones
    '#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F4A460', '#D2691E',
    # Purple/Pink variants
    '#800080', '#9932CC', '#BA55D3', '#DA70D6', '#FF69B4', '#FFB6C1',
    # Green variants
    '#228B22', '#32CD32', '#7CFC00', '#ADFF2F', '#9ACD32', '#6B8E23',
    # Blue variants
    '#4169E1', '#6495ED', '#87CEEB', '#87CEFA', '#00BFFF', '#1E90FF',
    # Orange/Red variants
    '#FF4500', '#FF6347', '#FA8072', '#E9967A', '#FFA07A', '#FF7F50',
    # Gray variants for contrast
    '#696969', '#808080', '#A9A9A9', '#C0C0C0', '#D3D3D3', '#DCDCDC'
]

# T-shirt size mappings
SIZE_MAPPINGS = {
    'xs': (16, 16),
    's': (32, 32),
    'm': (64, 64),
    'l': (128, 128),
    'xl': (256, 256)
}

class PixelCubeGenerator:
    """Generates pixelized isometric cube images."""
    
    def __init__(self, width=64, height=64, cube_count=1, min_cubes=1, max_cubes=10, background_color=None):
        self.width = width
        self.height = height
        self.min_cubes = min_cubes
        self.max_cubes = max_cubes
        self.cube_count = cube_count if cube_count else random.randint(min_cubes, max_cubes)
        self.background_color = background_color
        
        # Calculate cube size based on number of cubes and canvas size
        if self.cube_count == 1:
            self.base_cube_size = min(width, height) // 3  # Larger for single cube
        else:
            # Smaller cubes when multiple, with some overlap allowed
            self.base_cube_size = min(width, height) // (2 + int(self.cube_count ** 0.5))
        
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _darken_color(self, color, factor=0.7):
        """Darken a color by a given factor."""
        if isinstance(color, str):
            color = self._hex_to_rgb(color)
        return tuple(int(c * factor) for c in color)
    
    def _lighten_color(self, color, factor=1.3):
        """Lighten a color by a given factor."""
        if isinstance(color, str):
            color = self._hex_to_rgb(color)
        return tuple(min(255, int(c * factor)) for c in color)
    
    def _draw_isometric_face(self, draw, points, color, is_top=False, is_left=False):
        """Draw one face of the isometric cube."""
        if isinstance(color, str):
            color = self._hex_to_rgb(color)
            
        # Apply shading based on face position
        if is_top:
            # Top face is lightest
            face_color = self._lighten_color(color, 1.2)
        elif is_left:
            # Left face is medium
            face_color = color
        else:
            # Right face is darkest
            face_color = self._darken_color(color, 0.8)
        
        # Draw the face
        draw.polygon(points, fill=face_color, outline='#000000', width=1)
        
        # Add pixel texture
        self._add_pixel_texture(draw, points, face_color)
    
    def _add_pixel_texture(self, draw, points, base_color):
        """Add subtle pixel texture to a face."""
        # Calculate bounding box and ensure integers
        min_x = int(min(p[0] for p in points))
        max_x = int(max(p[0] for p in points))
        min_y = int(min(p[1] for p in points))
        max_y = int(max(p[1] for p in points))
        
        # Add small random pixels for texture
        pixel_size = max(1, self.base_cube_size // 16)
        for i in range(3):  # Add a few random pixels
            if random.random() < 0.3:  # 30% chance for each pixel
                # Ensure we have valid ranges for randint
                if max_x - pixel_size > min_x + pixel_size and max_y - pixel_size > min_y + pixel_size:
                    px = random.randint(min_x + pixel_size, max_x - pixel_size)
                    py = random.randint(min_y + pixel_size, max_y - pixel_size)
                    
                    # Slightly vary the color
                    varied_color = tuple(
                        max(0, min(255, c + random.randint(-20, 20))) 
                        for c in base_color
                    )
                    
                    draw.rectangle([px, py, px + pixel_size, py + pixel_size], 
                                 fill=varied_color)
    
    def _generate_cube_points(self, center_x, center_y, size, depth_offset=0):
        """Generate points for isometric cube faces with better 3D perspective."""
        
        # Enhanced isometric angles for more 3D appearance
        # Using 30-degree angles for better depth perception
        angle_x = 0.866  # cos(30°) for horizontal offset
        angle_y = 0.5    # sin(30°) for vertical offset
        
        # Calculate 3D projected points
        depth = size * 0.6 + depth_offset  # Depth factor for 3D effect
        
        # Top face points (more diamond-like with proper perspective)
        top_points = [
            (center_x, center_y - size // 2),                    # top
            (center_x + int(size * angle_x // 2), center_y - int(size * angle_y // 2)),  # top-right
            (center_x, center_y),                                # center/bottom
            (center_x - int(size * angle_x // 2), center_y - int(size * angle_y // 2)),  # top-left
        ]
        
        # Left face (with proper depth)
        left_points = [
            (center_x - int(size * angle_x // 2), center_y - int(size * angle_y // 2)),  # top-left
            (center_x, center_y),                                              # center
            (center_x, center_y + int(depth // 2)),                           # bottom-center
            (center_x - int(size * angle_x // 2), center_y - int(size * angle_y // 2) + int(depth // 2)), # bottom-left
        ]
        
        # Right face (with proper depth and shading angle)
        right_points = [
            (center_x, center_y),                                              # center
            (center_x + int(size * angle_x // 2), center_y - int(size * angle_y // 2)),  # top-right  
            (center_x + int(size * angle_x // 2), center_y - int(size * angle_y // 2) + int(depth // 2)), # bottom-right
            (center_x, center_y + int(depth // 2)),                           # bottom-center
        ]
        
        return top_points, left_points, right_points
    
    def _generate_cube_positions(self):
        """Generate random positions for multiple cubes, avoiding too much overlap."""
        positions = []
        max_attempts = 50
        
        for i in range(self.cube_count):
            attempts = 0
            while attempts < max_attempts:
                # Generate random position with margins
                margin = self.base_cube_size
                x = random.randint(margin, self.width - margin)
                y = random.randint(margin, self.height - margin)
                
                # Check for overlap with existing cubes
                too_close = False
                min_distance = self.base_cube_size * 0.7  # Allow some overlap for depth
                
                for existing_x, existing_y, _ in positions:
                    distance = ((x - existing_x) ** 2 + (y - existing_y) ** 2) ** 0.5
                    if distance < min_distance:
                        too_close = True
                        break
                
                if not too_close or attempts > max_attempts * 0.8:
                    # Add some size variation for visual interest
                    size_variation = random.uniform(0.8, 1.2)
                    cube_size = int(self.base_cube_size * size_variation)
                    positions.append((x, y, cube_size))
                    break
                    
                attempts += 1
        
        # Sort by Y coordinate for proper depth rendering (back to front)
        positions.sort(key=lambda pos: pos[1])
        
        return positions
    
    def generate_cube(self, base_color=None, pattern_type='solid'):
        """Generate a pixelized isometric cube image with multiple cubes support."""
        # Determine background
        if self.background_color == 'transparent' or self.background_color is None:
            img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        elif self.background_color == 'palette':
            # Random color from palette for background
            bg_color = self._hex_to_rgb(random.choice(GAMING_PALETTE))
            # Make it much darker for contrast
            bg_color = tuple(int(c * 0.3) for c in bg_color)
            img = Image.new('RGBA', (self.width, self.height), bg_color + (255,))
        else:
            # Specific background color
            if isinstance(self.background_color, str):
                bg_color = self._hex_to_rgb(self.background_color)
            else:
                bg_color = self.background_color
            img = Image.new('RGBA', (self.width, self.height), bg_color + (255,))
        
        draw = ImageDraw.Draw(img)
        
        # Generate cube positions
        positions = self._generate_cube_positions()
        
        # Draw all cubes
        for i, (center_x, center_y, cube_size) in enumerate(positions):
            # Each cube can have different colors/patterns
            if base_color is None:
                cube_base_color = random.choice(GAMING_PALETTE)
            else:
                if self.cube_count > 1:
                    # Vary colors slightly for multiple cubes
                    cube_base_color = self._vary_color(base_color, i)
                else:
                    cube_base_color = base_color
            
            # Get cube face points for this position and size
            top_points, left_points, right_points = self._generate_cube_points(
                center_x, center_y, cube_size, depth_offset=i * 2
            )
            
            # Apply pattern variations
            if pattern_type == 'mixed':
                colors = self._generate_related_colors(cube_base_color)
                top_color, left_color, right_color = colors
            elif pattern_type == 'gradient':
                top_color = self._lighten_color(cube_base_color, 1.4)
                left_color = cube_base_color
                right_color = self._darken_color(cube_base_color, 0.6)
            else:  # solid
                top_color = left_color = right_color = cube_base_color
            
            # Draw faces in correct order (back to front)
            self._draw_isometric_face(draw, left_points, left_color, is_left=True)
            self._draw_isometric_face(draw, right_points, right_color)
            self._draw_isometric_face(draw, top_points, top_color, is_top=True)
        
        return img
    
    def _vary_color(self, base_color, index):
        """Create color variations for multiple cubes."""
        base_rgb = self._hex_to_rgb(base_color) if isinstance(base_color, str) else base_color
        
        # Create variations based on index
        variations = [
            (1.0, 1.0, 1.0),    # Original
            (1.2, 0.8, 0.9),    # More red, less green/blue
            (0.8, 1.2, 0.9),    # More green, less red/blue
            (0.9, 0.8, 1.2),    # More blue, less red/green
            (1.1, 1.1, 0.8),    # More red/green, less blue
            (0.9, 1.1, 1.1),    # More green/blue, less red
            (1.1, 0.9, 1.1),    # More red/blue, less green
            (0.85, 0.85, 0.85), # Darker overall
            (1.15, 1.15, 1.15), # Lighter overall
            (1.0, 1.3, 0.7),    # High contrast variation
        ]
        
        variation = variations[index % len(variations)]
        
        new_color = tuple(
            max(0, min(255, int(c * v))) 
            for c, v in zip(base_rgb, variation)
        )
        
        return new_color
    
    def _generate_related_colors(self, base_color):
        """Generate related colors for mixed pattern."""
        base_rgb = self._hex_to_rgb(base_color) if isinstance(base_color, str) else base_color
        
        # Generate variations
        colors = []
        for i in range(3):
            # Shift hue slightly
            shift = random.randint(-30, 30)
            new_color = tuple(
                max(0, min(255, c + shift)) for c in base_rgb
            )
            colors.append(new_color)
        
        return colors
    
    def generate_random_cube(self, pattern_type=None):
        """Generate a completely random cube."""
        patterns = ['solid', 'mixed', 'gradient']
        if pattern_type is None:
            pattern_type = random.choice(patterns)
        
        return self.generate_cube(pattern_type=pattern_type)


def generate_pixelcube_image(size='m', color=None, pattern='random', format='PNG', 
                           cube_count=None, min_cubes=1, max_cubes=10, background='transparent'):
    """
    Generate a pixel cube image.
    
    Args:
        size: T-shirt size ('xs', 's', 'm', 'l', 'xl') or tuple (width, height)
        color: Hex color string or None for random
        pattern: 'solid', 'mixed', 'gradient', or 'random'
        format: Image format ('PNG', 'JPEG', 'WEBP')
        cube_count: Specific number of cubes, or None for random
        min_cubes: Minimum number of cubes (if cube_count is None)
        max_cubes: Maximum number of cubes (if cube_count is None)
        background: 'transparent', 'palette' (random from palette), or hex color
    
    Returns:
        PIL Image object
    """
    # Handle size
    if isinstance(size, str) and size in SIZE_MAPPINGS:
        width, height = SIZE_MAPPINGS[size]
    elif isinstance(size, (tuple, list)) and len(size) == 2:
        width, height = size
    else:
        width, height = SIZE_MAPPINGS['m']  # Default to medium
    
    # Handle cube count
    if cube_count is None:
        actual_cube_count = random.randint(min_cubes, max_cubes)
    else:
        actual_cube_count = max(1, min(20, cube_count))  # Limit to reasonable range
    
    # Handle background
    if background == 'transparent':
        bg_color = None
    elif background == 'palette':
        bg_color = 'palette'
    elif background and background.startswith('#'):
        bg_color = background
    else:
        bg_color = None  # Default to transparent
    
    # Create generator
    generator = PixelCubeGenerator(
        width, height, 
        cube_count=actual_cube_count,
        min_cubes=min_cubes,
        max_cubes=max_cubes,
        background_color=bg_color
    )
    
    # Handle pattern
    if pattern == 'random':
        pattern = random.choice(['solid', 'mixed', 'gradient'])
    
    # Generate cube
    if color:
        image = generator.generate_cube(color, pattern)
    else:
        image = generator.generate_random_cube(pattern)
    
    return image


def pixelcube_to_base64(size='m', color=None, pattern='random', format='PNG', 
                       cube_count=None, min_cubes=1, max_cubes=10, background='transparent'):
    """
    Generate pixel cube image and return as base64 data URL.
    
    Returns:
        String: data:image/png;base64,... URL
    """
    image = generate_pixelcube_image(size, color, pattern, format, 
                                   cube_count, min_cubes, max_cubes, background)
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    img_data = buffer.getvalue()
    img_b64 = base64.b64encode(img_data).decode()
    
    # Return data URL
    mime_type = f'image/{format.lower()}'
    return f'data:{mime_type};base64,{img_b64}'


# Django template integration
register = template.Library()

@register.simple_tag
def pixelcube(size='m', color=None, pattern='random', css_class='', alt='Pixel Cube', 
             cube_count=None, min_cubes=1, max_cubes=10, background='transparent', **kwargs):
    """
    Django template tag for generating pixel cube images.
    
    Usage:
        {% pixelcube size='l' color='#FF0000' pattern='gradient' css_class='my-cube' %}
        {% pixelcube 'm' cube_count=5 background='palette' %}
        {% pixelcube size='xl' pattern='mixed' min_cubes=3 max_cubes=7 %}
    """
    # Generate image data URL
    data_url = pixelcube_to_base64(size, color, pattern, 'PNG', 
                                  cube_count, min_cubes, max_cubes, background)
    
    # Build HTML attributes
    attributes = []
    if css_class:
        attributes.append(f'class="{css_class}"')
    if alt:
        attributes.append(f'alt="{alt}"')
    
    # Add any additional attributes
    for key, value in kwargs.items():
        # Convert underscores to hyphens for HTML attributes
        attr_name = key.replace('_', '-')
        attributes.append(f'{attr_name}="{value}"')
    
    attrs_str = ' '.join(attributes)
    
    # Return HTML img tag
    return mark_safe(f'<img src="{data_url}" {attrs_str}>')


@register.simple_tag
def pixelcube_url(size='m', color=None, pattern='random', cube_count=None, 
                 min_cubes=1, max_cubes=10, background='transparent'):
    """
    Django template tag that returns just the data URL.
    
    Usage:
        <img src="{% pixelcube_url size='l' color='#00FF00' cube_count=3 %}">
    """
    return pixelcube_to_base64(size, color, pattern, 'PNG', 
                              cube_count, min_cubes, max_cubes, background)


# Showcase function for testing
def create_showcase():
    """Create a showcase of different pixel cubes."""
    showcase_data = []
    
    # Different sizes
    for size_name, (w, h) in SIZE_MAPPINGS.items():
        image = generate_pixelcube_image(size_name)
        data_url = pixelcube_to_base64(size_name)
        showcase_data.append({
            'title': f'Size: {size_name.upper()} ({w}x{h})',
            'data_url': data_url,
            'size': size_name
        })
    
    # Different patterns
    patterns = ['solid', 'mixed', 'gradient']
    for pattern in patterns:
        image = generate_pixelcube_image('l', pattern=pattern, color='#FF6B35')
        data_url = pixelcube_to_base64('l', pattern=pattern, color='#FF6B35')
        showcase_data.append({
            'title': f'Pattern: {pattern.title()}',
            'data_url': data_url,
            'pattern': pattern
        })
    
    # Random colors
    for i in range(6):
        color = random.choice(GAMING_PALETTE)
        image = generate_pixelcube_image('l', color=color)
        data_url = pixelcube_to_base64('l', color=color)
        showcase_data.append({
            'title': f'Color: {color}',
            'data_url': data_url,
            'color': color
        })
    
    return showcase_data