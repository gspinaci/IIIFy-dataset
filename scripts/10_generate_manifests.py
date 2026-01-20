#!/usr/bin/env python3
"""
Generate IIIF Presentation API 3.0 manifests with multiple images as canvases.
"""

import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import click
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Saint categories from the ArtDL CSV headers
SAINT_CATEGORIES = [
    "11F(MARY)",
    "11H(ANTONY ABBOT)",
    "11H(ANTONY OF PADUA)",
    "11H(AUGUSTINE)",
    "11H(DOMINIC)",
    "11H(FRANCIS)",
    "11H(JEROME)",
    "11H(JOHN THE BAPTIST)",
    "11H(JOHN)",
    "11H(JOSEPH)",
    "11H(PAUL)",
    "11H(PETER)",
    "11H(SEBASTIAN)",
    "11H(STEPHEN)",
    "11HH(BARBARA)",
    "11HH(CATHERINE)",
    "11HH(MARY MAGDALENE)"
]


def get_image_dimensions(image_path: str) -> tuple:
    """Get image width and height."""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        click.echo(f"Warning: Could not read dimensions for {image_path}: {e}", err=True)
        return (1000, 1000)  # Default dimensions


def find_image_file(item_id: str, images_dir: str) -> Optional[str]:
    """Find the actual image file for an item ID."""
    images_path = Path(images_dir)
    
    # Common image extensions
    extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.JPG', '.JPEG', '.PNG', '.TIF', '.TIFF']
    
    for ext in extensions:
        image_file = images_path / f"{item_id}{ext}"
        if image_file.exists():
            return str(image_file)
    
    return None


def create_canvas(item_id: str, image_filename: str, base_url: str, width: int, height: int, canvas_index: int, manifest_id: str) -> dict:
    """
    Create a IIIF Canvas for an image.
    
    Args:
        item_id: Image identifier
        image_filename: Full filename with extension
        base_url: Base URL of the IIIF server
        width: Image width in pixels
        height: Image height in pixels
        canvas_index: Index of this canvas in the manifest
        manifest_id: ID of the parent manifest
    
    Returns:
        Canvas dictionary
    """
    # IIIF Image API URL
    image_service_url = f"{base_url}/iiif/3/{image_filename}"
    
    canvas = {
        "id": f"{base_url}/collections/{manifest_id}/canvas/{canvas_index}",
        "type": "Canvas",
        "label": {
            "en": [item_id]
        },
        "height": height,
        "width": width,
        "items": [
            {
                "id": f"{base_url}/collections/{manifest_id}/page/{canvas_index}",
                "type": "AnnotationPage",
                "items": [
                    {
                        "id": f"{base_url}/collections/{manifest_id}/annotation/{canvas_index}",
                        "type": "Annotation",
                        "motivation": "painting",
                        "body": {
                            "id": f"{image_service_url}/full/max/0/default.jpg",
                            "type": "Image",
                            "format": "image/jpeg",
                            "height": height,
                            "width": width,
                            "service": [
                                {
                                    "id": image_service_url,
                                    "type": "ImageService3",
                                    "profile": "level2"
                                }
                            ]
                        },
                        "target": f"{base_url}/collections/{manifest_id}/canvas/{canvas_index}"
                    }
                ]
            }
        ]
    }
    
    return canvas


def create_multi_image_manifest(
    manifest_id: str,
    label: str,
    description: str,
    image_ids: List[str],
    images_dir: str,
    base_url: str,
    output_path: str,
    verbose: bool = False
) -> dict:
    """
    Create a IIIF Presentation API 3.0 manifest with multiple images as canvases.
    
    Args:
        manifest_id: Identifier for the manifest
        label: Human-readable label
        description: Description of the manifest
        image_ids: List of image IDs to include
        images_dir: Directory containing the images
        base_url: Base URL of the server
        output_path: Path to save the manifest
        verbose: Enable verbose output
    
    Returns:
        The manifest dictionary
    """
    manifest = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"{base_url}/collections/{manifest_id}.json",
        "type": "Manifest",
        "label": {
            "en": [label]
        },
        "summary": {
            "en": [description]
        },
        "items": []
    }
    
    # Add canvases for each image
    canvas_index = 1
    skipped = 0
    
    for item_id in image_ids:
        # Find the image file
        image_file = find_image_file(item_id, images_dir)
        
        if not image_file:
            if verbose:
                click.echo(f"  ⚠ Image file not found for {item_id}")
            skipped += 1
            continue
        
        # Get image dimensions
        width, height = get_image_dimensions(image_file)
        
        # Get filename with extension
        image_filename = Path(image_file).name
        
        # Create canvas
        canvas = create_canvas(
            item_id=item_id,
            image_filename=image_filename,
            base_url=base_url,
            width=width,
            height=height,
            canvas_index=canvas_index,
            manifest_id=manifest_id
        )
        
        manifest["items"].append(canvas)
        canvas_index += 1
    
    if verbose and skipped > 0:
        click.echo(f"  ⚠ Skipped {skipped} images (files not found)")
    
    # Save manifest to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest


