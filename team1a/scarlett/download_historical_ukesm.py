"""
Download historical and early future data for UKESM1-0-LL model
Covers 1950-2033 to complement existing future projections (2034-2100)
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

# Track downloads
downloaded_count = 0
skipped_count = 0
already_downloaded_count = 0
abfs_skipped_count = 0

print("="*60)
print(f"Downloading UKESM1-0-LL Historical and Early Future Data")
print(f"Period: 1950-2033")
print("="*60)

# Search for historical data (1950-2014)
print("\nSearching for historical data (1950-2014)...")
search_historical = catalog.search(
    collections=[collection_id],
    bbox=bbox,
    datetime="1950-01-01/2014-12-31"
)

historical_items = []
for item in search_historical.items():
    # Filter for UKESM1-0-LL historical items
    if f"{model}.historical." in item.id:
        historical_items.append(item)

print(f"Found {len(historical_items)} historical items for {model}")

# Search for early future data (2015-2033) with ssp245 scenario
print("\nSearching for early future data (2015-2033) with ssp245 scenario...")
search_early_future = catalog.search(
    collections=[collection_id],
    bbox=bbox,
    datetime="2015-01-01/2033-12-31"
)

early_future_items = []
for item in search_early_future.items():
    # Filter for UKESM1-0-LL ssp245 items
    if f"{model}.ssp245." in item.id:
        early_future_items.append(item)

print(f"Found {len(early_future_items)} early future items for {model} (ssp245)")

# Combine all items to download
all_items = historical_items + early_future_items
print(f"\nTotal items to process: {len(all_items)}")

# Download items
print("\n" + "="*60)
print("Starting downloads...")
print("="*60)

for item in all_items:
    # Try to find the main data asset
    asset_to_download = None
    
    # Priority order for asset selection
    asset_priority = ["data", "image", "visual", "raster", "tile"]
    
    for asset_name in asset_priority:
        if asset_name in item.assets:
            asset_to_download = item.assets[asset_name]
            break
    
    # If no priority asset found, try to find any non-metadata asset
    if asset_to_download is None:
        for asset_key, asset in item.assets.items():
            if asset_key.lower() not in ["metadata", "info", "thumbnail", "overview"]:
                asset_to_download = asset
                break
    
    if asset_to_download is None:
        print(f"  Skipped {item.id} (no downloadable asset found)")
        skipped_count += 1
        continue
    
    # Determine file extension from asset href
    asset_href = asset_to_download.href
    
    # Parse URL to check scheme
    parsed_url = urllib.parse.urlparse(asset_href)
    
    # Skip ABFS URLs
    if parsed_url.scheme in ['abfs', 'abfss']:
        abfs_skipped_count += 1
        continue
    
    # Only process HTTP/HTTPS URLs
    if parsed_url.scheme not in ['http', 'https']:
        skipped_count += 1
        continue
    
    url_path = parsed_url.path
    file_ext = Path(url_path).suffix or ".nc"
    
    # Create filename
    safe_item_id = sanitize_filename(item.id)
    local_filename = download_dir / f"nasa-nex-gddp-cmip6_{safe_item_id}{file_ext}"
    
    # Check if file already exists
    if local_filename.exists():
        already_downloaded_count += 1
        continue
    
    # Ensure the URL is properly signed
    try:
        signed_href = planetary_computer.sign(asset_href)
    except Exception:
        signed_href = asset_href
    
    try:
        urllib.request.urlretrieve(signed_href, str(local_filename))
        print(f"  Downloaded: {local_filename.name}")
        downloaded_count += 1
    except Exception as e:
        error_str = str(e).lower()
        if 'abfs' in error_str or 'unknown url type' in error_str:
            abfs_skipped_count += 1
            continue
        if '403' in str(e) or 'authentication' in error_str:
            try:
                signed_href = planetary_computer.sign(asset_href)
                urllib.request.urlretrieve(signed_href, str(local_filename))
                print(f"  Downloaded: {local_filename.name} (after re-signing)")
                downloaded_count += 1
            except Exception as e2:
                print(f"  Error downloading {item.id}: {e2}")
                skipped_count += 1
        else:
            print(f"  Error downloading {item.id}: {e}")
            skipped_count += 1

# Summary
print("\n" + "="*60)
print("Download Summary")
print("="*60)
print(f"Downloaded: {downloaded_count} files")
print(f"Already downloaded: {already_downloaded_count} files")
print(f"Skipped (other): {skipped_count} items")
print(f"Skipped (ABFS URLs): {abfs_skipped_count} items")
print(f"\nTotal files now in directory: {len(list(download_dir.glob('*.nc')))}")

# Show what was downloaded
if downloaded_count > 0:
    print("\nSample downloaded files:")
    recent_files = sorted(download_dir.glob("*.nc"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
    for f in recent_files:
        print(f"  {f.name}")




