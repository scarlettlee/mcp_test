"""
STAC Catalog Loader - Dynamic Catalog Management

This module loads STAC catalog JSON files and provides metadata
about available collections, date ranges, and assets.

Usage:
    from tools.catalog_loader import load_catalog, get_collection_info
    
    catalog = load_catalog("earth-search")
    info = get_collection_info(catalog, "sentinel-2-l2a")
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_catalog(catalog_name: str = "earth-search") -> Dict[str, Any]:
    """
    Load a STAC catalog from JSON file.
    
    Args:
        catalog_name: Name of the catalog to load
                     Options: "earth-search", "eocat.esa", "fedeo.ceos", 
                              "geoservice.dlr", "openeo.eodc", "earthdatahub.destine"
        
    Returns:
        Dictionary containing catalog data with API endpoint and collections
    """
    # Map catalog names to filenames
    catalog_files = {
        "earth-search": "stac-tags-earth-search.aws.element84.com.json",
        "eocat.esa": "stac-tags-eocat.esa.int.json",
        "fedeo.ceos": "stac-tags-fedeo.ceos.org.json",
        "geoservice.dlr": "stac-tags-geoservice.dlr.de.json",
        "openeo.eodc": "stac-tags-openeo.eodc.eu.json",
        "openeo.eurac": "stac-tags-openeo.eurac.edu.json",
        "earthdatahub.destine": "stac-tags-earthdatahub.destine.eu.json",
        "gep-supersites": "stac-tags-gep-supersites-stac.terradue.com.json",
        "s3ext.gptl": "stac-tags-s3ext.gptl.ru.json"
    }
    
    if catalog_name not in catalog_files:
        raise ValueError(f"Unknown catalog: {catalog_name}. Available: {list(catalog_files.keys())}")
    
    # Look for catalog file in data/Catalogs10_18 directory
    # From tools/ go up to victor/, then to team1a/, then to mcp_test/, then into data/Catalogs10_18/
    catalog_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "..", "data", "Catalogs10_18")
    catalog_dir = os.path.abspath(catalog_dir)  # Normalize the path
    catalog_path = os.path.join(catalog_dir, catalog_files[catalog_name])
    
    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")
    
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    
    return catalog


def get_api_endpoint(catalog: Dict[str, Any]) -> str:
    """
    Extract API endpoint from catalog.
    
    Args:
        catalog: Loaded catalog dictionary
        
    Returns:
        API endpoint URL
    """
    return catalog.get("stacApiUrl", "").rstrip('/')


def list_collections(catalog: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    List all available collections in catalog.
    
    Args:
        catalog: Loaded catalog dictionary
        
    Returns:
        List of dictionaries with collection metadata
    """
    collections = []
    
    for col in catalog.get("collections", []):
        collection_info = {
            "id": col.get("id"),
            "title": col.get("title", "No title"),
            "description": col.get("description", "")[:150] + "..."
            if len(col.get("description", "")) > 150 else col.get("description", "")
        }
        
        # Get temporal extent
        extent = col.get("extent", {})
        temporal = extent.get("temporal", {})
        interval = temporal.get("interval", [[None, None]])[0]
        
        if interval[0]:
            collection_info["start_date"] = interval[0]
        if interval[1]:
            collection_info["end_date"] = interval[1]
        else:
            collection_info["end_date"] = "present (ongoing)"
        
        # Get spatial extent
        spatial = extent.get("spatial", {})
        bbox = spatial.get("bbox", [[]])
        if bbox and bbox[0]:
            collection_info["spatial_extent"] = bbox[0]
        
        collections.append(collection_info)
    
    return collections


def get_collection_info(catalog: Dict[str, Any], collection_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific collection.
    
    Args:
        catalog: Loaded catalog dictionary
        collection_id: ID of the collection
        
    Returns:
        Dictionary with collection details or None if not found
    """
    for col in catalog.get("collections", []):
        if col.get("id") == collection_id:
            # Extract metadata
            info = {
                "id": col.get("id"),
                "title": col.get("title", "No title"),
                "description": col.get("description", ""),
                "license": col.get("license", "unknown")
            }
            
            # Get temporal extent
            extent = col.get("extent", {})
            temporal = extent.get("temporal", {})
            interval = temporal.get("interval", [[None, None]])[0]
            
            info["temporal"] = {
                "start": interval[0],
                "end": interval[1] or "present"
            }
            
            # Get spatial extent
            spatial = extent.get("spatial", {})
            bbox = spatial.get("bbox", [[]])
            if bbox and bbox[0]:
                info["spatial_bbox"] = bbox[0]
            
            # Get available assets
            item_assets = col.get("item_assets", {})
            info["available_assets"] = list(item_assets.keys())
            
            # Get asset details
            info["asset_details"] = {}
            for asset_key, asset_data in item_assets.items():
                info["asset_details"][asset_key] = {
                    "type": asset_data.get("type", "unknown"),
                    "title": asset_data.get("title", ""),
                    "roles": asset_data.get("roles", [])
                }
            
            # Get providers
            providers = col.get("providers", [])
            info["providers"] = [
                {"name": p.get("name"), "roles": p.get("roles", [])}
                for p in providers
            ]
            
            return info
    
    return None


def get_suggested_date_range(catalog: Dict[str, Any], collection_id: str) -> Dict[str, Optional[str]]:
    """
    Get suggested date range for a collection based on its temporal extent.
    
    Args:
        catalog: Loaded catalog dictionary
        collection_id: ID of the collection
        
    Returns:
        Dictionary with 'start' and 'end' dates
    """
    collection = get_collection_info(catalog, collection_id)
    
    if not collection:
        return {"start": None, "end": None}
    
    temporal = collection.get("temporal", {})
    start_date = temporal.get("start")
    end_date = temporal.get("end")
    
    # Parse dates
    suggested_start = None
    suggested_end = "today"
    
    if start_date:
        try:
            # Parse ISO date
            dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            suggested_start = dt.strftime("%Y-%m-%d")
        except:
            suggested_start = start_date.split('T')[0] if 'T' in start_date else start_date
    
    if end_date and end_date != "present":
        try:
            dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            suggested_end = dt.strftime("%Y-%m-%d")
        except:
            suggested_end = end_date.split('T')[0] if 'T' in end_date else end_date
    
    return {
        "start": suggested_start,
        "end": suggested_end,
        "start_full": start_date,
        "end_full": end_date
    }


def get_available_assets(catalog: Dict[str, Any], collection_id: str) -> List[str]:
    """
    Get list of available asset keys for a collection.
    
    Args:
        catalog: Loaded catalog dictionary
        collection_id: ID of the collection
        
    Returns:
        List of asset keys
    """
    collection = get_collection_info(catalog, collection_id)
    
    if not collection:
        return []
    
    return collection.get("available_assets", [])


def validate_collection(catalog: Dict[str, Any], collection_id: str) -> bool:
    """
    Check if a collection exists in the catalog.
    
    Args:
        catalog: Loaded catalog dictionary
        collection_id: ID of the collection
        
    Returns:
        True if collection exists, False otherwise
    """
    return get_collection_info(catalog, collection_id) is not None

