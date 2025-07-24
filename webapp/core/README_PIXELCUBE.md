# 🎮 PixelCube Image Generator

A Django library for generating pixelized isometric cube images with retro gaming aesthetics, similar to Minecraft blocks but with random colors and patterns.

## Features

- **T-shirt sizes**: xs (16×16), s (32×32), m (64×64), l (128×128), xl (256×256)
- **Multiple patterns**: solid, mixed, gradient, random
- **Gaming color palette**: 16-bit era inspired colors
- **Isometric 3D effect**: Proper cube shading and perspective
- **Django template integration**: Easy-to-use template tags
- **Direct image API**: Generate images via URL parameters
- **Base64 data URLs**: No file storage needed

## Quick Start

### 1. Template Usage

```html
{% load pixelcube %}

<!-- Basic usage -->
{% pixelcube size='m' %}
{% pixelcube 'l' color='#FF0000' %}
{% pixelcube size='xl' pattern='gradient' %}

<!-- With CSS classes -->
{% pixelcube size='m' css_class='rounded-lg shadow-md hover:scale-110' %}

<!-- Get just the data URL -->
<img src="{% pixelcube_url size='l' color='#00FF00' %}">
```

### 2. Python API

```python
from core.pixelcube import generate_pixelcube_image, pixelcube_to_base64

# Generate PIL Image
image = generate_pixelcube_image(size='l', color='#FF6B35', pattern='gradient')
image.save('my_cube.png')

# Generate base64 data URL
data_url = pixelcube_to_base64(size='m', pattern='mixed')
# Returns: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAE..."
```

### 3. Direct Image API

```
/core/pixelcube/?size=l&color=FF6B35&pattern=gradient
/core/pixelcube/?size=xl&pattern=mixed
/core/pixelcube/?color=00FF00&pattern=solid
```

## Parameters

### Size Options
- `'xs'` - 16×16 pixels
- `'s'` - 32×32 pixels  
- `'m'` - 64×64 pixels (default)
- `'l'` - 128×128 pixels
- `'xl'` - 256×256 pixels
- `(width, height)` - Custom tuple

### Pattern Types
- `'solid'` - Single color cube
- `'mixed'` - Each face has related but different colors
- `'gradient'` - Smooth color gradient across faces
- `'random'` - Randomly selected pattern

### Colors
- Any hex color (e.g., `'#FF0000'`, `'#4ECDC4'`)
- `None` for random color from gaming palette
- Gaming palette includes 40+ retro colors

## Color Palette

The library uses a carefully curated gaming/computer color palette inspired by the 16-bit era:

```python
# Bright primaries
'#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'

# Earth tones
'#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F4A460', '#D2691E'

# Vibrant variants
'#9932CC', '#32CD32', '#4169E1', '#FF4500', '#228B22'
# ... and many more
```

## Template Tag Reference

### `{% pixelcube %}`

```html
{% pixelcube [size] [color=color] [pattern=pattern] [css_class=class] [alt=text] [**kwargs] %}
```

**Parameters:**
- `size` - Size identifier or first positional argument
- `color` - Hex color string (optional)
- `pattern` - Pattern type (optional) 
- `css_class` - CSS classes to add (optional)
- `alt` - Alt text for accessibility (optional)
- `**kwargs` - Additional HTML attributes

**Examples:**
```html
{% pixelcube 'm' %}
{% pixelcube size='xl' pattern='gradient' css_class='my-cube' %}
{% pixelcube 'l' color='#FF0000' alt='Red Gaming Cube' title='Click me!' %}
```

### `{% pixelcube_url %}`

```html
{% pixelcube_url [size] [color=color] [pattern=pattern] %}
```

Returns just the base64 data URL string.

## Advanced Usage

### Custom Cube Generation

```python
from core.pixelcube import PixelCubeGenerator

# Create custom generator
generator = PixelCubeGenerator(width=200, height=150)

# Generate with specific parameters  
cube = generator.generate_cube(
    base_color='#4ECDC4',
    pattern_type='mixed'
)

# Or completely random
random_cube = generator.generate_random_cube()
```

### Integration Examples

**In a model's image_url property:**
```python
class Collection(models.Model):
    name = models.CharField(max_length=100)
    
    @property
    def placeholder_image_url(self):
        from core.pixelcube import pixelcube_to_base64
        return pixelcube_to_base64(size='l', pattern='gradient')
```

**As fallback images:**
```html
<img src="{{ item.image_url|default:'/core/pixelcube/?size=m&pattern=random' }}" 
     alt="{{ item.name }}">
```

**In CSS backgrounds:**
```html
<div style="background-image: url('{% pixelcube_url size='xl' %}')"></div>
```

## Showcase

Visit `/core/pixelcube/showcase/` for an interactive demonstration with:
- Live template tag examples
- Size comparisons
- Pattern variations  
- Color palette display
- Interactive parameter controls
- API usage examples

## Technical Details

### Dependencies
- **Pillow (PIL)** - Image generation and manipulation
- **Django** - Template system integration

### Performance
- Images generated in memory (no file I/O)
- Base64 encoding for immediate use
- Caching headers on API endpoints
- Efficient isometric calculations

### Customization
- Extend `PixelCubeGenerator` for custom patterns
- Modify `GAMING_PALETTE` for different color schemes
- Add new size mappings in `SIZE_MAPPINGS`

## File Structure

```
core/
├── pixelcube.py              # Main library
├── templatetags/
│   └── pixelcube.py         # Django template tags
├── views.py                 # Showcase and API views
├── urls.py                  # URL routing
└── templates/core/
    └── pixelcube_showcase.html  # Interactive demo
```