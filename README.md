# MCP Framework - Model Context Protocol

A simple, educational framework for creating MCP (Model Context Protocol) tools. This framework allows AI models to interact with external tools and resources through a clean, extensible interface.

## What is MCP?

**Model Context Protocol (MCP)** enables AI models to:
- **Call tools**: Execute functions to perform actions (calculations, API calls, etc.)
- **Access resources**: Retrieve data or information when needed
- **Maintain context**: Remember information across interactions

Think of it as giving an AI assistant the ability to:
- Use a calculator (tool)
- Check the weather (tool)
- Remember your name (context/memory)
- Access geospatial data (STAC API tool)

## Project Structure

```
├── mcp_framework.py       # Core framework (MCPServer class)
├── config/                 # API configuration management
│   ├── __init__.py        # Config exports
│   └── api_config.py      # API key and configuration management
├── tools/                  # Tool modules
│   ├── __init__.py        # Tool exports
│   ├── basic_tools.py      # Example tools (calculator, memory, weather)
│   └── stac_tools.py      # STAC API tools (geospatial data)
├── examples.py            # Comprehensive examples
├── requirements.txt       # Python dependencies
├── config.json.example    # Example configuration file
└── README.md              # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Some tools require API keys to function. Configure them in `config.json`:

Copy `config.json.example` to `config.json`:

```bash
cp config.json.example config.json  # On Windows: copy config.json.example config.json
```

Then edit `config.json` and add your API keys:

```json
{
  "weather": {
    "api_key": "your_openweathermap_api_key_here"
  },
  "stac": {
    "api_url": "https://planetarycomputer.microsoft.com/api/stac/v1"
  }
}
```

**Note:** `config.json` is gitignored to protect your API keys.

### 3. Get API Keys

- **Weather API**: Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
- **STAC API**: Microsoft Planetary Computer (default) doesn't require a key, but you can configure custom STAC endpoints

### 4. Run Examples

```bash
python examples.py
```

This demonstrates:
- Basic tools (calculator, memory, weather)
- STAC API tools (geospatial data access)
- Creating custom tools

## Framework Usage

### Basic Usage

```python
from mcp_framework import MCPServer
from tools import calculator_tool, memory_tool

# Create server
server = MCPServer()

# Register tools
server.register_tool("calculator", calculator_tool)
server.register_tool("memory", memory_tool)

# Use tools
result = server.call_tool("calculator", {
    "operation": "add",
    "a": 10,
    "b": 5
})
print(result["result"])  # "10 add 5 = 15"
```

### Creating Your Own Tool

```python
from mcp_framework import MCPServer
from typing import Dict, Any

def my_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """My custom tool."""
    name = args.get("name", "World")
    return f"Hello, {name}!"

# Register and use
server = MCPServer()
server.register_tool("greeting", my_tool)
result = server.call_tool("greeting", {"name": "Student"})
```

## Example Tools Included

### Basic Tools (`tools/basic_tools.py`)

1. **`calculator_tool`**: Simple arithmetic operations
   - Operations: add, subtract, multiply, divide
   - Args: `operation`, `a`, `b`

2. **`memory_tool`**: Store and retrieve data (context persistence example)
   - Actions: store, retrieve
   - Args: `action`, `key`, `value` (for store)

3. **`weather_tool`**: Real weather data from OpenWeatherMap API
   - Args: `city` (required)
   - Requires: API key in config.json: `{"weather": {"api_key": "..."}}`
   - Example: `{"city": "Beijing"}`
   - Returns: Simple format like "Weather in Beijing: Sunny, 25°C"

### STAC API Tools (`team1a/scarlett/stac_tools.py` - Example of student-developed tools)

4. **`stac_list_collections_tool`**: List available geospatial datasets

5. **`stac_search_tool`**: Search for geospatial data
   - Args: `collection`, `bbox`, `date_start`, `date_end`, `limit`
   - Example: `{"collection": "io-lulc-annual-v02", "bbox": [116.2, 39.8, 116.5, 40.0]}`

6. **`stac_download_tool`**: Download geospatial data files
   - Args: `item_index`, `asset_type`, `output_dir`

7. **`stac_visualize_tool`**: Create interactive maps
   - Args: `item_index`, `zoom`, `output_file`, `image_path` (optional)

## STAC API Example

```python
from mcp_framework import MCPServer
import sys
import os

# Import STAC tools from student directory (example)
sys.path.insert(0, os.path.join('team1a', 'scarlett'))
from stac_tools import (
    stac_search_tool,
    stac_download_tool,
    stac_visualize_tool
)

server = MCPServer()
server.register_tool("stac_search", stac_search_tool)
server.register_tool("stac_download", stac_download_tool)
server.register_tool("stac_visualize", stac_visualize_tool)

