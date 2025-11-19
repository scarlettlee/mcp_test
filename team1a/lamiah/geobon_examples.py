"""
GEO BON STAC Tools - Usage Examples

This file demonstrates how to use the GEO BON (Group on Earth Observations 
Biodiversity Observation Network) STAC tools for accessing and visualizing 
global biodiversity and environmental data, with focus on forest loss monitoring.
"""

import sys
import os

# Add the parent directory to the path so we can import mcp_framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_framework import MCPServer
from geobon_stac_tools import GEOBON_TOOLS


def example_forest_loss_analysis():
    """
    Example: Analyzing global forest loss data from GEO BON.
    
    This demonstrates ESG risk assessment for deforestation and climate change.
    Use Case: Supply chain sustainability, carbon credit verification, TCFD reporting
    """
    print("=" * 70)
    print("Example: GEO BON Global Forest Loss Analysis")
    print("ESG Risk: Environmental - Deforestation & Climate Change")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all GEO BON tools
    for tool_name, tool_func in GEOBON_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # Step 1: List collections related to forests
    print("\n1. Searching for forest-related collections...")
    result = server.call_tool("geobon_list_collections", {
        "search_term": "forest",
        "limit": 5
    })
    print(result.get("result", "Error"))
    
    # Step 2: Get detailed info about forest loss collection
    print("\n2. Getting detailed information about Global Forest Watch - Loss year...")
    collection_id = "gfw-lossyear"
    result = server.call_tool("geobon_get_collection_info", {
        "collection_id": collection_id
    })
    print(result.get("result", "Error"))
    
    # Step 3: Search for forest loss data items
    print("\n3. Searching for forest loss data (global coverage)...")
    result = server.call_tool("geobon_search_collection", {
        "collection_id": collection_id,
        "limit": 5
    })
    print(result.get("result", "Error"))
    
    # Step 4: Visualize on map
    print("\n4. Creating interactive forest loss visualization...")
    result = server.call_tool("geobon_visualize_forest_loss", {
        "item_index": 0,
        "output_file": "geobon_forest_loss_global.html",
        "zoom": 2,
        "region_name": "Global"
    })
    print(result.get("result", "Error"))
    
    print("\n" + "=" * 70)
    print("Forest Loss Analysis Complete!")
    print("=" * 70)


def example_biodiversity_intactness_analysis():
    """
    Example: Analyzing biodiversity intactness from GEO BON.
    
    This demonstrates ESG risk assessment for biodiversity loss.
    Use Case: Nature-related financial disclosure (TNFD), conservation planning
    """
    print("\n" + "=" * 70)
    print("Example: GEO BON Biodiversity Intactness Analysis")
    print("ESG Risk: Environmental - Biodiversity Loss")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all GEO BON tools
    for tool_name, tool_func in GEOBON_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # Step 1: Get info about Biodiversity Intactness Index
    print("\n1. Exploring Biodiversity Intactness Index...")
    collection_id = "bii_nhm"
    result = server.call_tool("geobon_get_collection_info", {
        "collection_id": collection_id
    })
    print(result.get("result", "Error"))
    
    # Step 2: Search for BII data
    print("\n2. Searching for Biodiversity Intactness data...")
    result = server.call_tool("geobon_search_collection", {
        "collection_id": collection_id,
        "limit": 3
    })
    print(result.get("result", "Error"))


def example_human_modification_analysis():
    """
    Example: Analyzing human modification of terrestrial systems.
    
    This demonstrates ESG assessment of human impact on ecosystems.
    Use Case: Infrastructure development impact, land use planning
    """
    print("\n" + "=" * 70)
    print("Example: GEO BON Human Modification Analysis")
    print("ESG Risk: Environmental - Ecosystem Degradation")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all GEO BON tools
    for tool_name, tool_func in GEOBON_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # Step 1: Get info about Global Human Modification
    print("\n1. Exploring Global Human Modification dataset...")
    collection_id = "ghmts"
    result = server.call_tool("geobon_get_collection_info", {
        "collection_id": collection_id
    })
    print(result.get("result", "Error"))
    
    # Step 2: Search for human modification data
    print("\n2. Searching for human modification data...")
    result = server.call_tool("geobon_search_collection", {
        "collection_id": collection_id,
        "limit": 3
    })
    print(result.get("result", "Error"))


