"""
BAFU STAC Tools - Swiss Federal Office for the Environment

Tools for accessing and visualizing geospatial data from the Swiss Federal
Office for the Environment's STAC catalog.

Author: Lamiah Khan
Date: November 2024
"""

from typing import Dict, Any
import requests
import json
import os
from datetime import datetime


def bafu_list_collections_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    List available collections from BAFU STAC catalog.
    
    Args:
        args: Dictionary with optional:
            - limit: Maximum number of collections to display (default: 10)
            - search_term: Filter collections by keyword in title/description
        context: Server context for storing collection data
    
    Returns:
        String with formatted list of available collections
    """
    stac_url = "https://data.geo.admin.ch/api/stac/v1/collections"
    limit = args.get("limit", 10)
    search_term = args.get("search_term", "").lower()
    
    try:
        response = requests.get(stac_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        collections = data.get("collections", [])
        
        # Filter by search term if provided
        if search_term:
            collections = [c for c in collections 
                         if search_term in c.get("title", "").lower() 
                         or search_term in c.get("description", "").lower()]
        
        # Store in context for later use
        context["bafu_collections"] = collections
        
        # Format output
        result = f"Found {len(collections)} BAFU collections"
        if search_term:
            result += f" matching '{search_term}'"
        result += ":\n\n"
        
        for i, collection in enumerate(collections[:limit]):
            coll_id = collection.get("id", "Unknown")
            title = collection.get("title", "No title")
            description = collection.get("description", "")[:150]
            
            result += f"{i+1}. {title}\n"
            result += f"   ID: {coll_id}\n"
            result += f"   Description: {description}...\n\n"
        
        if len(collections) > limit:
            result += f"\n(Showing {limit} of {len(collections)} collections. Increase 'limit' to see more.)"
        
        return result
        
    except Exception as e:
        return f"Error fetching collections: {str(e)}"


def bafu_search_collection_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Search for items within a specific BAFU collection.
    
    Args:
        args: Dictionary with:
            - collection_id: BAFU collection ID (e.g., "ch.bafu.gefaehrdungskarte-oberflaechenabfluss")
            - bbox: Optional bounding box [west, south, east, north] in WGS84
            - limit: Maximum number of items to return (default: 5)
        context: Server context for storing search results
    
    Returns:
        String with formatted search results
    """
    collection_id = args.get("collection_id")
    if not collection_id:
        return "Error: 'collection_id' parameter is required"
    
    limit = args.get("limit", 5)
    bbox = args.get("bbox")
    
    # STAC API search endpoint
    search_url = f"https://data.geo.admin.ch/api/stac/v1/collections/{collection_id}/items"
    
    try:
        params = {"limit": limit}
        if bbox:
            params["bbox"] = ",".join(map(str, bbox))
        
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        
        # Store in context for later use
        context["bafu_search_results"] = features
        context["bafu_collection_id"] = collection_id
        
        if not features:
            return f"No items found in collection '{collection_id}'"
        
        result = f"Found {len(features)} items in collection '{collection_id}':\n\n"
        
        for i, feature in enumerate(features):
            feature_id = feature.get("id", "Unknown")
            properties = feature.get("properties", {})
            
            result += f"{i+1}. Item ID: {feature_id}\n"
            
            # Show relevant properties
            if "datetime" in properties:
                result += f"   Date: {properties['datetime']}\n"
            if "title" in properties:
                result += f"   Title: {properties['title']}\n"
            
            # Show available assets
            assets = feature.get("assets", {})
            if assets:
                result += f"   Assets: {', '.join(assets.keys())}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error searching collection: {str(e)}"


