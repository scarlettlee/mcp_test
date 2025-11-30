"""

This script demonstrates downloading and visualizing geospatial data using
dynamic data from JSON catalog files.

This implementation:
1. Loads collection metadata from JSON catalog
2. Discovers available date ranges and assets
3. Makes informed search requests
4. Downloads validated assets
5. Creates interactive map visualizations

Usage:
    python milestone2_catalog_based.py
"""

from mcp_framework import MCPServer
from tools import (
    earth_search_search_tool,
    earth_search_download_tool,
    earth_search_visualize_tool,
    load_catalog,
    get_collection_info,
    get_suggested_date_range,
    get_available_assets,
    list_collections
)
import json


def complete_workflow_example():
    """
    Complete workflow for downloading and visualizing geospatial data using catalog metadata.
    
    Loads collection information from JSON catalog, searches for imagery,
    downloads assets, and creates an interactive map visualization.
    """
    print("=" * 80)
    print("Catalog-Based Implementation")
    print("Download and Visualize Geospatial Data")
    print("=" * 80)
    
    # ============================================================================
    # STEP 1: Load Catalog
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 1: Load STAC Catalog from JSON")
    print("=" * 80)
    
    catalog = load_catalog("earth-search")
    print(f"Loaded catalog: {catalog.get('stacApiUrl')}")
    print(f"  Exported: {catalog.get('exportedAt')}")
    
    # ============================================================================
    # STEP 2: Discover Available Collections
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 2: Discover Available Collections")
    print("=" * 80)
    
    collections = list_collections(catalog)
    print(f"Found {len(collections)} collections")
    
    # Show available options
    print("\nAvailable collections:")
    for idx, col in enumerate(collections[:5], 1):  # Show first 5
        print(f"  {idx}. {col['id']}")
        print(f"     {col['title']}")
        if 'start_date' in col:
            print(f"     Available: {col['start_date']} to {col.get('end_date', 'present')}")
    
    # Select collection
    collection_id = "sentinel-2-l2a"  # For demo, but this comes from catalog
    print(f"\nSelected collection: {collection_id}")
    
    # ============================================================================
    # STEP 3: Get Collection Metadata
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 3: Get Collection Metadata from Catalog")
    print("=" * 80)
    
    # Get detailed info
    collection_info = get_collection_info(catalog, collection_id)
    print(f"Collection: {collection_info['title']}")
    print(f"  Description: {collection_info['description'][:100]}...")
    
    # Get valid date range
    date_range = get_suggested_date_range(catalog, collection_id)
    print(f"\nTemporal extent:")
    print(f"  Start: {date_range['start']}")
    print(f"  End: {date_range['end']}")
    
    # Get available assets
    assets = get_available_assets(catalog, collection_id)
    print(f"\nAvailable assets: {len(assets)} total")
    print(f"  First 10: {assets[:10]}")
    
    # ============================================================================
    # STEP 4: Search Using Catalog Data
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 4: Search for Imagery (Using Catalog Metadata)")
    print("=" * 80)
    
    server = MCPServer()
    server.register_tool("search", earth_search_search_tool)
    server.register_tool("download", earth_search_download_tool)
    server.register_tool("visualize", earth_search_visualize_tool)
    
    # Define search area (this could also come from user input, config, etc.)
    search_bbox = [-122.5, 37.7, -122.3, 37.9]  # San Francisco Bay Area
    location_name = "San Francisco Bay Area"
    
    print(f"\nSearching for: {location_name}")
    print(f"  Collection: {collection_id} (from catalog)")
    print(f"  Bounding box: {search_bbox}")
    print(f"  Date range: Using recent data (catalog shows available from {date_range['start']})")
    
    # Make search with validated parameters
    search_result = server.call_tool("search", {
        "collection": collection_id,  # From catalog
        "bbox": search_bbox,
        "date_start": "30 days ago",  # Could use date_range['start']
        "date_end": "today",  # Could use date_range['end']
        "limit": 5,
        "max_cloud_cover": 15
    })
    
    if "error" in search_result:
        print(f"Search failed: {search_result['error']}")
        return
    
    # Parse results
    search_data = json.loads(search_result["result"])
    items_found = search_data.get("items_found", 0)
    
    print(f"\nSearch successful")
    print(f"  Found {items_found} items")
    
    if items_found > 0:
        print(f"\n  First result:")
        first_item = search_data["items"][0]
        print(f"    ID: {first_item['id']}")
        print(f"    Date: {first_item['date']}")
        print(f"    Cloud cover: {first_item['cloud_cover']}%")
        print(f"    Available assets: {first_item['assets'][:5]}...")
    else:
        print("\n  No items found. Try different parameters.")
        return
    
    # ============================================================================
    # STEP 5: Download Data (Using Valid Asset from Catalog)
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 5: Download Imagery (Using Catalog Asset List)")
    print("=" * 80)
    
    # Choose asset from catalog's available assets
    preferred_assets = ["thumbnail", "visual", "rendered_preview"]
    asset_to_download = None
    
    for preferred in preferred_assets:
        if preferred in assets:
            asset_to_download = preferred
            break
    
    if not asset_to_download:
        asset_to_download = assets[0]  # Fallback to first available
    
    print(f"\nDownloading asset: {asset_to_download}")
    print(f"  (Selected from {len(assets)} available assets in catalog)")
    
    download_result = server.call_tool("download", {
        "item_index": 0,
        "asset_key": asset_to_download,
        "output_dir": "downloads"
    })
    
    if "error" in download_result:
        print(f"Download failed: {download_result['error']}")
        return
    
    print(f"\n{download_result['result']}")
    
    # ============================================================================
    # STEP 6: Visualize on Map
    # ============================================================================
    print("\n" + "=" * 80)
    print("STEP 6: Create Interactive Map Visualization")
    print("=" * 80)
    
    output_map = f"milestone2_{location_name.replace(' ', '_').lower()}_catalog.html"
    
    print(f"\nCreating map: {output_map}")
    print(f"  Collection: {collection_id}")
    print(f"  Location: {location_name}")
    
    visualize_result = server.call_tool("visualize", {
        "item_index": 0,
        "zoom": 11,
        "output_file": output_map,
        "show_all_items": True
    })
    
    if "error" in visualize_result:
        print(f"Visualization failed: {visualize_result['error']}")
        return
    
    print(f"\n{visualize_result['result']}")
    
    # ============================================================================
    # Process Complete
    # ============================================================================
    print("\n" + "=" * 80)
    print("Process Complete")
    print("=" * 80)
    
    print(f"""
Summary:
--------
Loaded catalog from: cat_10_18/stac-tags-earth-search.aws.element84.com.json
Discovered {len(collections)} available collections
Selected collection: {collection_id}
Found {items_found} imagery items matching criteria
Downloaded {asset_to_download} asset
Created interactive map: {output_map}



Open '{output_map}' in your browser to view the map.
""")


