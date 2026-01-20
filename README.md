# IIIFy Dataset

A complete setup for serving images via IIIF (International Image Interoperability Framework) using Cantaloupe Image Server and generating IIIF Presentation API 3.0 manifests.

## Project Structure

```
.
├── docker-compose.yml          # Docker Compose with orchestration profiles
├── cantaloupe.properties       # Cantaloupe server configuration
├── nginx.conf                  # Nginx configuration for manifest server
├── start.sh                    # Interactive startup script
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration
├── scripts/
│   ├── 00_download_dataset.py  # Download and extract dataset (Python)
│   ├── 00_download_dataset.sh  # Download script (Bash - legacy)
│   └── 10_generate_manifests.py # Generate IIIF manifests
├── data/
│   ├── images/                 # Image files (populated by download script)
│   └── metadata.csv            # Optional metadata file
├── out/
│   └── collections/            # Generated IIIF manifests
└── venv/                       # Python virtual environment
```

## Prerequisites

- Docker and Docker Compose
- Python 3.8 or higher
- pip (Python package manager)

## Quick Start

### One-Command Setup 

For first-time setup, run everything with a single command:

```bash
# 1. Copy environment configuration (if not exists)
cp .env.example .env

# 2. Start everything (downloads dataset, generates manifests, starts server)
docker compose --profile init up
```

This will automatically:
- Download the ArtDL dataset from Zenodo
- Extract images to `data/images/`
- Generate IIIF manifests in `out/collections/`
- Start the Cantaloupe IIIF server at `http://localhost:8182`
- Start the manifest server at `http://localhost:8080`

### Manual Setup (Alternative)

If you prefer more control over each step:

### 1. Clone or Initialize Repository

```bash
cd IIIFy-dataset
```

### 2. Configure Environment

Copy the example environment file and customize if needed:

```bash
cp .env.example .env
```

Edit [`.env`](.env) to configure:
- `DATASET_URL`: URL to download dataset from (default: ArtDL from Zenodo)
- `DATA_DIR`: Directory for data storage (default: `data`)
- `IMAGES_DIR`: Directory for images (default: `data/images`)
- `CANTALOUPE_BASE_URL`: Base URL for IIIF server (default: `http://localhost:8182`)
- `OUTPUT_DIR`: Directory for generated manifests (default: `out/manifests`)
- `IMAGE_EXTENSIONS`: Supported image formats (default: `jpg,jpeg,png,tif,tiff`)
- `METADATA_FILE`: Optional CSV file with metadata

### 3. Set Up Python Environment

The virtual environment is already created. To activate it:

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

Dependencies are already installed, but if needed:

```bash
pip install -r requirements.txt
```

### 4. Download Dataset

Download and extract a dataset using the Python script:

```bash
./venv/bin/python scripts/00_download_dataset.py
```

The script will use the URL from your `.env` file or the default ArtDL dataset.

#### Custom Dataset URL

To download from a different URL:

```bash
./venv/bin/python scripts/00_download_dataset.py --url https://example.com/dataset.zip
```

Or update the `DATASET_URL` in your [`.env`](.env) file.

#### Force Re-download

```bash
./venv/bin/python scripts/00_download_dataset.py --force
```

### 5. Start the System

You have two options for starting the system:

#### Option A: Full Orchestration (Recommended for First Run)

This will automatically download the dataset, generate manifests, and start Cantaloupe:

```bash
docker compose --profile init up
```

This runs:
1. Downloads dataset (if not already present)
2. Generates IIIF manifests
3. Starts Cantaloupe server

#### Option B: Standalone Cantaloupe (If Data Already Exists)

If you've already downloaded data and generated manifests, start only Cantaloupe:

```bash
docker compose --profile standalone up -d
```

Or run the scripts manually first:

```bash
./venv/bin/python scripts/00_download_dataset.py
./venv/bin/python scripts/10_generate_manifests.py
docker compose --profile standalone up -d
```

#### Managing the Services

The services will be available at:
- **Cantaloupe IIIF Image Server**: `http://localhost:8182`
- **Manifest Server**: `http://localhost:8080`

To check if it's running:

```bash
docker compose ps
```

To view logs:

```bash
docker compose --profile standalone logs -f cantaloupe
# or for init profile:
docker compose --profile init logs -f
```

To stop the server:

```bash
docker compose --profile standalone down
# or
docker compose --profile init down
```

## Usage

### Generate IIIF Manifests

Generate IIIF Presentation API 3.0 manifests for all images:

