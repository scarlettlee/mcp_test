"""
MCP Tools Package

This package contains shared framework tools.
Students should create their own tools in their personal directories (e.g., team1a/scarlett/).

Note: STAC tools have been moved to team1a/scarlett/stac_tools.py as an example
of student-developed tools. Import them directly from that location.
"""

from .basic_tools import (
    calculator_tool,
    memory_tool,
    weather_tool
)

__all__ = [
    # Basic tools
    'calculator_tool',
    'memory_tool',
    'weather_tool',
]

from .hub_tools import (
    hubs_list,
    hubs_search,
    hubs_download,
    hubs_visualize
)


