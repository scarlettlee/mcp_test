# Geospatial Data Integration - Earth Search STAC API

A catalog-based implementation for accessing and visualizing satellite imagery and geospatial datasets through the Earth Search STAC API.

## Overview

This implementation provides tools for searching, downloading, and visualizing geospatial data from Earth Search (AWS Element84). The system uses JSON catalog files for dynamic collection discovery, eliminating hardcoded parameters and enabling flexible data access patterns.

## Features

- Dynamic collection discovery from STAC catalog JSON files
- Spatial and temporal search with cloud cover filtering
- Full-resolution asset download (satellite imagery, DEMs)
- Interactive map visualization with raster overlay
- Support for multiple collections (Sentinel-2, Landsat, NAIP, Copernicus DEM)

## Quick Start

### Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Demo

```bash
python mcp_m2.py
```

Select a demonstration mode:
1. Complete workflow for a single location
2. Batch processing for multiple locations
3. Interactive mode with user selection

## Architecture

### Components

**MCP Framework** (`mcp_framework.py`)
- Core server implementation
- Tool registration and execution
- Context management across calls

**Earth Search Tools** (`tools/earth_search_tools.py`)
- Collection listing
- Geospatial search
- Asset download
- Map visualization

**Catalog Loader** (`tools/catalog_loader.py`)
- JSON catalog parsing
- Collection metadata extraction
- Date range and asset discovery
- Collection validation

### Data Flow

```
JSON Catalog → Catalog Loader → Collection Info → Search → Download → Visualize
```

## Usage

### Load Catalog and Discover Collections

```python
from tools import load_catalog, list_collections, get_collection_info

catalog = load_catalog("earth-search")
collections = list_collections(catalog)
info = get_collection_info(catalog, "sentinel-2-l2a")
```

### Search for Geospatial Data

```python
from mcp_framework import MCPServer
from tools import earth_search_search_tool

server = MCPServer()
server.register_tool("search", earth_search_search_tool)

result = server.call_tool("search", {
    "collection": "sentinel-2-l2a",
    "bbox": [-122.5, 37.7, -122.3, 37.9],
    "date_start": "30 days ago",
    "date_end": "today",
    "max_cloud_cover": 15
})
```

### Download Full-Resolution Assets

```python
from tools import earth_search_download_tool

server.register_tool("download", earth_search_download_tool)

result = server.call_tool("download", {
    "item_index": 0,
    "asset_key": "visual",
    "output_dir": "downloads"
})
```

### Create Interactive Map

```python
from tools import earth_search_visualize_tool

server.register_tool("visualize", earth_search_visualize_tool)

result = server.call_tool("visualize", {
    "item_index": 0,
    "output_file": "map.html",
    "zoom": 11
})
```

## Available Collections

### Sentinel-2 Level-2A
- ID: `sentinel-2-l2a`
- Resolution: 10-60m
- Coverage: Global, 2015-present
- Assets: RGB visual, individual bands, cloud masks

### Landsat Collection 2 Level-2
- ID: `landsat-c2-l2`
- Resolution: 30m
- Coverage: Global, 1982-present
- Assets: Surface reflectance, thermal bands

### NAIP
- ID: `naip`
- Resolution: 0.6-1m
- Coverage: United States, 2010-2022
- Assets: High-resolution aerial imagery

### Copernicus DEM
- ID: `cop-dem-glo-30`, `cop-dem-glo-90`
- Resolution: 30m or 90m
- Coverage: Global elevation data

## Catalog System

### Catalog Structure

Catalogs are stored as JSON files in `cat_10_18/` directory:
```
stac-tags-earth-search.aws.element84.com.json
```

Each catalog contains:
- STAC API endpoint URL
- Collection metadata
- Temporal extents
- Available assets per collection
- Spatial coverage

### Catalog Functions

```python
load_catalog(name)                          # Load catalog from JSON
get_api_endpoint(catalog)                   # Extract API URL
list_collections(catalog)                   # List all collections
get_collection_info(catalog, collection_id) # Get detailed metadata
get_suggested_date_range(catalog, id)       # Get temporal extent
get_available_assets(catalog, id)           # List asset types
validate_collection(catalog, id)            # Check collection exists
```

## Technical Details

### Coordinate System

Bounding boxes use WGS84 (EPSG:4326):
```
[min_longitude, min_latitude, max_longitude, max_latitude]
```

Examples:
- San Francisco: `[-122.5, 37.7, -122.3, 37.9]`
- Beijing: `[116.2, 39.8, 116.5, 40.0]`

### Asset Types

Common assets available:
- `visual` - RGB composite (full resolution)
- `thumbnail` - Preview image (small)
- `red`, `green`, `blue`, `nir` - Individual bands
- `data` - Complete raster dataset

### Image Processing

The visualization pipeline:
1. Download GeoTIFF from cloud storage
2. Transform coordinates to WGS84 if needed
3. Downsample to max 2000px if necessary
4. Normalize pixel values to 0-255 range
5. Convert to RGB array
6. Embed as base64 PNG in HTML

### Output Structure

**Downloads** (`downloads/`)
- `{item_id}_{asset_key}.tif` - GeoTIFF raster
- `{item_id}_{asset_key}.jpg` - JPEG preview

**Maps** (HTML files)
- Interactive Folium map
- Satellite imagery overlay
- Bounding box visualization
- Metadata pop-ups

## Implementation Example

Complete workflow demonstrating all features:

```python
from mcp_framework import MCPServer
from tools import (
    earth_search_search_tool,
    earth_search_download_tool,
    earth_search_visualize_tool,
    load_catalog,
    get_available_assets
)

# Setup
server = MCPServer()
server.register_tool("search", earth_search_search_tool)
server.register_tool("download", earth_search_download_tool)
server.register_tool("visualize", earth_search_visualize_tool)

# Load catalog
catalog = load_catalog("earth-search")
assets = get_available_assets(catalog, "sentinel-2-l2a")

# Search
result = server.call_tool("search", {
    "collection": "sentinel-2-l2a",
    "bbox": [-122.5, 37.7, -122.3, 37.9],
    "date_start": "30 days ago",
    "date_end": "today",
    "max_cloud_cover": 15
})

# Download
result = server.call_tool("download", {
    "item_index": 0,
    "asset_key": "visual"
})

# Visualize
result = server.call_tool("visualize", {
    "item_index": 0,
    "output_file": "map.html"
})
```

## API Access

Earth Search provides public access without authentication. No API keys required.

Endpoint: `https://earth-search.aws.element84.com/v1`

## File Structure

```
mcp_test/
├── mcp_m2.py                     # Main demonstration script
├── mcp_framework.py              # Core MCP implementation
├── tools/
│   ├── earth_search_tools.py    # Earth Search STAC tools
│   ├── catalog_loader.py         # Catalog utilities
│   └── __init__.py               # Tool exports
├── cat_10_18/                    # STAC catalog JSON files
├── downloads/                    # Downloaded assets
└── *.html                        # Generated maps
```

