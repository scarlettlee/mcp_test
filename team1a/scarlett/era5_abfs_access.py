"""
ERA5 Climate Data Access via Azure Blob File System (ABFS)

This script demonstrates how to:
1. Connect to Azure Blob Storage (ABFS) to access ERA5 data
2. Retrieve long-term temperature data for a specific bounding box
3. Extract time series covering multiple years
4. Create visualizations of the temperature time series

Requirements:
- adlfs: Azure Data Lake File System library
- xarray: For handling Zarr datasets
- matplotlib: For visualization
- planetary-computer: For STAC API and authentication
- pystac-client: For STAC API queries

Installation:
    pip install adlfs xarray matplotlib planetary-computer pystac-client zarr

Authentication:
    Planetary Computer provides free access to ERA5 data. The adlfs library
    will automatically use anonymous access for public Azure Blob Storage.
    For Planetary Computer's signed URLs, we use the planetary-computer package.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Core libraries
try:
    import adlfs
    import xarray as xr
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import MaxNLocator
except ImportError as e:
    print(f"Error: Missing required library: {e}")
    print("\nPlease install required packages:")
    print("  pip install adlfs xarray matplotlib numpy")
    sys.exit(1)

# STAC API libraries
try:
    import planetary_computer
    import pystac_client
except ImportError as e:
    print(f"Error: Missing STAC library: {e}")
    print("\nPlease install required packages:")
    print("  pip install planetary-computer pystac-client")
    sys.exit(1)


class ERA5ABFSAccessor:
    """
    Class to handle ERA5 data access from Azure Blob File System.
    """
    
    def __init__(self, bbox=None, collection_id="era5-pds"):
        """
        Initialize ERA5 ABFS accessor.
        
        Parameters:
        -----------
        bbox : list, optional
            Bounding box as [min_lon, min_lat, max_lon, max_lat]
            Default: [17.9, 46.8, 18, 46.9]
        collection_id : str
            STAC collection ID for ERA5 data
            Default: "era5-pds"
        """
        self.bbox = bbox or [17.9, 46.8, 18, 46.9]
        self.collection_id = collection_id
        self.catalog = None
        self.fs = None
        
        # Validate bounding box
        if len(self.bbox) != 4:
            raise ValueError("Bounding box must have 4 elements: [min_lon, min_lat, max_lon, max_lat]")
        
        min_lon, min_lat, max_lon, max_lat = self.bbox
        if not (-180 <= min_lon <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= min_lat <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
    
    def connect_stac(self):
        """
        Connect to Planetary Computer STAC API.
        
        Returns:
        --------
        bool : True if connection successful
        """
        try:
            print("Connecting to Planetary Computer STAC API...")
            self.catalog = pystac_client.Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace
            )
            print("✓ Successfully connected to STAC API")
            return True
        except Exception as e:
            print(f"✗ Error connecting to STAC API: {e}")
            return False
    
    def connect_abfs(self):
        """
        Connect to Azure Blob File System.
        
        For Planetary Computer's public data, we use anonymous access.
        The adlfs library handles authentication automatically.
        
        Returns:
        --------
        bool : True if connection successful
        """
        try:
            print("Connecting to Azure Blob File System...")
            # For Planetary Computer's public Azure Blob Storage, we use anonymous access
            # The account name is typically 'ai4edataeuwest' or similar
            # We'll let adlfs handle the connection when we access the data
            self.fs = adlfs.AzureBlobFileSystem(account_name="ai4edataeuwest", anon=True)
            print("✓ Successfully connected to ABFS")
            return True
        except Exception as e:
            print(f"✗ Error connecting to ABFS: {e}")
            print("Note: ABFS connection will be established when accessing data")
            # Don't fail here - connection might work when we access the data
            return True
    
    def find_era5_items(self, variable="air_temperature_at_2_metres", years=None):
        """
        Find ERA5 STAC items for the specified variable and years.
        
        Parameters:
        -----------
        variable : str
            Variable name (e.g., "air_temperature_at_2_metres")
        years : list, optional
            List of years to search for. If None, searches for available years.
            Default: [2020, 2021, 2022, 2023, 2024]
        
        Returns:
        --------
        list : List of STAC items
        """
        if years is None:
            years = [2020, 2021, 2022, 2023, 2024]
        
        if self.catalog is None:
            if not self.connect_stac():
                return []
        
        print(f"\nSearching for ERA5 {variable} data...")
        print(f"Bounding box: {self.bbox}")
        print(f"Years: {years}")
        
        items = []
        for year in years:
            try:
                # Search for items in this collection
                search = self.catalog.search(
                    collections=[self.collection_id],
                    bbox=self.bbox,
                    datetime=f"{year}-01-01/{year}-12-31"
                )
                
                year_items = list(search.items())
                if year_items:
                    print(f"  Found {len(year_items)} items for {year}")
                    items.extend(year_items)
                else:
                    print(f"  No items found for {year}")
            except Exception as e:
                print(f"  Error searching for {year}: {e}")
                continue
        
        print(f"\nTotal items found: {len(items)}")
        return items
    
    def get_abfs_url_from_item(self, item, variable="air_temperature_at_2_metres"):
        """
        Extract ABFS URL or HTTPS URL from a STAC item.
        
        Parameters:
        -----------
        item : pystac.Item
            STAC item
        variable : str
            Variable name to look for in assets
        
        Returns:
        --------
        tuple : (url, url_type) where url_type is 'abfs', 'https', or None
        """
        # Check if the variable is directly in assets
        if variable in item.assets:
            asset = item.assets[variable]
            href = asset.href
            if href.startswith("abfs://") or href.startswith("abfss://"):
                return (href, 'abfs')
            elif href.startswith("https://") and ".blob.core.windows.net" in href:
                return (href, 'https')
        
        # Check for "data" asset
        if "data" in item.assets:
            asset = item.assets["data"]
            href = asset.href
            if href.startswith("abfs://") or href.startswith("abfss://"):
                return (href, 'abfs')
            elif href.startswith("https://") and ".blob.core.windows.net" in href:
                return (href, 'https')
        
        # Look for any ABFS or HTTPS asset
        for asset_key, asset in item.assets.items():
            href = asset.href
            if href.startswith("abfs://") or href.startswith("abfss://"):
                # Check if it contains the variable name
                if variable.replace("_", "-") in href.lower() or variable in href.lower():
                    return (href, 'abfs')
            elif href.startswith("https://") and ".blob.core.windows.net" in href:
                # Check if it contains the variable name
                if variable.replace("_", "-") in href.lower() or variable in href.lower():
                    return (href, 'https')
        
        return (None, None)
    
    def construct_abfs_path(self, year, month, variable="air_temperature_at_2_metres"):
        """
        Construct ABFS path for ERA5 data.
        
        ERA5 data on Planetary Computer is typically organized as:
        abfs://era5/ERA5/{year}/{month}/{variable}.zarr
        
        Parameters:
        -----------
        year : int
            Year
        month : int
            Month (1-12)
        variable : str
            Variable name
        
        Returns:
        --------
        str : ABFS path
        """
        # Convert variable name to filename format
        # e.g., "air_temperature_at_2_metres" -> "air_temperature_at_2_metres"
        month_str = f"{month:02d}"
        path = f"era5/ERA5/{year}/{month_str}/{variable}.zarr"
        return path
    
    def load_zarr_data(self, abfs_path, bbox=None, item=None, url_type=None):
        """
        Load Zarr data from ABFS path or HTTPS URL.
        
        Parameters:
        -----------
        abfs_path : str
            ABFS path or HTTPS URL to Zarr dataset
        bbox : list, optional
            Bounding box for spatial subsetting [min_lon, min_lat, max_lon, max_lat]
            If None, uses self.bbox
        item : pystac.Item, optional
            STAC item (used to extract account/container info if needed)
        url_type : str, optional
            Type of URL: 'abfs', 'https', or None (auto-detect)
        
        Returns:
        --------
        xarray.Dataset : Loaded dataset or None if error
        """
        if bbox is None:
            bbox = self.bbox
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        try:
            print(f"  Loading data from: {abfs_path[:100]}...")
            import fsspec
            
            # Auto-detect URL type if not provided
            if url_type is None:
                if abfs_path.startswith("abfs://") or abfs_path.startswith("abfss://"):
                    url_type = 'abfs'
                elif abfs_path.startswith("https://"):
                    url_type = 'https'
                else:
                    url_type = 'abfs'  # Default assumption
            
            # Method 1: If it's already an HTTPS URL, sign it directly
            if url_type == 'https':
                try:
                    print(f"    Signing HTTPS URL...")
                    # Check if URL is already signed (has 'sig=' parameter)
                    if 'sig=' in abfs_path or '?sv=' in abfs_path:
                        print(f"    URL appears to be already signed, using directly...")
                        signed_url = abfs_path
                    else:
                        signed_url = planetary_computer.sign(abfs_path)
                    
                    mapper = fsspec.get_mapper(signed_url)
                    ds = xr.open_zarr(mapper, consolidated=True)
                    print(f"    ✓ Successfully loaded using signed HTTPS URL")
                except Exception as e_https:
                    print(f"    HTTPS signing/loading failed: {e_https}")
                    # Don't raise yet, try other methods
                    if 'ds' not in locals():
                        raise
            
            # Method 2: Sign ABFS URL directly with Planetary Computer
            # Try this first for ABFS URLs
            elif url_type == 'abfs':
                try:
                    print(f"    Trying to sign ABFS URL directly...")
                    signed_abfs = planetary_computer.sign(abfs_path)
                    
                    # Use fsspec to access the signed ABFS URL
                    mapper = fsspec.get_mapper(signed_abfs)
                    ds = xr.open_zarr(mapper, consolidated=True)
                    print(f"    ✓ Successfully loaded using signed ABFS URL")
                    
                except Exception as e1:
                    print(f"    Direct ABFS signing failed: {e1}")
                
                # Method 2: Convert ABFS to HTTPS, then sign
                try:
                    print(f"    Converting ABFS to HTTPS and signing...")
                    
                    # Extract container and path from ABFS URL
                    # abfs://era5/ERA5/2020/12/variable.zarr
                    if abfs_path.startswith("abfs://") or abfs_path.startswith("abfss://"):
                        path_without_protocol = abfs_path.replace("abfs://", "").replace("abfss://", "")
                        parts = path_without_protocol.split("/", 1)
                        container = parts[0]
                        blob_path = parts[1] if len(parts) > 1 else ""
                    else:
                        container = "era5"
                        blob_path = abfs_path
                    
                    # Try to extract account name from STAC item if available
                    account_names = []
                    
                    # If we have the item, check for account info in assets
                    if item is not None:
                        # Check all assets for HTTPS URLs to extract account name
                        for asset_key, asset in item.assets.items():
                            href = asset.href
                            if href.startswith("https://") and ".blob.core.windows.net" in href:
                                # Extract account name from URL
                                # https://accountname.blob.core.windows.net/...
                                try:
                                    account_match = href.split("//")[1].split(".blob.core.windows.net")[0]
                                    if account_match and account_match not in account_names:
                                        account_names.append(account_match)
                                        print(f"    Found account name from asset: {account_match}")
                                except:
                                    pass
                        
                        # Also check item properties
                        props = getattr(item, 'properties', {})
                        if 'pc:storage_account' in props:
                            account_names.insert(0, props['pc:storage_account'])
                    
                    # Add common account names as fallback
                    common_accounts = ["ai4edataeuwest", "planetarycomputer", "pcstorage"]
                    for acc in common_accounts:
                        if acc not in account_names:
                            account_names.append(acc)
                    
                    if not account_names:
                        account_names = ["ai4edataeuwest"]  # Default fallback
                    
                    print(f"    Trying account names: {account_names[:3]}...")
                    signed_url = None
                    last_error = None
                    
                    for account_name in account_names:
                        try:
                            # Construct HTTPS URL
                            https_url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
                            
                            # Sign the HTTPS URL
                            signed_url = planetary_computer.sign(https_url)
                            
                            # Try to open with this signed URL
                            mapper = fsspec.get_mapper(signed_url)
                            ds = xr.open_zarr(mapper, consolidated=True)
                            print(f"    ✓ Successfully loaded using account '{account_name}'")
                            break
                            
                        except Exception as e_account:
                            last_error = e_account
                            # Don't print every failure, just continue
                            continue
                    
                    if signed_url is None or 'ds' not in locals():
                        raise Exception(f"Failed with all account names ({len(account_names)} tried). Last error: {last_error}")
                    
                except Exception as e2:
                    # Method 3: Try using adlfs with signed token
                    print(f"    Trying adlfs with authentication...")
                    try:
                        # Extract container and path
                        if abfs_path.startswith("abfs://") or abfs_path.startswith("abfss://"):
                            path_without_protocol = abfs_path.replace("abfs://", "").replace("abfss://", "")
                            parts = path_without_protocol.split("/", 1)
                            container = parts[0]
                            blob_path = parts[1] if len(parts) > 1 else ""
                        else:
                            container = "era5"
                            blob_path = abfs_path
                        
                        # Get SAS token for the container
                        # Try to sign a URL to get the token
                        test_url = f"https://ai4edataeuwest.blob.core.windows.net/{container}/"
                        try:
                            signed_base = planetary_computer.sign(test_url)
                            # Extract token from signed URL
                            # Use adlfs with the token
                            if self.fs is None:
                                self.fs = adlfs.AzureBlobFileSystem(
                                    account_name="ai4edataeuwest",
                                    account_key=None,
                                    anon=True
                                )
                            
                            full_path = f"{container}/{blob_path}"
                            mapper = self.fs.get_mapper(full_path)
                            ds = xr.open_zarr(mapper, consolidated=True)
                            print(f"    ✓ Successfully loaded using adlfs")
                            
                        except Exception as e_token:
                            raise Exception(f"Token-based access failed: {e_token}")
                    
                    except Exception as e3:
                        raise Exception(f"All access methods failed. Last error: {e3}")
            
            # Subset by bounding box if coordinates are available
            if 'longitude' in ds.coords or 'lon' in ds.coords:
                lon_name = 'longitude' if 'longitude' in ds.coords else 'lon'
                lat_name = 'latitude' if 'latitude' in ds.coords else 'lat'
                
                # Select spatial subset
                ds_subset = ds.sel(
                    {lon_name: slice(min_lon, max_lon),
                     lat_name: slice(min_lat, max_lat)}
                )
                
                print(f"    Dataset shape: {dict(ds_subset.dims)}")
                print(f"    Available variables: {list(ds_subset.data_vars)}")
                return ds_subset
            else:
                print(f"    Warning: No longitude/latitude coordinates found")
                print(f"    Available coordinates: {list(ds.coords)}")
                return ds
                
        except Exception as e:
            print(f"    ✗ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_time_series(self, years=None, variable="air_temperature_at_2_metres"):
        """
        Extract time series data for multiple years.
        
        Parameters:
        -----------
        years : list, optional
            List of years to extract. If None, uses [2020, 2021, 2022, 2023, 2024]
        variable : str
            Variable name
        
        Returns:
        --------
        xarray.DataArray : Time series data
        """
        if years is None:
            years = [2020, 2021, 2022, 2023, 2024]
        
        print(f"\n{'='*60}")
        print(f"Extracting {variable} time series for years {years}")
        print(f"{'='*60}")
        
        # Try to find items via STAC first
        items = self.find_era5_items(variable, years)
        
        all_datasets = []
        
        # If we found items, try to use them
        if items:
            print(f"\nAttempting to load data from {len(items)} STAC items...")
            for item in items[:5]:  # Limit to first 5 items for testing
                url, url_type = self.get_abfs_url_from_item(item, variable)
                if url:
                    print(f"\nProcessing item: {item.id}")
                    print(f"  URL type: {url_type}, URL: {url[:80]}...")
                    ds = self.load_zarr_data(url, item=item, url_type=url_type)
                    if ds is not None:
                        all_datasets.append(ds)
        else:
            # If no items found, try constructing paths directly
            print(f"\nNo STAC items found. Trying direct path construction...")
            print("Note: This method may not work if the data structure is different")
            
            for year in years:
                for month in range(1, 13):
                    abfs_path = self.construct_abfs_path(year, month, variable)
                    print(f"\nTrying: {abfs_path}")
                    ds = self.load_zarr_data(abfs_path)
                    if ds is not None:
                        all_datasets.append(ds)
                    else:
                        # Skip remaining months if this one failed (data might not exist)
                        break
        
        if not all_datasets:
            print("\n✗ No data could be loaded. Possible reasons:")
            print("  1. Data might not be available for the specified years")
            print("  2. Variable name might be incorrect")
            print("  3. Authentication/access issues")
            print("  4. Data structure might be different than expected")
            return None
        
        # Concatenate all datasets along time dimension
        print(f"\nConcatenating {len(all_datasets)} datasets...")
        try:
            combined = xr.concat(all_datasets, dim='time')
            
            # Get the variable data
            if variable in combined.data_vars:
                data = combined[variable]
            else:
                # Try to find the variable by partial name match
                matching_vars = [v for v in combined.data_vars if variable.split('_')[0] in v.lower()]
                if matching_vars:
                    data = combined[matching_vars[0]]
                    print(f"Using variable: {matching_vars[0]}")
                else:
                    print(f"Available variables: {list(combined.data_vars)}")
                    # Use the first data variable
                    data = list(combined.data_vars.values())[0]
                    print(f"Using first available variable: {data.name}")
            
            # Calculate spatial mean for the bounding box
            if 'longitude' in data.coords or 'lon' in data.coords:
                # Already subset, just take mean
                time_series = data.mean(dim=['longitude', 'latitude'], skipna=True)
            elif 'lon' in data.coords:
                time_series = data.mean(dim=['lon', 'lat'], skipna=True)
            else:
                # No spatial dimensions, use as is
                time_series = data
            
            print(f"✓ Successfully extracted time series")
            print(f"  Time range: {time_series.time.min().values} to {time_series.time.max().values}")
            print(f"  Data points: {len(time_series)}")
            
            return time_series
            
        except Exception as e:
            print(f"✗ Error concatenating datasets: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def visualize_time_series(self, time_series, variable="air_temperature_at_2_metres", 
                              output_file=None):
        """
        Create visualization of the time series.
        
        Parameters:
        -----------
        time_series : xarray.DataArray
            Time series data
        variable : str
            Variable name for labeling
        output_file : str, optional
            Output file path for saving the plot
        """
        if time_series is None:
            print("✗ No data to visualize")
            return
        
        print(f"\n{'='*60}")
        print("Creating visualization...")
        print(f"{'='*60}")
        
        try:
            # Convert to pandas for easier plotting
            df = time_series.to_pandas()
            
            # Create figure with subplots
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Plot 1: Full time series
            ax1 = axes[0]
            ax1.plot(df.index, df.values, linewidth=1, alpha=0.7, color='steelblue')
            ax1.set_xlabel('Date', fontsize=12)
            ax1.set_ylabel(f'{variable.replace("_", " ").title()} (K)', fontsize=12)
            ax1.set_title(f'ERA5 {variable.replace("_", " ").title()} Time Series\n'
                         f'Bounding Box: {self.bbox}', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_locator(mdates.YearLocator())
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax1.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add statistics text
            mean_val = df.mean()
            std_val = df.std()
            min_val = df.min()
            max_val = df.max()
            stats_text = (f'Mean: {mean_val:.2f} K\n'
                         f'Std: {std_val:.2f} K\n'
                         f'Min: {min_val:.2f} K\n'
                         f'Max: {max_val:.2f} K')
            ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', 
                    facecolor='wheat', alpha=0.5), fontsize=10)
            
            # Plot 2: Monthly averages
            ax2 = axes[1]
            monthly_avg = df.resample('M').mean()
            ax2.plot(monthly_avg.index, monthly_avg.values, 
                    linewidth=2, color='coral', marker='o', markersize=4)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.set_ylabel(f'{variable.replace("_", " ").title()} (K)', fontsize=12)
            ax2.set_title('Monthly Average Temperature', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_locator(mdates.YearLocator())
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save or show
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"✓ Visualization saved to: {output_file}")
            else:
                output_file = f"era5_temperature_timeseries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"✓ Visualization saved to: {output_file}")
            
            plt.show()
            
        except Exception as e:
            print(f"✗ Error creating visualization: {e}")
            import traceback
            traceback.print_exc()


def main():
    """
    Main function to demonstrate ERA5 data access.
    """
    print("="*60)
    print("ERA5 Climate Data Access via Azure Blob File System")
    print("="*60)
    
    # Configuration
    bbox = [17.9, 46.8, 18, 46.9]  # Your bounding box
    variable = "air_temperature_at_2_metres"
    years = [2020, 2021, 2022, 2023, 2024]
    
    # Create accessor
    accessor = ERA5ABFSAccessor(bbox=bbox)
    
    # Connect to services
    if not accessor.connect_stac():
        print("Warning: STAC connection failed, but continuing...")
    
    accessor.connect_abfs()
    
    # Extract time series
    time_series = accessor.extract_time_series(years=years, variable=variable)
    
    # Visualize
    if time_series is not None:
        accessor.visualize_time_series(time_series, variable=variable)
        
        # Print summary statistics
        print(f"\n{'='*60}")
        print("Time Series Summary Statistics")
        print(f"{'='*60}")
        df = time_series.to_pandas()
        print(f"Mean: {df.mean():.2f} K")
        print(f"Standard Deviation: {df.std():.2f} K")
        print(f"Minimum: {df.min():.2f} K")
        print(f"Maximum: {df.max():.2f} K")
        print(f"Time Range: {df.index.min()} to {df.index.max()}")
        print(f"Total Data Points: {len(df)}")
    else:
        print("\n" + "="*60)
        print("TROUBLESHOOTING GUIDE")
        print("="*60)
        print("""
If no data was loaded, try the following:

1. Check variable name:
   - Common ERA5 variables: air_temperature_at_2_metres, 
     precipitation_amount_1hour_Accumulation, etc.
   - Check Planetary Computer documentation for exact names

2. Check data availability:
   - ERA5 data might be organized differently than expected
   - Try searching the STAC catalog manually:
     https://planetarycomputer.microsoft.com/api/stac/v1/collections/era5-pds

3. Authentication:
   - Ensure planetary-computer package is installed
   - The package handles SAS token authentication automatically

4. Alternative approach:
   - Consider using the CDS API directly for ERA5 data
   - Or use pre-processed ERA5 datasets from other sources

5. Check ABFS path structure:
   - The actual path structure might differ
   - You may need to inspect the STAC items to see the exact paths
        """)


if __name__ == "__main__":
    main()

