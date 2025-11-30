"""
Earth Search STAC API Tools - AWS Element84 Integration

These tools work with the Earth Search STAC API catalog which provides access to:
- Sentinel-2 Level 2A imagery
- Landsat Collection 2 imagery
- NAIP imagery
- Copernicus DEM

Required packages: requests, rasterio, folium, numpy, pillow
"""

import json
import os
from typing import Dict, Any
from datetime import datetime, timedelta
import requests
import folium
from PIL import Image

# Import catalog loader
try:
    from .catalog_loader import (
        load_catalog, 
        get_api_endpoint, 
        list_collections as catalog_list_collections,
        get_collection_info,
        get_available_assets as catalog_get_assets
    )
    CATALOG_AVAILABLE = True
except ImportError:
    CATALOG_AVAILABLE = False

# Optional dependencies
try:
    import rasterio
    from rasterio.plot import reshape_as_image
    from rasterio.warp import transform_bounds
    from rasterio.enums import Resampling
    import numpy as np
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


# Earth Search STAC API endpoint
EARTH_SEARCH_API = "https://earth-search.aws.element84.com/v1"


def earth_search_list_collections_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    List available collections from Earth Search STAC API.
    
    Args:
        args: Dictionary with optional:
            - use_catalog: If True, read from JSON catalog file (default: True)
            - catalog_name: Name of catalog to use (default: "earth-search")
        context: Server context to store collection list
        
    Returns:
        JSON string with available collections
    """
    try:
        use_catalog = args.get("use_catalog", True)
        catalog_name = args.get("catalog_name", "earth-search")
        
        if use_catalog and CATALOG_AVAILABLE:
            # Load from JSON catalog file
            catalog = load_catalog(catalog_name)
            api_endpoint = get_api_endpoint(catalog)
            collection_list = catalog_list_collections(catalog)
            
            # Store in context
            context["earth_search_collections"] = collection_list
            context["catalog_loaded"] = catalog
            
            result = {
                "api": "Earth Search (AWS Element84)",
                "endpoint": api_endpoint,
                "source": f"Loaded from JSON catalog: {catalog_name}",
                "exported_at": catalog.get("exportedAt", "unknown"),
                "total_collections": len(collection_list),
                "collections": collection_list
            }
            
            return json.dumps(result, indent=2)
        else:
            # Fallback: Make API call (original behavior)
            collections_url = f"{EARTH_SEARCH_API}/collections"
            
            response = requests.get(collections_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            collections = data.get("collections", [])
            
            collection_list = []
            for col in collections:
                collection_info = {
                    "id": col.get("id"),
                    "title": col.get("title", "No title"),
                    "description": col.get("description", "")[:150] + "..."
                    if len(col.get("description", "")) > 150 else col.get("description", ""),
                    "license": col.get("license", "unknown")
                }
                
                # Get extent info if available
                extent = col.get("extent", {})
                spatial = extent.get("spatial", {})
                temporal = extent.get("temporal", {})
                
                if spatial.get("bbox"):
                    collection_info["spatial_extent"] = spatial["bbox"][0]
                if temporal.get("interval"):
                    collection_info["temporal_extent"] = temporal["interval"][0]
                
                collection_list.append(collection_info)
            
            # Store in context
            context["earth_search_collections"] = collection_list
            
            result = {
                "api": "Earth Search (AWS Element84)",
                "endpoint": EARTH_SEARCH_API,
                "source": "Live API call",
                "total_collections": len(collections),
                "collections": collection_list
            }
            
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing Earth Search collections: {str(e)}"


def earth_search_search_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Search for geospatial data using Earth Search STAC API.
    
    Args:
        args: Dictionary with:
            - collection: Collection ID (e.g., "sentinel-2-l2a", "landsat-c2-l2")
            - bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            - date_start: Start date (YYYY-MM-DD format or "30 days ago")
            - date_end: End date (YYYY-MM-DD format or "today")
            - limit: Maximum number of items to return (default 10)
            - max_cloud_cover: Maximum cloud cover percentage (default 20)
        context: Server context to store search results
        
    Returns:
        JSON string with search results
    """
    try:
        # Parse arguments
        collection = args.get("collection", "sentinel-2-l2a")
        bbox = args.get("bbox", [-122.5, 37.7, -122.3, 37.8])  # Default: San Francisco Bay Area
        date_start = args.get("date_start", "30 days ago")
        date_end = args.get("date_end", "today")
        limit = int(args.get("limit", 10))
        max_cloud_cover = float(args.get("max_cloud_cover", 20))
        
        # Parse dates
        if date_end == "today":
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(date_end, "%Y-%m-%d")
        
        if "days ago" in date_start:
            days = int(date_start.split()[0])
            start_date = end_date - timedelta(days=days)
        else:
            start_date = datetime.strptime(date_start, "%Y-%m-%d")
        
        date_range = f"{start_date.strftime('%Y-%m-%d')}T00:00:00Z/{end_date.strftime('%Y-%m-%d')}T23:59:59Z"
        
        # STAC API search request
        search_url = f"{EARTH_SEARCH_API}/search"
        search_params = {
            "collections": [collection],
            "bbox": bbox,
            "datetime": date_range,
            "limit": limit,
            "query": {
                "eo:cloud_cover": {
                    "lt": max_cloud_cover
                }
            }
        }
        
        response = requests.post(search_url, json=search_params, timeout=30)
        response.raise_for_status()
        results = response.json()
        items = results.get("features", [])
        
        # Store in context
        context["earth_search_last_search"] = {
            "api": "earth_search",
            "collection": collection,
            "items": items,
            "count": len(items),
            "bbox": bbox,
            "date_range": date_range
        }
        
        # Create summary
        summary = {
            "api": "Earth Search",
            "collection": collection,
            "bbox": bbox,
            "date_range": date_range,
            "max_cloud_cover": max_cloud_cover,
            "items_found": len(items),
            "items": []
        }
        
        for idx, item in enumerate(items[:5]):  # Show first 5
            props = item.get("properties", {})
            item_summary = {
                "index": idx,
                "id": item.get("id", "unknown"),
                "date": props.get("datetime", "unknown"),
                "cloud_cover": props.get("eo:cloud_cover", "N/A"),
                "assets": list(item.get("assets", {}).keys())
            }
            summary["items"].append(item_summary)
        
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error searching Earth Search: {str(e)}"


