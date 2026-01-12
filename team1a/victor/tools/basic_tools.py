"""
Basic MCP Tools - Example Tools for Learning

These are simple example tools that demonstrate how to create MCP tools.
Students can use these as templates for creating their own tools.
"""

from typing import Dict, Any


def calculator_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    A simple calculator tool.
    
    Args:
        args: Dictionary with:
            - operation: "add", "subtract", "multiply", or "divide"
            - a: First number
            - b: Second number
        context: Server context (not used)
    
    Returns:
        String with calculation result
    """
    operation = args.get("operation")
    try:
        a = float(args.get("a", 0))
        b = float(args.get("b", 0))
    except (ValueError, TypeError):
        return "Error: 'a' and 'b' must be numbers"
    
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Cannot divide by zero"
    }
    
    if operation not in operations:
        return f"Unknown operation: {operation}. Available: {list(operations.keys())}"
    
    result = operations[operation](a, b)
    return f"{a} {operation} {b} = {result}"


def memory_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    A tool that stores and retrieves memories (context persistence example).
    
    Args:
        args: Dictionary with:
            - action: "store" or "retrieve"
            - key: Key name for the memory
            - value: Value to store (only needed for "store" action)
        context: Server context where memories are stored
    
    Returns:
        String with operation result
    """
    action = args.get("action")
    key = args.get("key")
    
    if not key:
        return "Error: 'key' parameter is required"
    
    if action == "store":
        value = args.get("value")
        if value is None:
            return "Error: 'value' parameter required for 'store' action"
        context[f"memory_{key}"] = value
        return f"Stored '{value}' with key '{key}'"
    
    elif action == "retrieve":
        value = context.get(f"memory_{key}", None)
        if value is None:
            return f"No memory found for key '{key}'"
        return f"Retrieved: {value}"
    
    else:
        return f"Unknown action: {action}. Use 'store' or 'retrieve'"


def weather_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Real weather tool using OpenWeatherMap API.
    
    Requires API key in config.json: {"weather": {"api_key": "..."}}
    Get a free API key at: https://openweathermap.org/api
    
    Args:
        args: Dictionary with:
            - city: City name to get weather for
        context: Server context (not used)
    
    Returns:
        String with weather information in simple format
    """
    import requests
    from config import get_api_key
    
    city = args.get("city", "Unknown")
    
    # Get API key from configuration
    api_key = get_api_key('weather')
    
    if not api_key:
        return f"Weather data not available for: {city} (API key not configured)"
    
    # OpenWeatherMap API endpoint
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    try:
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract simple weather information
        temp = int(data["main"]["temp"])
        description = data["weather"][0]["description"].title()
        
        return f"Weather in {city}: {description}, {temp}°C"
        
    except Exception:
        return f"Weather data not available for: {city}"

