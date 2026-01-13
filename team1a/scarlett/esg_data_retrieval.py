"""
ESG Data Retrieval Script

This script reads the Joey - ESG Mapping.xlsx file to identify relevant
Planetary Computer collections for ESG risk analysis, then retrieves,
downloads, and analyzes the data according to the matching reasons.

Follows Microsoft's SAS token documentation:
https://planetarycomputer.microsoft.com/docs/concepts/sas/
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import framework
from planetary_computer_framework import PlanetaryComputerClient, CollectionProcessor

# Try to import pandas for Excel reading
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available. Install with: pip install pandas")

# Try to import openpyxl with better error handling
OPENPYXL_AVAILABLE = False
try:
    # Test if openpyxl can actually be used (not just imported)
    import openpyxl
    # Try a simple operation to verify it works
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
except Exception as e:
    # Handle DLL/expat issues
    OPENPYXL_AVAILABLE = False
    print(f"Warning: openpyxl has issues ({str(e)[:100]}). Will try alternative methods.")

# Try xlrd as alternative (for .xls files only)
XLRD_AVAILABLE = False
try:
    import xlrd  # type: ignore
    XLRD_AVAILABLE = True
except (ImportError, Exception):
    XLRD_AVAILABLE = False

# Try to import openpyxl with better error handling
OPENPYXL_AVAILABLE = False
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
except Exception as e:
    # Handle DLL/expat issues
    OPENPYXL_AVAILABLE = False
    print(f"Warning: openpyxl has issues ({str(e)[:100]}). Will try alternative methods.")

# San Francisco bounding box [min_lon, min_lat, max_lon, max_lat]
SAN_FRANCISCO_BBOX = [-122.5, 37.7, -122.3, 37.8]

# Paths
EXCEL_FILE = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.xlsx')
COLLECTIONS_JSON = os.path.join(project_root, 'data', 'Catalogs19_27', 'stac-tags-planetarycomputer.microsoft.com.json')


class ESGMappingParser:
    """Parser for the ESG mapping Excel file."""
    
    def __init__(self, excel_path: str):
        """
        Initialize the parser.
        
        Args:
            excel_path: Path to the Excel file
        """
        self.excel_path = excel_path
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    def parse_excel(self) -> List[Dict[str, Any]]:
        """
        Parse the Excel file and extract collection mappings.
        
        Returns:
            List of dictionaries with collection information
        """
        print(f"Reading Excel file: {self.excel_path}")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        # Try different engines
        engines_to_try = []
        
        if OPENPYXL_AVAILABLE:
            engines_to_try.append('openpyxl')
        # Note: xlrd only works with .xls (old format), not .xlsx
        # So we skip it for .xlsx files
        
        df = None
        last_error = None
        
        for engine in engines_to_try:
            try:
                print(f"  Trying engine: {engine}")
                df = pd.read_excel(self.excel_path, engine=engine)
                print(f"✓ Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
                print(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns
                break
            except Exception as e:
                last_error = e
                print(f"  ✗ Failed with {engine}: {str(e)[:200]}")
                continue
        
        if df is None:
            # Last resort: try without specifying engine
            try:
                print("  Trying default engine...")
                df = pd.read_excel(self.excel_path)
                print(f"✓ Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            except Exception as e:
                error_msg = f"Failed to read Excel file with all engines. Last error: {str(last_error)}"
                print(f"\n✗ {error_msg}")
                print("\n" + "="*70)
                print("TROUBLESHOOTING:")
                print("="*70)
                print("1. Fix openpyxl DLL/expat issue:")
                print("   conda install -c conda-forge openpyxl")
                print("   OR: conda install -c conda-forge expat libxml2")
                print("\n2. Alternative: Export Excel to CSV and use CSV parser")
                print("   See TROUBLESHOOTING.md for details")
                print("\n3. Create fresh conda environment:")
                print("   conda create -n esg_env python=3.10")
                print("   conda activate esg_env")
                print("   conda install -c conda-forge pandas openpyxl")
                print("="*70)
                raise RuntimeError(error_msg) from last_error
        
        # Extract collections
        collections = []
        
        # Iterate through all columns to find collection entries
        for col_idx, col_name in enumerate(df.columns):
            if col_idx < 5:  # Only print first 5 columns
                print(f"\nProcessing column: {col_name}")
            
            for row_idx, cell_value in enumerate(df[col_name]):
                if pd.isna(cell_value):
                    continue
                
                # Parse cell content
                cell_str = str(cell_value)
                parsed = self._parse_cell(cell_str, col_name, row_idx)
                
                if parsed:
                    collections.extend(parsed)
        
        print(f"\n✓ Extracted {len(collections)} collection entries")
        return collections
    
    def _parse_cell(self, cell_content: str, column_name: str, row_idx: int) -> List[Dict[str, Any]]:
        """
        Parse a cell content to extract collection information.
        
        Args:
            cell_content: Cell content string
            column_name: Name of the column
            row_idx: Row index
            
        Returns:
            List of parsed collection dictionaries
        """
        collections = []
        
        # Check if this cell contains geoservice for debugging
        has_geoservice = 'geoservice.dlr.de' in cell_content.lower()
        
        # Split by semicolons or <br> tags
        entries = re.split(r'[;\n]', cell_content)  # Split by semicolon or newline
        
        if has_geoservice:
            print(f"\n  DEBUG: Parsing cell with geoservice, found {len(entries)} entries after split")
        
        for idx, entry in enumerate(entries):
            entry = entry.strip()
            if not entry:
                continue
            
            if has_geoservice:
                # Show the entry being parsed
                print(f"    Entry {idx}: {entry[:150]}...")
            
            # Pattern: [catalog-name]-#. Dataset_ID, Dataset_Title (matching reason)
            # Example: planetarycomputer.microsoft.com-1. nasa-nex-gddp-cmip6, NASA NEX-GDDP-CMIP6 Climate Projections (assesses future temperature scenarios)
            # Note: dataset_id can contain underscores, so we use [\w-]+ which includes underscores via \w
            pattern = r'([\w\.-]+)-(\d+)\.\s*([\w_-]+),\s*([^(]+)\s*\(([^)]+)\)'
            match = re.search(pattern, entry)
            
            if match:
                catalog_name, entry_num, dataset_id, dataset_title, matching_reason = match.groups()
                
                collection_info = {
                    'catalog_name': catalog_name.strip(),
                    'entry_number': int(entry_num),
                    'dataset_id': dataset_id.strip(),
                    'dataset_title': dataset_title.strip(),
                    'matching_reason': matching_reason.strip(),
                    'column_name': column_name,
                    'row_index': row_idx,
                    'raw_entry': entry
                }
                
                collections.append(collection_info)
                
                if has_geoservice and 'geoservice' in catalog_name.lower():
                    print(f"      ✓ MATCHED DLR: {catalog_name} -> {dataset_id}")
            else:
                # Try simpler pattern without parentheses
                pattern2 = r'([\w\.-]+)-(\d+)\.\s*([\w_-]+),\s*(.+)'
                match2 = re.search(pattern2, entry)
                
                if match2:
                    catalog_name, entry_num, dataset_id, rest = match2.groups()
                    
                    collection_info = {
                        'catalog_name': catalog_name.strip(),
                        'entry_number': int(entry_num),
                        'dataset_id': dataset_id.strip(),
                        'dataset_title': rest.strip(),
                        'matching_reason': '',  # No matching reason found
                        'column_name': column_name,
                        'row_index': row_idx,
                        'raw_entry': entry
                    }
                    
                    collections.append(collection_info)
                    
                    if has_geoservice and 'geoservice' in catalog_name.lower():
                        print(f"      ✓ MATCHED DLR (no reason): {catalog_name} -> {dataset_id}")
                elif has_geoservice and 'geoservice' in entry.lower():
                    print(f"      ✗ FAILED TO PARSE: {entry[:100]}...")
        
        return collections
    
    def parse_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file as alternative to Excel (workaround for openpyxl issues).
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of dictionaries with collection information
        """
        print(f"Reading CSV file: {csv_path}")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required. Install with: pip install pandas")
        
        try:
            df = pd.read_csv(csv_path)
            print(f"✓ Loaded CSV file with {len(df)} rows and {len(df.columns)} columns")
            
            collections = []
            cells_with_geoservice = 0
            
            for col_idx, col_name in enumerate(df.columns):
                for row_idx, cell_value in enumerate(df[col_name]):
                    if pd.isna(cell_value):
                        continue
                    
                    cell_str = str(cell_value)
                    
                    # Debug: Check if cell contains geoservice
                    if 'geoservice' in cell_str.lower():
                        cells_with_geoservice += 1
                        print(f"\n  Found 'geoservice' in row {row_idx}, column '{col_name}':")
                        print(f"  Cell content: {cell_str[:200]}...")
                    
                    parsed = self._parse_cell(cell_str, col_name, row_idx)
                    if parsed:
                        collections.extend(parsed)
                        # Debug: Show parsed entries with geoservice
                        for p in parsed:
                            if 'geoservice' in p.get('catalog_name', '').lower():
                                print(f"    ✓ Parsed: {p.get('catalog_name')} -> {p.get('dataset_id')}")
            
            print(f"\n✓ Cells containing 'geoservice': {cells_with_geoservice}")
            print(f"✓ Extracted {len(collections)} collection entries total")
            return collections
            
        except Exception as e:
            print(f"✗ Error reading CSV file: {str(e)}")
            raise
    
    def filter_planetary_computer(self, collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter collections to only include Planetary Computer collections.
        
        Args:
            collections: List of collection dictionaries
            
        Returns:
            Filtered list
        """
        filtered = [
            c for c in collections
            if 'planetarycomputer.microsoft.com' in c.get('catalog_name', '').lower()
        ]
        print(f"✓ Filtered to {len(filtered)} Planetary Computer collections")
        return filtered
    
    def filter_dlr_geoservice(self, collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter collections to only include DLR Geoservice collections.
        
        Args:
            collections: List of collection dictionaries
            
        Returns:
            Filtered list
        """
        filtered = []
        for c in collections:
            catalog_name = c.get('catalog_name', '').lower()
            # Check for various forms of geoservice.dlr.de
            if 'geoservice.dlr.de' in catalog_name or 'geoservice' in catalog_name and 'dlr' in catalog_name:
                filtered.append(c)
        
        print(f"✓ Filtered to {len(filtered)} DLR Geoservice collections")
        if filtered:
            print(f"  Sample catalog names: {[c.get('catalog_name') for c in filtered[:5]]}")
        return filtered
    
    def filter_fedeo(self, collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter collections to only include FedEO collections.
        
        Args:
            collections: List of collection dictionaries
            
        Returns:
            Filtered list
        """
        filtered = []
        for c in collections:
            catalog_name = c.get('catalog_name', '').lower()
            if 'fedeo.ceos.org' in catalog_name or 'fedeo' in catalog_name:
                filtered.append(c)
        
        print(f"✓ Filtered to {len(filtered)} FedEO collections")
        if filtered:
            print(f"  Sample dataset IDs: {[c.get('dataset_id') for c in filtered[:5]]}")
        return filtered


class ESGDataRetriever:
    """Retrieves and analyzes ESG-relevant data from Planetary Computer."""
    
    def __init__(self, bbox: List[float], output_dir: str = "esg_data"):
        """
        Initialize the ESG data retriever.
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            output_dir: Output directory for downloaded data
        """
        self.bbox = bbox
        self.client = PlanetaryComputerClient()
        self.processor = CollectionProcessor(self.client, output_dir=output_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def retrieve_collections(
        self,
        collections: List[Dict[str, Any]],
        download_assets: bool = True,
        max_items_per_collection: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve data for specified collections.
        
        Args:
            collections: List of collection dictionaries from Excel parser
            download_assets: Whether to download asset files
            max_items_per_collection: Maximum items per collection
            
        Returns:
            Dictionary with retrieval results
        """
        print(f"\n{'='*70}")
        print(f"Retrieving ESG Data for {len(collections)} Collections")
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
                # Get collection info from STAC API
                collection_info = self.client.get_collection_info(dataset_id)
                
                # Determine datetime range based on matching reason
                datetime_range = self._determine_datetime_range(col_info.get('matching_reason', ''))
                
                # Search for items
                search_results = self.client.search_items(
                    collection=dataset_id,
                    bbox=self.bbox,
                    datetime_range=datetime_range,
                    limit=max_items_per_collection
                )
                
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
                    'items': processed_items
                }
                
                results['collection_results'].append(result)
                results['collections_successful'] += 1
                
            except Exception as e:
                print(f"  → Error: {str(e)}")
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
        
        # Future projections
        if 'future' in reason_lower or 'projection' in reason_lower or '2100' in reason_lower or '2050' in reason_lower:
            # For projections, get latest available data
            end_date = datetime.now()
            start_date = datetime(end_date.year - 5, 1, 1)
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
        
        # Climate variables
        if 'temperature' in reason_lower or 'temp' in reason_lower or 'heat' in reason_lower:
            variables.extend(['tasmax', 'tas', 'tmax', 'tmin', 'LST_Day', 'LST_Night'])
        
        if 'precipitation' in reason_lower or 'rain' in reason_lower or 'prcp' in reason_lower:
            variables.extend(['pr', 'prcp', 'precipitation'])
        
        # Water variables
        if 'water' in reason_lower or 'drought' in reason_lower or 'stress' in reason_lower:
            variables.extend(['pdsi', 'def', 'aet', 'pet', 'soil'])
        
        # Thermal variables
        if 'thermal' in reason_lower or 'heat island' in reason_lower:
            variables.extend(['LST_Day', 'LST_Night'])
        
        # Energy variables
        if 'energy' in reason_lower or 'cooling' in reason_lower:
            variables.extend(['tasmax', 'tas', 'tmax'])
        
        # Remove duplicates
        return list(set(variables))
    
    def _process_item(self, item: Dict[str, Any], col_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single STAC item.
        
        Args:
            item: STAC item dictionary
            col_info: Collection information from Excel
            
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
                'signed': asset.get('signed', False)
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
        
        for asset_key, asset in assets.items():
            if not asset.get('signed', False):
                continue
            
            try:
                href = asset.get('href', '')
                if not href:
                    continue
                
                # Download using processor
                download_path = self.processor._download_asset(
                    asset=asset,
                    item_id=item_id,
                    asset_key=asset_key,
                    collection_id=collection_id
                )
                
                print(f"    ✓ Downloaded {asset_key}: {download_path}")
                
            except Exception as e:
                print(f"    ✗ Failed to download {asset_key}: {str(e)}")


def main():
    """Main function."""
    print("=" * 70)
    print("ESG Data Retrieval from Planetary Computer")
    print("Following Microsoft SAS Token Documentation")
    print("=" * 70)
    print()
    
    # Check dependencies
    if not PANDAS_AVAILABLE:
        print("✗ pandas is required. Install with: pip install pandas")
        print("  Then install Excel engine: pip install openpyxl OR pip install xlrd")
        return
    
    if not OPENPYXL_AVAILABLE:
        print("⚠ Warning: openpyxl not available. Will try alternative Excel engines.")
        print("  For best results, install: pip install openpyxl")
        print("  Or: conda install -c conda-forge openpyxl")
    
    # Parse Excel file (or CSV as fallback)
    print("Step 1: Parsing ESG Mapping file...")
    parser = ESGMappingParser(EXCEL_FILE)
    
    # Try Excel first, fallback to CSV if available
    csv_file = EXCEL_FILE.replace('.xlsx', '.csv')
    if os.path.exists(csv_file):
        print(f"  CSV file found: {csv_file}")
        print("  Using CSV file (workaround for Excel reading issues)")
        all_collections = parser.parse_csv(csv_file)
    else:
        try:
            all_collections = parser.parse_excel()
        except Exception as e:
            print(f"\n✗ Failed to read Excel file: {str(e)}")
            print(f"\nWorkaround: Export Excel to CSV and save as:")
            print(f"  {csv_file}")
            print("Then run the script again.")
            return
    
    # Filter to Planetary Computer collections
    pc_collections = parser.filter_planetary_computer(all_collections)
    
    if not pc_collections:
        print("✗ No Planetary Computer collections found in Excel file")
        return
    
    print(f"\n✓ Found {len(pc_collections)} Planetary Computer collections")
    
    # Display collections
    print("\nCollections to retrieve:")
    for i, col in enumerate(pc_collections[:20], 1):  # Show first 20
        print(f"  {i}. {col['dataset_id']}: {col.get('dataset_title', 'N/A')}")
        print(f"     Reason: {col.get('matching_reason', 'N/A')[:100]}...")
    
    if len(pc_collections) > 20:
        print(f"  ... and {len(pc_collections) - 20} more collections")
    
    # Initialize retriever
    print("\nStep 2: Initializing Planetary Computer client...")
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, "esg_data_retrieval")
    
    retriever = ESGDataRetriever(
        bbox=SAN_FRANCISCO_BBOX,
        output_dir=output_dir
    )
    print(f"✓ Output directory: {output_dir}")
    
    # Retrieve collections
    print("\nStep 3: Retrieving collections...")
    results = retriever.retrieve_collections(
        collections=pc_collections,
        download_assets=True,  # Set to True to download files
        max_items_per_collection=5  # Adjust as needed
    )
    
    # Save results
    results_file = os.path.join(output_dir, "esg_retrieval_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to: {results_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("Retrieval Summary")
    print("=" * 70)
    print(f"Collections requested: {results['collections_requested']}")
    print(f"Collections processed: {results['collections_processed']}")
    print(f"Collections successful: {results['collections_successful']}")
    print(f"Collections failed: {results['collections_failed']}")
    
    # Show successful collections
    successful = [r for r in results['collection_results'] if r.get('status') == 'success']
    if successful:
        print(f"\nSuccessful collections ({len(successful)}):")
        for r in successful[:10]:  # Show first 10
            print(f"  • {r['dataset_id']}: {r.get('items_found', 0)} items")
            if r.get('relevant_variables'):
                print(f"    Variables: {', '.join(r['relevant_variables'])}")
    
    print("\n" + "=" * 70)
    print("Retrieval Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

