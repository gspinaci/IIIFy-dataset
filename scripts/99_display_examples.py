#!/usr/bin/env python3
"""
Display example URLs after initialization is complete.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_first_image():
    """Get the first image filename from the images directory."""
    images_dir = os.getenv('IMAGES_DIR', 'data/images')
    images_path = Path(images_dir)
    
    # Handle Docker container working directory
    if not images_path.is_absolute() and Path.cwd().name == 'scripts':
        images_path = Path('/') / images_dir
    
    if not images_path.exists():
        return None
    
    # Look for first image file
    image_extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']
    for ext in image_extensions:
        for image_file in images_path.glob(f'*{ext}'):
            return image_file.name
        for image_file in images_path.glob(f'*{ext.upper()}'):
            return image_file.name
    
    return None

def get_first_manifest():
    """Get the first manifest from the collections directory."""
    output_dir = os.getenv('OUTPUT_DIR', 'out/collections')
    output_path = Path(output_dir)
    
    # Handle Docker container working directory
    if not output_path.is_absolute() and Path.cwd().name == 'scripts':
        output_path = Path('/') / output_dir
    
    if not output_path.exists():
        return None
    
    # Look for train.json first, then any .json file
    train_manifest = output_path / 'train.json'
    if train_manifest.exists():
        return 'train.json'
    
    for manifest_file in output_path.glob('*.json'):
        return manifest_file.name
    
    return None

def main():
    base_url = os.getenv('CANTALOUPE_BASE_URL', 'http://localhost:8182')
    manifest_port = os.getenv('MANIFEST_SERVER_PORT', '8080')
    
    # Extract host from base_url for manifest server
    manifest_base = base_url.rsplit(':', 1)[0] + f':{manifest_port}'
    
    print("=" * 70)
    print("🎉 IIIF Setup Complete!")
    print("=" * 70)
    print()
    print("📡 Services Running:")
    print(f"   • Cantaloupe IIIF Image Server: {base_url}")
    print(f"   • Manifest Server: {manifest_base}")
    print()
    
    # Get example image
    first_image = get_first_image()
    if first_image:
        print("🖼️  IIIF Image API Examples:")
        print(f"   • Image Info: {base_url}/iiif/3/{first_image}/info.json")
        print(f"   • Full Image: {base_url}/iiif/3/{first_image}/full/max/0/default.jpg")
        print(f"   • Thumbnail:  {base_url}/iiif/3/{first_image}/full/!200,200/0/default.jpg")
        print()
    
    # Get example manifest
    first_manifest = get_first_manifest()
    if first_manifest:
        manifest_id = first_manifest.replace('.json', '')
        print("📋 IIIF Presentation API Examples:")
        print(f"   • Manifest: {manifest_base}/collections/{first_manifest}")
        print()
        print("🔍 View in IIIF Viewers:")
        manifest_url = f"{manifest_base}/collections/{first_manifest}"
        print(f"   • Mirador: https://projectmirador.org/embed/?iiif-content={manifest_url}")
        print(f"   • Universal Viewer: https://universalviewer.io/uv.html?manifest={manifest_url}")
        print()
    
    print("📂 Browse All Manifests:")
    print(f"   {manifest_base}/collections/")
    print()
    print("🎨 Interactive Viewer:")
    print(f"   Open in browser: {manifest_base}")
    print(f"   (Mirador viewer with manifest selector)")
    print()
    print("=" * 70)
    print("✨ Ready to explore your IIIF content!")
    print("=" * 70)

if __name__ == '__main__':
    main()
