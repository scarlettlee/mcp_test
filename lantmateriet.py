"""
Swedish Elevation Data (Markhöjdmodell) MCP Tools

Tools for accessing and visualizing Swedish elevation data from Lantmäteriet's STAC API.
"""

import requests
import json
from typing import Dict, Any
import folium
from datetime import datetime


def swedish_elevation_list_collections(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    List all available Swedish elevation (Markhöjdmodell) collections.
    
    Args:
        args: Optional filters like 'keyword' to filter by municipality
        context: Server context
    
    Returns:
        String with formatted collection information
    """
    base_url = "https://api.lantmateriet.se/stac-hojd/v1"
    
    try:
        # Fetch collections
        response = requests.get(f"{base_url}/collections")
        response.raise_for_status()
        data = response.json()
        
        collections = data.get("collections", [])
        
        # Filter by keyword if provided
        keyword = args.get("keyword", "").lower()
        if keyword:
            collections = [c for c in collections if keyword in " ".join(c.get("keywords", [])).lower()]
        
        # Store in context for later use
        context["collections"] = collections
        
        # Format output
        result = f"Found {len(collections)} elevation model collections:\n\n"
        
        for i, collection in enumerate(collections[:10]):  # Show first 10
            result += f"{i+1}. {collection['id']}\n"
            result += f"   Title: {collection.get('title', 'N/A')}\n"
            
            # Get spatial extent
            bbox = collection.get("extent", {}).get("spatial", {}).get("bbox", [[]])[0]
            if bbox:
                result += f"   Bbox: [{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]\n"
            
            # Get temporal extent
            temporal = collection.get("extent", {}).get("temporal", {}).get("interval", [[]])[0]
            if temporal:
                result += f"   Time range: {temporal[0]} to {temporal[1]}\n"
            
            # Show some keywords (municipalities)
            keywords = collection.get("keywords", [])[:3]
            if keywords:
                result += f"   Municipalities: {', '.join(keywords)}\n"
            
            result += "\n"
        
        if len(collections) > 10:
            result += f"... and {len(collections) - 10} more collections\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching collections: {str(e)}"


def swedish_elevation_search(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Search for elevation data in a specific collection and area.
    
    Args:
        args: {
            "collection": Collection ID (e.g., "mhm-66_6"),
            "bbox": [min_lon, min_lat, max_lon, max_lat],
            "date_start": Optional start date (ISO format),
            "date_end": Optional end date (ISO format),
            "limit": Maximum number of items to return (default: 10)
        }
        context: Server context
    
    Returns:
        String with search results
    """
    base_url = "https://api.lantmateriet.se/stac-hojd/v1"
    
    collection = args.get("collection")
    if not collection:
        return "Error: 'collection' parameter is required"
    
    bbox = args.get("bbox")
    if not bbox or len(bbox) != 4:
        return "Error: 'bbox' parameter must be [min_lon, min_lat, max_lon, max_lat]"
    
    try:
        # Build search parameters
        params = {
            "bbox": ",".join(map(str, bbox)),
            "limit": args.get("limit", 10)
        }
        
        # Add datetime filter if provided
        date_start = args.get("date_start")
        date_end = args.get("date_end")
        if date_start and date_end:
            params["datetime"] = f"{date_start}/{date_end}"
        
        # Search the collection
        url = f"{base_url}/collections/{collection}/items"
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("features", [])
        
        # Store items in context for visualization
        context["search_results"] = items
        context["search_collection"] = collection
        
        # Format output
        result = f"Found {len(items)} elevation data items in collection '{collection}':\n\n"
        
        for i, item in enumerate(items):
            result += f"{i+1}. Item ID: {item['id']}\n"
            
            # Get properties
            props = item.get("properties", {})
            result += f"   Date: {props.get('datetime', 'N/A')}\n"
            
            # Get bbox
            item_bbox = item.get("bbox")
            if item_bbox:
                result += f"   Bbox: [{item_bbox[0]:.3f}, {item_bbox[1]:.3f}, {item_bbox[2]:.3f}, {item_bbox[3]:.3f}]\n"
            
            # List available assets
            assets = item.get("assets", {})
            result += f"   Assets: {', '.join(assets.keys())}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error searching collection: {str(e)}"


def swedish_elevation_visualize(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Create an interactive map visualization of elevation data search results.
    
    Args:
        args: {
            "item_index": Index of item to visualize (default: 0),
            "zoom": Initial zoom level (default: 10),
            "output_file": Output HTML filename (default: "elevation_map.html")
        }
        context: Server context (uses stored search results)
    
    Returns:
        Status message
    """
    # Get search results from context
    items = context.get("search_results", [])
    if not items:
        return "Error: No search results found. Run swedish_elevation_search first."
    
    item_index = args.get("item_index", 0)
    if item_index >= len(items):
        return f"Error: Item index {item_index} out of range (0-{len(items)-1})"
    
    item = items[item_index]
    output_file = args.get("output_file", "elevation_map.html")
    zoom = args.get("zoom", 10)
    
    try:
        # Get item bbox for map center
        bbox = item.get("bbox")
        if not bbox:
            return "Error: Item has no bounding box"
        
        # Calculate center
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles="OpenStreetMap"
        )
        
        # Add bounding box rectangle
        folium.Rectangle(
            bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
            color="red",
            fill=True,
            fill_opacity=0.2,
            popup=f"Elevation Data: {item['id']}"
        ).add_to(m)
        
        # Add marker at center
        props = item.get("properties", {})
        popup_text = f"""
        <b>Item ID:</b> {item['id']}<br>
        <b>Collection:</b> {context.get('search_collection', 'N/A')}<br>
        <b>Date:</b> {props.get('datetime', 'N/A')}<br>
        <b>Bbox:</b> [{bbox[0]:.3f}, {bbox[1]:.3f}, {bbox[2]:.3f}, {bbox[3]:.3f}]<br>
        <b>Assets:</b> {', '.join(item.get('assets', {}).keys())}
        """
        
        folium.Marker(
            [center_lat, center_lon],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        # Add all items from search as light overlays
        for idx, search_item in enumerate(items):
            if idx == item_index:
                continue
            
            item_bbox = search_item.get("bbox")
            if item_bbox:
                folium.Rectangle(
                    bounds=[[item_bbox[1], item_bbox[0]], [item_bbox[3], item_bbox[2]]],
                    color="blue",
                    fill=True,
                    fill_opacity=0.1,
                    popup=f"Item: {search_item['id']}"
                ).add_to(m)
        
        # Save map
        m.save(output_file)
        
        return f"✓ Map saved to '{output_file}'\n\nVisualized item {item_index}: {item['id']}\nCenter: ({center_lat:.4f}, {center_lon:.4f})\nTotal items on map: {len(items)}"
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}"


def swedish_elevation_download(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Get download information for elevation data assets.
    
    Args:
        args: {
            "item_index": Index of item (default: 0),
            "asset_type": Asset type to download (e.g., "data", "metadata")
        }
        context: Server context (uses stored search results)
    
    Returns:
        Download information and URLs
    """
    items = context.get("search_results", [])
    if not items:
        return "Error: No search results found. Run swedish_elevation_search first."
    
    item_index = args.get("item_index", 0)
    if item_index >= len(items):
        return f"Error: Item index {item_index} out of range (0-{len(items)-1})"
    
    item = items[item_index]
    assets = item.get("assets", {})
    
    if not assets:
        return "Error: No assets found for this item"
    
    # Format asset information
    result = f"Assets available for item '{item['id']}':\n\n"
    
    asset_type = args.get("asset_type")
    
    for key, asset in assets.items():
        if asset_type and key != asset_type:
            continue
            
        result += f"Asset: {key}\n"
        result += f"  Title: {asset.get('title', 'N/A')}\n"
        result += f"  Type: {asset.get('type', 'N/A')}\n"
        result += f"  URL: {asset.get('href', 'N/A')}\n"
        
        # Show file size if available
        file_size = asset.get('file:size')
        if file_size:
            size_mb = file_size / (1024 * 1024)
            result += f"  Size: {size_mb:.2f} MB\n"
        
        result += "\n"
    
    if asset_type and asset_type not in assets:
        result += f"\nAsset type '{asset_type}' not found. Available types: {', '.join(assets.keys())}\n"
    
    return result