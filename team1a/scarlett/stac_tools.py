"""
STAC API Tools - Microsoft Planetary Computer Integration

This is an example of student-developed tools created in a personal directory.
This demonstrates how students can create their own tools following the MCP framework.

These tools demonstrate how to integrate external APIs (STAC) with MCP.
Students can use these as examples for creating tools that access web APIs.

Required packages: requests, planetary-computer, rasterio, folium, numpy
"""

import json
import os
import sys
from typing import Dict, Any
from datetime import datetime, timedelta
import requests
import folium

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Optional dependencies
try:
    import planetary_computer
    PLANETARY_COMPUTER_AVAILABLE = True
except ImportError:
    PLANETARY_COMPUTER_AVAILABLE = False

try:
    import rasterio
    from rasterio.plot import reshape_as_image
    from rasterio.warp import transform_bounds
    from rasterio.enums import Resampling
    import numpy as np
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False


def stac_list_collections_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """List available collections from Microsoft Planetary Computer."""
    try:
        from config import get_api_url
        
        # Get STAC API URL from configuration, default to Microsoft Planetary Computer
        stac_url = get_api_url('stac', "https://planetarycomputer.microsoft.com/api/stac/v1")
        collections_url = f"{stac_url}/collections"
        
        response = requests.get(collections_url)
        response.raise_for_status()
        collections = response.json().get("collections", [])
        
        collection_list = [
            {
                "id": col.get("id"),
                "title": col.get("title", "No title"),
                "description": col.get("description", "")[:100] + "..."
                if len(col.get("description", "")) > 100 else col.get("description", "")
            }
            for col in collections[:20]
        ]
        
        context["available_collections"] = collection_list
        
        result = {
            "total_collections": len(collections),
            "popular_collections": [
                "io-lulc-annual-v02 - 10m Annual Land Use/Land Cover",
                "sentinel-2-l2a - Sentinel-2 Level 2A",
                "landsat-c2-l2 - Landsat Collection 2 Level 2",
                "modis-09a1 - MODIS Surface Reflectance",
                "naip - National Agriculture Imagery Program"
            ],
            "all_collections": collection_list
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing collections: {str(e)}"


def stac_search_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Search for geospatial data using Microsoft Planetary Computer STAC API."""
    try:
        collection = args.get("collection", "io-lulc-annual-v02")
        bbox = args.get("bbox", [-122.5, 37.7, -122.3, 37.8])
        date_start = args.get("date_start", "30 days ago")
        date_end = args.get("date_end", "today")
        limit = int(args.get("limit", 10))
        
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
        
        date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # STAC API request
        from config import get_api_url
        
        stac_url = get_api_url('stac', "https://planetarycomputer.microsoft.com/api/stac/v1")
        search_url = f"{stac_url}/search"
        search_params = {
            "collections": [collection],
            "bbox": bbox,
            "datetime": date_range,
            "limit": limit
        }
        
        response = requests.post(search_url, json=search_params)
        response.raise_for_status()
        results = response.json()
        items = results.get("features", [])
        
        # Store in context
        context["last_search"] = {
            "collection": collection,
            "items": items,
            "count": len(items)
        }
        
        summary = {
            "collection": collection,
            "bbox": bbox,
            "date_range": date_range,
            "items_found": len(items),
            "sample_items": [
                {
                    "id": item.get("id", "unknown"),
                    "date": item.get("properties", {}).get("datetime", "unknown"),
                    "cloud_cover": item.get("properties", {}).get("eo:cloud_cover", "N/A")
                }
                for item in items[:5]
            ]
        }
        
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error searching STAC: {str(e)}"


def stac_download_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Download a specific STAC item asset."""
    try:
        item_id = args.get("item_id")
        item_index = args.get("item_index", 0)
        asset_type = args.get("asset_type", "data")
        output_dir = args.get("output_dir", "downloads")
        
        # Get last search results
        last_search = context.get("last_search", {})
        items = last_search.get("items", [])
        
        if not items:
            return "Error: No items found. Please run a search first."
        
        # Find the item
        item = None
        if item_id:
            item = next((i for i in items if i.get("id") == item_id), None)
        elif items:
            item_index = int(item_index)
            if 0 <= item_index < len(items):
                item = items[item_index]
        
        if not item and items:
            item = items[0]
        
        if not item:
            return "Error: No items found."
        
        # Get asset URL
        assets = item.get("assets", {})
        if asset_type not in assets:
            collection = context.get("last_search", {}).get("collection", "")
            if "lulc" in collection.lower():
                alternatives = ["data", "lulc", "landcover", "classification", "thumbnail"]
            else:
                alternatives = ["visual", "thumbnail", "data"]
            
            found = False
            for alt in alternatives:
                if alt in assets:
                    asset_type = alt
                    found = True
                    break
            
            if not found:
                available = list(assets.keys())
                return f"Error: Asset type not found. Available: {', '.join(available)}"
        
        asset = assets[asset_type]
        asset_url = asset.get("href", "")
        
        if not asset_url:
            return "Error: No URL found for asset"
        
        # Sign URL
        if PLANETARY_COMPUTER_AVAILABLE:
            signed_url = planetary_computer.sign(asset_url)
        else:
            return "Error: planetary-computer package required. Install: pip install planetary-computer"
        
        # Download file
        os.makedirs(output_dir, exist_ok=True)
        response = requests.get(signed_url, timeout=60)
        response.raise_for_status()
        
        # Save file
        actual_item_id = item.get("id", "unknown_item")
        file_ext = asset_url.split(".")[-1].split("?")[0] if "." in asset_url else "tif"
        filename = f"{actual_item_id}_{asset_type}.{file_ext}"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        # Store in context
        context["last_download"] = {
            "item_id": actual_item_id,
            "asset_type": asset_type,
            "filepath": filepath
        }
        
        return f"Downloaded {asset_type} for item {actual_item_id} to: {filepath}"
    except Exception as e:
        return f"Error downloading: {str(e)}"


def stac_visualize_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Visualize STAC search results on a map."""
    try:
        item_index = int(args.get("item_index", 0))
        zoom = int(args.get("zoom", 10))
        output_file = args.get("output_file", "map.html")
        
        # Get last search results
        last_search = context.get("last_search", {})
        items = last_search.get("items", [])
        
        if not items:
            return "Error: No search results found. Please run a search first."
        
        if item_index >= len(items):
            return f"Error: Item index {item_index} out of range. Found {len(items)} items."
        
        item = items[item_index]
        item_id = item.get("id", "unknown")
        
        # Get center coordinates
        geometry = item.get("geometry", {})
        if geometry.get("type") == "Polygon":
            coords = geometry.get("coordinates", [])[0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
        else:
            bbox = item.get("bbox", [-122.4, 37.7, -122.3, 37.8])
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
        
        # Add marker
        item_date = item.get("properties", {}).get("datetime", "unknown")
        popup_text = f"<b>STAC Item</b><br>ID: {item_id}<br>Date: {item_date}<br>Collection: {last_search.get('collection', 'unknown')}"
        folium.Marker([center_lat, center_lon], popup=folium.Popup(popup_text, max_width=300), tooltip=item_id).add_to(m)
        
        # Draw bounding box
        if "bbox" in item:
            bbox = item["bbox"]
            bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            folium.Rectangle(bounds=bounds, color="red", fill=False, weight=2).add_to(m)
        
        # Try to overlay downloaded image
        image_path = args.get("image_path")
        if not image_path:
            last_download = context.get("last_download", {})
            if last_download.get("item_id") == item_id:
                image_path = last_download.get("filepath")
        
        if image_path and os.path.exists(image_path) and RASTERIO_AVAILABLE:
            try:
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
                        bounds = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
                    
                    # Downsample if needed
                    max_dimension = 5000
                    width, height = src.width, src.height
                    if width > max_dimension or height > max_dimension:
                        scale = min(max_dimension / width, max_dimension / height)
                        img_data = src.read(
                            out_shape=(src.count, int(height * scale), int(width * scale)),
                            resampling=Resampling.bilinear
                        )
                    else:
                        img_data = src.read()
                    
                    # Process image
                    if len(img_data.shape) == 3:
                        if img_data.shape[0] >= 3:
                            img_array = reshape_as_image(img_data[:3])
                        else:
                            img_array = img_data[0]
                            img_array = np.stack([img_array, img_array, img_array], axis=-1)
                    else:
                        img_array = img_data
                        img_array = np.stack([img_array, img_array, img_array], axis=-1)
                    
                    # Normalize
                    if img_array.max() <= 11 and img_array.max() > 0:
                        img_array = (img_array.astype(np.uint16) * 255 // img_array.max()).astype(np.uint8)
                    elif img_array.max() > 255:
                        if img_array.max() < 65536:
                            img_array = (img_array.astype(np.uint16) * 255 // img_array.max()).astype(np.uint8)
                        else:
                            img_array = (img_array.astype(np.float32) / img_array.max() * 255).astype(np.uint8)
                    else:
                        img_array = img_array.astype(np.uint8)
                    
                    # Add overlay
                    folium.raster_layers.ImageOverlay(
                        image=img_array, bounds=bounds, opacity=0.7, name="Geospatial Data"
                    ).add_to(m)
                    m.fit_bounds(bounds)
            except Exception as e:
                pass  # Continue without overlay if it fails
        
        m.save(output_file)
        context["last_map"] = {"item_id": item_id, "filepath": output_file}
        return f"Map created: {output_file} (showing item {item_index}: {item_id})"
    except Exception as e:
        return f"Error creating map: {str(e)}"

