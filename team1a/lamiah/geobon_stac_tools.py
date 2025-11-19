"""
GEO BON STAC Tools - Group on Earth Observations Biodiversity Observation Network

Tools for accessing and visualizing biodiversity and environmental data from 
the GEO BON STAC catalog, with a focus on forest loss monitoring for ESG analysis.

Author: Lamiah Khan
Date: November 2024
"""

from typing import Dict, Any
import requests
import json
import os
from datetime import datetime


def geobon_list_collections_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    List available collections from GEO BON STAC catalog.
    
    Args:
        args: Dictionary with optional:
            - limit: Maximum number of collections to display (default: 10)
            - search_term: Filter collections by keyword in title/description
        context: Server context for storing collection data
    
    Returns:
        String with formatted list of available collections
    """
    stac_url = "https://stac.geobon.org/collections"
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
        context["geobon_collections"] = collections
        
        # Format output
        result = f"Found {len(collections)} GEO BON collections"
        if search_term:
            result += f" matching '{search_term}'"
        result += ":\n\n"
        
        for i, collection in enumerate(collections[:limit]):
            coll_id = collection.get("id", "Unknown")
            title = collection.get("title", "No title")
            description = collection.get("description", "")[:200]
            
            result += f"{i+1}. {title}\n"
            result += f"   ID: {coll_id}\n"
            result += f"   Description: {description}...\n\n"
        
        if len(collections) > limit:
            result += f"\n(Showing {limit} of {len(collections)} collections. Increase 'limit' to see more.)"
        
        return result
        
    except Exception as e:
        return f"Error fetching collections: {str(e)}"


def geobon_get_collection_info_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Get detailed information about a specific GEO BON collection.
    
    Args:
        args: Dictionary with:
            - collection_id: GEO BON collection ID (e.g., "gfw-lossyear")
        context: Server context (not used)
    
    Returns:
        String with detailed collection information
    """
    collection_id = args.get("collection_id")
    if not collection_id:
        return "Error: 'collection_id' parameter is required"
    
    url = f"https://stac.geobon.org/collections/{collection_id}"
    
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
        
        result = f"🌍 Collection: {title}\n"
        result += f"ID: {collection_id}\n\n"
        result += f"Description:\n{description}\n\n"
        result += f"License: {license_info}\n\n"
        
        if spatial and spatial[0]:
            bbox = spatial[0]
            result += f"Spatial Extent (bbox): {bbox}\n"
            result += f"Coverage: Global\n"
        
        if temporal and temporal[0]:
            start = temporal[0][0] if temporal[0][0] else "Unknown"
            end = temporal[0][1] if temporal[0][1] else "Present"
            result += f"Temporal Extent: {start} to {end}\n"
        
        # Get summaries if available
        summaries = collection.get("summaries", {})
        if summaries:
            result += f"\n📊 Additional Information:\n"
            for key, value in summaries.items():
                if isinstance(value, list) and len(value) <= 5:
                    result += f"   {key}: {', '.join(map(str, value))}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching collection info: {str(e)}"


