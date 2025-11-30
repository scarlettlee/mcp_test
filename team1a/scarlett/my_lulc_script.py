"""
Example: Using STAC Tools for LULC Data

This script demonstrates how to use the STAC tools to work with 
Land Use/Land Cover (LULC) data.

Run this script from the project root directory:
    python team1a/scarlett/my_lulc_script.py
"""

import sys
import os

# Add project root directory to path (two levels up from this file)
# This allows Python to find mcp_framework.py and other modules
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))

# Now we can import from the project root
from mcp_framework import MCPServer

# Add the current directory to path to find stac_tools.py in the same directory
sys.path.insert(0, os.path.dirname(__file__))
from stac_tools import (
    stac_search_tool,
    stac_download_tool,
    stac_visualize_tool
)

# Create server
server = MCPServer()

# Register STAC tools
server.register_tool("stac_search", stac_search_tool)
server.register_tool("stac_download", stac_download_tool)
server.register_tool("stac_visualize", stac_visualize_tool)

# 1. Search for LULC data in California
print("=" * 70)
print("Step 1: Searching for LULC data...")
print("=" * 70)
result = server.call_tool("stac_search", {
    "collection": "io-lulc-annual-v02",
    "bbox": [-122.5, 37.7, -122.3, 37.8],  # California area
    "date_start": "2023-01-01",
    "date_end": "2023-12-31",
    "limit": 3
})
print(result.get("result", "Error"))

# 2. Download the first item
print("\n" + "=" * 70)
print("Step 2: Downloading LULC data...")
print("=" * 70)
result = server.call_tool("stac_download", {
    "item_index": 0,
    "asset_type": "data",
    "output_dir": "downloads"
})
print(result.get("result", "Error"))

# 3. Visualize on a map
print("\n" + "=" * 70)
print("Step 3: Creating map visualization...")
print("=" * 70)

# Save the map in the student's own directory
script_dir = os.path.dirname(__file__)
output_file = os.path.join(script_dir, "lulc_map.html")

result = server.call_tool("stac_visualize", {
    "item_index": 0,
    "zoom": 10,
    "output_file": output_file
})
print(result.get("result", "Error"))

print("\n" + "=" * 70)
print(f"Done! Open '{output_file}' in your browser to view the map!")
print("=" * 70)

