#!/usr/bin/env python3
"""
ESG Matching Demo Script

This script demonstrates how to use the ESG Matching MCP Tool
to match STAC catalog datasets with ESG risk metrics using Claude AI.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Add your Claude API key to ../../config.json

Usage:
    python demo_esg_matching.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from mcp_framework import MCPServer
from esg_matching_tool import (
    esg_load_catalog_tool,
    esg_load_template_tool,
    esg_match_with_claude_tool,
    esg_save_results_tool,
    esg_get_status_tool
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(result: dict):
    """Print a tool result nicely."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(result.get("result", result))


def main():
    """Run the ESG matching demo."""
    print_section("ESG Data Matching Demo")
    print("This demo shows how to use Claude AI to match STAC datasets")
    print("to ESG (Environmental, Social, Governance) risk metrics.")
    
    # Create MCP server and register tools
    print_section("Step 1: Initialize MCP Server")
    server = MCPServer()
    
    # Register all ESG matching tools
    server.register_tool("esg_load_catalog", esg_load_catalog_tool)
    server.register_tool("esg_load_template", esg_load_template_tool)
    server.register_tool("esg_match_with_claude", esg_match_with_claude_tool)
    server.register_tool("esg_save_results", esg_save_results_tool)
    server.register_tool("esg_get_status", esg_get_status_tool)
    
    print(f"\nAvailable tools: {server.list_tools()}")
    
    # Step 2: Load STAC Catalog
    print_section("Step 2: Load STAC Catalog")
    print("Loading Microsoft Planetary Computer catalog...")
    print("Note: Loading ALL public collections (126 out of 255 total)")
    
    result = server.call_tool("esg_load_catalog", {
        "catalog_path": "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json",
        "filter_public": True  # Load only public collections
        # max_collections not specified = load all public collections
    })
    print_result(result)
    
    # Step 3: Load ESG Template
    print_section("Step 3: Load ESG Risk Template")
    print("Loading ESG risk matching template...")
    
    result = server.call_tool("esg_load_template", {
        "template_path": "ESG risk matching template.xlsx"
    })
    print_result(result)
    
    # Step 4: Check Status
    print_section("Step 4: Check Workflow Status")
    result = server.call_tool("esg_get_status", {})
    print_result(result)
    
    # Step 5: Run Claude Matching
    print_section("Step 5: Run Claude AI Matching")
    print("Sending data to Claude for intelligent matching...")
    print("(This may take a minute depending on the amount of data)")
    
    result = server.call_tool("esg_match_with_claude", {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 8000,
        "temperature": 0.1
    })
    print_result(result)
    
    # Check if matching was successful
    if "error" in result:
        print("\n⚠️  Matching failed. Please check:")
        print("   1. Claude API key is set in config.json")
        print("   2. API key has valid credits")
        print("   3. Network connection is available")
        return
    
    # Step 6: Save Results
    print_section("Step 6: Save Results")
    print("Saving matching results to Excel file...")
    
    result = server.call_tool("esg_save_results", {
        "format": "excel"  # Options: "excel", "txt", "json", "md"
    })
    print_result(result)
    
    # Final status
    print_section("Complete!")
    print("✓ ESG matching workflow completed successfully.")
    print("\nCheck the data/TablesMatched folder for output files.")


if __name__ == "__main__":
    main()


