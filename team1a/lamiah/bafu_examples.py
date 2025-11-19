"""
BAFU STAC Tools - Usage Examples

This file demonstrates how to use the BAFU (Swiss Federal Office for the Environment)
STAC tools for accessing and visualizing environmental geospatial data.
"""

import sys
import os

# Add the parent directory to the path so we can import mcp_framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_framework import MCPServer
from bafu_stac_tools import BAFU_TOOLS


def example_overland_flow_analysis():
    """
    Example: Analyzing overland flow hazard maps from BAFU.
    
    This demonstrates ESG risk assessment for flooding/water management.
    """
    print("=" * 70)
    print("Example: BAFU Overland Flow Hazard Analysis")
    print("ESG Risk: Environmental - Flood Risk & Water Management")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all BAFU tools
    for tool_name, tool_func in BAFU_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # Step 1: List collections with search
    print("\n1. Searching for flood-related collections...")
    result = server.call_tool("bafu_list_collections", {
        "search_term": "flood",
        "limit": 5
    })
    print(result.get("result", "Error"))
    
    # Step 2: Get detailed info about overland flow collection
    print("\n2. Getting detailed information about overland flow hazard...")
    collection_id = "ch.bafu.gefaehrdungskarte-oberflaechenabfluss"
    result = server.call_tool("bafu_get_collection_info", {
        "collection_id": collection_id
    })
    print(result.get("result", "Error"))
    
    # Step 3: Search for items in the collection
    print("\n3. Searching for overland flow hazard data...")
    result = server.call_tool("bafu_search_collection", {
        "collection_id": collection_id,
        "limit": 3
    })
    print(result.get("result", "Error"))
    
    # Step 4: Visualize on map
    print("\n4. Creating interactive map visualization...")
    result = server.call_tool("bafu_visualize_map", {
        "item_index": 0,
        "output_file": "bafu_overland_flow_map.html",
        "zoom": 8
    })
    print(result.get("result", "Error"))
    
    print("\n" + "=" * 70)
    print("Analysis complete! Check bafu_overland_flow_map.html")
    print("=" * 70)


def example_biodiversity_analysis():
    """
    Example: Analyzing biodiversity and protected areas from BAFU.
    
    This demonstrates ESG risk assessment for biodiversity conservation.
    """
    print("\n" + "=" * 70)
    print("Example: BAFU Biodiversity & Protected Areas Analysis")
    print("ESG Risk: Environmental - Biodiversity Loss")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all BAFU tools
    for tool_name, tool_func in BAFU_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # Step 1: Search for biodiversity-related collections
    print("\n1. Searching for biodiversity collections...")
    result = server.call_tool("bafu_list_collections", {
        "search_term": "biodiversity",
        "limit": 5
    })
    print(result.get("result", "Error"))
    
    # Example with Federal Inventory collections
    print("\n2. Exploring Federal Inventory of Floodplains...")
    collection_id = "ch.bafu.bundesinventare-auen"
    result = server.call_tool("bafu_get_collection_info", {
        "collection_id": collection_id
    })
    print(result.get("result", "Error"))


def main():
    """Run all BAFU examples"""
    print("\n" + "=" * 70)
    print("BAFU STAC Tools - Environmental Data Analysis")
    print("Swiss Federal Office for the Environment")
    print("=" * 70)
    
    # Run examples
    example_overland_flow_analysis()
    example_biodiversity_analysis()
    
    print("\n" + "=" * 70)
    print("All Examples Complete!")
    print("=" * 70)
    print("\nAvailable BAFU Collections for ESG Analysis:")
    print("• Overland Flow Maps - Flood risk assessment")
    print("• Forest Fire Risk - Climate risk & forest management")
    print("• Seismic Hazard - Infrastructure risk")
    print("• Federal Inventories - Biodiversity conservation")
    print("• Soil Contamination - Environmental pollution")
    print("\nNext Steps:")
    print("1. Open generated HTML maps in your browser")
    print("2. Download specific datasets for detailed analysis")
    print("3. Integrate with ESG risk assessment frameworks")


if __name__ == "__main__":
    main()