# Search for Land Use/Land Cover data
result = server.call_tool("stac_search", {
    "collection": "io-lulc-annual-v02",
    "bbox": [-122.5, 37.7, -122.3, 37.8],  # California
    "date_start": "2023-01-01",
    "date_end": "2023-12-31"
})

# Download the data
result = server.call_tool("stac_download", {
    "item_index": 0,
    "asset_type": "data"
})

# Visualize on map
result = server.call_tool("stac_visualize", {
    "item_index": 0,
    "output_file": "map.html"
})
```

## Popular STAC Collections

- **`io-lulc-annual-v02`**: 10m Annual Land Use/Land Cover (9 classes)
- **`sentinel-2-l2a`**: Sentinel-2 satellite imagery (10m resolution)
- **`landsat-c2-l2`**: Landsat satellite imagery (30m resolution)
- **`modis-09a1`**: MODIS surface reflectance data
- **`naip`**: National Agriculture Imagery Program

### Understanding Bounding Boxes

Bounding boxes use: `[min_longitude, min_latitude, max_longitude, max_latitude]`

Example (Beijing):
- Longitude: 116.2°E to 116.5°E
- Latitude: 39.8°N to 40.0°N
- Bbox: `[116.2, 39.8, 116.5, 40.0]`

## Key Concepts

### 1. Tools
Tools are functions with signature: `func(args: Dict[str, Any], context: Dict[str, Any]) -> str`

### 2. Server
The MCPServer class:
- Registers tools
- Executes tools
- Maintains context across calls

### 3. Context
Shared data that persists across tool calls:
```python
server.set_context("key", "value")
value = server.get_context("key")
```

## Extending the Framework

### Adding New Tools

**Important**: There are two places to create tools:

1. **`tools/` directory** - For shared/common tools (like `basic_tools.py` and `stac_tools.py`)
   - These are framework tools available to everyone
   - Only add tools here if they're meant to be shared across the project

2. **Your personal directory** - For your own tools (e.g., `team1a/scarlett/`, `team1b/joey/`)
   - **This is where you should create your own tools**
   - Each student has their own directory to avoid conflicts
   - See `CONTRIBUTING.md` for detailed instructions

**For Students**: Create your tools in your personal directory (e.g., `team1a/scarlett/my_tools.py`)

Example:
```python
# team1a/scarlett/my_tools.py
def my_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    param = args.get("param", "default")
    return f"Result: {param}"
```

Then use it in your scripts:
```python
from mcp_framework import MCPServer
import sys
sys.path.append('team1a/scarlett')  # Add your directory to path
from my_tools import my_tool

server = MCPServer()
server.register_tool("my_tool", my_tool)
```

## Requirements

Core dependencies:
- Python 3.7+

For STAC tools:
- `requests` - HTTP requests
- `planetary-computer` - URL signing for Microsoft Planetary Computer
- `rasterio` - Geospatial raster I/O
- `folium` - Interactive maps
- `numpy` - Numerical operations

## API Configuration

The project includes a simple API configuration system that loads from `config.json`.

### Supported Services

#### Weather API (OpenWeatherMap)

```python
from config import get_api_key

# Get API key from config.json
api_key = get_api_key('weather')
```

Configure in `config.json`:
```json
{
  "weather": {
    "api_key": "your_api_key_here"
  }
}
```

#### STAC API

```python
from config import get_api_url

# Get STAC API URL (defaults to Microsoft Planetary Computer)
stac_url = get_api_url('stac')
```

Configure in `config.json`:
```json
{
  "stac": {
    "api_url": "https://planetarycomputer.microsoft.com/api/stac/v1"
  }
}
```

## Authentication

Microsoft Planetary Computer requires URL signing to access data files. The `planetary-computer` package handles this automatically - no account needed for basic usage.

For other STAC APIs, configure the `STAC_API_URL` and optionally `STAC_API_KEY` in your configuration.

## Learning Path

1. **Start Simple**: Run `examples.py` to see basic tools in action
2. **Study Examples**: Read `tools/basic_tools.py` to understand tool structure
3. **Explore STAC**: Try the STAC tools with different collections
4. **Create Your Own**: Add new tools in your personal directory (e.g., `team1a/scarlett/`)
5. **Extend Framework**: Modify `mcp_framework.py` if needed (advanced)

## Next Steps

- Read through `mcp_framework.py` to understand the core framework
- Study `tools/basic_tools.py` for simple tool examples
- Examine `team1a/scarlett/stac_tools.py` for API integration examples (student-developed tool example)
- **Create your own tools in your personal directory** (see `CONTRIBUTING.md`)
- Experiment with different STAC collections and regions

## License

Educational use - designed for learning and teaching MCP concepts.
