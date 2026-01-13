# Planetary Computer Data Retrieval Framework

This framework provides comprehensive data retrieval from Microsoft Planetary Computer STAC API for San Francisco, following Microsoft's official SAS token documentation.

## Overview

The framework consists of two main components:

1. **`planetary_computer_framework.py`**: Core framework with SAS token handling
2. **`my_lulc_script.py`**: Main script that retrieves all collections for San Francisco

## Features

- ✅ **Proper SAS Token Authentication**: Follows Microsoft's official documentation
  - Uses `planetary-computer` package for token signing
  - Automatically handles token caching and expiration
  - Signs Azure Blob Storage URLs correctly

- ✅ **Comprehensive Collection Processing**: 
  - Loads all collections from JSON catalog file
  - Processes each collection for San Francisco area
  - Handles different data types (raster, vector, zarr, etc.)

- ✅ **Smart Filtering**:
  - Checks spatial extent overlap before searching
  - Filters collections by bounding box
  - Handles missing or unavailable data gracefully

- ✅ **Flexible Configuration**:
  - Configurable date ranges
  - Adjustable item limits per collection
  - Optional asset downloading
  - Collection filtering support

## Microsoft SAS Token Documentation

This framework follows the official Microsoft documentation:
https://planetarycomputer.microsoft.com/docs/concepts/sas/

Key points:
- SAS tokens are required for accessing Azure Blob Storage URLs
- The `planetary-computer` Python package handles token generation automatically
- Tokens are cached and refreshed automatically
- No subscription key required for anonymous access

## Installation

Make sure you have the required packages installed:

```bash
pip install planetary-computer requests rasterio numpy folium
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the main script to retrieve all collections for San Francisco:

```bash
python team1a/scarlett/my_lulc_script.py
```

### Customizing the Script

Edit `my_lulc_script.py` to customize:

1. **Change the area**: Modify `SAN_FRANCISCO_BBOX`
   ```python
   # Example: New York area
   SAN_FRANCISCO_BBOX = [-74.1, 40.6, -73.9, 40.8]
   ```

2. **Filter specific collections**: Uncomment and modify `collection_filter`
   ```python
   test_collections = ['io-lulc-annual-v02', 'sentinel-2-l2a']
   collections = [c for c in collections if c.get('id') in test_collections]
   ```

3. **Download assets**: Set `download_assets=True`
   ```python
   download_assets=True  # Set to True to download asset files
   ```

4. **Adjust item limits**: Change `max_items_per_collection`
   ```python
   max_items_per_collection=10  # Increase for more items per collection
   ```

### Using the Framework Directly

You can also use the framework components directly:

```python
from planetary_computer_framework import PlanetaryComputerClient, CollectionProcessor

# Initialize client
client = PlanetaryComputerClient()

# Initialize processor
processor = CollectionProcessor(client, output_dir="my_downloads")

# Load collections
collections = processor.load_collections_from_json("path/to/collections.json")

# Process a single collection
result = processor.process_collection(
    collection=collections[0],
    bbox=[-122.5, 37.7, -122.3, 37.8],
    max_items=5,
    download_assets=False
)

# Process all collections
results = processor.process_all_collections(
    collections=collections,
    bbox=[-122.5, 37.7, -122.3, 37.8],
    max_items_per_collection=3,
    download_assets=False
)
```

## Output Structure

The framework creates the following directory structure:

```
sf_data_retrieval/
├── retrieval_results.json    # Summary of all processing results
├── rasters/                  # Raster data files (if downloaded)
│   └── {collection_id}/
├── vectors/                  # Vector data files (if downloaded)
│   └── {collection_id}/
└── metadata/                 # Metadata files (if downloaded)
    └── {collection_id}/
```

## Results Format

The `retrieval_results.json` file contains:

```json
{
  "total_collections": 100,
  "processed_collections": 100,
  "successful_collections": 45,
  "failed_collections": 5,
  "skipped_collections": 50,
  "bbox": [-122.5, 37.7, -122.3, 37.8],
  "collections": [
    {
      "collection_id": "io-lulc-annual-v02",
      "collection_title": "10m Annual Land Use/Land Cover",
      "status": "success",
      "items_found": 2,
      "items_processed": 2,
      "items": [
        {
          "item_id": "io-lulc-annual-v02-2023",
          "datetime": "2023-01-01T00:00:00Z",
          "assets_count": 3,
          "assets": {
            "data": {
              "href": "https://...",
              "signed": true,
              "type": "image/tiff"
            }
          }
        }
      ]
    }
  ]
}
```

## Example: LULC Data

The script includes special handling for LULC (Land Use/Land Cover) data as an example. The framework automatically:

- Searches for LULC items in the specified area
- Signs asset URLs with SAS tokens
- Provides detailed information about available assets
- Can download and process raster data

## Error Handling

The framework includes comprehensive error handling:

- **Network errors**: Retries and clear error messages
- **Missing data**: Gracefully skips collections without data
- **Invalid URLs**: Validates and reports issues
- **Token errors**: Provides helpful error messages

## Performance Considerations

- **Token Caching**: The `planetary-computer` package caches tokens automatically
- **Rate Limiting**: Microsoft applies rate limits; the framework respects these
- **Concurrent Processing**: Currently processes collections sequentially (can be parallelized)
- **Memory Usage**: Large collections may require significant memory

## Troubleshooting

### "planetary-computer package not available"
```bash
pip install planetary-computer
```

### "Failed to sign URL"
- Check that the URL is a valid Azure Blob Storage URL
- Verify internet connection
- Check if the collection requires authentication

### "No items found"
- The collection may not have data for the specified area
- Try expanding the bounding box
- Check the collection's spatial extent

### "Collection extent does not overlap"
- The collection doesn't cover the search area
- This is normal - many collections are regional

## References

- [Microsoft Planetary Computer SAS Documentation](https://planetarycomputer.microsoft.com/docs/concepts/sas/)
- [Planetary Computer Python SDK](https://github.com/microsoft/planetary-computer-sdk-for-python)
- [STAC Specification](https://stacspec.org/)

## License

This framework is part of the ESG STAC Access project.






