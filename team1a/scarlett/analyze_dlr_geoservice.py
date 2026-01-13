"""
DLR Geoservice ESG Data Retrieval and Analysis

Main script that:
1. Parses CSV to extract DLR Geoservice collections
2. Retrieves data using DLR Geoservice client
3. Analyzes collections for ESG risks
4. Generates comprehensive risk report
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
from dlr_esg_retriever import DLRGeoserviceRetriever, SAN_FRANCISCO_BBOX
from esg_data_analysis import ESGDataAnalyzer

# Paths
CSV_FILE = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.csv')
CATALOG_JSON = os.path.join(project_root, 'data', 'Catalogs10_18', 'stac-tags-geoservice.dlr.de.json')

# European test region - Berlin, Germany
# DLR Geoservice has extensive European data coverage
BERLIN_BBOX = [13.0, 52.3, 13.8, 52.7]  # [min_lon, min_lat, max_lon, max_lat]


def main():
    """Main function."""
    print("=" * 70)
    print("DLR Geoservice ESG Data Retrieval and Analysis")
    print("Test Region: Berlin, Germany (European coverage)")
    print("=" * 70)
    print()
    
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "dlr_geoservice_data")
    
    # Step 1: Parse CSV to extract DLR collections
    print("Step 1: Parsing ESG Mapping CSV...")
    csv_path = CSV_FILE.replace('.xlsx', '.csv')
    
    if not os.path.exists(csv_path):
        print(f"✗ CSV file not found: {csv_path}")
        print("  Please ensure the CSV file exists")
        return
    
    # ESGMappingParser expects excel_path in constructor, but we'll use parse_csv method
    parser = ESGMappingParser(CSV_FILE)  # Pass original Excel path for constructor
    
    try:
        all_collections = parser.parse_csv(csv_path)
    except Exception as e:
        print(f"✗ Failed to parse CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Debug: Show what catalog names were extracted
    if all_collections:
        print(f"\nDebug: Sample catalog names found:")
        catalog_names = set()
        for col in all_collections[:20]:
            catalog_name = col.get('catalog_name', 'N/A')
            catalog_names.add(catalog_name)
            if 'geoservice' in catalog_name.lower() or 'dlr' in catalog_name.lower():
                print(f"  *** '{catalog_name}' -> {col.get('dataset_id', 'N/A')}")
            else:
                print(f"  - '{catalog_name}' -> {col.get('dataset_id', 'N/A')}")
        print(f"\nTotal unique catalog names: {len(catalog_names)}")
        print(f"Catalog names containing 'geoservice' or 'dlr': {[c for c in catalog_names if 'geoservice' in c.lower() or 'dlr' in c.lower()]}")
    
    # Filter to DLR Geoservice collections
    dlr_collections = parser.filter_dlr_geoservice(all_collections)
    
    if not dlr_collections:
        print("✗ No DLR Geoservice collections found in CSV file")
        return
    
    print(f"\n✓ Found {len(dlr_collections)} DLR Geoservice collections")
    
    # Display collections
    print("\nCollections to retrieve:")
    for i, col in enumerate(dlr_collections[:20], 1):  # Show first 20
        print(f"  {i}. {col['dataset_id']}: {col.get('dataset_title', 'N/A')}")
        print(f"     Reason: {col.get('matching_reason', 'N/A')[:100]}...")
    
    if len(dlr_collections) > 20:
        print(f"  ... and {len(dlr_collections) - 20} more collections")
    
    # Step 2: Initialize retriever
    print("\nStep 2: Initializing DLR Geoservice retriever...")
    print(f"Using Berlin, Germany region for testing (DLR has extensive European coverage)")
    print(f"Bounding box: {BERLIN_BBOX}")
    
    retriever = DLRGeoserviceRetriever(
        bbox=BERLIN_BBOX,
        output_dir=output_dir
    )
    print(f"✓ Output directory: {output_dir}")
    
    # Step 3: Retrieve collections
    print("\nStep 3: Retrieving collections...")
    print("Note: Downloading assets for Berlin area")
    retrieval_results = retriever.retrieve_collections(
        collections=dlr_collections,
        download_assets=True,  # Set to True to download files
        max_items_per_collection=3,  # Reduced for testing
        catalog_json_path=CATALOG_JSON if os.path.exists(CATALOG_JSON) else None
    )
    
    # Save retrieval results
    results_file = os.path.join(output_dir, "dlr_retrieval_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(retrieval_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Retrieval results saved to: {results_file}")
    
    # Print retrieval summary
    print("\n" + "=" * 70)
    print("Retrieval Summary")
    print("=" * 70)
    print(f"Collections requested: {retrieval_results['collections_requested']}")
    print(f"Collections processed: {retrieval_results['collections_processed']}")
    print(f"Collections successful: {retrieval_results['collections_successful']}")
    print(f"Collections failed: {retrieval_results['collections_failed']}")
    
    # Show successful collections
    successful = [r for r in retrieval_results['collection_results'] if r.get('status') == 'success']
    if successful:
        print(f"\nSuccessful collections ({len(successful)}):")
        for r in successful[:10]:  # Show first 10
            print(f"  • {r['dataset_id']}: {r.get('items_found', 0)} items")
    
    # Step 4: Analyze collections
    if successful:
        print("\n" + "=" * 70)
        print("Step 4: Analyzing collections for ESG risks...")
        print("=" * 70)
        
        # Create analyzer
        analyzer = ESGDataAnalyzer(
            data_dir=output_dir,
            results_json=results_file,
            excel_file=None  # We already have matching reasons in retrieval results
        )
        
        # Update analyzer's retrieval results
        analyzer.retrieval_results = retrieval_results
        
        # Analyze all collections
        analysis_results = analyzer.analyze_all_collections()
        
        # Save analysis results
        analysis_file = os.path.join(output_dir, "dlr_esg_analysis_results.json")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Analysis results saved to: {analysis_file}")
        
        # Print risk summary
        risk_summary = analysis_results.get('summary', {}).get('risk_summary', {})
        if risk_summary:
            print("\n" + "=" * 70)
            print("ESG Risk Summary")
            print("=" * 70)
            
            if 'temperature_risk' in risk_summary:
                temp_risk = risk_summary['temperature_risk']
                print(f"Temperature Risk: {temp_risk.get('level', 'unknown').upper()}")
                print(f"  Score: {temp_risk.get('score', 0):.2f}")
                print(f"  Sources: {len(temp_risk.get('sources', []))} datasets")
            
            if 'water_risk' in risk_summary:
                water_risk = risk_summary['water_risk']
                print(f"Water Risk: {water_risk.get('level', 'unknown').upper()}")
                print(f"  Score: {water_risk.get('score', 0):.2f}")
                print(f"  Sources: {len(water_risk.get('sources', []))} datasets")
            
            if 'hazard_risk' in risk_summary:
                hazard_risk = risk_summary['hazard_risk']
                print(f"Hazard Risk: {hazard_risk.get('level', 'unknown').upper()}")
                print(f"  Score: {hazard_risk.get('score', 0):.2f}")
                print(f"  Sources: {len(hazard_risk.get('sources', []))} datasets")
            
            if 'overall_risk' in risk_summary:
                overall_risk = risk_summary['overall_risk']
                print(f"\nOverall ESG Risk: {overall_risk.get('level', 'unknown').upper()}")
                print(f"  Score: {overall_risk.get('score', 0):.2f}")
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\nResults saved in: {output_dir}")
    print(f"  - Retrieval results: dlr_retrieval_results.json")
    print(f"  - Analysis results: dlr_esg_analysis_results.json")
    print(f"  - Analysis report: esg_analysis_report.txt")


if __name__ == "__main__":
    main()