def process_multiple_locations():
    """
    Process multiple locations using catalog data.
    Demonstrates iterating through different regions to search, download, and visualize data.
    """
    print("\n" + "=" * 80)
    print("Multiple Locations Processing (Catalog-Based)")
    print("=" * 80)
    
    # Load catalog once
    catalog = load_catalog("earth-search")
    collection_id = "sentinel-2-l2a"
    assets = get_available_assets(catalog, collection_id)
    
    # Define locations (could come from database, user input, config file, etc.)
    locations = [
        {"name": "San Francisco", "bbox": [-122.5, 37.7, -122.3, 37.9]},
        {"name": "Beijing", "bbox": [116.2, 39.8, 116.5, 40.0]},
        {"name": "London", "bbox": [-0.15, 51.48, 0.05, 51.53]},
    ]
    
    # Setup server
    server = MCPServer()
    server.register_tool("search", earth_search_search_tool)
    server.register_tool("download", earth_search_download_tool)
    server.register_tool("visualize", earth_search_visualize_tool)
    
    print(f"\nProcessing {len(locations)} locations...")
    print(f"Collection: {collection_id} (from catalog)")
    print(f"Asset to download: {assets[0] if 'thumbnail' not in assets else 'thumbnail'}")
    
    results = []
    
    for idx, location in enumerate(locations, 1):
        print(f"\n{'-' * 80}")
        print(f"Location {idx}/{len(locations)}: {location['name']}")
        print(f"{'-' * 80}")
        
        # Search
        search_result = server.call_tool("search", {
            "collection": collection_id,
            "bbox": location["bbox"],
            "date_start": "30 days ago",
            "date_end": "today",
            "limit": 3
        })
        
        if "error" in search_result:
            print(f"  Search failed")
            continue
        
        search_data = json.loads(search_result["result"])
        items_found = search_data.get("items_found", 0)
        print(f"  Found {items_found} items")
        
        if items_found == 0:
            continue
        
        # Download
        asset_key = "thumbnail" if "thumbnail" in assets else assets[0]
        download_result = server.call_tool("download", {
            "item_index": 0,
            "asset_key": asset_key
        })
        
        if "error" not in download_result:
            print(f"  Downloaded {asset_key}")
        
        # Visualize
        map_file = f"milestone2_{location['name'].lower().replace(' ', '_')}_catalog.html"
        visualize_result = server.call_tool("visualize", {
            "item_index": 0,
            "output_file": map_file
        })
        
        if "error" not in visualize_result:
            print(f"  Created map: {map_file}")
            results.append({"location": location['name'], "map": map_file, "items": items_found})
    
    print(f"\n{'=' * 80}")
    print("Processed all locations")
    print(f"{'=' * 80}")
    
    print(f"\nResults:")
    for result in results:
        print(f"  • {result['location']}: {result['items']} items → {result['map']}")


