"""
DLR Geoservice ESG Data Retriever

Retrieves and downloads ESG-relevant data from DLR Geoservice STAC API
for collections matched in the ESG mapping table.
"""

import sys
import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))
sys.path.insert(0, os.path.dirname(__file__))

from dlr_geoservice_client import DLRGeoserviceClient

# San Francisco bounding box [min_lon, min_lat, max_lon, max_lat]
SAN_FRANCISCO_BBOX = [-122.5, 37.7, -122.3, 37.8]


class DLRGeoserviceRetriever:
    """Retrieves and analyzes ESG-relevant data from DLR Geoservice."""
    
    def __init__(self, bbox: List[float], output_dir: str = "dlr_geoservice_data"):
        """
        Initialize the DLR Geoservice ESG data retriever.
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            output_dir: Output directory for downloaded data
        """
        self.bbox = bbox
        self.client = DLRGeoserviceClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def retrieve_collections(
        self,
        collections: List[Dict[str, Any]],
        download_assets: bool = True,
        max_items_per_collection: int = 10,
        catalog_json_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve data for specified collections.
        
        Args:
            collections: List of collection dictionaries from CSV parser
            download_assets: Whether to download asset files
            max_items_per_collection: Maximum items per collection
            catalog_json_path: Optional path to local catalog JSON file
            
        Returns:
            Dictionary with retrieval results
        """
        print(f"\n{'='*70}")
        print(f"Retrieving DLR Geoservice ESG Data for {len(collections)} Collections")
        print(f"{'='*70}\n")
        
        results = {
            'bbox': self.bbox,
            'collections_requested': len(collections),
            'collections_processed': 0,
            'collections_successful': 0,
            'collections_failed': 0,
            'collection_results': []
        }
        
        # Group by dataset_id to avoid duplicates
        unique_collections = {}
        for col in collections:
            dataset_id = col['dataset_id']
            if dataset_id not in unique_collections:
                unique_collections[dataset_id] = col
        
        print(f"Processing {len(unique_collections)} unique collections\n")
        
        for dataset_id, col_info in unique_collections.items():
            print(f"\n{'='*70}")
            print(f"Collection: {dataset_id}")
            print(f"Title: {col_info.get('dataset_title', 'N/A')}")
            print(f"ESG Reason: {col_info.get('matching_reason', 'N/A')}")
            print(f"{'='*70}")
            
            try:
                # Get collection info from STAC API or local JSON
                if catalog_json_path and os.path.exists(catalog_json_path):
                    collection_info = self.client.find_collection_by_id(
                        dataset_id,
                        json_path=catalog_json_path
                    )
                else:
                    collection_info = self.client.get_collection_info(dataset_id)
                
                if not collection_info:
                    print(f"  → Collection {dataset_id} not found")
                    results['collection_results'].append({
                        'dataset_id': dataset_id,
                        'status': 'not_found',
                        'items_found': 0
                    })
                    continue
                
                # Determine datetime range based on matching reason
                datetime_range = self._determine_datetime_range(col_info.get('matching_reason', ''))
                
                # Check if collection extent overlaps with our bbox
                collection_extent = collection_info.get('extent', {}).get('spatial', {}).get('bbox', [[]])
                use_global_bbox = False
                
                if collection_extent and collection_extent[0]:
                    # Check if San Francisco bbox overlaps with collection extent
                    coll_bbox = collection_extent[0]
                    if len(coll_bbox) >= 4:
                        # Simple overlap check
                        sf_overlaps = not (
                            self.bbox[2] < coll_bbox[0] or  # SF east < collection west
                            self.bbox[0] > coll_bbox[2] or  # SF west > collection east
                            self.bbox[3] < coll_bbox[1] or  # SF north < collection south
                            self.bbox[1] > coll_bbox[3]     # SF south > collection north
                        )
                        if not sf_overlaps:
                            print(f"  → San Francisco bbox doesn't overlap with collection extent")
                            print(f"     Using global bbox instead")
                            use_global_bbox = True
                
                # Use global bbox if needed (for Europe-focused datasets)
                search_bbox = [-180, -90, 180, 90] if use_global_bbox else self.bbox
                
                # Search for items
                try:
                    search_results = self.client.search_items(
                        collection=dataset_id,
                        bbox=search_bbox,
                        datetime_range=datetime_range,
                        limit=max_items_per_collection
                    )
                except RuntimeError as e:
                    # If search fails with specific bbox, try without bbox constraint
                    if '500' in str(e) and not use_global_bbox:
                        print(f"  → Search failed with SF bbox, trying without spatial constraint...")
                        try:
                            search_results = self.client.search_items(
                                collection=dataset_id,
                                bbox=[-180, -90, 180, 90],
                                datetime_range=datetime_range,
                                limit=max_items_per_collection
                            )
                        except Exception:
                            # If still fails, return empty results
                            search_results = {'type': 'FeatureCollection', 'features': []}
                    else:
                        search_results = {'type': 'FeatureCollection', 'features': []}
                
                items = search_results.get('features', [])
                
                if not items:
                    print(f"  → No items found for {dataset_id}")
                    results['collection_results'].append({
                        'dataset_id': dataset_id,
                        'status': 'no_items',
                        'items_found': 0
                    })
                    continue
                
                print(f"  → Found {len(items)} items")
                
                # Process items
                processed_items = []
                for item in items:
                    item_result = self._process_item(item, col_info)
                    processed_items.append(item_result)
                    
                    # Download assets if requested
                    if download_assets:
                        self._download_item_assets(item, dataset_id)
                
                # Extract relevant variables based on matching reason
                variables = self._extract_relevant_variables(col_info.get('matching_reason', ''))
                
                result = {
                    'dataset_id': dataset_id,
                    'dataset_title': col_info.get('dataset_title', ''),
                    'matching_reason': col_info.get('matching_reason', ''),
                    'status': 'success',
                    'items_found': len(items),
                    'items_processed': len(processed_items),
                    'relevant_variables': variables,
                    'datetime_range': datetime_range,
                    'items': processed_items,
                    'collection_info': {
                        'title': collection_info.get('title', ''),
                        'description': collection_info.get('description', ''),
                        'extent': collection_info.get('extent', {})
                    }
                }
                
                results['collection_results'].append(result)
                results['collections_successful'] += 1
                
            except Exception as e:
                print(f"  → Error: {str(e)}")
                import traceback
                traceback.print_exc()
                results['collection_results'].append({
                    'dataset_id': dataset_id,
                    'status': 'error',
                    'error': str(e)
                })
                results['collections_failed'] += 1
            
            results['collections_processed'] += 1
        
        return results
    
    def _determine_datetime_range(self, matching_reason: str) -> Optional[str]:
        """
        Determine datetime range based on matching reason.
        
        Args:
            matching_reason: Matching reason text
            
        Returns:
            Datetime range string or None
        """
        reason_lower = matching_reason.lower()
        
        # Historical baseline (past 10-20 years)
        if 'historical' in reason_lower or 'baseline' in reason_lower or 'past' in reason_lower:
            end_date = datetime.now()
            start_date = datetime(end_date.year - 20, 1, 1)
            return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Long-term trends (40+ years for TIMELINE)
        if '40+' in matching_reason or 'long-term' in reason_lower:
            end_date = datetime.now()
            start_date = datetime(end_date.year - 40, 1, 1)
            return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Recent data (last 5 years)
        if 'recent' in reason_lower or 'current' in reason_lower:
            end_date = datetime.now()
            start_date = datetime(end_date.year - 5, 1, 1)
            return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Default: last 10 years
        end_date = datetime.now()
        start_date = datetime(end_date.year - 10, 1, 1)
        return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
    
    def _extract_relevant_variables(self, matching_reason: str) -> List[str]:
        """
        Extract relevant variable names based on matching reason.
        
        Args:
            matching_reason: Matching reason text
            
        Returns:
            List of variable names
        """
        variables = []
        reason_lower = matching_reason.lower()
        
        # Temperature variables
        if 'temperature' in reason_lower or 'temp' in reason_lower or 'thermal' in reason_lower or 'lst' in reason_lower:
            variables.extend(['LST', 'LSTD', 'temperature', 'temp'])
        
        # Water variables
        if 'water' in reason_lower or 'drought' in reason_lower or 'stress' in reason_lower:
            variables.extend(['water', 'water_extent', 'water_occurrence'])
        
        # Snow variables
        if 'snow' in reason_lower or 'snowpack' in reason_lower:
            variables.extend(['snow_cover', 'snow_extent', 'snow_duration'])
        
        # Elevation/terrain variables
        if 'elevation' in reason_lower or 'dem' in reason_lower or 'terrain' in reason_lower:
            variables.extend(['elevation', 'dem', 'height'])
        
        # Settlement variables
        if 'settlement' in reason_lower or 'wsf' in reason_lower:
            variables.extend(['settlement', 'built_up', 'urban'])
        
        # Hazard variables
        if 'hazard' in reason_lower or 'flood' in reason_lower or 'deformation' in reason_lower:
            variables.extend(['flood', 'deformation', 'hazard'])
        
        # Remove duplicates
        return list(set(variables))
    
    def _process_item(self, item: Dict[str, Any], col_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single STAC item.
        
        Args:
            item: STAC item dictionary
            col_info: Collection information from CSV
            
        Returns:
            Processed item dictionary
        """
        item_id = item.get('id', 'unknown')
        assets = item.get('assets', {})
        properties = item.get('properties', {})
        
        # Extract asset information
        asset_info = {}
        for asset_key, asset in assets.items():
            asset_info[asset_key] = {
                'href': asset.get('href', ''),
                'type': asset.get('type', ''),
                'roles': asset.get('roles', []),
                'title': asset.get('title', '')
            }
        
        return {
            'item_id': item_id,
            'datetime': properties.get('datetime', 'unknown'),
            'assets_count': len(assets),
            'assets': asset_info,
            'bbox': item.get('bbox', [])
        }
    
    def _download_item_assets(self, item: Dict[str, Any], collection_id: str):
        """
        Download assets for an item.
        
        Args:
            item: STAC item dictionary
            collection_id: Collection ID
        """
        assets = item.get('assets', {})
        item_id = item.get('id', 'unknown')
        
        # Create collection-specific directory
        collection_dir = self.output_dir / collection_id
        collection_dir.mkdir(exist_ok=True)
        
        for asset_key, asset in assets.items():
            href = asset.get('href', '')
            if not href:
                continue
            
            # Skip metadata and thumbnail assets
            roles = asset.get('roles', [])
            if 'metadata' in roles or 'thumbnail' in roles or 'overview' in roles:
                continue
            
            try:
                # Determine file extension
                file_ext = 'tif'
                if href.endswith('.tif') or href.endswith('.tiff'):
                    file_ext = 'tif'
                elif href.endswith('.nc'):
                    file_ext = 'nc'
                elif href.endswith('.json'):
                    file_ext = 'json'
                elif href.endswith('.geojson'):
                    file_ext = 'geojson'
                
                filename = f"{item_id}_{asset_key}.{file_ext}"
                filepath = collection_dir / filename
                
                # Download file
                response = requests.get(href, timeout=120, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"    ✓ Downloaded {asset_key}: {filepath}")
                
            except Exception as e:
                print(f"    ✗ Failed to download {asset_key}: {str(e)}")

