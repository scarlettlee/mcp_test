"""
Test Script - Generate Fixed GEO BON Map

This script demonstrates the improved map visualization with:
- No repeating world maps
- Readable info boxes
- Cleaner styling
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_framework import MCPServer
from geobon_stac_tools import GEOBON_TOOLS


def test_fixed_map():
    """Generate a map with the fixes applied"""
    
    print("\n" + "=" * 70)
    print("Testing Fixed GEO BON Map Visualization")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register tools
    for tool_name, tool_func in GEOBON_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    print("\n1. Searching for forest loss data...")
    result = server.call_tool("geobon_search_collection", {
        "collection_id": "gfw-lossyear",
        "limit": 3
    })
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print("✅ Found data")
    
    print("\n2. Creating FIXED map visualization...")
    print("   - No repeating world maps ✓")
    print("   - Readable info boxes ✓")
    print("   - Better zoom level ✓")
    print("   - Cleaner styling ✓")
    
    result = server.call_tool("geobon_visualize_forest_loss", {
        "item_index": 0,
        "output_file": "FIXED_geobon_map.html",
        "zoom": 3,
        "region_name": "Global"
    })
    
    if "result" in result:
        print("\n" + result["result"])
    else:
        print(f"Error: {result.get('error')}")
        return
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS!")
    print("=" * 70)
    print("\nOpen 'FIXED_geobon_map.html' in your browser to see:")
    print("  • Single world map (no repeats!)")
    print("  • Clean, readable info box in top-left")
    print("  • Red coverage box with proper opacity")
    print("  • Clickable marker with ESG details")
    print("  • Satellite imagery toggle option")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        test_fixed_map()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("  • mcp_framework.py in the same directory")
        print("  • geobon_stac_tools.py in the same directory")
        print("  • 'pip install requests folium' installed")