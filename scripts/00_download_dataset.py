#!/usr/bin/env python3
"""
Download and extract dataset from a configurable URL.
"""

import os
import sys
import zipfile
from pathlib import Path
import click
import requests
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def download_file(url: str, destination: str) -> bool:
    """
    Download a file from URL with progress bar.
    
    Args:
        url: URL to download from
        destination: Local file path to save to
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Add headers to avoid 403 errors from Zenodo and other services
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, stream=True, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destination, 'wb') as f, tqdm(
            desc=os.path.basename(destination),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        return True
    except Exception as e:
        click.echo(f"Error downloading file: {e}", err=True)
        return False


def extract_zip(zip_path: str, extract_to: str) -> bool:
    """
    Extract a ZIP file.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        click.echo(f"Error extracting ZIP file: {e}", err=True)
        return False


def find_and_move_files(source_dir: Path, images_dir: Path, data_dir: Path):
    """
    Find and move image and metadata files to appropriate directories.
    
    Args:
        source_dir: Source directory to search
        images_dir: Destination for image files
        data_dir: Destination for metadata files
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp'}
    
    moved_images = 0
    moved_metadata = 0
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = Path(root) / file
            file_ext = file_path.suffix.lower()
            
            # Move image files
            if file_ext in image_extensions:
                dest_path = images_dir / file
                file_path.rename(dest_path)
                moved_images += 1
            
            # Move CSV files (metadata)
            elif file_ext == '.csv':
                dest_path = data_dir / file
                file_path.rename(dest_path)
                moved_metadata += 1
    
    click.echo(f"Moved {moved_images} image files")
    click.echo(f"Moved {moved_metadata} metadata files")


@click.command()
@click.option(
    '--url',
    default=lambda: os.getenv('DATASET_URL', 'https://zenodo.org/records/6473001/files/ArtDL.zip'),
    help='URL to download dataset from (default: from .env or fallback URL)'
)
@click.option(
    '--data-dir',
    type=click.Path(file_okay=False, dir_okay=True),
    default=lambda: os.getenv('DATA_DIR', 'data'),
    help='Directory to store data (default: from .env or "data")'
)
@click.option(
    '--force',
    is_flag=True,
    help='Force re-download even if data exists'
)
def download_dataset(url: str, data_dir: str, force: bool):
    """
    Download and extract dataset from a URL.
    
    The script will:
    1. Download the ZIP file from the specified URL
    2. Extract it to the data directory
    3. Move images to data/images/
    4. Move metadata files to data/
    5. Clean up temporary files
    """
    click.echo("=== Dataset Download Script ===")
    click.echo(f"URL: {url}")
    click.echo("")
    
    # Setup paths - handle Docker container working directory
    data_path = Path(data_dir)
    
    # If running in Docker and path is relative, make it absolute from root
    if not data_path.is_absolute():
        # Check if we're in /scripts directory (Docker container)
        if Path.cwd().name == 'scripts':
            data_path = Path('/') / data_dir
        else:
            data_path = data_path.resolve()
    
    images_path = data_path / 'images'
    
    # Create directories
    data_path.mkdir(exist_ok=True)
    images_path.mkdir(exist_ok=True)
    
    # Check if dataset already exists
    if not force and any(images_path.iterdir()):
        click.echo("✓ Dataset already exists in data/images/")
        click.echo("Skipping download.")
        return
    
    # Determine filename from URL
    filename = url.split('/')[-1]
    if not filename.endswith('.zip'):
        filename = 'dataset.zip'
    
    zip_path = data_path / filename
    
    # Check if ZIP already downloaded
    if zip_path.exists() and not force:
        click.echo(f"ZIP file already exists: {zip_path}")
        click.echo("Using existing ZIP file.")
    else:
        # Download the file
        click.echo(f"Downloading dataset from {url}...")
        if not download_file(url, str(zip_path)):
            click.echo("Download failed!", err=True)
            sys.exit(1)
        click.echo("\nDownload complete!")
    
    # Check if data is already extracted
    extracted_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name not in ['images', '__MACOSX']]
    
    if extracted_dirs and not force:
        click.echo(f"✓ Extracted data already exists: {[d.name for d in extracted_dirs]}")
        click.echo("Skipping extraction.")
    else:
        # Extract the ZIP file
        click.echo("\nExtracting dataset...")
        if not extract_zip(str(zip_path), str(data_path)):
            click.echo("Extraction failed!", err=True)
            sys.exit(1)
        click.echo("Extraction complete!")
    
    # Find extracted directory (refresh the list after extraction)
    extracted_dirs = [d for d in data_path.iterdir() if d.is_dir() and d.name not in ['images', '__MACOSX']]
    
    if extracted_dirs:
        click.echo("\nMoving files to appropriate directories...")
        for extracted_dir in extracted_dirs:
            click.echo(f"Processing directory: {extracted_dir.name}")
            find_and_move_files(extracted_dir, images_path, data_path)
            # Remove empty extracted directory
            try:
                extracted_dir.rmdir()
                click.echo(f"Removed empty directory: {extracted_dir.name}")
            except OSError:
                # Directory not empty, remove recursively
                import shutil
                shutil.rmtree(extracted_dir, ignore_errors=True)
                click.echo(f"Removed directory tree: {extracted_dir.name}")
    else:
        # Files might be directly in data_path, check for images and CSV files
        click.echo("\nNo subdirectories found, checking for files in data directory...")
        direct_files = [f for f in data_path.iterdir() if f.is_file() and f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.csv'}]
        if direct_files:
            click.echo(f"Found {len(direct_files)} files directly in data directory, organizing...")
            for file_path in direct_files:
                file_ext = file_path.suffix.lower()
                if file_ext in {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp'}:
                    dest_path = images_path / file_path.name
                    file_path.rename(dest_path)
                # CSV files are already in the correct location (data_path)
    
    # Clean up ZIP file
    click.echo("\nCleaning up...")
    zip_path.unlink()
    
    # Count images
    image_count = len(list(images_path.glob('*')))
    
    click.echo("\n=== Dataset extraction complete! ===")
    click.echo(f"Images directory: {images_path}")
    click.echo(f"Image count: {image_count}")
    
    # Check for metadata
    metadata_files = list(data_path.glob('*.csv'))
    if metadata_files:
        click.echo(f"Metadata files: {', '.join(f.name for f in metadata_files)}")


if __name__ == '__main__':
    download_dataset()
