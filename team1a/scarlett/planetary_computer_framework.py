"""
Comprehensive Planetary Computer Data Retrieval Framework

This framework follows Microsoft's official SAS token documentation:
https://planetarycomputer.microsoft.com/docs/concepts/sas/

Features:
- Loads all collections from STAC catalog JSON
- Properly signs URLs using SAS tokens via planetary-computer package
- Handles different data types (raster, vector, zarr, etc.)
- Retrieves data for San Francisco area
- Comprehensive error handling and logging
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from pathlib import Path

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))

# Import planetary-computer for SAS token signing
try:
    import planetary_computer
    PLANETARY_COMPUTER_AVAILABLE = True
except ImportError:
    PLANETARY_COMPUTER_AVAILABLE = False
    print("Warning: planetary-computer package not available. Install with: pip install planetary-computer")

# Optional dependencies for data processing
try:
    import rasterio
    from rasterio.plot import reshape_as_image
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class PlanetaryComputerClient:
    """
    Client for Microsoft Planetary Computer STAC API with proper SAS token handling.
    
    Follows Microsoft's official documentation:
    https://planetarycomputer.microsoft.com/docs/concepts/sas/
    """
    
    def __init__(self, stac_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"):
        """
        Initialize the Planetary Computer client.
        
        Args:
            stac_api_url: Base URL for the STAC API
        """
        self.stac_api_url = stac_api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PlanetaryComputerClient/1.0'
        })
        
        if not PLANETARY_COMPUTER_AVAILABLE:
            raise ImportError(
                "planetary-computer package is required. "
                "Install with: pip install planetary-computer"
            )
    
    def sign_url(self, url: str) -> str:
        """
        Sign a URL with a SAS token using planetary-computer package.
        
        According to Microsoft docs, this uses the sign endpoint:
        https://planetarycomputer.microsoft.com/api/sas/v1/sign?href={url}
        
        The planetary-computer package handles this automatically.
        
        Args:
            url: Unsigned Azure Blob Storage URL
            
        Returns:
            Signed URL with SAS token
        """
        if not PLANETARY_COMPUTER_AVAILABLE:
            raise RuntimeError("planetary-computer package not available")
        
        try:
            # Use planetary_computer.sign() as per Microsoft documentation
            # This automatically handles token caching and expiration
            signed_url = planetary_computer.sign(url)
            return signed_url
        except Exception as e:
            raise RuntimeError(f"Failed to sign URL: {str(e)}")
    
    def sign_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign all assets in a STAC item.
        
        Args:
            item: STAC item dictionary
            
        Returns:
            Item with all asset URLs signed
        """
        if not PLANETARY_COMPUTER_AVAILABLE:
            return item
        
        signed_item = item.copy()
        signed_assets = {}
        
        for asset_key, asset in item.get('assets', {}).items():
            signed_asset = asset.copy()
            href = asset.get('href', '')
            
            # Only sign Azure Blob Storage URLs
            if href.startswith('https://') and '.blob.core.windows.net' in href:
                try:
                    signed_asset['href'] = self.sign_url(href)
                    signed_asset['signed'] = True
                except Exception as e:
                    print(f"Warning: Failed to sign asset {asset_key}: {str(e)}")
                    signed_asset['signed'] = False
                    signed_asset['sign_error'] = str(e)
            else:
                # Non-blob URLs don't need signing
                signed_asset['signed'] = False
            
            signed_assets[asset_key] = signed_asset
        
        signed_item['assets'] = signed_assets
        return signed_item
    
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
            return data.get('collections', [])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch collections: {str(e)}")
    
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
            response = self.session.post(search_url, json=search_params, timeout=60)
            response.raise_for_status()
            results = response.json()
            
            # Sign all items in the results
            signed_features = []
            for feature in results.get('features', []):
                signed_item = self.sign_item(feature)
                signed_features.append(signed_item)
            
            results['features'] = signed_features
            return results
        except Exception as e:
            raise RuntimeError(f"Failed to search items in {collection}: {str(e)}")
    
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
            response = self.session.get(collection_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch collection {collection_id}: {str(e)}")


class CollectionProcessor:
    """
    Processes collections and retrieves data for a specific area.
    """
    
    def __init__(self, client: PlanetaryComputerClient, output_dir: str = "downloads"):
        """
        Initialize the collection processor.
        
        Args:
            client: PlanetaryComputerClient instance
            output_dir: Directory to save downloaded data
        """
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different data types
        self.raster_dir = self.output_dir / "rasters"
        self.vector_dir = self.output_dir / "vectors"
        self.metadata_dir = self.output_dir / "metadata"
        
        for dir_path in [self.raster_dir, self.vector_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def load_collections_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load collections from a JSON file.
        
        Args:
            json_path: Path to the JSON file containing collections
            
        Returns:
            List of collection dictionaries
        """
        json_path = Path(json_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"Collections JSON file not found: {json_path}")
        
        print(f"Loading collections from {json_path}...")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            collections = data.get('collections', [])
            print(f"Loaded {len(collections)} collections from JSON file")
            return collections
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to load collections: {str(e)}")
    
    def process_collection(
        self,
        collection: Dict[str, Any],
        bbox: List[float],
        datetime_range: Optional[str] = None,
        max_items: int = 5,
        download_assets: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single collection: search for items and optionally download.
        
        Args:
            collection: Collection dictionary
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            datetime_range: Optional datetime range
            max_items: Maximum number of items to retrieve
            download_assets: Whether to download asset files
            
        Returns:
            Dictionary with processing results
        """
        collection_id = collection.get('id', 'unknown')
        collection_title = collection.get('title', collection_id)
        
        print(f"\n{'='*70}")
        print(f"Processing collection: {collection_id}")
        print(f"Title: {collection_title}")
        print(f"{'='*70}")
        
        result = {
            'collection_id': collection_id,
            'collection_title': collection_title,
            'status': 'pending',
            'items_found': 0,
            'items_processed': 0,
            'errors': []
        }
        
        try:
            # Check if collection spatial extent overlaps with bbox
            extent = collection.get('extent', {})
            spatial = extent.get('spatial', {})
            collection_bboxes = spatial.get('bbox', [])
            
            if collection_bboxes:
                # Check if any collection bbox overlaps with our search area
                overlaps = False
                for cb in collection_bboxes:
                    if self._bboxes_overlap(cb, bbox):
                        overlaps = True
                        break
                
                if not overlaps:
                    result['status'] = 'skipped'
                    result['reason'] = 'Collection extent does not overlap with search area'
                    print(f"  → Skipped: Collection extent does not overlap with search area")
                    return result
            
            # Search for items
            search_results = self.client.search_items(
                collection=collection_id,
                bbox=bbox,
                datetime_range=datetime_range,
                limit=max_items
            )
            
            items = search_results.get('features', [])
            result['items_found'] = len(items)
            
            if not items:
                result['status'] = 'no_items'
                result['reason'] = 'No items found in search area'
                print(f"  → No items found")
                return result
            
            print(f"  → Found {len(items)} items")
            
            # Process each item
            processed_items = []
            for idx, item in enumerate(items):
                try:
                    item_result = self._process_item(
                        item=item,
                        collection_id=collection_id,
                        download_assets=download_assets
                    )
                    processed_items.append(item_result)
                    result['items_processed'] += 1
                    
                    print(f"    [{idx+1}/{len(items)}] {item.get('id', 'unknown')}: "
                          f"{item_result.get('status', 'unknown')}")
                except Exception as e:
                    error_msg = f"Error processing item {item.get('id', 'unknown')}: {str(e)}"
                    result['errors'].append(error_msg)
                    print(f"    [{idx+1}/{len(items)}] Error: {str(e)}")
            
            result['items'] = processed_items
            result['status'] = 'success'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['errors'].append(str(e))
            print(f"  → Error: {str(e)}")
        
        return result
    
    def _process_item(
        self,
        item: Dict[str, Any],
        collection_id: str,
        download_assets: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single STAC item.
        
        Args:
            item: STAC item dictionary
            collection_id: Collection ID
            download_assets: Whether to download asset files
            
        Returns:
            Dictionary with item processing results
        """
        item_id = item.get('id', 'unknown')
        assets = item.get('assets', {})
        
        result = {
            'item_id': item_id,
            'collection_id': collection_id,
            'datetime': item.get('properties', {}).get('datetime', 'unknown'),
            'assets_count': len(assets),
            'assets': {},
            'status': 'success'
        }
        
        # Process each asset
        for asset_key, asset in assets.items():
            asset_info = {
                'key': asset_key,
                'href': asset.get('href', ''),
                'type': asset.get('type', 'unknown'),
                'roles': asset.get('roles', []),
                'signed': asset.get('signed', False)
            }
            
            # Download asset if requested
            if download_assets and asset_info['signed']:
                try:
                    download_path = self._download_asset(
                        asset=asset,
                        item_id=item_id,
                        asset_key=asset_key,
                        collection_id=collection_id
                    )
                    asset_info['download_path'] = str(download_path)
                    asset_info['downloaded'] = True
                except Exception as e:
                    asset_info['download_error'] = str(e)
                    asset_info['downloaded'] = False
            
            result['assets'][asset_key] = asset_info
        
        return result
    
    def _download_asset(
        self,
        asset: Dict[str, Any],
        item_id: str,
        asset_key: str,
        collection_id: str
    ) -> Path:
        """
        Download an asset file.
        
        Args:
            asset: Asset dictionary
            item_id: Item ID
            asset_key: Asset key
            collection_id: Collection ID
            
        Returns:
            Path to downloaded file
        """
        href = asset.get('href', '')
        if not href:
            raise ValueError("Asset has no href")
        
        # Determine output directory based on asset type
        asset_type = asset.get('type', '')
        roles = asset.get('roles', [])
        
        if 'data' in roles or 'visual' in roles:
            if 'image' in asset_type or 'tif' in href.lower() or 'geotif' in asset_type.lower():
                output_dir = self.raster_dir / collection_id
            else:
                output_dir = self.vector_dir / collection_id
        else:
            output_dir = self.metadata_dir / collection_id
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get file extension
        file_ext = 'tif'
        if '.' in href.split('?')[0]:
            file_ext = href.split('?')[0].split('.')[-1]
        
        # Create filename
        filename = f"{item_id}_{asset_key}.{file_ext}"
        filepath = output_dir / filename
        
        # Download file
        response = requests.get(href, timeout=300, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
    
    def _bboxes_overlap(self, bbox1: List[float], bbox2: List[float]) -> bool:
        """
        Check if two bounding boxes overlap.
        
        Args:
            bbox1: First bounding box [min_lon, min_lat, max_lon, max_lat]
            bbox2: Second bounding box [min_lon, min_lat, max_lon, max_lat]
            
        Returns:
            True if bboxes overlap, False otherwise
        """
        # Handle both 2D and 3D bboxes
        if len(bbox1) >= 4 and len(bbox2) >= 4:
            min_lon1, min_lat1, max_lon1, max_lat1 = bbox1[0], bbox1[1], bbox1[2], bbox1[3]
            min_lon2, min_lat2, max_lon2, max_lat2 = bbox2[0], bbox2[1], bbox2[2], bbox2[3]
            
            # Check for overlap
            return not (max_lon1 < min_lon2 or max_lon2 < min_lon1 or
                       max_lat1 < min_lat2 or max_lat2 < min_lat1)
        
        return True  # If we can't determine, assume overlap
    
    def process_all_collections(
        self,
        collections: List[Dict[str, Any]],
        bbox: List[float],
        datetime_range: Optional[str] = None,
        max_items_per_collection: int = 5,
        download_assets: bool = False,
        collection_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process all collections.
        
        Args:
            collections: List of collection dictionaries
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            datetime_range: Optional datetime range
            max_items_per_collection: Maximum items per collection
            download_assets: Whether to download assets
            collection_filter: Optional list of collection IDs to process (None = all)
            
        Returns:
            Dictionary with processing results for all collections
        """
        results = {
            'total_collections': len(collections),
            'processed_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'skipped_collections': 0,
            'collections': [],
            'bbox': bbox,
            'datetime_range': datetime_range,
            'start_time': datetime.now().isoformat()
        }
        
        # Filter collections if needed
        if collection_filter:
            collections = [c for c in collections if c.get('id') in collection_filter]
            print(f"\nFiltered to {len(collections)} collections")
        
        print(f"\n{'='*70}")
        print(f"Processing {len(collections)} collections for San Francisco area")
        print(f"Bounding box: {bbox}")
        if datetime_range:
            print(f"Date range: {datetime_range}")
        print(f"{'='*70}\n")
        
        for idx, collection in enumerate(collections):
            try:
                collection_result = self.process_collection(
                    collection=collection,
                    bbox=bbox,
                    datetime_range=datetime_range,
                    max_items=max_items_per_collection,
                    download_assets=download_assets
                )
                
                results['collections'].append(collection_result)
                results['processed_collections'] += 1
                
                if collection_result['status'] == 'success':
                    results['successful_collections'] += 1
                elif collection_result['status'] == 'skipped':
                    results['skipped_collections'] += 1
                else:
                    results['failed_collections'] += 1
                
            except Exception as e:
                error_result = {
                    'collection_id': collection.get('id', 'unknown'),
                    'status': 'error',
                    'error': str(e)
                }
                results['collections'].append(error_result)
                results['failed_collections'] += 1
                print(f"  → Error processing collection: {str(e)}")
        
        results['end_time'] = datetime.now().isoformat()
        
        # Print summary
        print(f"\n{'='*70}")
        print("Processing Summary")
        print(f"{'='*70}")
        print(f"Total collections: {results['total_collections']}")
        print(f"Processed: {results['processed_collections']}")
        print(f"Successful: {results['successful_collections']}")
        print(f"Skipped: {results['skipped_collections']}")
        print(f"Failed: {results['failed_collections']}")
        print(f"{'='*70}\n")
        
        return results






