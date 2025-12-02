# ESG Data Matching MCP Tool

This MCP tool uses Claude AI to intelligently match ESG (Environmental, Social, Governance) risk metrics with STAC (SpatioTemporal Asset Catalog) datasets.

## Features

✅ **Load STAC Catalogs** - Loads and filters public datasets from STAC catalogs  
✅ **Load ESG Template** - Reads ESG risk matching template from Excel  
✅ **Claude AI Matching** - Uses Claude API for intelligent dataset-to-metric matching  
✅ **Excel Export** - Saves matching results directly to Excel with formatting  
✅ **Multiple Formats** - Supports Excel, Markdown, JSON, and text output  

## Files

- `esg_matching_tool.py` - Main MCP tool with 5 tools
- `demo_esg_matching.py` - Complete workflow demonstration
- `requirements.txt` - Python dependencies
- `ESG_Data_Mapping_Prompt_joey.txt` - Prompt template for Claude
- `README.md` - This file
- `run_demo.bat` - Windows batch script to run demo with specific Python

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or with specific Python environment:

```bash
D:\ProgramData\Anaconda3\envs\streamlit\python.exe -m pip install -r requirements.txt
```

### 2. Configure Claude API Key

Edit `../../config.json` and add your Claude API key:

```json
{
  "claude": {
    "api_key": "your-api-key-here",
    "default_model": "claude-sonnet-4-20250514"
  }
}
```

## Usage

### Quick Start (Windows)

```bash
run_demo.bat
```

### Manual Execution

```bash
python demo_esg_matching.py
```

Or with specific Python:

```bash
D:\ProgramData\Anaconda3\envs\streamlit\python.exe demo_esg_matching.py
```

### Programmatic Usage

```python
from mcp_framework import MCPServer
from team1b.scarlett.esg_matching_tool import *

# Create server
server = MCPServer()
server.register_tool("esg_load_catalog", esg_load_catalog_tool)
server.register_tool("esg_load_template", esg_load_template_tool)
server.register_tool("esg_match_with_claude", esg_match_with_claude_tool)
server.register_tool("esg_save_results", esg_save_results_tool)

# Load data
server.call_tool("esg_load_catalog", {
    "catalog_path": "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json",
    "filter_public": True
})
server.call_tool("esg_load_template", {})

# Run matching
server.call_tool("esg_match_with_claude", {})

# Save to Excel
server.call_tool("esg_save_results", {"format": "excel"})
```

## MCP Tools

### 1. `esg_load_catalog`

Loads a STAC catalog JSON file.

**Arguments:**
- `catalog_path` (str): Path to catalog file (relative to data folder)
- `filter_public` (bool): Filter only public collections (default: True)
- `max_collections` (int): Maximum collections to load (default: None = all)

**Example:**
```python
server.call_tool("esg_load_catalog", {
    "catalog_path": "Catalogs19_27/stac-tags-planetarycomputer.microsoft.com.json",
    "filter_public": True
})
```

### 2. `esg_load_template`

Loads the ESG risk matching template Excel file.

**Arguments:**
- `template_path` (str): Path to template file (default: "ESG risk matching template.xlsx")

**Example:**
```python
server.call_tool("esg_load_template", {})
```

### 3. `esg_match_with_claude`

Uses Claude AI to match datasets to ESG metrics.

**Arguments:**
- `model` (str): Claude model (default: "claude-sonnet-4-20250514")
- `max_tokens` (int): Max response tokens (default: 8000)
- `temperature` (float): Generation temperature (default: 0.1)

**Example:**
```python
server.call_tool("esg_match_with_claude", {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 8000
})
```

### 4. `esg_save_results`

Saves matching results to file.

**Arguments:**
- `format` (str): Output format - "excel", "md", "json", or "txt" (default: "excel")
- `output_path` (str): Custom output path (optional)

**Example:**
```python
server.call_tool("esg_save_results", {"format": "excel"})
```

### 5. `esg_get_status`

Gets current workflow status.

**Example:**
```python
server.call_tool("esg_get_status", {})
```

## Understanding Collection Counts

When loading the Planetary Computer catalog:

- **Total Collections in File**: 255 (all collections in the JSON)
- **Public Collections**: 126 (collections with "accessibility": "Public")
- **Loaded Collections**: 126 by default (loads all public collections)

The tool filters for public collections by default because:
1. They are freely accessible without authentication
2. Better suited for ESG analysis and reporting
3. More reliable for long-term monitoring

To load ALL collections (including private ones):
```python
server.call_tool("esg_load_catalog", {"filter_public": False})
```

## Output

Results are saved to: `../../data/TablesMatched/`

### Excel Format (Default)

The Excel file contains:
- **ESG Matching Sheet**: Complete table with all 33 metrics and matched datasets
- **Metadata Sheet**: Generation info (timestamp, model, catalog, counts)
- **Auto-sized columns**: Columns automatically adjusted for readability

### Other Formats

- **Markdown (.md)**: Formatted markdown with table
- **JSON (.json)**: Complete results with metadata
- **Text (.txt)**: Plain text format

## Troubleshooting

### "Claude API Error"
- Check API key in config.json
- Verify API key has credits
- Check network connection

### "Could not parse table from Claude response"
- Try saving as 'md' format first to see the raw response
- Claude may have returned text instead of a table
- Increase max_tokens if response was truncated

### "Catalog file not found"
- Check the catalog_path is correct
- Ensure data folder exists
- Verify JSON file is in the correct location

## Dependencies

- `anthropic>=0.30.0` - Claude API client
- `pandas>=2.0.0` - Data manipulation and Excel export
- `openpyxl>=3.1.0` - Excel file handling

## Notes

- The tool uses the ESG Data Mapping Prompt created by Joey
- Results quality depends on the Claude model and prompt
- Larger catalogs may take longer to process
- Default temperature (0.1) provides more consistent results