def interactive_workflow():
    """
    Interactive workflow where user selects collection and parameters from catalog.
    Allows dynamic selection of collections and custom bounding box input.
    """
    print("\n" + "=" * 80)
    print("Interactive Workflow (User Selects from Catalog)")
    print("=" * 80)
    
    # Load catalog
    catalog = load_catalog("earth-search")
    collections = list_collections(catalog)
    
    # Show available collections
    print("\nAvailable collections from catalog:")
    for idx, col in enumerate(collections, 1):
        print(f"{idx}. {col['id']}")
        print(f"   {col['title']}")
        if 'start_date' in col:
            print(f"   Available: {col.get('start_date', 'N/A')} to {col.get('end_date', 'present')}")
        print()
    
    try:
        # User selects collection
        choice = input(f"Select collection (1-{len(collections)}): ").strip()
        selected_idx = int(choice) - 1
        
        if selected_idx < 0 or selected_idx >= len(collections):
            print("Invalid selection")
            return
        
        collection_id = collections[selected_idx]['id']
        print(f"\nSelected: {collection_id}")
        
        # Get collection details from catalog
        info = get_collection_info(catalog, collection_id)
        assets = get_available_assets(catalog, collection_id)
        date_range = get_suggested_date_range(catalog, collection_id)
        
        print(f"\nCollection details (from catalog):")
        print(f"  Title: {info['title']}")
        print(f"  Available from: {date_range['start']} to {date_range['end']}")
        print(f"  Assets: {len(assets)} available")
        
        # Get location
        print(f"\nEnter bounding box (or press Enter for San Francisco):")
        print("Format: min_lon,min_lat,max_lon,max_lat")
        bbox_input = input("Bbox: ").strip()
        
        if bbox_input:
            bbox = [float(x) for x in bbox_input.split(",")]
        else:
            bbox = [-122.5, 37.7, -122.3, 37.9]
        
        # Complete workflow
        server = MCPServer()
        server.register_tool("search", earth_search_search_tool)
        server.register_tool("download", earth_search_download_tool)
        server.register_tool("visualize", earth_search_visualize_tool)
        
        # Search
        print(f"\nSearching {collection_id}...")
        result = server.call_tool("search", {
            "collection": collection_id,
            "bbox": bbox,
            "date_start": "30 days ago",
            "date_end": "today",
            "limit": 5
        })
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        
        data = json.loads(result["result"])
        print(f"Found {data.get('items_found', 0)} items")
        
        if data.get("items_found", 0) == 0:
            print("No items found. Try different parameters.")
            return
        
        # Download
        asset_key = "thumbnail" if "thumbnail" in assets else assets[0]
        print(f"\nDownloading {asset_key}...")
        result = server.call_tool("download", {"item_index": 0, "asset_key": asset_key})
        print(result.get("result", "Error"))
        
        # Visualize
        print(f"\nCreating map...")
        result = server.call_tool("visualize", {
            "item_index": 0,
            "output_file": f"{collection_id}_interactive_map.html"
        })
        print(result.get("result", "Error"))
        
        print("\nProcess complete")
        
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except Exception as e:
        print(f"\nError: {e}")


def main():
    """Run demonstrations of catalog-based geospatial data workflows."""
    print("\n" + "=" * 80)
    print("Catalog-Based Geospatial Data Tool")
    print("Dynamic Data Loading from JSON Catalogs")
    print("=" * 80)
    
    print("""
Select a demonstration:

1. Complete Workflow Example (Single Location)
   - Shows full workflow using catalog data
   - Download and visualize geospatial data

2. Multiple Locations (Batch Processing)
   - Process several locations dynamically

3. Interactive Mode (User Selection)
   - Choose collection from catalog
   - Enter custom parameters

4. Run Complete Example (Recommended)
""")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            complete_workflow_example()
        elif choice == "2":
            process_multiple_locations()
        elif choice == "3":
            interactive_workflow()
        elif choice == "4":
            complete_workflow_example()
        else:
            print("Invalid choice. Running complete example...")
            complete_workflow_example()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

