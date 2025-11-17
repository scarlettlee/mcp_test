"""
MCP Tools Package

This package contains example MCP tools organized by category.
Students can add their own tools here or create new modules.
"""

from .basic_tools import (
    calculator_tool,
    memory_tool,
    weather_tool
)

from .stac_tools import (
    stac_list_collections_tool,
    stac_search_tool,
    stac_download_tool,
    stac_visualize_tool
)

__all__ = [
    # Basic tools
    'calculator_tool',
    'memory_tool',
    'weather_tool',
    # STAC tools
    'stac_list_collections_tool',
    'stac_search_tool',
    'stac_download_tool',
    'stac_visualize_tool',
]

from .hub_tools import (
    hubs_list,
    hubs_search,
    hubs_download,
    hubs_visualize
)


