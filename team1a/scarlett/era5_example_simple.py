"""
Simple Example: Accessing ERA5 Data from ABFS

This is a minimal example showing how to access ERA5 data.
For a complete solution with error handling and visualization,
see era5_abfs_access.py
"""

import xarray as xr
import fsspec
import planetary_computer
import pystac_client

# Step 1: Connect to STAC API
catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

# Step 2: Search for ERA5 data
print("Searching for ERA5 data...")
search = catalog.search(
    collections=["era5-pds"],
    bbox=[17.9, 46.8, 18, 46.9],  # Your bounding box
    datetime="2020-01-01/2020-12-31"
)

items = list(search.items())
print(f"Found {len(items)} items")

# Step 3: Get ABFS URL from first item
if items:
    item = items[0]
    print(f"\nProcessing item: {item.id}")
    
    # Find ABFS URL in assets
    abfs_url = None
    for asset_key, asset in item.assets.items():
        href = asset.href
        if href.startswith("abfs://") or href.startswith("abfss://"):
            abfs_url = href
            print(f"Found ABFS URL: {abfs_url}")
            break
    
    # Step 4: Load Zarr data
    if abfs_url:
        print("\nLoading Zarr data...")
        
        # Create filesystem mapper
        storage_options = {
            'account_name': 'ai4edataeuwest',
            'anon': True
        }
        mapper = fsspec.get_mapper(abfs_url, **storage_options)
        
        # Open with xarray
        ds = xr.open_zarr(mapper, consolidated=True)
        print(f"Dataset loaded!")
        print(f"Variables: {list(ds.data_vars)}")
        print(f"Dimensions: {dict(ds.dims)}")
        
        # Step 5: Subset by bounding box
        if 'longitude' in ds.coords:
            ds_subset = ds.sel(
                longitude=slice(17.9, 18.0),
                latitude=slice(46.8, 46.9)
            )
            
            # Step 6: Extract time series (spatial mean)
            if 'air_temperature_at_2_metres' in ds_subset.data_vars:
                temp = ds_subset['air_temperature_at_2_metres']
                time_series = temp.mean(dim=['longitude', 'latitude'], skipna=True)
                
                print(f"\nTime series extracted!")
                print(f"Time range: {time_series.time.min().values} to {time_series.time.max().values}")
                print(f"Mean temperature: {time_series.mean().values:.2f} K")
                print(f"Min temperature: {time_series.min().values:.2f} K")
                print(f"Max temperature: {time_series.max().values:.2f} K")
            else:
                print(f"\nAvailable variables: {list(ds_subset.data_vars)}")
        else:
            print(f"\nAvailable coordinates: {list(ds.coords)}")
    else:
        print("No ABFS URL found in item assets")
else:
    print("No items found")

