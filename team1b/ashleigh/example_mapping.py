"""
Example: Using the ESG Mapping Tool with MCP Framework

This script demonstrates how to:
1. Register the ESG mapping tool with MCP
2. Process STAC catalog data against SASB metrics
3. Generate Excel-ready CSV output
"""

import sys
from pathlib import Path

# Import MCP framework (adjust path as needed for your project structure)
# from mcp_framework import MCPServer

# For standalone demo without full MCP framework
class SimpleMCPServer:
    """Simplified MCP server for demonstration."""
    def __init__(self):
        self.tools = {}
        self.context = {}
    
    def register_tool(self, name: str, func):
        self.tools[name] = func
        print(f"✓ Registered tool: {name}")
    
    def call_tool(self, name: str, args: dict):
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}
        return {"result": self.tools[name](args, self.context)}
    
    def get_context(self, key: str):
        return self.context.get(key)


# Import our ESG mapping tool
from esg_mapping_tool import esg_mapping_tool


def main():
    """Main example demonstrating ESG mapping workflow."""
    
    print("=" * 70)
    print("ESG DATA MAPPING TOOL - MCP FRAMEWORK EXAMPLE")
    print("=" * 70)
    print()
    
    # Initialize MCP server
    server = SimpleMCPServer()
    
    # Register the ESG mapping tool
    server.register_tool("esg_mapper", esg_mapping_tool)
    print()
    
    # Example 1: Basic mapping with provided files
    print("Example 1: Basic ESG Mapping")
    print("-" * 70)
    
    result = server.call_tool("esg_mapper", {
        "sasb_csv_path": "SASB_RIsk_-_Sheet1.csv",
        "stac_json_path": "stac-tags-dop_stac_lgln_niedersachsen_de.json",
        "output_csv_path": "esg_mapping_output.csv"
    })
    
    print(result["result"])
    print()
    
    # Example 2: Custom output location
    print("Example 2: Custom Output Location")
    print("-" * 70)
    
    result = server.call_tool("esg_mapper", {
        "sasb_csv_path": "SASB_RIsk_-_Sheet1.csv",
        "stac_json_path": "stac-tags-dop_stac_lgln_niedersachsen_de.json",
        "output_csv_path": "results/software_it_esg_mapping.csv"
    })
    
    print(result["result"])
    print()
    
    # Show context usage
    print("Example 3: Accessing Output from Context")
    print("-" * 70)
    last_output = server.get_context("last_esg_output")
    if last_output:
        print(f"Last generated file: {last_output}")
    print()
    
    # Example 4: Error handling
    print("Example 4: Error Handling - Missing File")
    print("-" * 70)
    
    result = server.call_tool("esg_mapper", {
        "sasb_csv_path": "nonexistent.csv",
        "stac_json_path": "stac-tags-dop_stac_lgln_niedersachsen_de.json"
    })
    
    print(result["result"])
    print()
    
    print("=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("1. Open the generated CSV file in Excel")
    print("2. Review the dataset mappings by relevance category")
    print("3. Adjust the mapping logic in esg_mapping_tool.py as needed")
    print("4. Create additional tools for specific STAC catalogs")


def quick_test():
    """Quick test with actual files if available."""
    
    print("\nQUICK TEST MODE")
    print("=" * 70)
    
    # Check if files exist
    sasb_file = Path("SASB_RIsk_-_Sheet1.csv")
    stac_file = Path("stac-tags-dop_stac_lgln_niedersachsen_de.json")
    
    if not sasb_file.exists():
        print(f"⚠ SASB file not found: {sasb_file}")
        print("  Please ensure SASB_RIsk_-_Sheet1.csv is in the current directory")
        return
    
    if not stac_file.exists():
        print(f"⚠ STAC file not found: {stac_file}")
        print("  Please ensure stac-tags-dop_stac_lgln_niedersachsen_de.json is in the current directory")
        return
    
    # Run the tool
    server = SimpleMCPServer()
    server.register_tool("esg_mapper", esg_mapping_tool)
    
    print("\n✓ Files found! Running mapping...")
    print()
    
    result = server.call_tool("esg_mapper", {
        "sasb_csv_path": str(sasb_file),
        "stac_json_path": str(stac_file),
        "output_csv_path": "quick_test_output.csv"
    })
    
    print(result["result"])


if __name__ == "__main__":
    # Run quick test if files are available, otherwise show examples
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        quick_test()
    else:
        main()
        print("\nTip: Run with --test flag to quick test with actual files")
        print("     python example_esg_mapping.py --test")