def earth_search_download_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Download a specific asset from an Earth Search STAC item.
    
    Args:
        args: Dictionary with:
            - item_index: Index of item from search results (default 0)
            - asset_key: Asset key to download (e.g., "visual", "thumbnail", "red", "green", "blue")
            - output_dir: Directory to save downloaded files (default "downloads")
        context: Server context with search results
        
    Returns:
        String with download result
    """
    try:
        item_index = int(args.get("item_index", 0))
        asset_key = args.get("asset_key", "thumbnail")
        output_dir = args.get("output_dir", "downloads")
        
        # Get last search results
        last_search = context.get("earth_search_last_search", {})
        if not last_search or last_search.get("api") != "earth_search":
            return "Error: No Earth Search results found. Please run a search first."
        
        items = last_search.get("items", [])
        if not items:
            return "Error: No items found in last search."
        
        if item_index >= len(items):
            return f"Error: Item index {item_index} out of range. Found {len(items)} items."
        
        item = items[item_index]
        item_id = item.get("id", "unknown")
        assets = item.get("assets", {})
        
        # Try to find a suitable asset
        if asset_key not in assets:
            # Look for alternatives
            alternatives = ["visual", "thumbnail", "rendered_preview", "overview", "preview"]
            found = False
            for alt in alternatives:
                if alt in assets:
                    asset_key = alt
                    found = True
                    break
            
            if not found:
                available = list(assets.keys())
                return f"Error: Asset '{asset_key}' not found. Available: {', '.join(available)}"
        
        asset = assets[asset_key]
        asset_url = asset.get("href", "")
        
        if not asset_url:
            return "Error: No URL found for asset"
        
        # Download file (Earth Search doesn't require URL signing)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Downloading from: {asset_url}")
        response = requests.get(asset_url, timeout=120, stream=True)
        response.raise_for_status()
        
        # Determine file extension
        file_ext = asset_url.split(".")[-1].split("?")[0] if "." in asset_url else "tif"
        if file_ext not in ["tif", "tiff", "jpg", "jpeg", "png", "jp2"]:
            file_ext = "tif"
        
        filename = f"{item_id}_{asset_key}.{file_ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Save file
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        
        # Store in context
        context["earth_search_last_download"] = {
            "item_id": item_id,
            "item_index": item_index,
            "asset_key": asset_key,
            "filepath": filepath,
            "file_size_mb": round(file_size_mb, 2)
        }
        
        return f"✓ Downloaded {asset_key} for item {item_id}\n  Path: {filepath}\n  Size: {file_size_mb:.2f} MB"
    except Exception as e:
        return f"Error downloading: {str(e)}"


def earth_search_visualize_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Create an interactive map visualization of Earth Search STAC items.
    
    Args:
        args: Dictionary with:
            - item_index: Index of item to visualize (default 0)
            - zoom: Initial zoom level (default 10)
            - output_file: Output HTML file path (default "earth_search_map.html")
            - show_all_items: Show all items from search (default False)
        context: Server context with search results and downloads
        
    Returns:
        String with map creation result
    """
    try:
        item_index = int(args.get("item_index", 0))
        zoom = int(args.get("zoom", 10))
        output_file = args.get("output_file", "earth_search_map.html")
        show_all_items = args.get("show_all_items", False)
        
        # Get last search results
        last_search = context.get("earth_search_last_search", {})
        if not last_search or last_search.get("api") != "earth_search":
            return "Error: No Earth Search results found. Please run a search first."
        
        items = last_search.get("items", [])
        if not items:
            return "Error: No items found in last search."
        
        if item_index >= len(items):
            return f"Error: Item index {item_index} out of range. Found {len(items)} items."
        
        main_item = items[item_index]
        
        # Get center coordinates from main item
        geometry = main_item.get("geometry", {})
        if geometry.get("type") == "Polygon":
            coords = geometry.get("coordinates", [])[0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
        else:
            bbox = main_item.get("bbox", last_search.get("bbox", [-122.4, 37.7, -122.3, 37.8]))
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add main item marker
        item_id = main_item.get("id", "unknown")
        props = main_item.get("properties", {})
        item_date = props.get("datetime", "unknown")
        cloud_cover = props.get("eo:cloud_cover", "N/A")
        
        popup_html = f"""
        <div style="font-family: Arial; min-width: 250px;">
            <h4 style="margin: 0 0 10px 0;">Earth Search Item</h4>
            <b>ID:</b> {item_id}<br>
            <b>Date:</b> {item_date}<br>
            <b>Collection:</b> {last_search.get('collection', 'unknown')}<br>
            <b>Cloud Cover:</b> {cloud_cover}%<br>
            <b>Index:</b> {item_index}
        </div>
        """
        
        folium.Marker(
            [center_lat, center_lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Item {item_index}: {item_id}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Draw bounding box for main item
        if "bbox" in main_item:
            bbox = main_item["bbox"]
            bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            folium.Rectangle(
                bounds=bounds,
                color="red",
                fill=True,
                fillOpacity=0.2,
                weight=3,
                popup=f"Main Item: {item_id}"
            ).add_to(m)
        
        # Optionally show all items
        if show_all_items:
            for idx, item in enumerate(items):
                if idx == item_index:
                    continue  # Skip main item
                
                if "bbox" in item:
                    bbox = item["bbox"]
                    bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
                    item_id_other = item.get("id", f"item_{idx}")
                    
                    folium.Rectangle(
                        bounds=bounds,
                        color="blue",
                        fill=True,
                        fillOpacity=0.1,
                        weight=1,
                        popup=f"Item {idx}: {item_id_other}"
                    ).add_to(m)
        
        # Try to overlay downloaded image if available
        last_download = context.get("earth_search_last_download", {})
        if last_download.get("item_index") == item_index:
            image_path = last_download.get("filepath")
            
            if image_path and os.path.exists(image_path):
                try:
                    # Check if it's a simple image format (PNG, JPG)
                    if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # For regular images, we need the bbox
                        if "bbox" in main_item:
                            bbox = main_item["bbox"]
                            bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
                            
                            # Load and add image overlay
                            img = Image.open(image_path)
                            img_array = np.array(img)
                            
                            folium.raster_layers.ImageOverlay(
                                image=img_array,
                                bounds=bounds,
                                opacity=0.7,
                                name="Downloaded Image"
                            ).add_to(m)
                            m.fit_bounds(bounds)
                    
                    # For GeoTIFF files
                    elif RASTERIO_AVAILABLE and image_path.lower().endswith(('.tif', '.tiff')):
                        with rasterio.open(image_path) as src:
                            # Transform bounds to WGS84
                            if src.crs and src.crs.to_string() != 'EPSG:4326':
                                left, bottom, right, top = transform_bounds(
                                    src.crs, 'EPSG:4326',
                                    src.bounds.left, src.bounds.bottom,
                                    src.bounds.right, src.bounds.top
                                )
                                bounds = [[bottom, left], [top, right]]
                            else:
                                bounds = [[src.bounds.bottom, src.bounds.left],
                                         [src.bounds.top, src.bounds.right]]
                            
                            # Read and downsample if needed
                            max_dimension = 2000
                            width, height = src.width, src.height
                            if width > max_dimension or height > max_dimension:
                                scale = min(max_dimension / width, max_dimension / height)
                                img_data = src.read(
                                    out_shape=(src.count, int(height * scale), int(width * scale)),
                                    resampling=Resampling.bilinear
                                )
                            else:
                                img_data = src.read()
                            
                            # Convert to displayable format
                            if len(img_data.shape) == 3:
                                if img_data.shape[0] >= 3:
                                    img_array = reshape_as_image(img_data[:3])
                                else:
                                    img_array = img_data[0]
                                    img_array = np.stack([img_array, img_array, img_array], axis=-1)
                            else:
                                img_array = img_data
                                img_array = np.stack([img_array, img_array, img_array], axis=-1)
                            
                            # Normalize to uint8
                            if img_array.max() > 255:
                                img_array = (img_array.astype(np.float32) / img_array.max() * 255).astype(np.uint8)
                            else:
                                img_array = img_array.astype(np.uint8)
                            
                            folium.raster_layers.ImageOverlay(
                                image=img_array,
                                bounds=bounds,
                                opacity=0.7,
                                name="Satellite Image"
                            ).add_to(m)
                            m.fit_bounds(bounds)
                
                except Exception as e:
                    pass  # Continue without overlay if it fails
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save map
        m.save(output_file)
        
        context["earth_search_last_map"] = {
            "item_id": item_id,
            "item_index": item_index,
            "filepath": output_file
        }
        
        return f"✓ Map created: {output_file}\n  Showing item {item_index}: {item_id}\n  Collection: {last_search.get('collection')}\n  Open the HTML file in a browser to view!"
    except Exception as e:
        return f"Error creating map: {str(e)}"

