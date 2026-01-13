"""
ESG Data Matching MCP Tool - Claude API Integration

This MCP tool uses Claude API to match ESG risk metrics with STAC data catalogs.
It reads the ESG risk matching template and STAC catalog data, then uses Claude
to intelligently map datasets to ESG metrics based on relevance categories.

Author: Team 1B - Scarlett
Required packages: anthropic, pandas, openpyxl

Usage:
    from mcp_framework import MCPServer
    from esg_matching_tool import (
        esg_load_catalog_tool,
        esg_load_template_tool,
        esg_match_with_claude_tool,
        esg_save_results_tool
    )
    
    server = MCPServer()
    server.register_tool("esg_load_catalog", esg_load_catalog_tool)
    server.register_tool("esg_load_template", esg_load_template_tool)
    server.register_tool("esg_match_with_claude", esg_match_with_claude_tool)
    server.register_tool("esg_save_results", esg_save_results_tool)
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def _get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def _load_prompt_template() -> str:
    """Load the ESG Data Mapping Prompt from file."""
    prompt_file = Path(__file__).parent / "ESG_Data_Mapping_Prompt_joey.txt"
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")


def esg_load_catalog_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Load a STAC catalog JSON file for ESG matching.
    
    Args:
        args: Dictionary with:
            - catalog_path: Path to the STAC catalog JSON file (relative to data folder)
                           Default: "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json"
            - filter_public: Filter only public collections (default: True)
            - max_collections: Maximum number of collections to load (default: None = all)
        context: Server context for storing loaded data
    
    Returns:
        String with summary of loaded catalog
    """
    try:
        project_root = _get_project_root()
        data_folder = project_root / "data"
        
        # Get catalog path
        catalog_path = args.get(
            "catalog_path", 
            "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json"
        )
        full_path = data_folder / catalog_path
        
        if not full_path.exists():
            return f"Error: Catalog file not found: {full_path}"
        
        # Load catalog
        with open(full_path, 'r', encoding='utf-8') as f:
            catalog_data = json.load(f)
        
        # Extract collections
        all_collections = catalog_data.get("collections", [])
        total_collections = len(all_collections)
        
        # Filter for public collections if requested (default: True)
        filter_public = args.get("filter_public", True)
        if filter_public:
            collections = [col for col in all_collections if col.get("accessibility") == "Public"]
            public_count = len(collections)
        else:
            collections = all_collections
            public_count = len([col for col in all_collections if col.get("accessibility") == "Public"])
        
        # Apply max_collections limit if specified
        max_collections = args.get("max_collections")
        if max_collections:
            collections = collections[:int(max_collections)]
        
        # Create summaries for Claude
        collection_summaries = []
        for col in collections:
            summary = {
                "id": col.get("id", "unknown"),
                "title": col.get("title", "No title"),
                "description": col.get("description", "")[:500],  # Truncate long descriptions
                "keywords": col.get("keywords", []),
                "providers": [p.get("name", "") for p in col.get("providers", [])],
                "accessibility": col.get("accessibility", "Unknown")
            }
            
            # Add cube variables if available (useful for ESG matching)
            if "cube:variables" in col:
                variables = list(col["cube:variables"].keys())[:10]  # Top 10 variables
                summary["variables"] = variables
            
            collection_summaries.append(summary)
        
        # Store in context
        context["stac_catalog"] = {
            "source_file": str(catalog_path),
            "stac_api_url": catalog_data.get("stacApiUrl", "unknown"),
            "total_collections": total_collections,
            "public_collections": public_count,
            "loaded_collections": len(collection_summaries),
            "collections": collection_summaries
        }
        
        # Extract catalog name from filename
        catalog_name = Path(catalog_path).stem.replace("stac-tags-", "")
        context["catalog_name"] = catalog_name
        
        result = {
            "status": "success",
            "catalog_name": catalog_name,
            "source": str(catalog_path),
            "total_collections": total_collections,
            "public_collections": public_count,
            "loaded_collections": len(collection_summaries),
            "filter_applied": "Public collections only" if filter_public else "All collections",
            "sample_collections": [c["id"] for c in collection_summaries[:5]]
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return f"Error loading catalog: {str(e)}"


def esg_load_template_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Load the ESG risk matching template Excel file.
    
    Args:
        args: Dictionary with:
            - template_path: Path to template file (relative to data folder)
                           Default: "ESG risk matching template.xlsx"
        context: Server context for storing template data
    
    Returns:
        String with summary of loaded template
    """
    if not PANDAS_AVAILABLE:
        return "Error: pandas package required. Install with: pip install pandas openpyxl"
    
    try:
        project_root = _get_project_root()
        data_folder = project_root / "data"
        
        # Get template path
        template_path = args.get("template_path", "ESG risk matching template.xlsx")
        full_path = data_folder / template_path
        
        if not full_path.exists():
            return f"Error: Template file not found: {full_path}"
        
        # Load Excel file
        df = pd.read_excel(full_path)
        
        # Convert to list of metrics
        metrics = df.to_dict(orient='records')
        
        # Store in context
        context["esg_template"] = {
            "source_file": str(template_path),
            "columns": list(df.columns),
            "total_metrics": len(metrics),
            "metrics": metrics
        }
        
        result = {
            "status": "success",
            "source": str(template_path),
            "columns": list(df.columns),
            "total_metrics": len(metrics),
            "sample_metrics": [
                {k: v for k, v in m.items() if pd.notna(v)} 
                for m in metrics[:3]
            ]
        }
        
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return f"Error loading template: {str(e)}"


def esg_match_with_claude_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Use Claude API to match ESG metrics with STAC catalog datasets.
    
    This tool sends the ESG template and STAC catalog to Claude for intelligent
    matching based on the ESG Data Mapping Prompt.
    
    Args:
        args: Dictionary with:
            - model: Claude model to use (default: "claude-sonnet-4-20250514")
            - max_tokens: Maximum response tokens (default: 8000)
            - temperature: Temperature for generation (default: 0.1)
        context: Server context containing loaded catalog and template
    
    Returns:
        String with matching results
    """
    if not ANTHROPIC_AVAILABLE:
        return "Error: anthropic package required. Install with: pip install anthropic"
    
    # Check if catalog and template are loaded
    if "stac_catalog" not in context:
        return "Error: No catalog loaded. Please run esg_load_catalog first."
    
    if "esg_template" not in context:
        return "Error: No template loaded. Please run esg_load_template first."
    
    try:
        from config import get_api_key
        
        # Get Claude API key
        api_key = get_api_key('claude')
        if not api_key:
            return "Error: Claude API key not configured. Add 'claude' section to config.json"
        
        # Load prompt template
        try:
            base_prompt = _load_prompt_template()
        except FileNotFoundError as e:
            return f"Error: {str(e)}"
        
        # Get parameters
        model = args.get("model", "claude-sonnet-4-20250514")
        max_tokens = int(args.get("max_tokens", 8000))
        temperature = float(args.get("temperature", 0.1))
        
        # Prepare catalog data for prompt
        catalog_data = context["stac_catalog"]
        catalog_name = context.get("catalog_name", "unknown")
        
        # Create catalog summary for Claude
        catalog_summary = f"""
## STAC Catalog: {catalog_name}
Source: {catalog_data['stac_api_url']}
Total Collections in File: {catalog_data['total_collections']}
Public Collections: {catalog_data['public_collections']}
Collections Being Analyzed: {catalog_data['loaded_collections']}

### Available Datasets:
"""
        for col in catalog_data["collections"]:
            catalog_summary += f"""
**{col['id']}** - {col['title']}
Description: {col['description'][:300]}...
Keywords: {', '.join(col.get('keywords', [])[:5])}
Variables: {', '.join(col.get('variables', [])[:5])}
---
"""
        
        # Prepare template data
        template_data = context["esg_template"]
        template_summary = f"""
## ESG Risk Matching Template
Total Metrics: {template_data['total_metrics']}
Columns: {', '.join(template_data['columns'])}

### Metrics to Match:
"""
        for i, metric in enumerate(template_data["metrics"], 1):
            # Clean metric data (remove NaN values)
            clean_metric = {k: v for k, v in metric.items() if pd.notna(v)}
            template_summary += f"{i}. {json.dumps(clean_metric)}\n"
        
        # Construct the full prompt
        user_message = f"""
{base_prompt}

---

# DATA PROVIDED FOR MATCHING

{catalog_summary}

{template_summary}

---

Please analyze the above STAC catalog and match datasets to the ESG metrics according to the prompt instructions.
Format your output as a structured table that can be imported into Excel.
"""
        
        # Call Claude API
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Extract response
        response_text = message.content[0].text
        
        # Store results in context
        context["matching_results"] = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "catalog_name": catalog_name,
            "metrics_count": template_data['total_metrics'],
            "collections_count": catalog_data['loaded_collections'],
            "response": response_text
        }
        
        result = {
            "status": "success",
            "model": model,
            "catalog": catalog_name,
            "metrics_matched": template_data['total_metrics'],
            "datasets_analyzed": catalog_data['loaded_collections'],
            "response_length": len(response_text),
            "message": "Matching complete. Use esg_save_results to export to Excel.",
            "preview": response_text[:1000] + "..." if len(response_text) > 1000 else response_text
        }
        
        return json.dumps(result, indent=2)
    
    except anthropic.APIError as e:
        return f"Claude API Error: {str(e)}"
    except Exception as e:
        return f"Error during matching: {str(e)}"