```bash
./venv/bin/python scripts/10_generate_manifests.py
```

The script will use configuration from your [`.env`](.env) file.

#### Command-Line Options

All options can be overridden via command-line arguments:

- `--images-dir DIRECTORY`: Directory containing images
- `--output-dir DIRECTORY`: Directory to save manifests
- `--base-url TEXT`: Base URL of Cantaloupe server
- `--metadata-file FILE`: Optional CSV file with metadata (must have "filename" column)
- `--extensions TEXT`: Comma-separated image extensions
- `--verbose`: Enable verbose output

#### Examples

Generate manifests with verbose output:

```bash
./venv/bin/python scripts/10_generate_manifests.py --verbose
```

Generate manifests with custom base URL:

```bash
./venv/bin/python scripts/10_generate_manifests.py --base-url http://example.com:8182
```

Generate manifests with metadata:

```bash
./venv/bin/python scripts/10_generate_manifests.py --metadata-file data/metadata.csv
```

### Access Images via IIIF

Once Cantaloupe is running, you can access images using IIIF Image API URLs:

```
http://localhost:8182/iiif/3/{filename}/info.json
http://localhost:8182/iiif/3/{filename}/full/max/0/default.jpg
```

Replace `{filename}` with the actual image filename (e.g., `image001.jpg`).

### View Manifests

Generated manifests can be viewed in IIIF-compatible viewers like:

