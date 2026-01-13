"""
Comprehensive Planetary Computer Data Retrieval for San Francisco

This script follows Microsoft's official SAS token documentation:
https://planetarycomputer.microsoft.com/docs/concepts/sas/

It retrieves data from all collections in the Planetary Computer catalog
for the San Francisco area, properly handling SAS token authentication.

Run this script from the project root directory:
    python team1a/scarlett/my_lulc_script.py
"""

import sys
import os
import json
from pathlib import Path

# Add project root directory to path (two levels up from this file)
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the comprehensive framework
from planetary_computer_framework import PlanetaryComputerClient, CollectionProcessor

# San Francisco bounding box [min_lon, min_lat, max_lon, max_lat]
SAN_FRANCISCO_BBOX = [-122.5, 37.7, -122.3, 37.8]

# Path to collections JSON file
COLLECTIONS_JSON = os.path.join(
    project_root,
    'data',
    'Catalogs19_27',
    'stac-tags-planetarycomputer.microsoft.com.json'
)


def main():
    """Main function to retrieve all collections for San Francisco."""
    
    print("=" * 70)
    print("Planetary Computer Data Retrieval - San Francisco")
    print("Following Microsoft SAS Token Documentation")
    print("=" * 70)
    print()
    
    # Initialize client
    print("Initializing Planetary Computer client...")
    try:
        client = PlanetaryComputerClient()
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {str(e)}")
        print("\nMake sure you have installed the required packages:")
        print("  pip install planetary-computer requests")
        return
    
    # Initialize processor
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "sf_data_retrieval")
    processor = CollectionProcessor(client, output_dir=output_dir)
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Load collections from JSON file
    print("Loading collections from JSON file...")
    try:
        collections = processor.load_collections_from_json(COLLECTIONS_JSON)
        print(f"✓ Loaded {len(collections)} collections")
    except Exception as e:
        print(f"✗ Failed to load collections: {str(e)}")
        return
    
    # Optional: Filter to specific collections for testing
    # Uncomment to test with a subset of collections
    # test_collections = ['io-lulc-annual-v02', 'sentinel-2-l2a', 'landsat-c2-l2']
    # collections = [c for c in collections if c.get('id') in test_collections]
    
    # Process all collections
    print("\nStarting data retrieval for San Francisco area...")
    print(f"Bounding box: {SAN_FRANCISCO_BBOX}")
    print()
    
    # Process collections (set download_assets=True to download files)
    results = processor.process_all_collections(
        collections=collections,
        bbox=SAN_FRANCISCO_BBOX,
        datetime_range=None,  # Use None to search all available dates
        max_items_per_collection=3,  # Limit items per collection for initial run
        download_assets=False,  # Set to True to download asset files
        collection_filter=None  # Set to list of IDs to filter specific collections
    )
    
    # Save results to JSON
    results_file = os.path.join(output_dir, "retrieval_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {results_file}")
    
    # Print detailed summary
    print("\n" + "=" * 70)
    print("Detailed Summary")
    print("=" * 70)
    
    # Show collections with items found
    collections_with_items = [
        r for r in results['collections']
        if r.get('items_found', 0) > 0
    ]
    
    if collections_with_items:
        print(f"\nCollections with data found ({len(collections_with_items)}):")
        for result in collections_with_items[:20]:  # Show first 20
            print(f"  • {result['collection_id']}: {result['items_found']} items")
            if result.get('items'):
                for item in result['items'][:2]:  # Show first 2 items
                    print(f"    - {item['item_id']}: {item['assets_count']} assets")
        
        if len(collections_with_items) > 20:
            print(f"  ... and {len(collections_with_items) - 20} more collections")
    
    # Show example: LULC collection
    lulc_results = [
        r for r in results['collections']
        if 'lulc' in r.get('collection_id', '').lower()
    ]
    
    if lulc_results:
        print(f"\n{'='*70}")
        print("Example: LULC Collection")
        print(f"{'='*70}")
        lulc = lulc_results[0]
        print(f"Collection: {lulc['collection_id']}")
        print(f"Title: {lulc.get('collection_title', 'N/A')}")
        print(f"Items found: {lulc.get('items_found', 0)}")
        
        if lulc.get('items'):
            item = lulc['items'][0]
            print(f"\nFirst item: {item['item_id']}")
            print(f"Date: {item.get('datetime', 'N/A')}")
            print(f"Assets: {item['assets_count']}")
            
            # Show asset details
            for asset_key, asset_info in list(item['assets'].items())[:5]:
                print(f"  • {asset_key}:")
                print(f"    Type: {asset_info.get('type', 'N/A')}")
                print(f"    Signed: {asset_info.get('signed', False)}")
                if asset_info.get('download_path'):
                    print(f"    Downloaded: {asset_info['download_path']}")
    
    print("\n" + "=" * 70)
    print("Retrieval Complete!")
    print("=" * 70)
    print(f"\nTo download assets, set download_assets=True in the script")
    print(f"Results saved to: {results_file}")
    print(f"Data directory: {output_dir}")


if __name__ == "__main__":
    main()