def esg_save_results_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Save the ESG matching results to a file.
    
    Args:
        args: Dictionary with:
            - output_path: Path for output file (relative to data/TablesMatched folder)
                          Default: auto-generated based on catalog name and timestamp
            - format: Output format - "txt", "json", "md", or "excel" (default: "excel")
        context: Server context containing matching results
    
    Returns:
        String with save confirmation
    """
    if "matching_results" not in context:
        return "Error: No matching results found. Please run esg_match_with_claude first."
    
    try:
        project_root = _get_project_root()
        output_folder = project_root / "data" / "TablesMatched"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        results = context["matching_results"]
        
        # Generate filename if not provided
        output_format = args.get("format", "excel")
        if "output_path" in args:
            output_path = args["output_path"]
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            catalog_name = results.get("catalog_name", "unknown")
            ext = "xlsx" if output_format == "excel" else output_format
            output_path = f"ESG_Matching_{catalog_name}_{timestamp}.{ext}"
        
        full_path = output_folder / output_path
        
        # Prepare content based on format
        if output_format == "excel":
            if not PANDAS_AVAILABLE:
                return "Error: pandas package required for Excel export. Install with: pip install pandas openpyxl"
            
            # Parse the Claude response to extract table data
            response_text = results['response']
            
            # Try to parse markdown table from response
            df = _parse_markdown_table(response_text)
            
            if df is None:
                return "Error: Could not parse table from Claude response. Try saving as 'md' or 'txt' format instead."
            
            # Save to Excel with formatting
            with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='ESG Matching', index=False)
                
                # Add metadata sheet
                metadata_df = pd.DataFrame({
                    'Property': ['Generated', 'Model', 'Catalog', 'Metrics Matched', 'Collections Analyzed'],
                    'Value': [
                        results['timestamp'],
                        results['model'],
                        results['catalog_name'],
                        results['metrics_count'],
                        results['collections_count']
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                
                # Auto-adjust column widths
                workbook = writer.book
                worksheet = writer.sheets['ESG Matching']
                
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            result = {
                "status": "success",
                "output_file": str(full_path),
                "format": "Excel",
                "rows": len(df),
                "columns": len(df.columns)
            }
            
        elif output_format == "json":
            content = json.dumps(results, indent=2)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            result = {
                "status": "success",
                "output_file": str(full_path),
                "format": output_format,
                "size_bytes": len(content)
            }
            
        elif output_format == "md":
            content = f"""# ESG Data Matching Results

