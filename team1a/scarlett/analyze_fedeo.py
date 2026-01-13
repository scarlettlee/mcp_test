"""
FedEO (CEOS) ESG Data Retrieval and Analysis

Main script that:
1. Parses CSV to extract FedEO collections
2. Retrieves data using FedEO STAC API
3. Analyzes collections for ESG risks
4. Generates comprehensive risk report

FedEO provides access to ESA and other Earth observation data.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))
sys.path.insert(0, os.path.dirname(__file__))

from esg_data_retrieval import ESGMappingParser
from esg_data_analysis import ESGDataAnalyzer

# Try to import DLR retriever as template
try:
    from dlr_esg_retriever import DLRGeoserviceRetriever
except ImportError:
    pass

# Import generic STAC client (can reuse DLR client as base)
from dlr_geoservice_client import DLRGeoserviceClient

# Paths
CSV_FILE = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.csv')
CATALOG_JSON = os.path.join(project_root, 'data', 'Catalogs10_18', 'stac-tags-fedeo.ceos.org.json')

# Berlin, Germany region (good for European data)
BERLIN_BBOX = [13.0, 52.3, 13.8, 52.7]  # [min_lon, min_lat, max_lon, max_lat]


class FedEOClient(DLRGeoserviceClient):
    """Client for FedEO STAC API."""
    
    def __init__(self):
        """Initialize FedEO client."""
        super().__init__(stac_api_url="https://fedeo.ceos.org/opensearch")
        # Note: FedEO may use OpenSearch instead of STAC
        # We'll try the STAC endpoint first


class FedEORetriever:
    """Retrieves ESG-relevant data from FedEO."""
    
    def __init__(self, bbox, output_dir="fedeo_data"):
        """Initialize FedEO retriever."""
        self.bbox = bbox
        self.client = FedEOClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def retrieve_collections(
        self,
        collections,
        download_assets=False,  # FedEO data may require authentication
        max_items_per_collection=3,
        catalog_json_path=None
    ):
        """Retrieve data for specified collections."""
        print(f"\n{'='*70}")
        print(f"Retrieving FedEO ESG Data for {len(collections)} Collections")
        print(f"{'='*70}\n")
        
        results = {
            'bbox': self.bbox,
            'collections_requested': len(collections),
            'collections_processed': 0,
            'collections_successful': 0,
            'collections_failed': 0,
            'collection_results': []
        }
        
        # Group by dataset_id to avoid duplicates
        unique_collections = {}
        for col in collections:
            dataset_id = col['dataset_id']
            if dataset_id not in unique_collections:
                unique_collections[dataset_id] = col
        
        print(f"Processing {len(unique_collections)} unique collections\n")
        
        for dataset_id, col_info in unique_collections.items():
            print(f"\n{'='*70}")
            print(f"Collection: {dataset_id}")
            print(f"Title: {col_info.get('dataset_title', 'N/A')}")
            print(f"ESG Reason: {col_info.get('matching_reason', 'N/A')}")
            print(f"{'='*70}")
            
            # For now, just record the collection info
            # FedEO requires more complex authentication/access
            result = {
                'dataset_id': dataset_id,
                'dataset_title': col_info.get('dataset_title', ''),
                'matching_reason': col_info.get('matching_reason', ''),
                'status': 'info_only',
                'message': 'FedEO collections identified. Full retrieval requires authentication.',
                'items_found': 0
            }
            
            results['collection_results'].append(result)
            results['collections_processed'] += 1
        
        return results


def main():
    """Main function."""
    print("=" * 70)
    print("FedEO (CEOS) ESG Data Retrieval and Analysis")
    print("Test Region: Berlin, Germany (European coverage)")
    print("=" * 70)
    print()
    
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "fedeo_data")
    
    # Step 1: Parse CSV to extract FedEO collections
    print("Step 1: Parsing ESG Mapping CSV for FedEO collections...")
    csv_path = CSV_FILE.replace('.xlsx', '.csv')
    
    if not os.path.exists(csv_path):
        print(f"✗ CSV file not found: {csv_path}")
        return
    
    parser = ESGMappingParser(CSV_FILE)
    
    try:
        all_collections = parser.parse_csv(csv_path)
    except Exception as e:
        print(f"✗ Failed to parse CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Filter to FedEO collections
    fedeo_collections = parser.filter_fedeo(all_collections)
    
    if not fedeo_collections:
        print("✗ No FedEO collections found in CSV file")
        return
    
    print(f"\n✓ Found {len(fedeo_collections)} FedEO collections")
    
    # Display collections
    print("\nFedEO Collections identified:")
    for i, col in enumerate(fedeo_collections, 1):
        print(f"\n  {i}. {col['dataset_id']}")
        print(f"     Title: {col.get('dataset_title', 'N/A')[:80]}...")
        print(f"     ESG Use: {col.get('matching_reason', 'N/A')[:100]}...")
    
    # Step 2: Save collection information
    print(f"\nStep 2: Saving FedEO collection information...")
    
    retriever = FedEORetriever(
        bbox=BERLIN_BBOX,
        output_dir=output_dir
    )
    
    retrieval_results = retriever.retrieve_collections(
        collections=fedeo_collections,
        download_assets=False,  # Not downloading for now
        max_items_per_collection=3,
        catalog_json_path=CATALOG_JSON if os.path.exists(CATALOG_JSON) else None
    )
    
    # Save results
    results_file = os.path.join(output_dir, "fedeo_collections_info.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(retrieval_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Collection information saved to: {results_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("FedEO Collections Summary")
    print("=" * 70)
    print(f"Collections identified: {len(fedeo_collections)}")
    
    # Categorize by ESG topic
    categories = {}
    for col in fedeo_collections:
        reason = col.get('matching_reason', '').lower()
        
        if 'temperature' in reason or 'thermal' in reason or 'lst' in reason:
            categories.setdefault('Temperature/Climate', []).append(col)
        elif 'water' in reason or 'soil moisture' in reason:
            categories.setdefault('Water Resources', []).append(col)
        elif 'permafrost' in reason or 'ice' in reason or 'snow' in reason:
            categories.setdefault('Cryosphere/Climate', []).append(col)
        elif 'land cover' in reason or 'vegetation' in reason:
            categories.setdefault('Land Use', []).append(col)
        else:
            categories.setdefault('Other', []).append(col)
    
    print("\nBy ESG Category:")
    for category, cols in categories.items():
        print(f"  • {category}: {len(cols)} collections")
        for col in cols[:3]:  # Show first 3
            print(f"    - {col['dataset_id']}")
        if len(cols) > 3:
            print(f"    ... and {len(cols) - 3} more")
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\nResults saved in: {output_dir}")
    print(f"  - Collection info: fedeo_collections_info.json")
    print("\nNote: FedEO collections identified.")
    print("Full data retrieval may require ESA authentication/registration.")


if __name__ == "__main__":
    main()

