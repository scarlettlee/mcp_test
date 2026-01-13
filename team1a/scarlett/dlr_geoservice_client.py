"""
DLR Geoservice STAC API Client

This client works with the DLR Geoservice STAC API at:
https://geoservice.dlr.de/eoc/ogc/stac/v1/

Unlike Planetary Computer, DLR Geoservice uses standard OGC STAC API
and may not require SAS token signing for asset URLs.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from pathlib import Path

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))


class DLRGeoserviceClient:
    """
    Client for DLR Geoservice STAC API.
    
    Uses standard OGC STAC API endpoints without SAS token requirements.
    """
    
    def __init__(self, stac_api_url: str = "https://geoservice.dlr.de/eoc/ogc/stac/v1"):
        """
        Initialize the DLR Geoservice client.
        
        Args:
            stac_api_url: Base URL for the STAC API
        """
        self.stac_api_url = stac_api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DLRGeoserviceClient/1.0',
            'Accept': 'application/json'
        })
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get all collections from the STAC API.
        
        Returns:
            List of collection dictionaries
        """
        collections_url = f"{self.stac_api_url}/collections"
        
        try:
            response = self.session.get(collections_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Handle both paginated and non-paginated responses
            if 'collections' in data:
                return data.get('collections', [])
            elif isinstance(data, list):
                return data
            else:
                return []
        except Exception as e:
            raise RuntimeError(f"Failed to fetch collections: {str(e)}")
    
    def get_collection_info(self, collection_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Collection metadata dictionary
        """
        collection_url = f"{self.stac_api_url}/collections/{collection_id}"
        
        try:
            # Try with JSON format parameter
            params = {'f': 'application/json'}
            response = self.session.get(collection_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Try without format parameter
            try:
                response = self.session.get(collection_url, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e2:
                raise RuntimeError(f"Failed to fetch collection {collection_id}: {str(e2)}")
    
    def search_items(
        self,
        collection: str,
        bbox: List[float],
        datetime_range: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for STAC items in a collection.
        
        Args:
            collection: Collection ID
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            datetime_range: Optional datetime range (e.g., "2023-01-01/2023-12-31")
            limit: Maximum number of items to return
            **kwargs: Additional search parameters
            
        Returns:
            STAC search response with features
        """
        search_url = f"{self.stac_api_url}/search"
        
        # Build search parameters
        search_params = {
            "collections": [collection],
            "bbox": bbox,
            "limit": limit
        }
        
        if datetime_range:
            search_params["datetime"] = datetime_range
        
        # Add any additional parameters
        search_params.update(kwargs)
        
        try:
            # Try POST request first (OGC STAC standard)
            response = self.session.post(
                search_url,
                json=search_params,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            response.raise_for_status()
            results = response.json()
            
            # Handle pagination if present
            features = results.get('features', [])
            
            # If there are more results and we haven't reached the limit
            if 'links' in results:
                next_link = None
                for link in results['links']:
                    if link.get('rel') == 'next':
                        next_link = link.get('href')
                        break
                
                # For now, we'll just return what we have
                # Full pagination handling can be added if needed
            
            return results
        except requests.exceptions.HTTPError as e:
            # Handle server errors gracefully
            if e.response.status_code >= 500:
                # Server error - return empty results instead of crashing
                print(f"      Warning: Server error ({e.response.status_code}) for {collection}")
                return {'type': 'FeatureCollection', 'features': []}
            # Try GET request as fallback for client errors
            try:
                get_params = {
                    "collections": collection,
                    "bbox": ",".join(map(str, bbox)),
                    "limit": limit
                }
                if datetime_range:
                    get_params["datetime"] = datetime_range
                
                response = self.session.get(search_url, params=get_params, timeout=60)
                response.raise_for_status()
                return response.json()
            except Exception as e2:
                raise RuntimeError(f"Failed to search items in {collection}: {str(e2)}")
        except requests.exceptions.RequestException as e:
            # Try GET request as fallback
            try:
                get_params = {
                    "collections": collection,
                    "bbox": ",".join(map(str, bbox)),
                    "limit": limit
                }
                if datetime_range:
                    get_params["datetime"] = datetime_range
                
                response = self.session.get(search_url, params=get_params, timeout=60)
                response.raise_for_status()
                return response.json()
            except Exception as e2:
                raise RuntimeError(f"Failed to search items in {collection}: {str(e2)}")
    
    def get_item(self, collection_id: str, item_id: str) -> Dict[str, Any]:
        """
        Get a specific STAC item.
        
        Args:
            collection_id: Collection ID
            item_id: Item ID
            
        Returns:
            STAC item dictionary
        """
        item_url = f"{self.stac_api_url}/collections/{collection_id}/items/{item_id}"
        
        try:
            params = {'f': 'application/json'}
            response = self.session.get(item_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch item {item_id} from {collection_id}: {str(e)}")
    
    def load_collections_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load collections from a local JSON file (e.g., exported catalog).
        
        Args:
            json_path: Path to JSON file containing collections
            
        Returns:
            List of collection dictionaries
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if 'collections' in data:
                return data['collections']
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Invalid JSON structure: expected 'collections' key or list")
        except Exception as e:
            raise RuntimeError(f"Failed to load collections from {json_path}: {str(e)}")
    
    def find_collection_by_id(
        self,
        collection_id: str,
        json_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a collection by ID, either from API or local JSON.
        
        Args:
            collection_id: Collection ID to find
            json_path: Optional path to local JSON file
            
        Returns:
            Collection dictionary or None if not found
        """
        if json_path and os.path.exists(json_path):
            collections = self.load_collections_from_json(json_path)
            for col in collections:
                if col.get('id') == collection_id:
                    return col
        
        # Try API
        try:
            return self.get_collection_info(collection_id)
        except Exception:
            return None