**Generated:** {results['timestamp']}
**Model:** {results['model']}
**Catalog:** {results['catalog_name']}
**Metrics Matched:** {results['metrics_count']}
**Collections Analyzed:** {results['collections_count']}

---

## Matching Results

{results['response']}
"""
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            result = {
                "status": "success",
                "output_file": str(full_path),
                "format": output_format,
                "size_bytes": len(content)
            }
            
        else:  # txt format
            content = f"""ESG Data Matching Results
{'='*50}
Generated: {results['timestamp']}
Model: {results['model']}
Catalog: {results['catalog_name']}
Metrics Matched: {results['metrics_count']}
Collections Analyzed: {results['collections_count']}
{'='*50}

{results['response']}
"""
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            result = {
                "status": "success",
                "output_file": str(full_path),
                "format": output_format,
                "size_bytes": len(content)
            }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return f"Error saving results: {str(e)}"


def _parse_markdown_table(text: str) -> Optional[pd.DataFrame]:
    """
    Parse a markdown table from text and convert to DataFrame.
    
    Args:
        text: Text containing a markdown table
    
    Returns:
        DataFrame or None if parsing fails
    """
    if not PANDAS_AVAILABLE:
        return None
    
    try:
        # Find table in text (lines starting with |)
        lines = text.split('\n')
        table_lines = [line.strip() for line in lines if line.strip().startswith('|')]
        
        if len(table_lines) < 3:  # Need at least header, separator, and one data row
            return None
        
        # Parse header
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]  # Remove empty first/last
        
        # Skip separator line (the one with dashes)
        data_lines = [line for line in table_lines[2:] if not line.strip().startswith('|--')]
        
        # Parse data rows
        data = []
        for line in data_lines:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) == len(headers):
                data.append(cells)
        
        if not data:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Clean up empty cells
        df = df.replace('', pd.NA)
        
        return df
        
    except Exception as e:
        print(f"Warning: Could not parse markdown table: {e}")
        return None


def esg_get_status_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Get the current status of ESG matching workflow.
    
    Shows what data is currently loaded in context.
    
    Args:
        args: Not used
        context: Server context to check
    
    Returns:
        String with current status
    """
    status = {
        "catalog_loaded": "stac_catalog" in context,
        "template_loaded": "esg_template" in context,
        "matching_complete": "matching_results" in context,
    }
    
    if "stac_catalog" in context:
        status["catalog_info"] = {
            "name": context.get("catalog_name", "unknown"),
            "collections": context["stac_catalog"]["loaded_collections"]
        }
    
    if "esg_template" in context:
        status["template_info"] = {
            "metrics": context["esg_template"]["total_metrics"],
            "columns": context["esg_template"]["columns"]
        }
    
    if "matching_results" in context:
        status["results_info"] = {
            "timestamp": context["matching_results"]["timestamp"],
            "model": context["matching_results"]["model"]
        }
    
    return json.dumps(status, indent=2)


