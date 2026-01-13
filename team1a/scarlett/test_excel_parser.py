"""Test script for Excel parser."""
import sys
import os
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from esg_data_retrieval import ESGMappingParser

excel_file = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.xlsx')

print(f"Reading Excel file: {excel_file}")
print(f"File exists: {os.path.exists(excel_file)}")

try:
    parser = ESGMappingParser(excel_file)
    collections = parser.parse_excel()
    
    print(f"\n✓ Successfully parsed {len(collections)} collections")
    
    # Filter to Planetary Computer
    pc_collections = parser.filter_planetary_computer(collections)
    print(f"✓ Found {len(pc_collections)} Planetary Computer collections")
    
    # Show first 5
    print("\nFirst 5 collections:")
    for i, col in enumerate(pc_collections[:5], 1):
        print(f"\n{i}. Dataset ID: {col['dataset_id']}")
        print(f"   Title: {col.get('dataset_title', 'N/A')}")
        print(f"   Reason: {col.get('matching_reason', 'N/A')[:100]}")
        
except Exception as e:
    import traceback
    print(f"Error: {str(e)}")
    traceback.print_exc()






