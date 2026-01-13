import planetary_computer
import pystac_client

# Setup
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

# Download to local storage
import urllib.request
import urllib.parse
import re
import time
from pathlib import Path
from datetime import datetime

# Try to import pandas and openpyxl for Excel export
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed. Excel export will be skipped.")
    print("Install with: pip install pandas openpyxl")

def sanitize_filename(name):
    """Remove invalid characters for Windows filesystem"""
    # Windows doesn't allow: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', name)

def download_with_retry(asset_href, local_filename, item_id, max_retries=3, retry_delay=2):
    """
    Download a file with retry logic for authentication errors.
    
    Args:
        asset_href: The asset URL to download
        local_filename: Path where to save the file
        item_id: Item ID for logging
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
    
    Returns:
        Tuple of (success: bool, is_auth_error: bool, error_message: str)
        - success: True if download succeeded
        - is_auth_error: True if the failure was an authentication error (worth retrying later)
        - error_message: Error message if failed, empty string if succeeded
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            # Sign the URL fresh for each attempt
            signed_href = planetary_computer.sign(asset_href)
            urllib.request.urlretrieve(signed_href, str(local_filename))
            return (True, False, "")
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            error_message = str(e)
            
            # Check if it's an ABFS error
            if 'abfs' in error_str or 'unknown url type' in error_str:
                return (False, False, error_message)
            
            # Check for authentication errors
            is_auth_error = '403' in str(e) or 'authentication' in error_str or 'authorization' in error_str
            
            if is_auth_error:
                if attempt < max_retries - 1:
                    # Wait before retrying (exponential backoff)
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"  Authentication error for {item_id}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed, but it was an auth error
                    return (False, True, error_message)
            else:
                # Non-authentication error, don't retry
                return (False, False, error_message)
    
    # Should not reach here, but handle it
    if last_error:
        return (False, False, str(last_error))
    return (False, False, "Unknown error")

# Create downloads directory if it doesn't exist
download_dir = Path("downloads")
download_dir.mkdir(exist_ok=True)

# Track downloaded items
downloaded_count = 0
skipped_count = 0
abfs_skipped_count = 0
already_downloaded_count = 0
total_collections = 0
failed_downloads = []  # Track failed downloads for retry

print("Starting download of all available data...")
print(f"Bounding box: [17.9, 46.8, 18, 46.9]")
print("-" * 60)

# Get all available collections
print("Fetching available collections...")
collections = list(catalog.get_collections())
print(f"Found {len(collections)} collections")
print("-" * 60)

# Organize collections by prefix
def get_collection_prefix(collection_id):
    """Extract prefix from collection ID (e.g., 'modis-17a2h-061' -> 'modis')"""
    parts = collection_id.lower().split('-')
    if len(parts) > 1:
        # Handle special cases
        if collection_id.lower().startswith('nex-gddp-cmip6'):
            return 'nex-gddp-cmip6'
        return parts[0]
    return 'other'

# Group collections by prefix
collection_groups = {}
for collection in collections:
    prefix = get_collection_prefix(collection.id)
    if prefix not in collection_groups:
        collection_groups[prefix] = []
    title = collection.title if hasattr(collection, 'title') and collection.title else "N/A"
    collection_groups[prefix].append((collection.id, title))

# Define preferred order for common prefixes
prefix_order = [
    'modis', 'landsat', 'sentinel', 'hls2', 'nasa', 'noaa', 'ecmwf',
    'nex-gddp-cmip6', 'other'
]

# Sort other prefixes alphabetically
other_prefixes = sorted([p for p in collection_groups.keys() if p not in prefix_order])

# Create ordered prefix list
ordered_prefixes = []
for prefix in prefix_order:
    if prefix in collection_groups:
        ordered_prefixes.append(prefix)
for prefix in other_prefixes:
    ordered_prefixes.append(prefix)

# Initialize collection status tracking
collection_status = {}
for collection in collections:
    collection_status[collection.id] = {
        'status': 'Pending',
        'message': '',
        'items_found': 0,
        'items_downloaded': 0,
        'items_skipped': 0
    }

# Print initial table summary (before downloads)
print("\n" + "=" * 130)
print("DATA COLLECTIONS SUMMARY TABLE (Before Download)")
print("=" * 130)
print(f"{'Group':<20} {'Collection ID':<45} {'Title':<45} {'Status':<20}")
print("-" * 130)

total_collections_count = 0
for prefix in ordered_prefixes:
    group_collections = collection_groups[prefix]
    group_count = len(group_collections)
    total_collections_count += group_count
    
    # Print group header
    print(f"\n{prefix.upper() + ' (' + str(group_count) + ')':<20} {'':<45} {'':<45} {'':<20}")
    print("-" * 130)
    
    # Print collections in this group
    for collection_id, title in sorted(group_collections):
        # Truncate long titles
        display_title = title[:43] + "..." if len(title) > 45 else title
        display_id = collection_id[:43] + "..." if len(collection_id) > 45 else collection_id
        status_info = collection_status.get(collection_id, {'status': 'Unknown', 'message': ''})
        status_display = status_info['status'][:18] + "..." if len(status_info['status']) > 20 else status_info['status']
        print(f"{'':<20} {display_id:<45} {display_title:<45} {status_display:<20}")

print("-" * 130)
print(f"\nTotal Collections: {total_collections_count}")
print("=" * 130)
print()

# Search each collection for data in the area of interest
for collection in collections:
    collection_id = collection.id
    total_collections += 1
    
    # Track skip reasons
    skip_reason = None
    
    # Skip NEX-GDDP-CMIP6 collections (handled by another script)
    if "nex-gddp-cmip6" in collection_id.lower():
        skip_reason = "Skipped - NEX-GDDP-CMIP6 (handled by another script)"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (NEX-GDDP-CMIP6 - handled by another script)")
        continue
    
    # Skip all Sentinel collections (sentinel-*)
    if collection_id.lower().startswith("sentinel-"):
        skip_reason = "Skipped - Sentinel collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (Sentinel collection)")
        continue
    
    # Skip all Landsat collections (landsat-*)
    if collection_id.lower().startswith("landsat-"):
        skip_reason = "Skipped - Landsat collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (Landsat collection)")
        continue
    
    # Skip all ECMWF collections (ecmwf-*)
    if collection_id.lower().startswith("ecmwf-"):
        skip_reason = "Skipped - ECMWF collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (ECMWF collection)")
        continue
    
    # Skip all NOAA collections (noaa-*)
    if collection_id.lower().startswith("noaa-"):
        skip_reason = "Skipped - NOAA collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (NOAA collection)")
        continue
    
    # Skip all HLS2 collections (hls2-*)
    if collection_id.lower().startswith("hls2-"):
        skip_reason = "Skipped - HLS2 collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (HLS2 collection)")
        continue
    
    # Skip all NASA collections (nasa-*)
    if collection_id.lower().startswith("nasa-"):
        skip_reason = "Skipped - NASA collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (NASA collection)")
        continue
    
    # Skip all MODIS collections (modis-*)
    if collection_id.lower().startswith("modis-"):
        skip_reason = "Skipped - MODIS collection"
        collection_status[collection_id]['status'] = 'Skipped'
        collection_status[collection_id]['message'] = skip_reason
        print(f"Skipping collection '{collection_id}' (MODIS collection)")
        continue
    
    try:
        # Search this collection for items in the bounding box
        search = catalog.search(
            collections=[collection_id],
            bbox=[17.9, 46.8, 18, 46.9],  # Your area
            # No datetime filter = get all available time periods
        )
        
        items_in_collection = 0
        items_downloaded_this_collection = 0
        items_skipped_this_collection = 0
        items_already_downloaded_this_collection = 0
        items_abfs_skipped_this_collection = 0
        items_no_asset_this_collection = 0
        error_messages = []  # Track error messages for this collection
        detailed_errors = []  # Track detailed error information: [(item_id, error_message), ...]
        
        for item in search.items():
            items_in_collection += 1
            
            # Sanitize collection name for Windows filesystem
            safe_collection_id = sanitize_filename(collection_id)
            
            # Create subdirectory for each collection
            collection_dir = download_dir / safe_collection_id
            collection_dir.mkdir(exist_ok=True)
            
            # Try to find the main data asset
            # Common asset names: "data", "image", "visual", "thumbnail", etc.
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
                    # Skip metadata and info assets
                    if asset_key.lower() not in ["metadata", "info", "thumbnail", "overview"]:
                        asset_to_download = asset
                        break
            
            if asset_to_download is None:
                print(f"  Skipped {item.id} (no downloadable asset found)")
                skipped_count += 1
                items_skipped_this_collection += 1
                items_no_asset_this_collection += 1
                continue
            
            # Determine file extension from asset href or default to .tif
            asset_href = asset_to_download.href
            
            # Parse URL to check scheme and remove query parameters
            parsed_url = urllib.parse.urlparse(asset_href)
            
            # Skip ABFS URLs (Azure Blob File System) - these require special libraries
            if parsed_url.scheme in ['abfs', 'abfss']:
                abfs_skipped_count += 1
                items_abfs_skipped_this_collection += 1
                items_skipped_this_collection += 1
                continue  # Skip silently to reduce noise
            
            # Only process HTTP/HTTPS URLs
            if parsed_url.scheme not in ['http', 'https']:
                skipped_count += 1
                items_skipped_this_collection += 1
                continue
            
            url_path = parsed_url.path
            
            # Extract file extension from the path (without query parameters)
            file_ext = Path(url_path).suffix or ".tif"
            
            # Sanitize filename: remove invalid characters for Windows filesystem
            safe_item_id = sanitize_filename(item.id)
            
            # Create filename: collection_itemid.ext
            local_filename = collection_dir / f"{safe_collection_id}_{safe_item_id}{file_ext}"
            
            # Check if file already exists
            if local_filename.exists():
                already_downloaded_count += 1
                items_already_downloaded_this_collection += 1
                continue  # Skip silently to reduce noise
            
            # Try to download with retry logic
            try:
                success, is_auth_error, error_message = download_with_retry(asset_href, local_filename, item.id)
                
                if success:
                    print(f"  Downloaded: {local_filename}")
                    downloaded_count += 1
                    items_downloaded_this_collection += 1
                else:
                    # Check if it's an ABFS error
                    parsed_url_check = urllib.parse.urlparse(asset_href)
                    if parsed_url_check.scheme in ['abfs', 'abfss']:
                        abfs_skipped_count += 1
                        continue
                    
                    # If it's an authentication error, store for retry later
                    if is_auth_error:
                        failed_downloads.append({
                            'asset_href': asset_href,
                            'local_filename': local_filename,
                            'item_id': item.id,
                            'collection_id': collection_id
                        })
                        print(f"  Failed to download {item.id} (auth error), will retry later")
                    else:
                        # Non-auth error - capture the actual error with details
                        error_msg = f"Download failed for {item.id}"
                        error_messages.append(error_msg)
                        detailed_errors.append((item.id, error_message))
                        print(f"  Error downloading {item.id}: {error_message}")
                        skipped_count += 1
                        items_skipped_this_collection += 1
            except Exception as e:
                # Catch any unexpected errors during download
                error_msg = f"Error downloading {item.id}: {str(e)[:50]}"
                error_messages.append(error_msg)
                detailed_errors.append((item.id, str(e)))
                print(f"  {error_msg}")
                skipped_count += 1
                items_skipped_this_collection += 1
        
        # Update collection status after processing
        if items_in_collection > 0:
            print(f"Collection '{collection_id}': {items_in_collection} items processed")
            total_items = items_downloaded_this_collection + items_already_downloaded_this_collection + items_skipped_this_collection
            
            # Build status message with detailed skip reasons
            status_parts = []
            if items_downloaded_this_collection > 0:
                status_parts.append(f"{items_downloaded_this_collection} downloaded")
            if items_already_downloaded_this_collection > 0:
                status_parts.append(f"{items_already_downloaded_this_collection} already existed")
            if items_skipped_this_collection > 0:
                skip_details = []
                if items_abfs_skipped_this_collection > 0:
                    skip_details.append(f"{items_abfs_skipped_this_collection} ABFS")
                if items_no_asset_this_collection > 0:
                    skip_details.append(f"{items_no_asset_this_collection} no asset")
                if error_messages:
                    skip_details.append(f"{len(error_messages)} errors")
                
                other_skipped = items_skipped_this_collection - items_abfs_skipped_this_collection - items_no_asset_this_collection - len(error_messages)
                if other_skipped > 0:
                    skip_details.append(f"{other_skipped} other")
                
                if skip_details:
                    status_parts.append(f"{items_skipped_this_collection} skipped ({', '.join(skip_details)})")
                else:
                    status_parts.append(f"{items_skipped_this_collection} skipped")
            
            status_message = ", ".join(status_parts)
            
            # Add detailed error information if available
            if detailed_errors:
                # Format detailed errors for display (show first 3, then count)
                if len(detailed_errors) <= 3:
                    error_details = "; ".join([f"{item_id}: {err[:100]}" for item_id, err in detailed_errors])
                else:
                    error_details = "; ".join([f"{item_id}: {err[:100]}" for item_id, err in detailed_errors[:3]])
                    error_details += f" ... and {len(detailed_errors) - 3} more errors"
                
                if len(status_message) + len(error_details) > 200:
                    # Truncate if too long
                    status_message += f" | Errors: {len(detailed_errors)} items failed"
                else:
                    status_message += f" | {error_details}"
            
            if items_downloaded_this_collection > 0 or items_already_downloaded_this_collection > 0:
                if error_messages or items_skipped_this_collection > 0:
                    collection_status[collection_id]['status'] = 'Partial'
                else:
                    collection_status[collection_id]['status'] = 'Downloaded'
                collection_status[collection_id]['message'] = status_message
            elif items_skipped_this_collection > 0:
                # Determine if it's a failure or partial based on skip reasons
                if error_messages and len(error_messages) == items_skipped_this_collection:
                    # All items failed with errors
                    collection_status[collection_id]['status'] = 'Failed'
                elif items_abfs_skipped_this_collection == items_skipped_this_collection:
                    # All items were ABFS URLs (not really a failure, more like unsupported)
                    collection_status[collection_id]['status'] = 'Skipped-ABFS'
                elif items_no_asset_this_collection == items_skipped_this_collection:
                    # All items had no downloadable assets
                    collection_status[collection_id]['status'] = 'No Assets'
                else:
                    # Mixed reasons
                    collection_status[collection_id]['status'] = 'Partial'
                collection_status[collection_id]['message'] = status_message
            else:
                collection_status[collection_id]['status'] = 'No Items'
                collection_status[collection_id]['message'] = 'No items found in bounding box'
            
            # Store detailed information
            collection_status[collection_id]['items_found'] = items_in_collection
            collection_status[collection_id]['items_downloaded'] = items_downloaded_this_collection
            collection_status[collection_id]['items_already_existed'] = items_already_downloaded_this_collection
            collection_status[collection_id]['items_skipped'] = items_skipped_this_collection
            collection_status[collection_id]['items_abfs'] = items_abfs_skipped_this_collection
            collection_status[collection_id]['items_no_asset'] = items_no_asset_this_collection
            collection_status[collection_id]['detailed_errors'] = detailed_errors  # Store full error details
        else:
            collection_status[collection_id]['status'] = 'No Items'
            collection_status[collection_id]['message'] = 'No items found in bounding box'
    
    except Exception as e:
        error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        collection_status[collection_id]['status'] = 'Error'
        collection_status[collection_id]['message'] = f"Error: {error_msg}"
        print(f"Error processing collection '{collection_id}': {e}")
        continue

# Retry failed downloads
if failed_downloads:
    print("-" * 60)
    print(f"Retrying {len(failed_downloads)} failed downloads...")
    print("-" * 60)
    
    retry_success_count = 0
    retry_failed_count = 0
    
    for failed_item in failed_downloads:
        # Check if file was already downloaded (maybe by another process)
        if failed_item['local_filename'].exists():
            already_downloaded_count += 1
            retry_success_count += 1
            continue
        
        # Try downloading again with more retries and longer delays
        success, is_auth_error, error_message = download_with_retry(
            failed_item['asset_href'],
            failed_item['local_filename'],
            failed_item['item_id'],
            max_retries=5,  # More retries for failed items
            retry_delay=5   # Longer delay between retries
        )
        
        if success:
            print(f"  Successfully downloaded (retry): {failed_item['local_filename']}")
            downloaded_count += 1
            retry_success_count += 1
        else:
            print(f"  Still failed after retries: {failed_item['item_id']}: {error_message}")
            retry_failed_count += 1
            skipped_count += 1
            # Update the collection's detailed errors if possible
            collection_id = failed_item['collection_id']
            if collection_id in collection_status:
                if 'detailed_errors' not in collection_status[collection_id]:
                    collection_status[collection_id]['detailed_errors'] = []
                collection_status[collection_id]['detailed_errors'].append((failed_item['item_id'], error_message))
    
    print(f"Retry results: {retry_success_count} succeeded, {retry_failed_count} still failed")

print("-" * 60)
print(f"Download complete!")
print(f"Processed {total_collections} collections")
print(f"Downloaded: {downloaded_count} files")
print(f"Already downloaded: {already_downloaded_count} files")
print(f"Skipped (other): {skipped_count} items")
print(f"Skipped (ABFS URLs): {abfs_skipped_count} items")
print(f"Note: ABFS URLs require Azure Data Lake libraries and cannot be downloaded with urllib")

# Print final table with download status
print("\n" + "=" * 150)
print("DATA COLLECTIONS SUMMARY TABLE (After Download)")
print("=" * 150)
print(f"{'Group':<20} {'Collection ID':<40} {'Title':<40} {'Status':<20} {'Details':<30}")
print("-" * 150)

# Count status types for summary
status_counts = {
    'Skipped': 0,
    'Downloaded': 0,
    'Partial': 0,
    'Failed': 0,
    'Skipped-ABFS': 0,
    'No Assets': 0,
    'No Items': 0,
    'Error': 0,
    'Pending': 0
}

total_collections_count = 0
processed_collections_count = 0
for prefix in ordered_prefixes:
    group_collections = collection_groups[prefix]
    
    # Filter collections that were actually processed (not "Pending")
    processed_collections = []
    for collection_id, title in sorted(group_collections):
        status_info = collection_status.get(collection_id, {'status': 'Pending', 'message': ''})
        current_status = status_info['status']
        
        # Count status types
        if current_status in status_counts:
            status_counts[current_status] += 1
        
        # Include all collections except "Pending" (unprocessed)
        if current_status != 'Pending':
            processed_collections.append((collection_id, title))
    
    if not processed_collections:
        continue  # Skip groups with no processed collections
    
    group_count = len(processed_collections)
    total_collections_count += group_count
    processed_collections_count += group_count
    
    # Print group header
    print(f"\n{prefix.upper() + ' (' + str(group_count) + ')':<20} {'':<40} {'':<40} {'':<20} {'':<30}")
    print("-" * 150)
    
    # Print collections in this group, sorted by status for better readability
    def sort_by_status(item):
        collection_id, title = item
        status_info = collection_status.get(collection_id, {'status': 'Unknown', 'message': ''})
        status = status_info['status']
        # Define priority order for sorting
        priority = {
            'Skipped': 1, 'Downloaded': 2, 'Partial': 3, 'Failed': 4, 
            'Skipped-ABFS': 5, 'No Assets': 6, 'No Items': 7, 'Error': 8, 'Unknown': 9
        }
        return (priority.get(status, 99), collection_id)
    
    for collection_id, title in sorted(processed_collections, key=sort_by_status):
        # Truncate long strings
        display_title = title[:38] + "..." if len(title) > 40 else title
        display_id = collection_id[:38] + "..." if len(collection_id) > 40 else collection_id
        
        status_info = collection_status.get(collection_id, {'status': 'Unknown', 'message': ''})
        status_display = status_info['status'][:18] + "..." if len(status_info['status']) > 20 else status_info['status']
        message_display = status_info['message'][:28] + "..." if len(status_info['message']) > 30 else status_info['message']
        
        print(f"{'':<20} {display_id:<40} {display_title:<40} {status_display:<20} {message_display:<30}")

print("-" * 150)
print(f"\nTotal Processed Collections: {processed_collections_count}")
print("\nStatus Summary:")
print(f"  Skipped (user-defined): {status_counts['Skipped']}")
print(f"  Downloaded: {status_counts['Downloaded']}")
print(f"  Partial (some succeeded, some failed): {status_counts['Partial']}")
print(f"  Failed (all items failed with errors): {status_counts['Failed']}")
print(f"  Skipped-ABFS (all items use ABFS protocol): {status_counts['Skipped-ABFS']}")
print(f"  No Assets (no downloadable assets found): {status_counts['No Assets']}")
print(f"  No Items (no items in bounding box): {status_counts['No Items']}")
print(f"  Error (processing exception): {status_counts['Error']}")
print(f"  Pending (not processed): {status_counts['Pending']}")
print("=" * 150)
print()

# Export to Excel
if not HAS_PANDAS:
    print("Skipping Excel export (pandas not installed)")
else:
    print("Exporting results to Excel...")
    excel_data = []

    for prefix in ordered_prefixes:
        group_collections = collection_groups[prefix]
        
        for collection_id, title in sorted(group_collections):
            status_info = collection_status.get(collection_id, {'status': 'Pending', 'message': ''})
            
            # Skip unprocessed collections
            if status_info['status'] == 'Pending':
                continue
            
            # Format detailed errors
            detailed_errors = status_info.get('detailed_errors', [])
            if detailed_errors:
                error_details = "\n".join([f"{item_id}: {err}" for item_id, err in detailed_errors])
            else:
                error_details = ""
            
            # Get collection statistics
            items_found = status_info.get('items_found', 0)
            items_downloaded = status_info.get('items_downloaded', 0)
            items_already_existed = status_info.get('items_already_existed', 0)
            items_skipped = status_info.get('items_skipped', 0)
            items_abfs = status_info.get('items_abfs', 0)
            items_no_asset = status_info.get('items_no_asset', 0)
            
            excel_data.append({
                'Group': prefix,
                'Collection ID': collection_id,
                'Title': title,
                'Status': status_info['status'],
                'Items Found': items_found,
                'Items Downloaded': items_downloaded,
                'Items Already Existed': items_already_existed,
                'Items Skipped': items_skipped,
                'ABFS URLs': items_abfs,
                'No Asset': items_no_asset,
                'Error Count': len(detailed_errors),
                'Status Message': status_info['message'],
                'Detailed Errors': error_details
            })

    # Create DataFrame and export to Excel
    if excel_data:
        df = pd.DataFrame(excel_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = download_dir / f"download_summary_{timestamp}.xlsx"
        
        # Write to Excel with formatting
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Collections Summary', index=False)
            
            # Get the worksheet to adjust column widths
            worksheet = writer.sheets['Collections Summary']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                # Set reasonable max width
                max_length = min(max_length, 100)
                worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
        
        print(f"Results exported to: {excel_filename}")
        print(f"Total collections exported: {len(excel_data)}")
    else:
        print("No data to export.")
print()