# Example usage and testing
if __name__ == "__main__":
    print("ESG Matching Tool - Example Usage")
    print("=" * 50)
    
    # Check dependencies
    print(f"\nDependencies:")
    print(f"  - pandas: {'✓ Available' if PANDAS_AVAILABLE else '✗ Not installed'}")
    print(f"  - anthropic: {'✓ Available' if ANTHROPIC_AVAILABLE else '✗ Not installed'}")
    
    if not PANDAS_AVAILABLE or not ANTHROPIC_AVAILABLE:
        print("\nInstall missing dependencies:")
        print("  pip install pandas openpyxl anthropic")
        sys.exit(1)
    
    # Add parent to path for imports
    sys.path.insert(0, str(_get_project_root()))
    
    from mcp_framework import MCPServer
    
    # Create server and register tools
    server = MCPServer()
    server.register_tool("esg_load_catalog", esg_load_catalog_tool)
    server.register_tool("esg_load_template", esg_load_template_tool)
    server.register_tool("esg_match_with_claude", esg_match_with_claude_tool)
    server.register_tool("esg_save_results", esg_save_results_tool)
    server.register_tool("esg_get_status", esg_get_status_tool)
    
    print("\nRegistered tools:", server.list_tools())
    
    # Example workflow (uncomment to test with actual API key)
    # print("\n--- Loading Catalog ---")
    # result = server.call_tool("esg_load_catalog", {
    #     "catalog_path": "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json",
    #     "filter_public": True  # Load only public collections (126 out of 255)
    # })
    # print(result)
    
    # print("\n--- Loading Template ---")
    # result = server.call_tool("esg_load_template", {})
    # print(result)
    
    # print("\n--- Check Status ---")
    # result = server.call_tool("esg_get_status", {})
    # print(result)
    
    # print("\n--- Run Claude Matching ---")
    # result = server.call_tool("esg_match_with_claude", {
    #     "model": "claude-sonnet-4-20250514",
    #     "max_tokens": 8000
    # })
    # print(result)
    
    # print("\n--- Save Results to Excel ---")
    # result = server.call_tool("esg_save_results", {"format": "excel"})
    # print(result)
    
    print("\n" + "=" * 50)
    print("To use this tool:")
    print("1. Add your Claude API key to config.json")
    print("2. Uncomment the example workflow above")
    print("3. Run this script")