def load_csv_data(csv_path: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], List[str]]:
    """
    Load and parse the ArtDL CSV file.
    
    Returns:
        Tuple of (set_data, saint_data, all_items) where:
        - set_data: Dict mapping set name to list of image IDs
        - saint_data: Dict mapping saint category to list of image IDs
        - all_items: List of all item IDs
    """
    set_data = {
        'train': [],
        'test': [],
        'val': []
    }
    
    saint_data = {saint: [] for saint in SAINT_CATEGORIES}
    all_items = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            item_id = row['item']
            set_name = row['set']
            all_items.append(item_id)
            
            # Add to set collection
            if set_name in set_data:
                set_data[set_name].append(item_id)
            
            # Add to saint collections (where value is 1)
            for saint in SAINT_CATEGORIES:
                if row.get(saint, '0') == '1':
                    saint_data[saint].append(item_id)
    
    return set_data, saint_data, all_items


def sanitize_filename(name: str) -> str:
    """Convert a saint category name to a valid filename."""
    return name.replace('(', '_').replace(')', '').replace(' ', '_')


@click.command()
@click.option(
    '--csv-file',
    type=click.Path(file_okay=True, dir_okay=False),
    default='data/ArtDL.csv',
    help='Path to the ArtDL.csv file (default: "data/ArtDL.csv")'
)
@click.option(
    '--images-dir',
    type=click.Path(file_okay=False, dir_okay=True),
    default=lambda: os.getenv('IMAGES_DIR', 'data/images'),
    help='Directory containing images (default: from .env or "data/images")'
)
@click.option(
    '--output-dir',
    type=click.Path(file_okay=False, dir_okay=True),
    default='out/collections',
    help='Directory to save manifests (default: "out/collections")'
)
@click.option(
    '--base-url',
    default=lambda: os.getenv('CANTALOUPE_BASE_URL', 'http://localhost:8182'),
    help='Base URL of the IIIF server (default: from .env or "http://localhost:8182")'
)
@click.option(
    '--sample-size',
    type=int,
    default=10,
    help='Generate a sample manifest with N images (default: 10)'
)
@click.option(
    '--generate-splits',
    is_flag=True,
    help='Generate dataset split manifests (train, test, val)'
)
@click.option(
    '--generate-saints',
    is_flag=True,
    help='Generate saint category manifests'
)
@click.option(
    '--generate-all',
    is_flag=True,
    help='Generate all manifests (splits, saints, and sample)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--force',
    is_flag=True,
    help='Force regeneration even if manifests already exist'
)
def generate_manifests(
    csv_file: str,
    images_dir: str,
    output_dir: str,
    base_url: str,
    sample_size: Optional[int],
    generate_splits: bool,
    generate_saints: bool,
    generate_all: bool,
    verbose: bool,
    force: bool
):
    """
    Generate IIIF Presentation API 3.0 manifests with multiple images.
    
    By default, only generates a sample manifest with 10 images.
    
    Use flags to generate additional manifests:
    - --generate-splits: Generate train.json, test.json, val.json
    - --generate-saints: Generate saint category manifests (e.g., 11H_JEROME.json)
    - --generate-all: Generate all manifests
    - --sample-size N: Change sample size (default: 10)
    
    The script will skip generation if manifests already exist unless --force is used.
    """
    # If generate-all is set, enable all generation types
    if generate_all:
        generate_splits = True
        generate_saints = True
    click.echo("=" * 60)
    click.echo("Generating IIIF Manifests")
    click.echo("=" * 60)
    
    # Resolve paths - handle Docker container working directory
    csv_path = Path(csv_file)
    if not csv_path.is_absolute():
        if Path.cwd().name == 'scripts':
            csv_path = Path('/') / csv_file
        else:
            csv_path = csv_path.resolve()
    
    images_path = Path(images_dir)
    if not images_path.is_absolute():
        if Path.cwd().name == 'scripts':
            images_path = Path('/') / images_dir
        else:
            images_path = images_path.resolve()
    
    output_path_resolved = Path(output_dir)
    if not output_path_resolved.is_absolute():
        if Path.cwd().name == 'scripts':
            output_path_resolved = Path('/') / output_dir
        else:
            output_path_resolved = output_path_resolved.resolve()
    
    # Update variables with resolved paths
    csv_file = str(csv_path)
    images_dir = str(images_path)
    output_dir = str(output_path_resolved)
    
    click.echo(f"DEBUG: CSV file path: {csv_file}")
    click.echo(f"DEBUG: Images directory: {images_dir}")
    click.echo(f"DEBUG: Output directory: {output_dir}")
    click.echo("")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        click.echo(f"✗ Error: CSV file not found: {csv_file}", err=True)
        click.echo("")
        click.echo("Please ensure the ArtDL.csv file exists.")
        click.echo("You may need to download the dataset first.")
        return
    
    # Check if images directory exists
    if not os.path.exists(images_dir):
        click.echo(f"✗ Error: Images directory not found: {images_dir}", err=True)
        click.echo("")
        click.echo("Please ensure the images directory exists.")
        click.echo("You may need to download the dataset first.")
        return
    
    # Check if images directory has any images
    images_path = Path(images_dir)
    image_extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']
    image_files = [f for f in images_path.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        click.echo(f"✗ Error: No image files found in {images_dir}", err=True)
        click.echo("")
        click.echo("Please ensure the images directory contains image files.")
        click.echo("You may need to download the dataset first.")
        return
    
    click.echo(f"✓ CSV file: {csv_file}")
    click.echo(f"✓ Images directory: {images_dir} ({len(image_files)} images found)")
    
    # Check if output directory exists and has manifests
    output_path = Path(output_dir)
    if output_path.exists() and not force:
        # Check if any manifest files exist
        manifest_files = list(output_path.glob('*.json'))
        if manifest_files:
            click.echo("")
            click.echo(f"⚠ Manifests already exist in {output_dir}")
            click.echo(f"  Found {len(manifest_files)} existing manifest files.")
            click.echo("")
            click.echo("  Use --force to regenerate manifests.")
            click.echo("=" * 60)
            return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    click.echo(f"✓ Output directory: {output_dir}")
    click.echo(f"✓ Base URL: {base_url}")
    if sample_size:
        click.echo(f"✓ Sample size: {sample_size} images")
    click.echo("")
    
    # Load CSV data
    click.echo("Loading data from CSV...")
    set_data, saint_data, all_items = load_csv_data(csv_file)
    click.echo(f"Found {len(all_items)} total images in CSV")
    
    manifests_generated = 0
    
    # Generate set manifests (train, test, val) if requested
    if generate_splits:
        click.echo("")
        click.echo("Creating dataset split manifests...")
        set_descriptions = {
            'train': 'Training set images from the ArtDL dataset',
            'test': 'Test set images from the ArtDL dataset',
            'val': 'Validation set images from the ArtDL dataset'
        }
        
        for set_name, image_ids in set_data.items():
            if not image_ids:
                click.echo(f"  ⚠ Skipping {set_name}.json (no images)", err=True)
                continue
            
            click.echo(f"  Creating {set_name}.json with {len(image_ids)} images...")
            output_path = os.path.join(output_dir, f"{set_name}.json")
            create_multi_image_manifest(
                manifest_id=set_name,
                label=f"{set_name.capitalize()} Set",
                description=set_descriptions[set_name],
                image_ids=image_ids,
                images_dir=images_dir,
                base_url=base_url,
                output_path=output_path,
                verbose=verbose
            )
            
            click.echo(f"  ✓ {set_name}.json created")
            manifests_generated += 1
    
    # Generate saint category manifests if requested
    saint_count = 0
    if generate_saints:
        click.echo("")
        click.echo("Creating saint category manifests...")
        
        for saint in SAINT_CATEGORIES:
            image_ids = saint_data[saint]
            
            if not image_ids:
                if verbose:
                    click.echo(f"  ⚠ Skipping {saint} (no images)")
                continue
            
            # Create filename from saint category
            filename = sanitize_filename(saint) + '.json'
            
            click.echo(f"  Creating {filename} with {len(image_ids)} images...")
            output_path = os.path.join(output_dir, filename)
            
            create_multi_image_manifest(
                manifest_id=sanitize_filename(saint),
                label=saint,
                description=f"Images depicting {saint} from the ArtDL dataset",
                image_ids=image_ids,
                images_dir=images_dir,
                base_url=base_url,
                output_path=output_path,
                verbose=verbose
            )
            
            saint_count += 1
            click.echo(f"  ✓ {filename} created")
        
        manifests_generated += saint_count
    
    # Generate sample manifest (always generated by default)
    if sample_size and sample_size > 0:
        sample_path = os.path.join(output_dir, "sample.json")
        
        # Check if sample already exists
        if Path(sample_path).exists() and not force:
            click.echo("")
            click.echo(f"✓ Sample manifest already exists: sample.json")
            click.echo("  (Use --force to regenerate)")
        else:
            click.echo("")
            click.echo(f"Creating sample manifest with {sample_size} images...")
            
            sample_items = all_items[:sample_size]
            
            create_multi_image_manifest(
                manifest_id="sample",
                label=f"Sample Collection ({sample_size} images)",
                description=f"Sample collection of {sample_size} images from the ArtDL dataset",
                image_ids=sample_items,
                images_dir=images_dir,
                base_url=base_url,
                output_path=sample_path,
                verbose=verbose
            )
            
            click.echo(f"  ✓ sample.json created")
            manifests_generated += 1
    
    # Summary
    click.echo("")
    click.echo("=" * 60)
    click.echo("Manifest generation complete!")
    if generate_splits:
        click.echo(f"  Dataset splits: 3 manifests (train, test, val)")
    if generate_saints:
        click.echo(f"  Saint categories: {saint_count} manifests")
    if sample_size:
        click.echo(f"  Sample manifest: 1 manifest ({sample_size} images)")
    click.echo(f"  Total manifests generated: {manifests_generated}")
    click.echo("=" * 60)
    
    if not generate_splits and not generate_saints:
        click.echo("")
        click.echo("💡 Tip: Use --generate-splits or --generate-saints to create more manifests")
        click.echo("   Or use --generate-all to create all available manifests")


if __name__ == '__main__':
    generate_manifests()