def geobon_search_collection_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Search for items within a specific GEO BON collection.
    
    Args:
        args: Dictionary with:
            - collection_id: GEO BON collection ID (e.g., "gfw-lossyear")
            - bbox: Optional bounding box [west, south, east, north] in WGS84
            - limit: Maximum number of items to return (default: 10)
        context: Server context for storing search results
    
    Returns:
        String with formatted search results
    """
    collection_id = args.get("collection_id")
    if not collection_id:
        return "Error: 'collection_id' parameter is required"
    
    limit = args.get("limit", 10)
    bbox = args.get("bbox")
    
    # STAC API search endpoint
    search_url = f"https://stac.geobon.org/collections/{collection_id}/items"
    
    try:
        params = {"limit": limit}
        if bbox:
            params["bbox"] = ",".join(map(str, bbox))
        
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        
        # Store in context for later use
        context["geobon_search_results"] = features
        context["geobon_collection_id"] = collection_id
        
        if not features:
            return f"No items found in collection '{collection_id}'"
        
        result = f"🔍 Found {len(features)} items in collection '{collection_id}':\n\n"
        
        for i, feature in enumerate(features):
            feature_id = feature.get("id", "Unknown")
            properties = feature.get("properties", {})
            
            result += f"{i+1}. Item ID: {feature_id}\n"
            
            # Show relevant properties
            if "datetime" in properties:
                result += f"   Date: {properties['datetime']}\n"
            if "title" in properties:
                result += f"   Title: {properties['title']}\n"
            
            # Show geometry type
            geometry = feature.get("geometry", {})
            if geometry:
                geom_type = geometry.get("type", "Unknown")
                result += f"   Geometry: {geom_type}\n"
            
            # Show available assets
            assets = feature.get("assets", {})
            if assets:
                asset_list = []
                for asset_key, asset_info in assets.items():
                    asset_type = asset_info.get("type", "unknown")
                    asset_list.append(f"{asset_key} ({asset_type})")
                result += f"   Assets: {', '.join(asset_list[:3])}"
                if len(asset_list) > 3:
                    result += f" and {len(asset_list) - 3} more"
                result += "\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error searching collection: {str(e)}"


def geobon_download_asset_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Download an asset from a GEO BON STAC item.
    
    Args:
        args: Dictionary with:
            - item_index: Index of item from search results (default: 0)
            - asset_key: Key of asset to download (if not specified, lists available assets)
            - output_dir: Directory to save downloaded file (default: "downloads/geobon")
        context: Server context containing search results
    
    Returns:
        String with download status and file path
    """
    item_index = args.get("item_index", 0)
    asset_key = args.get("asset_key")
    output_dir = args.get("output_dir", "downloads/geobon")
    
    # Get search results from context
    features = context.get("geobon_search_results", [])
    if not features:
        return "Error: No search results found. Please run geobon_search_collection first."
    
    if item_index >= len(features):
        return f"Error: Item index {item_index} out of range. Only {len(features)} items available."
    
    feature = features[item_index]
    assets = feature.get("assets", {})
    
    # If no asset_key specified, list available assets
    if not asset_key:
        if not assets:
            return "Error: No assets found in this item."
        result = "Available assets for this item:\n\n"
        for key, asset_info in assets.items():
            title = asset_info.get("title", "No title")
            asset_type = asset_info.get("type", "unknown")
            result += f"• {key}: {title} (type: {asset_type})\n"
        result += "\nSpecify 'asset_key' parameter to download a specific asset."
        return result
    
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
        # Clean feature_id for filename
        clean_id = feature_id.replace("/", "_").replace("\\", "_")
        file_ext = asset_url.split(".")[-1].split("?")[0] if "." in asset_url else "dat"
        filename = f"{clean_id}_{asset_key}.{file_ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Download file
        print(f"Downloading {asset_url}...")
        response = requests.get(asset_url, timeout=120, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filepath)
        size_mb = file_size / (1024 * 1024)
        
        return f"✅ Downloaded successfully!\nFile: {filepath}\nSize: {size_mb:.2f} MB"
        
    except Exception as e:
        return f"Error downloading asset: {str(e)}"


