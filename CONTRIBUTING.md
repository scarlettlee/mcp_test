# Contributing Guide

Welcome to the MCP Framework project! This guide will help you get started.

## Project Structure

```
├── README.md              # Project documentation
├── CONTRIBUTING.md        # This file - contribution guidelines
├── mcp_framework.py       # Core framework
├── examples.py            # Usage examples
├── requirements.txt       # Python dependencies
├── tools/                 # Tool modules
│   └── basic_tools.py     # Basic tool examples
├── team1a/                # Team 1A workspace
│   ├── scarlett/          # Scarlett's working directory (contains stac_tools.py example)
│   ├── victor/            # Victor's working directory
│   ├── lamiah/            # Lamiah's working directory
│   ├── jessica/           # Jessica's working directory
│   └── karina/            # Karina's working directory
└── team1b/                # Team 1B workspace
    ├── joey/              # Joey's working directory
    ├── furkan/            # Furkan's working directory
    ├── ashleigh/          # Ashleigh's working directory
    └── neeti/             # Neeti's working directory
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Examples

```bash
python examples.py
```

This will show you how to use the framework and tools.

### 3. Work in Your Directory

**Important**: Each student has their own directory (e.g., `team1a/scarlett/`). 

**Where to create your tools:**
- ✅ **Your personal directory** (e.g., `team1a/scarlett/my_tools.py`) - **This is where you should create your tools**
- ❌ **NOT in `tools/` directory** - This is for shared framework tools only

In your directory:
- Create your own scripts and tools
- Test new tools
- Develop your features
- Keep your work organized

## Creating New Tools

### Tool Format

All tools should follow this format:

```python
def my_tool(args, context):
    """
    Tool description
    
    args: Dictionary with parameters, e.g., {"param1": "value1"}
    context: Shared context (can store data between tool calls)
    
    Returns: String result
    """
    # Your tool logic
    return "Result"
```

### Example: Using STAC Tools for LULC Data

Let's use the existing STAC tools from `team1a/scarlett/stac_tools.py` to work with Land Use/Land Cover (LULC) data. Create a script in your directory:

```python
# team1a/scarlett/my_lulc_script.py
from mcp_framework import MCPServer
import sys
import os

# Add the directory containing stac_tools to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
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
print("Searching for LULC data...")
result = server.call_tool("stac_search", {
    "collection": "io-lulc-annual-v02",
    "bbox": [-122.5, 37.7, -122.3, 37.8],  # California area
    "date_start": "2023-01-01",
    "date_end": "2023-12-31",
    "limit": 3
})
print(result.get("result", "Error"))

# 2. Download the first item
print("\nDownloading LULC data...")
result = server.call_tool("stac_download", {
    "item_index": 0,
    "asset_type": "data",
    "output_dir": "downloads"
})
print(result.get("result", "Error"))

# 3. Visualize on a map
print("\nCreating map visualization...")
result = server.call_tool("stac_visualize", {
    "item_index": 0,
    "zoom": 10,
    "output_file": "lulc_map.html"
})
print(result.get("result", "Error"))
print("\nOpen 'lulc_map.html' in your browser to view the map!")
```

### Steps to Use

**Step 1: Create a new Python file**

In your directory (e.g., `team1a/scarlett/`), create a new file called `my_lulc_script.py`. Copy the code from the example above into this file.

**Step 2: Understand the import**

The line `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))` adds the current directory to Python's search path. This allows Python to find `stac_tools.py` in the same directory.

**Step 3: Run the script**

Open a terminal/command prompt, navigate to your project root directory (where `mcp_framework.py` is located), and run:

```bash
python team1a/scarlett/my_lulc_script.py
```

**Note:** The file `my_lulc_script.py` already exists in `team1a/scarlett/` as an example. You can run it directly, or create your own version in your personal directory.

**What happens:**

1. The script imports the STAC tools from `stac_tools.py`
2. Creates an MCP server
3. Registers the tools (search, download, visualize)
4. Searches for LULC data in California
5. Downloads the first result
6. Creates a map visualization
7. Saves the map as `lulc_map.html`

**Step 4: View the results**

Open `lulc_map.html` in your web browser to see the map with the LULC data.

## Workflow

1. **Read documentation**: Start with `README.md` to understand the project
2. **Run examples**: Run `python examples.py` to see how it works
3. **Study existing tools**: Check `tools/basic_tools.py` and `team1a/scarlett/stac_tools.py` to learn the pattern
4. **Create your tools**: Develop in **your personal directory** (e.g., `team1a/scarlett/`)
5. **Test**: Make sure your code runs without errors

**Remember**: 
- `tools/` directory = Shared framework tools (don't modify unless adding shared features)
- Your directory = Your personal tools and experiments

## Best Practices

- **Write clear code**: Make it easy to understand, add comments when needed
- **Test your code**: Run it to make sure there are no errors
- **Organize files**: **Always keep your work in your own directory** - never modify files in `tools/` unless you're adding shared features
- **Use clear names**: Use meaningful file and variable names

## Team Collaboration

- Communicate with team members
- Share ideas and solutions
- Help each other solve problems
- Ask questions when needed

## Need Help?

1. Check `README.md` to understand the project
2. Run `examples.py` to see examples
3. Look at tool code in the `tools/` directory
4. Ask team members or instructor

## Tips

1. **Start small**: Begin with simple tools, then add more features
2. **Experiment**: Try different approaches, learn from mistakes
3. **Read code**: Study how existing tools are implemented
4. **Ask questions**: Don't hesitate to ask for help

Happy coding! 🚀

