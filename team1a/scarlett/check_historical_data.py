"""
Check for historical data availability in NASA NEX-GDDP-CMIP6 collection
"""
import planetary_computer
import pystac_client
from datetime import datetime

# Setup
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

print("="*60)
print("Checking NASA NEX-GDDP-CMIP6 for Historical Data")
print("="*60)

# Get the collection
collection_id = "nasa-nex-gddp-cmip6"
collection = catalog.get_collection(collection_id)

print(f"\nCollection: {collection.id}")
print(f"Title: {collection.title}")
print(f"Description: {collection.description[:200]}...")

# Search for historical data (1950-2014)
print("\n" + "="*60)
print("Searching for HISTORICAL data (1950-2014)...")
print("="*60)

search_historical = catalog.search(
    collections=[collection_id],
    bbox=[17.9, 46.8, 18, 46.9],  # Your study area
    datetime="1950-01-01/2014-12-31"
)

historical_items = list(search_historical.items())
print(f"\nFound {len(historical_items)} historical items (1950-2014)")

if historical_items:
    print("\nSample historical items:")
    for item in historical_items[:10]:
        print(f"  {item.id}")
        if hasattr(item, 'datetime') and item.datetime:
            print(f"    Date: {item.datetime}")
        elif hasattr(item, 'properties') and 'datetime' in item.properties:
            print(f"    Date: {item.properties['datetime']}")
else:
    print("\nNo historical items found in this bounding box.")

# Search for future data (2015-2100)
print("\n" + "="*60)
print("Searching for FUTURE data (2015-2100)...")
print("="*60)

search_future = catalog.search(
    collections=[collection_id],
    bbox=[17.9, 46.8, 18, 46.9],
    datetime="2015-01-01/2100-12-31"
)

future_items = list(search_future.items())
print(f"\nFound {len(future_items)} future items (2015-2100)")

if future_items:
    print("\nSample future items:")
    for item in future_items[:10]:
        print(f"  {item.id}")
        if hasattr(item, 'datetime') and item.datetime:
            print(f"    Date: {item.datetime}")
        elif hasattr(item, 'properties') and 'datetime' in item.properties:
            print(f"    Date: {item.properties['datetime']}")

# Search without datetime filter to see all available
print("\n" + "="*60)
print("Searching ALL data (no datetime filter)...")
print("="*60)

search_all = catalog.search(
    collections=[collection_id],
    bbox=[17.9, 46.8, 18, 46.9]
)

all_items = list(search_all.items())
print(f"\nFound {len(all_items)} total items")

# Analyze date ranges and item patterns
if all_items:
    dates = []
    historical_pattern = []
    future_pattern = []
    
    for item in all_items:
        item_id = item.id
        # Check if it's historical or future
        if '.historical.' in item_id:
            historical_pattern.append(item_id)
        elif any(f'.ssp{scenario}.' in item_id for scenario in ['126', '245', '370', '585']):
            future_pattern.append(item_id)
        
        if hasattr(item, 'datetime') and item.datetime:
            dates.append(item.datetime)
        elif hasattr(item, 'properties') and 'datetime' in item.properties:
            dt = item.properties['datetime']
            if dt:
                dates.append(dt)
    
    if dates:
        dates = sorted([d for d in dates if d is not None])
        if dates:
            print(f"\nDate range in items:")
            print(f"  Earliest: {dates[0]}")
            print(f"  Latest: {dates[-1]}")
            print(f"  Total years covered: {len(set([str(d)[:4] for d in dates if d]))}")
    
    print(f"\nItem patterns:")
    print(f"  Historical pattern items: {len(set(historical_pattern))}")
    print(f"  Future scenario items: {len(set(future_pattern))}")
    
    if historical_pattern:
        print(f"\nSample historical item IDs:")
        for item_id in sorted(set(historical_pattern))[:10]:
            print(f"  {item_id}")

# Check collection metadata for temporal extent
print("\n" + "="*60)
print("Collection Temporal Extent:")
print("="*60)
if hasattr(collection, 'extent') and collection.extent:
    if hasattr(collection.extent, 'temporal'):
        temporal = collection.extent.temporal
        if temporal and temporal.intervals:
            for interval in temporal.intervals:
                if interval:
                    print(f"  {interval[0]} to {interval[1]}")

print("\n" + "="*60)
print("Summary:")
print("="*60)
print(f"Historical items (1950-2014): {len(historical_items)}")
print(f"Future items (2015-2100): {len(future_items)}")
print(f"Total items: {len(all_items)}")

if len(historical_items) == 0:
    print("\nNOTE: No historical data found. Possible reasons:")
    print("  1. Historical data may not be available for this specific bounding box")
    print("  2. Historical data might be stored in a different collection")
    print("  3. Historical data might require different search parameters")
    print("  4. The STAC catalog might only index future projections")

