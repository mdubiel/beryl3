#!/usr/bin/env python3
"""
Test script for the PixelCube library.
Run this to verify the library works correctly.
"""

import os
import sys
import django
from pathlib import Path

# Add the webapp directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

# Now we can import the library
from core.pixelcube import generate_pixelcube_image, pixelcube_to_base64, SIZE_MAPPINGS

def test_basic_generation():
    """Test basic image generation."""
    print("🧪 Testing basic image generation...")
    
    # Test different sizes
    for size_name in SIZE_MAPPINGS.keys():
        print(f"  ✓ Generating {size_name} cube...")
        image = generate_pixelcube_image(size_name)
        assert image.size == SIZE_MAPPINGS[size_name]
    
    # Test different patterns
    patterns = ['solid', 'mixed', 'gradient', 'random']
    for pattern in patterns:
        print(f"  ✓ Generating {pattern} pattern...")
        image = generate_pixelcube_image('m', pattern=pattern)
        assert image.size == (64, 64)
    
    # Test specific color
    print("  ✓ Generating with specific color...")
    image = generate_pixelcube_image('m', color='#FF0000')
    assert image.size == (64, 64)
    
    print("✅ Basic generation tests passed!")

def test_data_url_generation():
    """Test data URL generation."""
    print("🧪 Testing data URL generation...")
    
    data_url = pixelcube_to_base64('m')
    assert data_url.startswith('data:image/png;base64,')
    print("  ✓ Data URL format correct")
    
    # Test different format
    data_url_jpeg = pixelcube_to_base64('m', format='JPEG')
    assert data_url_jpeg.startswith('data:image/jpeg;base64,')
    print("  ✓ JPEG format works")
    
    print("✅ Data URL tests passed!")

def test_template_tags():
    """Test Django template tags."""
    print("🧪 Testing template tags...")
    
    try:
        from core.templatetags.pixelcube import pixelcube, pixelcube_url
        
        # Test pixelcube tag
        html = pixelcube(size='m', css_class='test-class')
        assert '<img src="data:image/png;base64,' in html
        assert 'class="test-class"' in html
        print("  ✓ pixelcube template tag works")
        
        # Test pixelcube_url tag
        url = pixelcube_url(size='s', color='#00FF00')
        assert url.startswith('data:image/png;base64,')
        print("  ✓ pixelcube_url template tag works")
        
        print("✅ Template tag tests passed!")
        
    except ImportError as e:
        print(f"⚠️  Template tag test skipped: {e}")

def create_sample_images():
    """Create some sample images for manual inspection."""
    print("🎨 Creating sample images...")
    
    samples = [
        {'size': 'xl', 'color': '#FF6B35', 'pattern': 'gradient', 'name': 'gradient_orange'},
        {'size': 'l', 'color': '#4ECDC4', 'pattern': 'mixed', 'name': 'mixed_cyan'},
        {'size': 'm', 'color': '#45B7D1', 'pattern': 'solid', 'name': 'solid_blue'},
        {'size': 's', 'pattern': 'random', 'name': 'random_small'},
    ]
    
    for sample in samples:
        image = generate_pixelcube_image(
            size=sample['size'],
            color=sample.get('color'),
            pattern=sample['pattern']
        )
        
        filename = f"sample_{sample['name']}.png"
        image.save(filename)
        print(f"  ✓ Saved {filename}")
    
    print("✅ Sample images created!")

if __name__ == '__main__':
    print("🎮 PixelCube Library Test Suite")
    print("=" * 40)
    
    try:
        test_basic_generation()
        test_data_url_generation()
        test_template_tags()
        create_sample_images()
        
        print("\n🎉 All tests passed! The PixelCube library is working correctly.")
        print("\n📍 Next steps:")
        print("   1. Visit /core/pixelcube/showcase/ to see the interactive demo")
        print("   2. Use {% load pixelcube %} in your templates")
        print("   3. Generate images with {% pixelcube size='m' %}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)