def bafu_get_collection_info_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Get detailed information about a specific BAFU collection.
    
    Args:
        args: Dictionary with:
            - collection_id: BAFU collection ID
        context: Server context (not used)
    
    Returns:
        String with detailed collection information
    """
    collection_id = args.get("collection_id")
    if not collection_id:
        return "Error: 'collection_id' parameter is required"
    
    url = f"https://data.geo.admin.ch/api/stac/v1/collections/{collection_id}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        collection = response.json()
        
        title = collection.get("title", "No title")
        description = collection.get("description", "No description")
        license_info = collection.get("license", "Unknown")
        
        # Get extent information
        extent = collection.get("extent", {})
        spatial = extent.get("spatial", {}).get("bbox", [[]])
        temporal = extent.get("temporal", {}).get("interval", [[]])
        
        # Get providers
        providers = collection.get("providers", [])
        provider_names = [p.get("name", "Unknown") for p in providers]
        
        result = f"Collection: {title}\n"
        result += f"ID: {collection_id}\n\n"
        result += f"Description:\n{description}\n\n"
        result += f"License: {license_info}\n"
        result += f"Providers: {', '.join(provider_names)}\n\n"
        
        if spatial and spatial[0]:
            bbox = spatial[0]
            result += f"Spatial Extent (bbox): {bbox}\n"
        
        if temporal and temporal[0]:
            start = temporal[0][0] if temporal[0][0] else "Unknown"
            end = temporal[0][1] if temporal[0][1] else "Present"
            result += f"Temporal Extent: {start} to {end}\n"
        
        # Get links
        links = collection.get("links", [])
        for link in links:
            if link.get("rel") == "about":
                result += f"\nMore Info: {link.get('href', '')}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching collection info: {str(e)}"


def bafu_download_asset_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Download an asset from a BAFU STAC item.
    
    Args:
        args: Dictionary with:
            - item_index: Index of item from search results (default: 0)
            - asset_key: Key of asset to download (e.g., "data", "metadata")
            - output_dir: Directory to save downloaded file (default: "downloads/bafu")
        context: Server context containing search results
    
    Returns:
        String with download status and file path
    """
    item_index = args.get("item_index", 0)
    asset_key = args.get("asset_key")
    output_dir = args.get("output_dir", "downloads/bafu")
    
    # Get search results from context
    features = context.get("bafu_search_results", [])
    if not features:
        return "Error: No search results found. Please run bafu_search_collection first."
    
    if item_index >= len(features):
        return f"Error: Item index {item_index} out of range. Only {len(features)} items available."
    
    feature = features[item_index]
    assets = feature.get("assets", {})
    
    # If no asset_key specified, use the first available asset
    if not asset_key:
        if not assets:
            return "Error: No assets found in this item."
        asset_key = list(assets.keys())[0]
    
    if asset_key not in assets:
        available = ", ".join(assets.keys())
        return f"Error: Asset '{asset_key}' not found. Available assets: {available}"
    
    asset = assets[asset_key]
    asset_url = asset.get("href")
    
    if not asset_url:
        return f"Error: No URL found for asset '{asset_key}'"
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        feature_id = feature.get("id", "unknown")
        file_ext = asset_url.split(".")[-1] if "." in asset_url else "dat"
        filename = f"{feature_id}_{asset_key}.{file_ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Download file
        print(f"Downloading {asset_url}...")
        response = requests.get(asset_url, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        size_mb = file_size / (1024 * 1024)
        
        return f"✅ Downloaded successfully!\nFile: {filepath}\nSize: {size_mb:.2f} MB"
        
    except Exception as e:
        return f"Error downloading asset: {str(e)}"


def bafu_visualize_map_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Create an interactive map visualization of BAFU data coverage area.
    
    NOTE: This shows the geographic coverage area of the data, not the detailed
    geospatial features (which would require downloading and processing GIS files).
    
    Args:
        args: Dictionary with:
            - item_index: Index of item from search results (default: 0)
            - output_file: HTML file to save map (default: "bafu_map.html")
            - zoom: Initial zoom level (default: 8)
        context: Server context containing search results
    
    Returns:
        String with map creation status
    """
    try:
        import folium
    except ImportError:
        return "Error: folium library not installed. Run: pip install folium"
    
    item_index = args.get("item_index", 0)
    output_file = args.get("output_file", "bafu_map.html")
    zoom = args.get("zoom", 8)
    
    # Get search results from context
    features = context.get("bafu_search_results", [])
    collection_id = context.get("bafu_collection_id", "Unknown")
    
    if not features:
        return "Error: No search results found. Please run bafu_search_collection first."
    
    if item_index >= len(features):
        return f"Error: Item index {item_index} out of range. Only {len(features)} items available."
    
    feature = features[item_index]
    properties = feature.get("properties", {})
    feature_id = feature.get("id", "Unknown")
    
    # Get bbox from feature
    bbox = feature.get("bbox")
    if bbox and len(bbox) == 4:
        # Calculate center from bbox [west, south, east, north]
        center = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]
    else:
        # Default to Switzerland center
        center = [46.8182, 8.2275]
        bbox = [5.96, 45.82, 10.49, 47.81]  # Switzerland bbox
    
    # Create map
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    
    # Add a rectangle showing the data coverage area
    if bbox and len(bbox) == 4:
        folium.Rectangle(
            bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
            color='#FF4444',
            weight=3,
            fill=True,
            fillColor='#FF8888',
            fillOpacity=0.3,
            popup=f"""
            <b>Data Coverage Area</b><br>
            Collection: {collection_id}<br>
            Item: {feature_id}
            """
        ).add_to(m)
    
    # Add a marker at the center
    folium.Marker(
        location=center,
        popup=f"""
        <div style="width:200px">
        <b>BAFU Environmental Data</b><br><br>
        <b>Collection:</b> {collection_id}<br>
        <b>Item:</b> {feature_id}<br>
        <b>Date:</b> {properties.get('datetime', 'N/A')}<br>
        <br>
        <i>The red box shows the geographic coverage area of this dataset.</i>
        </div>
        """,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add title box
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 450px; 
                background-color: white; border:3px solid #FF4444; z-index:9999; 
                font-size:14px; padding: 15px; border-radius: 5px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
    <b style="font-size:16px;">🗺️ BAFU Environmental Data Visualization</b><br>
    <hr style="margin: 10px 0;">
    <b>Collection:</b> {collection_id}<br>
    <b>Item:</b> {feature_id}<br>
    <b>Date:</b> {properties.get('datetime', 'N/A')}<br>
    <br>
    <i style="font-size:12px; color:#666;">
    ℹ️ This map shows the geographic coverage area (red box).<br>
    For detailed flood zones, download the GIS files using bafu_download_asset.
    </i>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    
    return f"""✅ Map created successfully!

📍 What the map shows:
- Red box = Geographic coverage area of this dataset
- Red marker = Center point with dataset information

⚠️ Note: This is a coverage map, not the detailed flood/environmental data.
To see actual flood zones, you would need to:
1. Download the GIS files using bafu_download_asset
2. Open them in GIS software (QGIS, ArcGIS)

📁 File: {output_file}
💡 Open this file in your browser to view the interactive map!
"""


# Tool registration dictionary for easy import
BAFU_TOOLS = {
    "bafu_list_collections": bafu_list_collections_tool,
    "bafu_search_collection": bafu_search_collection_tool,
    "bafu_get_collection_info": bafu_get_collection_info_tool,
    "bafu_download_asset": bafu_download_asset_tool,
    "bafu_visualize_map": bafu_visualize_map_tool,
}