# BAFU STAC Tools - Swiss Environmental Data

MCP tools for accessing and visualizing geospatial data from the Swiss Federal Office for the Environment (BAFU).

## Overview

These tools provide access to Switzerland's comprehensive environmental datasets including:
- Flood hazard and overland flow maps
- Biodiversity and protected areas
- Forest fire risk assessments
- Soil quality and contamination
- Climate and seismic hazards

## Installation

1. Install required packages:
```bash
pip install requests folium
```

2. Place `bafu_stac_tools.py` in your project directory

3. Import in your code:
```python
from bafu_stac_tools import BAFU_TOOLS
```

## Tools Available

### 1. bafu_list_collections
List and search available BAFU data collections.

**Parameters:**
- `limit` (int): Maximum collections to display (default: 10)
- `search_term` (str): Filter by keyword

**Example:**
```python
server.call_tool("bafu_list_collections", {
    "search_term": "flood",
    "limit": 5
})
```

### 2. bafu_get_collection_info
Get detailed information about a specific collection.

**Parameters:**
- `collection_id` (str): BAFU collection ID

**Example:**
```python
server.call_tool("bafu_get_collection_info", {
    "collection_id": "ch.bafu.gefaehrdungskarte-oberflaechenabfluss"
})
```

### 3. bafu_search_collection
Search for items within a collection.

**Parameters:**
- `collection_id` (str): BAFU collection ID
- `bbox` (list): Optional bounding box [west, south, east, north]
- `limit` (int): Maximum items to return

**Example:**
```python
server.call_tool("bafu_search_collection", {
    "collection_id": "ch.bafu.bundesinventare-auen",
    "limit": 5
})
```

### 4. bafu_download_asset
Download data files from BAFU.

**Parameters:**
- `item_index` (int): Index from search results
- `asset_key` (str): Asset type to download
- `output_dir` (str): Download directory

**Example:**
```python
server.call_tool("bafu_download_asset", {
    "item_index": 0,
    "asset_key": "data",
    "output_dir": "downloads/bafu"
})
```

### 5. bafu_visualize_map
Create interactive map visualizations.

**Parameters:**
- `item_index` (int): Index from search results
- `output_file` (str): HTML output file
- `zoom` (int): Initial zoom level

**Example:**
```python
server.call_tool("bafu_visualize_map", {
    "item_index": 0,
    "output_file": "flood_map.html",
    "zoom": 10
})
```

## ESG Risk Applications

### Environmental Risks
- **Flood Risk**: Overland flow maps for infrastructure planning
- **Biodiversity**: Protected areas and habitat conservation
- **Climate Change**: Forest fire risk and climate data
- **Pollution**: Soil contamination and quality assessments

### Governance
- Federal inventories and regulatory compliance data
- Environmental monitoring and reporting

## Data Collections

Key collections include:
- `ch.bafu.gefaehrdungskarte-oberflaechenabfluss` - Overland flow hazard
- `ch.bafu.bundesinventare-auen` - Federal Inventory of Floodplains
- `ch.bafu.gefahren-waldbrand_warnung` - Forest fire warnings
- `ch.bafu.geochemischer-bodenatlas_schweiz_*` - Soil quality atlas
- `ch.bafu.bundesinventare-*` - Various federal inventories

## Example Usage

See `bafu_examples.py` for complete working examples.

## Resources

- BAFU STAC Catalog: https://data.geo.admin.ch/api/stac/v1/
- Documentation: https://www.geocat.ch/
- BAFU Website: https://www.bafu.admin.ch/

## License

Data from BAFU is typically licensed under Swiss Open Government Data terms.
Check individual collection licenses for specific terms.