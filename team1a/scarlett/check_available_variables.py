"""
Check what variables are available in NEX-GDDP-CMIP6 STAC catalog
"""
import planetary_computer
import pystac_client
from collections import Counter

# Setup
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

collection_id = "nasa-nex-gddp-cmip6"
bbox = [17.9, 46.8, 18, 46.9]  # Your study area
model = "UKESM1-0-LL"

print("="*60)
print("Checking Available Variables in NEX-GDDP-CMIP6")
print("="*60)

# Search for UKESM1-0-LL items
print(f"\nSearching for {model} items in your area...")
search = catalog.search(
    collections=[collection_id],
    bbox=bbox
)

# Collect item IDs and check their structure
items = list(search.items())
print(f"Found {len(items)} total items")

# Filter for UKESM1-0-LL
ukesm_items = [item for item in items if model in item.id]
print(f"Found {len(ukesm_items)} items for {model}")

# Check item properties and assets to identify variables
print("\n" + "="*60)
print("Analyzing item structure to identify variables...")
print("="*60)

# Sample a few items to see their structure
sample_items = {
    'historical': [item for item in ukesm_items if '.historical.' in item.id][:5],
    'ssp245': [item for item in ukesm_items if '.ssp245.' in item.id][:5]
}

for scenario_type, items_list in sample_items.items():
    if items_list:
        print(f"\n{scenario_type.upper()} items:")
        for item in items_list[:3]:
            print(f"\n  Item ID: {item.id}")
            print(f"  Assets available:")
            for asset_key, asset in item.assets.items():
                print(f"    - {asset_key}")
                if hasattr(asset, 'title') and asset.title:
                    print(f"      Title: {asset.title}")
                if hasattr(asset, 'description') and asset.description:
                    print(f"      Description: {asset.description[:100]}...")
            
            # Check item properties
            if hasattr(item, 'properties'):
                props = item.properties
                if 'eo:bands' in props:
                    print(f"  EO Bands: {props['eo:bands']}")
                if 'variables' in props:
                    print(f"  Variables: {props['variables']}")

# Check collection metadata
print("\n" + "="*60)
print("Collection Metadata:")
print("="*60)
collection = catalog.get_collection(collection_id)
if hasattr(collection, 'extra_fields'):
    if 'item_assets' in collection.extra_fields:
        print("\nItem Assets defined in collection:")
        for asset_key, asset_info in collection.extra_fields['item_assets'].items():
            print(f"  - {asset_key}")
            if isinstance(asset_info, dict):
                if 'title' in asset_info:
                    print(f"    Title: {asset_info['title']}")
                if 'description' in asset_info:
                    print(f"    Description: {asset_info['description'][:100]}...")

# Search for items with different variable names in their IDs
print("\n" + "="*60)
print("Checking item ID patterns for variable indicators...")
print("="*60)

# Common variable abbreviations
variable_patterns = {
    'pr': 'precipitation',
    'tas': 'temperature (average)',
    'tasmax': 'temperature (max)',
    'tasmin': 'temperature (min)',
    'hurs': 'relative humidity',
    'huss': 'specific humidity',
    'rlds': 'downwelling longwave radiation',
    'rsds': 'downwelling shortwave radiation',
    'sfcWind': 'surface wind speed'
}

# Check what asset keys (variables) are available across all items
print("\n" + "="*60)
print("Checking available asset keys (variables) in items...")
print("="*60)

all_asset_keys = set()
for item in ukesm_items[:50]:  # Check first 50 items
    all_asset_keys.update(item.assets.keys())

print(f"\nAll asset keys (variables) found: {sorted(all_asset_keys)}")

# Check if variables are in item IDs or need to be searched differently
print("\n" + "="*60)
print("Searching for items with different variable patterns...")
print("="*60)

for var_code, var_name in variable_patterns.items():
    # Check if variable exists as an asset key
    if var_code in all_asset_keys:
        matching_items = [item for item in ukesm_items if var_code in item.assets]
        print(f"  {var_code} ({var_name}): {len(matching_items)} items found (as asset key)")
        if len(matching_items) > 0:
            print(f"    Example item ID: {matching_items[0].id}")
    else:
        # Try searching with variable in item ID pattern
        matching_items = [item for item in ukesm_items if var_code in item.id.lower()]
        if matching_items:
            print(f"  {var_code} ({var_name}): {len(matching_items)} items found (in item ID)")
            if len(matching_items) > 0:
                print(f"    Example: {matching_items[0].id}")
        else:
            print(f"  {var_code} ({var_name}): Not found")

# Check if variables are stored as separate collections or need different search
print("\n" + "="*60)
print("NOTE: NEX-GDDP-CMIP6 may organize variables differently.")
print("Each STAC item might represent one variable-year combination.")
print("="*60)

