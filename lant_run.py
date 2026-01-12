"""
Swedish Elevation Data Examples

This script demonstrates how to use the MCP framework with Swedish elevation data tools.
"""

from mcp_framework import MCPServer
from lantmateriet import (
    swedish_elevation_list_collections,
    swedish_elevation_search,
    swedish_elevation_visualize,
    swedish_elevation_download
)


def example_stockholm_area():
    """Example: Explore elevation data around Stockholm"""
    print("=" * 70)
    print("Example 1: Stockholm Area Elevation Data")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register tools
    server.register_tool("list_collections", swedish_elevation_list_collections)
    server.register_tool("search", swedish_elevation_search)
    server.register_tool("visualize", swedish_elevation_visualize)
    server.register_tool("download", swedish_elevation_download)
    
    # 1. List collections with Stockholm keyword
    print("\n1. Finding collections covering Stockholm area...")
    result = server.call_tool("list_collections", {"keyword": "Stockholm"})
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 2. Search for elevation data in Stockholm area
    # Approximate bbox for Stockholm: [17.8, 59.2, 18.3, 59.5]
    print("\n2. Searching for elevation data in Stockholm...")
    result = server.call_tool("search", {
        "collection": "mhm-65_6",  # Collection covering Stockholm
        "bbox": [17.8, 59.2, 18.3, 59.5],
        "limit": 5
    })
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 3. Visualize the first result
    print("\n3. Creating interactive map...")
    result = server.call_tool("visualize", {
        "item_index": 0,
        "zoom": 11,
        "output_file": "stockholm_elevation.html"
    })
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 4. Get download information
    print("\n4. Getting download information...")
    result = server.call_tool("download", {
        "item_index": 0
    })
    print(result.get("result", result.get("error", "Unknown error")))


def example_gotland_island():
    """Example: Explore elevation data for Gotland island"""
    print("\n" + "=" * 70)
    print("Example 2: Gotland Island Elevation Data")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register tools
    server.register_tool("list_collections", swedish_elevation_list_collections)
    server.register_tool("search", swedish_elevation_search)
    server.register_tool("visualize", swedish_elevation_visualize)
    
    # 1. Find Gotland collections
    print("\n1. Finding Gotland collections...")
    result = server.call_tool("list_collections", {"keyword": "Gotland"})
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 2. Search Gotland area
    # Gotland bbox approximately: [18.0, 57.0, 19.0, 58.0]
    print("\n2. Searching Gotland elevation data...")
    result = server.call_tool("search", {
        "collection": "mhm-63_7",  # Gotland collection
        "bbox": [18.2, 57.3, 18.7, 57.7],
        "limit": 3
    })
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 3. Visualize
    print("\n3. Creating Gotland elevation map...")
    result = server.call_tool("visualize", {
        "item_index": 0,
        "zoom": 10,
        "output_file": "gotland_elevation.html"
    })
    print(result.get("result", result.get("error", "Unknown error")))


def example_lapland_mountains():
    """Example: Explore mountain elevation data in Swedish Lapland"""
    print("\n" + "=" * 70)
    print("Example 3: Lapland Mountain Elevation Data")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register tools
    server.register_tool("list_collections", swedish_elevation_list_collections)
    server.register_tool("search", swedish_elevation_search)
    server.register_tool("visualize", swedish_elevation_visualize)
    
    # 1. Find Kiruna collections (northernmost Sweden)
    print("\n1. Finding Kiruna/Lapland collections...")
    result = server.call_tool("list_collections", {"keyword": "Kiruna"})
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 2. Search for mountain data
    # Kiruna area bbox: [20.0, 67.5, 21.0, 68.0]
    print("\n2. Searching for mountain elevation data...")
    result = server.call_tool("search", {
        "collection": "mhm-76_7",  # Kiruna area
        "bbox": [20.0, 67.8, 20.5, 68.2],
        "limit": 3
    })
    print(result.get("result", result.get("error", "Unknown error")))
    
    # 3. Visualize
    print("\n3. Creating Lapland mountain map...")
    result = server.call_tool("visualize", {
        "item_index": 0,
        "zoom": 9,
        "output_file": "lapland_mountains.html"
    })
    print(result.get("result", result.get("error", "Unknown error")))


def example_custom_exploration():
    """Example: Interactive exploration template"""
    print("\n" + "=" * 70)
    print("Example 4: Custom Exploration Template")
    print("=" * 70)
    
    server = MCPServer()
    
    # Register tools
    server.register_tool("list_collections", swedish_elevation_list_collections)
    server.register_tool("search", swedish_elevation_search)
    server.register_tool("visualize", swedish_elevation_visualize)
    server.register_tool("download", swedish_elevation_download)
    
    print("\nTemplate for exploring any Swedish municipality:")
    print("1. Replace 'YOUR_CITY' with your municipality name")
    print("2. Adjust bbox coordinates for your area")
    print("3. Choose appropriate collection from list\n")
    
    # Example: Malmö (southernmost major city)
    print("Example: Exploring Malmö area...")
    
    result = server.call_tool("list_collections", {"keyword": "Malmö"})
    print("\nAvailable collections:")
    print(result.get("result", "")[:500] + "...")
    
    # Malmö bbox: [12.9, 55.5, 13.1, 55.7]
    result = server.call_tool("search", {
        "collection": "mhm-61_3",
        "bbox": [12.9, 55.5, 13.1, 55.7],
        "limit": 3
    })
    print("\nSearch results:")
    print(result.get("result", result.get("error", "")))


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Swedish Elevation Data MCP Tools - Examples")
    print("Lantmäteriet Markhöjdmodell API")
    print("=" * 70)
    
    # Run examples
    example_stockholm_area()
    example_gotland_island()
    example_lapland_mountains()
    example_custom_exploration()
    
    print("\n" + "=" * 70)
    print("All Examples Complete!")
    print("=" * 70)
    print("\nGenerated HTML maps:")
    print("- stockholm_elevation.html")
    print("- gotland_elevation.html")
    print("- lapland_mountains.html")
    print("\nNext Steps:")
    print("1. Open the HTML files in your browser to view interactive maps")
    print("2. Modify the bbox coordinates to explore different areas")
    print("3. Try different municipalities by changing the 'keyword' parameter")
    print("4. Create your own tools in swedish_elevation_tools.py")
    print("\nFor more info: https://api.lantmateriet.se/stac-hojd/v1/")


if __name__ == "__main__":
    main()