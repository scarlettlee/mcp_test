# team1b/joey/test_my_matching_tools.py

import sys
import os
import json

# Setup paths
current_dir = os.path.dirname(__file__)
team_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(team_dir)

sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

from mcp_framework import MCPServer
from my_matching_tools import esg_data_mapping_tool

def test_with_fedeo_file():
    """Test with the CEOS fedeo STAC catalog JSON file."""
    
    print("=" * 60)
    print("Testing ESG Mapping Tool with fedeo.ceos.org")
    print("=" * 60)
    
    # Create MCP server
    server = MCPServer()
    server.register_tool("esg_mapping", esg_data_mapping_tool)
    print("✓ Tool registered successfully\n")
    
    # Path to your JSON file
    catalog_file = os.path.join(current_dir, "stac-tags-fedeo.ceos.org.json")
    
    # Verify file exists
    if not os.path.exists(catalog_file):
        print(f"✗ ERROR: File not found at {catalog_file}")
        print(f"Please place stac-tags-fedeo.ceos.org.json in: {current_dir}")
        return
    
    # Load and preview the catalog
    with open(catalog_file, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    
    num_collections = len(catalog_data.get('collections', []))
    print(f"Loaded fedeo.ceos.org catalog: {num_collections} collections\n")
    
    # Show first few collections
    if 'collections' in catalog_data and num_collections > 0:
        print("Sample collections:")
        for i, col in enumerate(catalog_data['collections'][:5]):
            col_id = col.get('id', 'unknown')
            col_title = col.get('title', 'No title')
            print(f"  • {col_id}")
            print(f"    {col_title[:80]}...")
        if num_collections > 5:
            print(f"\n  ... and {num_collections - 5} more collections\n")
    
    print("Calling ESG mapping tool with fedeo catalog...")
    print("(This will take a moment - OpenAI is processing the catalog)\n")
    
    # Call the tool
    try:
        result = server.call_tool("esg_mapping", {
            "catalog_data": catalog_file,  # Pass file path
            "model": "gpt-4o-2024-08-06",
            "output_file": "fedeo_esg_mapping_output.csv"
        })
        
        print(result['result'])
        print()
        
        # Validate results
        mapping_info = server.get_context('last_esg_mapping')
        if mapping_info:
            print("=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)
            print(f"✓ Output file: {mapping_info['output_file']}")
            print(f"✓ Row count: {mapping_info['row_count']}")
            
            if mapping_info['row_count'] == 33:
                print("✓ SUCCESS: Exactly 33 rows generated!")
            else:
                print(f"✗ WARNING: Expected 33 rows, got {mapping_info['row_count']}")
            
            # Display sample output
            print("\n" + "=" * 60)
            print("SAMPLE OUTPUT (First 3 Metrics)")
            print("=" * 60)
            
            with open(mapping_info['output_file'], 'r', encoding='utf-8') as f:
                import csv
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if i >= 3:
                        break
                    print(f"\n{i+1}. {row['Metric']}")
                    print(f"   Category: {row['Category']}")
                    print(f"   Code: {row['Code']}")
                    if row['Direct Measurement']:
                        dm = row['Direct Measurement'][:100]
                        print(f"   Direct Measurement: {dm}...")
                    if row['Risk Assessment']:
                        ra = row['Risk Assessment'][:100]
                        print(f"   Risk Assessment: {ra}...")
            
            print("\n" + "=" * 60)
            print(f"✓ Full results saved to: {mapping_info['output_file']}")
            print("=" * 60)
                    
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_fedeo_file()

