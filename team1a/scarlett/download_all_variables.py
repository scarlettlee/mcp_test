"""
Download all climate variables from UKESM1-0-LL NEX-GDDP-CMIP6 data
Each STAC item contains multiple variables as assets - download all of them
"""
import planetary_computer
import pystac_client
import urllib.request
import urllib.parse
import re
from pathlib import Path

def sanitize_filename(name):
    """Remove invalid characters for Windows filesystem"""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', name)

# Setup
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

# Configuration
collection_id = "nasa-nex-gddp-cmip6"
model = "UKESM1-0-LL"
bbox = [17.9, 46.8, 18, 46.9]  # Your study area
download_dir = Path("downloads/nasa-nex-gddp-cmip6")
download_dir.mkdir(parents=True, exist_ok=True)

# Variables to download (all available in NEX-GDDP-CMIP6)
variables = ['pr', 'tas', 'tasmax', 'tasmin', 'hurs', 'huss', 'rlds', 'rsds', 'sfcWind']

# Track downloads
stats = {
    'downloaded': 0,
    'skipped': 0,
    'already_downloaded': 0,
    'abfs_skipped': 0,
    'errors': 0
}

print("="*60)
print(f"Downloading ALL Variables from UKESM1-0-LL")
print(f"Scenarios: historical (1950-2014) + ssp245 (2015-2100)")
print(f"Variables: {', '.join(variables)}")
print("="*60)

# Get all UKESM1-0-LL items we already have
existing_files = list(download_dir.glob("*.nc"))
print(f"\nFound {len(existing_files)} existing files")

# Extract unique item IDs from existing files
existing_item_ids = set()
for f in existing_files:
    # Extract item ID from filename: nasa-nex-gddp-cmip6_ITEMID.nc
    match = re.search(r'nasa-nex-gddp-cmip6_(.+?)\.nc', f.name)
    if match:
        existing_item_ids.add(match.group(1))

print(f"Found {len(existing_item_ids)} unique item IDs in existing files")

# Search for items
print("\nSearching STAC catalog for items...")
search = catalog.search(
    collections=[collection_id],
    bbox=bbox
)

# Filter for UKESM1-0-LL items with ssp245 scenario or historical
ukesm_items = []
for item in search.items():
    if model in item.id:
        # Only include ssp245 or historical scenarios (exclude ssp585, ssp126, ssp370)
        item_id = item.id
        if '.ssp245.' in item_id or '.historical.' in item_id:
            ukesm_items.append(item)

print(f"Found {len(ukesm_items)} UKESM1-0-LL items (ssp245 + historical) in catalog")

# Download all variables from each item
print("\n" + "="*60)
print("Downloading all variables from each item...")
print("="*60)

for item in ukesm_items:
    item_id = item.id
    
    # Download each variable asset
    for var_name in variables:
        if var_name not in item.assets:
            continue
        
        asset = item.assets[var_name]
        asset_href = asset.href
        
        # Parse URL
        parsed_url = urllib.parse.urlparse(asset_href)
        
        # Skip ABFS URLs
        if parsed_url.scheme in ['abfs', 'abfss']:
            stats['abfs_skipped'] += 1
            continue
        
        # Only process HTTP/HTTPS URLs
        if parsed_url.scheme not in ['http', 'https']:
            stats['skipped'] += 1
            continue
        
        # Create filename: nasa-nex-gddp-cmip6_ITEMID_VARIABLE.nc
        url_path = parsed_url.path
        file_ext = Path(url_path).suffix or ".nc"
        safe_item_id = sanitize_filename(item_id)
        local_filename = download_dir / f"nasa-nex-gddp-cmip6_{safe_item_id}_{var_name}{file_ext}"
        
        # Check if file already exists
        if local_filename.exists():
            stats['already_downloaded'] += 1
            continue
        
        # Sign URL
        try:
            signed_href = planetary_computer.sign(asset_href)
        except Exception:
            signed_href = asset_href
        
        # Download
        try:
            urllib.request.urlretrieve(signed_href, str(local_filename))
            print(f"  Downloaded: {local_filename.name}")
            stats['downloaded'] += 1
        except Exception as e:
            error_str = str(e).lower()
            if 'abfs' in error_str or 'unknown url type' in error_str:
                stats['abfs_skipped'] += 1
                continue
            if '403' in str(e) or 'authentication' in error_str:
                try:
                    signed_href = planetary_computer.sign(asset_href)
                    urllib.request.urlretrieve(signed_href, str(local_filename))
                    print(f"  Downloaded: {local_filename.name} (after re-signing)")
                    stats['downloaded'] += 1
                except Exception as e2:
                    print(f"  Error downloading {item_id} {var_name}: {e2}")
                    stats['errors'] += 1
            else:
                print(f"  Error downloading {item_id} {var_name}: {e}")
                stats['errors'] += 1

# Summary
print("\n" + "="*60)
print("Download Summary")
print("="*60)
print(f"Downloaded: {stats['downloaded']} files")
print(f"Already downloaded: {stats['already_downloaded']} files")
print(f"Skipped (other): {stats['skipped']} items")
print(f"Skipped (ABFS URLs): {stats['abfs_skipped']} items")
print(f"Errors: {stats['errors']} items")
print(f"\nTotal files now in directory: {len(list(download_dir.glob('*.nc')))}")

# Show breakdown by variable
print("\n" + "="*60)
print("Files by variable:")
print("="*60)
for var in variables:
    var_files = list(download_dir.glob(f"*_{var}.nc"))
    print(f"  {var}: {len(var_files)} files")

