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

from .earth_search_tools import (
    earth_search_list_collections_tool,
    earth_search_search_tool,
    earth_search_download_tool,
    earth_search_visualize_tool
)

# Catalog loader functions (for dynamic catalog management)
try:
    from .catalog_loader import (
        load_catalog,
        get_api_endpoint,
        list_collections,
        get_collection_info,
        get_suggested_date_range,
        get_available_assets,
        validate_collection
    )
    CATALOG_LOADER_AVAILABLE = True
except ImportError:
    CATALOG_LOADER_AVAILABLE = False

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
    # Earth Search tools
    'earth_search_list_collections_tool',
    'earth_search_search_tool',
    'earth_search_download_tool',
    'earth_search_visualize_tool',
]

# Add catalog loader functions if available
if CATALOG_LOADER_AVAILABLE:
    __all__.extend([
        'load_catalog',
        'get_api_endpoint',
        'list_collections',
        'get_collection_info',
        'get_suggested_date_range',
        'get_available_assets',
        'validate_collection',
    ])