def example_download_assets():
    """
    Example: Downloading geospatial assets for detailed analysis.
    
    This shows how to download actual GeoTIFF files for processing.
    """
    print("\n" + "=" * 70)
    print("Example: Downloading GEO BON Assets")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register all GEO BON tools
    for tool_name, tool_func in GEOBON_TOOLS.items():
        server.register_tool(tool_name, tool_func)
    
    # First, we need to search for items
    print("\n1. Searching for forest loss data to download...")
    collection_id = "gfw-lossyear"
    result = server.call_tool("geobon_search_collection", {
        "collection_id": collection_id,
        "limit": 2
    })
    print(result.get("result", "Error"))
    
    # Step 2: List available assets
    print("\n2. Listing available assets for the first item...")
    result = server.call_tool("geobon_download_asset", {
        "item_index": 0
        # Not specifying asset_key will list available assets
    })
    print(result.get("result", "Error"))
    
    print("\n💡 To download a specific asset, run:")
    print('   server.call_tool("geobon_download_asset", {')
    print('       "item_index": 0,')
    print('       "asset_key": "data"  # or whichever asset key you want')
    print('   })')


def main():
    """Run all GEO BON examples"""
    print("\n" + "=" * 70)
    print("GEO BON STAC Tools - Biodiversity & Environmental Data Analysis")
    print("Group on Earth Observations Biodiversity Observation Network")
    print("=" * 70)
    
    # Run examples
    example_forest_loss_analysis()
    example_biodiversity_intactness_analysis()
    example_human_modification_analysis()
    example_download_assets()
    
    print("\n" + "=" * 70)
    print("All Examples Complete!")
    print("=" * 70)
    print("\n🌍 Available GEO BON Collections for ESG Analysis:")
    print("\n🌲 Forest & Land Cover:")
    print("   • Global Forest Watch - Loss Year (gfw-lossyear)")
    print("   • Global Forest Watch - Tree Cover (gfw-treecover2000)")
    print("   • Global Forest Watch - Forest Gain (gfw-gain)")
    print("   • CEC North American Land Cover (cec_land_cover)")
    
    print("\n🦋 Biodiversity:")
    print("   • Biodiversity Intactness Index (bii_nhm)")
    print("   • GBIF Occurrence Density Maps (gbif_heatmaps)")
    
    print("\n🏭 Human Impact:")
    print("   • Global Human Modification (ghmts)")
    
    print("\n🌡️ Climate:")
    print("   • CHELSA Climatologies (chelsa-clim)")
    
    print("\n🌿 Ecosystem Services:")
    print("   • Nature's Contributions to People (ncp_cna)")
    
    print("\n🌏 Soil & Land:")
    print("   • SoilGrids Datasets (soilgrids)")
    
    print("\n" + "=" * 70)
    print("ESG Use Cases:")
    print("=" * 70)
    print("1. 🌲 Deforestation Risk: Track forest loss in supply chains")
    print("2. 🦋 Biodiversity: TNFD reporting & nature-related risks")
    print("3. 🏭 Land Use: Infrastructure impact assessments")
    print("4. 🌡️ Climate: Carbon sequestration & climate risk")
    print("5. 💧 Ecosystem Services: Natural capital accounting")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Open generated HTML maps in your browser")
    print("2. Download GeoTIFF files for detailed spatial analysis")
    print("3. Process data with Python (rasterio, geopandas, xarray)")
    print("4. Integrate with ESG/TNFD reporting frameworks")
    print("5. Create custom analyses for specific regions of interest")
    
    print("\n💡 Pro Tip: Use bbox parameter in search to focus on specific regions:")
    print("   Example for Amazon rainforest: bbox=[-75, -15, -45, 5]")


if __name__ == "__main__":
    main()