- [Mirador](https://projectmirador.org/)
- [Universal Viewer](https://universalviewer.io/)
- [Clover IIIF](https://samvera-labs.github.io/clover-iiif/)

#### Serving Manifests

When using the Docker Compose setup with the `init` or `default` profile, manifests are automatically served via the included nginx server at `http://localhost:8080`.

Access manifests at: `http://localhost:8080/collections/{manifest_id}.json`

For example:
- Training set: `http://localhost:8080/collections/train.json`
- Test set: `http://localhost:8080/collections/test.json`
- Validation set: `http://localhost:8080/collections/val.json`
- Saint categories: `http://localhost:8080/collections/11H_JEROME.json`

You can browse available manifests at: `http://localhost:8080/collections/`

**Alternative: Manual HTTP Server**

If you're not using Docker Compose or prefer a different setup:

```bash
cd out/collections
python3 -m http.server 8080
```

Then access manifests at: `http://localhost:8080/{manifest_id}.json`

## Architecture

### Docker Compose Orchestration

The system uses Docker Compose profiles to provide flexible deployment options:

**Init Profile (`--profile init`):**
- Runs an initialization container that:
  1. Installs Python dependencies
  2. Downloads the dataset
  3. Generates IIIF manifests
- Starts two services after initialization completes:
  - Cantaloupe IIIF Image Server (port 8182)
  - Nginx Manifest Server (port 8080)
- Use for first-time setup or when you want full automation

**Default Profile (`--profile default`):**
- Starts both Cantaloupe and the manifest server
- Assumes data and manifests already exist
- Use for subsequent runs when data is ready

**Standalone Profile (`--profile standalone`):**
- Starts only the Cantaloupe IIIF server
- Assumes data and manifests already exist
- Use when you only need the image server

**Service Dependencies:**
```
init (Python container)
  ↓ (depends_on: service_completed_successfully)
cantaloupe (IIIF Image Server - port 8182)
manifest-server (Nginx - port 8080)
```

This ensures the servers only start after data is ready.

### Manifest Server

The manifest server is a lightweight nginx container that:
- Serves IIIF manifests from `out/collections/`
- Enables CORS for cross-origin requests (required by IIIF viewers)
- Provides directory listing for browsing manifests
- Serves JSON files with proper content-type headers

The server is configured via [`nginx.conf`](nginx.conf) and runs on port 8080.

## Configuration

### Environment Variables (.env)

The [`.env`](.env) file contains all configuration options. Copy from [`.env.example`](.env.example):

```bash
cp .env.example .env
```

Key configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATASET_URL` | URL to download dataset from | ArtDL Zenodo URL |
| `DATA_DIR` | Data storage directory | `data` |
| `IMAGES_DIR` | Images directory | `data/images` |
| `CANTALOUPE_BASE_URL` | IIIF server base URL | `http://localhost:8182` |
| `CANTALOUPE_PORT` | IIIF server port | `8182` |
| `MANIFEST_SERVER_PORT` | Manifest server port | `8080` |
| `OUTPUT_DIR` | Manifests output directory | `out/collections` |
| `IMAGE_EXTENSIONS` | Supported image formats | `jpg,jpeg,png,tif,tiff` |
| `METADATA_FILE` | Optional metadata CSV file | (empty) |

### Cantaloupe Configuration

Edit [`cantaloupe.properties`](cantaloupe.properties) to customize:

- Image processing settings
- Cache configuration
- Logging levels
- Overlay and redaction settings

After changing configuration, restart Cantaloupe:

```bash
docker compose restart
```

### Docker Compose Configuration

Edit [`docker-compose.yml`](docker-compose.yml) to:

- Change port mappings (Cantaloupe: 8182, Manifest Server: 8080)
- Adjust volume mounts
- Modify environment variables

### Nginx Configuration

Edit [`nginx.conf`](nginx.conf) to customize the manifest server:

- CORS headers
- Directory listing format
- Cache settings
- Content-type headers

After changing nginx configuration, restart the manifest server:

```bash
docker compose restart manifest-server
```

## Scripts

### 00_download_dataset.py

Python script to download and extract datasets from configurable URLs.

**Features:**
- Downloads ZIP files with progress bar
- Extracts and organizes images automatically
- Moves metadata files to appropriate locations
- Configurable via `.env` or command-line arguments
- Supports force re-download

**Usage:**
```bash
./venv/bin/python scripts/00_download_dataset.py [OPTIONS]
```

**Options:**
- `--url TEXT`: Dataset URL (from `.env` or default)
- `--data-dir DIRECTORY`: Data directory (from `.env` or `data`)
- `--force`: Force re-download

### 10_generate_manifests.py

Python script to generate IIIF Presentation API 3.0 manifests.

**Features:**
- Generates compliant IIIF v3 manifests
- Reads image dimensions automatically
- Supports metadata from CSV files
- Progress bar for batch processing
- Configurable via `.env` or command-line arguments

**Usage:**
```bash
./venv/bin/python scripts/10_generate_manifests.py [OPTIONS]
```

**Options:**
- `--images-dir DIRECTORY`: Images directory (from `.env` or `data/images`)
- `--output-dir DIRECTORY`: Output directory (from `.env` or `out/manifests`)
- `--base-url TEXT`: IIIF server URL (from `.env` or `http://localhost:8182`)
- `--metadata-file FILE`: Metadata CSV (from `.env`)
- `--extensions TEXT`: Image extensions (from `.env` or `jpg,jpeg,png,tif,tiff`)
- `--verbose`: Verbose output

## Troubleshooting

### Cantaloupe won't start

Check logs:

```bash
docker compose logs cantaloupe
```

Ensure port 8182 is not in use:

```bash
lsof -i :8182  # On macOS/Linux
netstat -ano | findstr :8182  # On Windows
```

### Images not appearing

1. Verify images are in `data/images/`:

```bash
ls -la data/images/
```

2. Check Cantaloupe can access the images:

```bash
docker compose exec cantaloupe ls -la /imageroot/
```

3. Test image access directly:

```bash
curl http://localhost:8182/iiif/3/{filename}/info.json
```

### Manifest generation fails

1. Ensure virtual environment is activated
2. Check image files are readable
3. Run with `--verbose` flag for detailed error messages
4. Verify `.env` configuration is correct

### Download script fails

1. Check internet connection
2. Verify the dataset URL is accessible
3. Ensure you have write permissions in the data directory
4. Check available disk space

## Dataset Information

This project uses the ArtDL dataset by default:

- **Dataset**: ArtDL - Art Dataset for Deep Learning
- **URL**: https://zenodo.org/record/6473001
- **License**: Check the dataset page for license information

You can use any other dataset by updating the `DATASET_URL` in your [`.env`](.env) file.

## IIIF Resources

- [IIIF Image API 3.0](https://iiif.io/api/image/3.0/)
- [IIIF Presentation API 3.0](https://iiif.io/api/presentation/3.0/)
- [Cantaloupe Documentation](https://cantaloupe-project.github.io/)
- [IIIF Awesome List](https://github.com/IIIF/awesome-iiif)

## Development

### Adding New Features

1. Update scripts in [`scripts/`](scripts/)
2. Add new configuration to [`.env.example`](.env.example)
3. Update [`requirements.txt`](requirements.txt) if needed
4. Document changes in this README

### Testing

Test the download script:

```bash
./venv/bin/python scripts/00_download_dataset.py --help
```

Test the manifest generation:

```bash
./venv/bin/python scripts/10_generate_manifests.py --help
```

## License

This project setup is provided as-is for educational and research purposes. Please respect the license of any datasets you process.
