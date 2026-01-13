# ESG Data Retrieval Guide

This guide explains how to use the ESG data retrieval system to extract, download, and analyze Planetary Computer collections based on the Joey - ESG Mapping.xlsx table.

## Overview

The system consists of three main components:

1. **`planetary_computer_framework.py`**: Core framework for Planetary Computer STAC API access with SAS token authentication
2. **`esg_data_retrieval.py`**: ESG-specific data retrieval script that reads the Excel mapping table
3. **`my_lulc_script.py`**: General-purpose script for retrieving all collections (original script)

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas openpyxl planetary-computer requests rasterio numpy
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Run ESG Data Retrieval

```bash
python team1a/scarlett/esg_data_retrieval.py
```

This will:
- Read the Excel mapping file (`data/TablesMatched/Joey - ESG Mapping.xlsx`)
- Extract all Planetary Computer collection IDs and matching reasons
- Retrieve data for San Francisco area
- Download assets according to matching reasons
- Save results to `esg_data_retrieval/` directory

## How It Works

### Step 1: Parse Excel File

The `ESGMappingParser` class reads the Excel file and extracts collection information:

- **Pattern Recognition**: Identifies entries in format: `[catalog-name]-#. Dataset_ID, Dataset_Title (matching reason)`
- **Catalog Filtering**: Filters to only Planetary Computer collections (`planetarycomputer.microsoft.com`)
- **Extraction**: Extracts Dataset_ID, Dataset_Title, and matching reason for each entry

### Step 2: Determine Data Requirements

Based on the matching reason, the system determines:

1. **Time Period**:
   - Historical baseline: Past 10-20 years
   - Future projections: Latest 5 years (for projection datasets)
   - Recent data: Last 5 years
   - Default: Last 10 years

2. **Relevant Variables**:
   - Temperature: `tasmax`, `tas`, `tmax`, `tmin`, `LST_Day`, `LST_Night`
   - Precipitation: `pr`, `prcp`, `precipitation`
   - Water/Drought: `pdsi`, `def`, `aet`, `pet`, `soil`
   - Thermal: `LST_Day`, `LST_Night`

### Step 3: Retrieve Data

For each collection:

1. **Get Collection Info**: Query STAC API for collection metadata
2. **Search Items**: Search for items in San Francisco bounding box `[-122.5, 37.7, -122.3, 37.8]`
3. **Sign URLs**: Use SAS tokens to sign Azure Blob Storage URLs
4. **Download Assets**: Download relevant asset files
5. **Extract Variables**: Identify which variables are available in the assets

### Step 4: Save Results

Results are saved to `esg_data_retrieval/esg_retrieval_results.json` with:

- Collection metadata
- Items found and processed
- Relevant variables identified
- Asset download paths
- Error information

## Output Structure

```
esg_data_retrieval/
├── esg_retrieval_results.json    # Summary of all processing
├── rasters/                      # Raster data files
│   └── {collection_id}/
│       └── {item_id}_{asset_key}.tif
├── vectors/                      # Vector data files
│   └── {collection_id}/
└── metadata/                     # Metadata files
    └── {collection_id}/
```

## Customization

### Change Location

Edit `SAN_FRANCISCO_BBOX` in `esg_data_retrieval.py`:

```python
# Example: New York area
SAN_FRANCISCO_BBOX = [-74.1, 40.6, -73.9, 40.8]
```

### Adjust Download Settings

In the `main()` function:

```python
results = retriever.retrieve_collections(
    collections=pc_collections,
    download_assets=True,  # Set to False to skip downloads
    max_items_per_collection=10  # Increase for more items
)
```

### Filter Specific Collections

Add filtering in `main()`:

```python
# Filter to specific collections
filtered_collections = [
    c for c in pc_collections
    if c['dataset_id'] in ['nasa-nex-gddp-cmip6', 'terraclimate']
]
results = retriever.retrieve_collections(collections=filtered_collections)
```

## Understanding Matching Reasons

The matching reason explains why each collection is relevant for ESG analysis:

### Climate Risk Collections

**Example**: `nasa-nex-gddp-cmip6`
- **Reason**: "assesses future temperature scenarios through 2100 to assess climate-related risks to cooling energy demands"
- **Variables**: `tasmax`, `tas`, `pr`
- **Time Period**: Historical + projections (2050, 2100)
- **Use Case**: Assess future cooling energy needs

### Water Stress Collections

**Example**: `terraclimate`
- **Reason**: "water stress and drought assessment"
- **Variables**: `pdsi`, `def`, `aet`, `soil`
- **Time Period**: Historical baseline (past 20 years)
- **Use Case**: Assess water availability and drought risk

### Thermal Stress Collections

**Example**: `modis-11A1-061`
- **Reason**: "monitors heat island effects and thermal stress"
- **Variables**: `LST_Day`, `LST_Night`
- **Time Period**: Recent data (last 5 years)
- **Use Case**: Assess urban heat island effects

## Data Analysis

After retrieval, you can analyze the downloaded data:

### Raster Data (GeoTIFF)

```python
import rasterio
import numpy as np

# Open raster file
with rasterio.open('esg_data_retrieval/rasters/nasa-nex-gddp-cmip6/item_tasmax.tif') as src:
    data = src.read(1)  # Read first band
    # Calculate statistics
    mean_temp = np.nanmean(data)
    max_temp = np.nanmax(data)
```

### Zarr Data

```python
import xarray as xr

# Open Zarr dataset
ds = xr.open_zarr('path/to/zarr', consolidated=True)
# Extract variable
tasmax = ds['tasmax']
# Calculate statistics
mean_temp = tasmax.mean(dim=['lat', 'lon'])
```

## Error Handling

The system includes comprehensive error handling:

- **Missing Collections**: Collections not found in STAC API are reported but don't stop processing
- **No Items Found**: Collections with no items in the search area are reported
- **Download Failures**: Asset download failures are logged but don't stop processing
- **Network Errors**: Network errors are caught and reported

## Troubleshooting

### "pandas not available"
```bash
pip install pandas openpyxl
```

### "No collections found in Excel"
- Check that the Excel file path is correct
- Verify the Excel file format matches the expected pattern
- Check that entries follow format: `[catalog-name]-#. Dataset_ID, Title (reason)`

### "Collection not found in STAC API"
- Some collections may not be available
- Check collection ID spelling
- Verify collection exists: `https://planetarycomputer.microsoft.com/api/stac/v1/collections/{Dataset_ID}`

### "No items found for collection"
- Collection may not have data for the specified bounding box
- Try expanding the bounding box
- Check collection's spatial extent

## Next Steps

After retrieving data:

1. **Analyze Variables**: Extract and analyze relevant variables based on matching reasons
2. **Calculate Metrics**: Compute ESG risk metrics according to SASB standards
3. **Generate Reports**: Create ESG risk reports structured by SASB disclosure topics
4. **Visualize Data**: Create maps and charts showing ESG risk factors

## References

- [Microsoft Planetary Computer SAS Documentation](https://planetarycomputer.microsoft.com/docs/concepts/sas/)
- [STAC Specification](https://stacspec.org/)
- [SASB Standards](https://www.sasb.org/)