def geobon_visualize_forest_loss_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Create an interactive map visualization of Global Forest Watch forest loss data.
    
    This visualizes forest loss areas from the GEO BON catalog, useful for ESG
    analysis of deforestation risk and environmental impact.
    
    The map automatically centers on the data and adjusts zoom based on area size.
    
    Args:
        args: Dictionary with:
            - item_index: Index of item from search results (default: 0)
            - output_file: HTML file to save map (default: "geobon_forest_loss_map.html")
            - zoom: Optional manual zoom level (auto-calculated if not provided)
            - region_name: Optional name for the region being visualized
        context: Server context containing search results
    
    Returns:
        String with map creation status
    """
    try:
        import folium
    except ImportError:
        return "Error: folium library not installed. Run: pip install folium"
    
    item_index = args.get("item_index", 0)
    output_file = args.get("output_file", "geobon_forest_loss_map.html")
    region_name = args.get("region_name", "Global")
    
    # Get search results from context
    features = context.get("geobon_search_results", [])
    collection_id = context.get("geobon_collection_id", "Unknown")
    
    if not features:
        return "Error: No search results found. Please run geobon_search_collection first."
    
    if item_index >= len(features):
        return f"Error: Item index {item_index} out of range. Only {len(features)} items available."
    
    feature = features[item_index]
    properties = feature.get("properties", {})
    feature_id = feature.get("id", "Unknown")
    
    # Get bbox from feature and calculate optimal zoom
    bbox = feature.get("bbox")
    if bbox and len(bbox) == 4:
        # Calculate center from bbox [west, south, east, north]
        center = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]
        
        # Calculate appropriate zoom level based on bbox size
        lat_range = abs(bbox[3] - bbox[1])
        lon_range = abs(bbox[2] - bbox[0])
        max_range = max(lat_range, lon_range)
        
        # Auto-adjust zoom - larger areas need lower zoom
        if max_range > 100:  # Continental/global
            auto_zoom = 2
        elif max_range > 50:  # Country-sized
            auto_zoom = 3
        elif max_range > 20:  # Regional
            auto_zoom = 4
        elif max_range > 10:  # State-sized
            auto_zoom = 5
        else:  # City/local-sized
            auto_zoom = 6
            
        # Use auto zoom if user didn't specify, otherwise use their value
        zoom = args.get("zoom", auto_zoom)
    else:
        # Default to global center
        center = [0, 0]
        bbox = [-180, -90, 180, 90]
        zoom = args.get("zoom", 2)
    
    # Create map with world wrap disabled and proper bounds
    m = folium.Map(
        location=center, 
        zoom_start=zoom, 
        tiles="OpenStreetMap",
        world_copy_jump=False,  # Disable world wrapping
        no_wrap=True,  # Don't wrap the world
        min_zoom=2,  # Prevent zooming out too far
        max_bounds=True  # Constrain panning to one world
    )
    
    # Add satellite imagery option
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite Imagery',
        overlay=False,
        control=True,
        no_wrap=True
    ).add_to(m)
    
    # Add a rectangle showing the data coverage area with popup that STAYS ON SCREEN
    if bbox and len(bbox) == 4:
        folium.Rectangle(
            bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
            color='#D32F2F',
            weight=2,
            fill=True,
            fillColor='#EF5350',
            fillOpacity=0.15,
            popup=folium.Popup(f"""
            <div style="width: 280px; font-family: Arial, sans-serif; font-size: 14px; padding: 5px; line-height: 1.8;">
                <b style="color: #D32F2F; font-size: 16px;">🌲 Coverage Area</b><br><br>
                <b>Collection:</b> {collection_id}<br>
                <b>Item:</b> {feature_id}<br>
                <b>Region:</b> {region_name}<br>
                <hr style="margin: 10px 0; border: none; border-top: 2px solid #ddd;">
                <div style="font-size: 12px; color: #666;">
                    <b>Bounding Box:</b><br>
                    West: {bbox[0]:.2f}°, South: {bbox[1]:.2f}°<br>
                    East: {bbox[2]:.2f}°, North: {bbox[3]:.2f}°
                </div>
            </div>
            """, max_width=320, keep_in_view=True, auto_pan=True)
        ).add_to(m)
    
    # Add a marker at the center with popup that STAYS ON SCREEN
    folium.Marker(
        location=center,
        popup=folium.Popup(f"""
        <div style="width: 300px; font-family: Arial, sans-serif; line-height: 1.8; padding: 5px;">
            <div style="font-size: 16px; font-weight: bold; color: #D32F2F; margin-bottom: 10px;">
                🌍 GEO BON Data
            </div>
            <div style="font-size: 14px;">
                <b>Collection:</b> {collection_id}<br>
                <b>Item:</b> {feature_id}<br>
                <b>Region:</b> {region_name}<br>
                <b>Date:</b> {properties.get('datetime', 'N/A')[:10]}
            </div>
            <hr style="margin: 10px 0; border: none; border-top: 2px solid #ddd;">
            <div style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; font-size: 13px;">
                <b style="color: #D32F2F;">🌲 ESG Applications:</b><br>
                • Deforestation tracking<br>
                • Climate risk analysis<br>
                • Biodiversity monitoring<br>
                • Supply chain sustainability
            </div>
        </div>
        """, max_width=350, keep_in_view=True, auto_pan=True),
        icon=folium.Icon(color='darkred', icon='tree', prefix='fa')
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add compact info box on the RIGHT side (not blocking the map)
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 320px; 
                background-color: rgba(255, 255, 255, 0.95); 
                border: 3px solid #D32F2F; 
                z-index: 9999; 
                font-size: 11px; 
                padding: 10px; 
                border-radius: 5px; 
                box-shadow: 3px 3px 10px rgba(0,0,0,0.4);
                font-family: Arial, sans-serif;">
    <div style="font-size: 13px; font-weight: bold; margin-bottom: 6px; color: #D32F2F;">
        🌲 GEO BON Forest Loss
    </div>
    <div style="line-height: 1.5; font-size: 10px;">
        <b>Collection:</b> {collection_id}<br>
        <b>Item:</b> {feature_id}<br>
        <b>Region:</b> {region_name}<br>
        <b>Date:</b> {properties.get('datetime', 'N/A')[:10]}
    </div>
    <hr style="margin: 6px 0; border: none; border-top: 1px solid #ddd;">
    <div style="background-color: #fff3f3; padding: 6px; border-radius: 3px;">
        <b style="color: #D32F2F; font-size: 10px;">🎯 ESG Uses:</b>
        <ul style="margin: 3px 0; padding-left: 18px; font-size: 9px; color: #555; line-height: 1.4;">
            <li>Supply chain deforestation</li>
            <li>Climate risk assessment</li>
            <li>Biodiversity monitoring</li>
        </ul>
    </div>
    <div style="font-size: 8px; color: #999; margin-top: 4px; font-style: italic;">
        💡 Click marker/box for details
    </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    
    # Get asset information for download instructions
    assets = feature.get("assets", {})
    asset_info = ""
    if assets:
        asset_info = "\n\n📦 Available Assets for Download:\n"
        for asset_key, asset_data in list(assets.items())[:3]:
            asset_type = asset_data.get("type", "unknown")
            asset_info += f"   • {asset_key} ({asset_type})\n"
    
    return f"""✅ Forest Loss Visualization Created!

🗺️ What the map shows:
- Red box = Geographic coverage area of forest loss data
- Satellite imagery toggle available
- Interactive popup with ESG context

🌲 About This Data:
This collection tracks forest cover loss, which is critical for:
- Environmental: Deforestation & climate change impact
- Social: Indigenous land rights & community impacts  
- Governance: Supply chain transparency & compliance
{asset_info}
💡 Next Steps:
1. Open {output_file} in your browser to explore the map
2. Use geobon_download_asset to get GeoTIFF files for detailed analysis
3. Integrate with ESG risk assessment frameworks

📊 For detailed spatial analysis, download the GeoTIFF assets and 
   process them with QGIS, ArcGIS, or Python (rasterio, geopandas)
"""


# Tool registration dictionary for easy import
GEOBON_TOOLS = {
    "geobon_list_collections": geobon_list_collections_tool,
    "geobon_get_collection_info": geobon_get_collection_info_tool,
    "geobon_search_collection": geobon_search_collection_tool,
    "geobon_download_asset": geobon_download_asset_tool,
    "geobon_visualize_forest_loss": geobon_visualize_forest_loss_tool,
}