# ERA5 Climate Data Access via Azure Blob File System (ABFS)

This guide explains how to access ERA5 climate reanalysis data stored in Azure Blob File System (ABFS) using Zarr format through Planetary Computer's STAC API.

## Overview

ERA5 is the fifth generation ECMWF reanalysis for global climate and weather data. The data is stored in Azure Blob Storage in Zarr format and accessed via ABFS URLs. This script demonstrates how to:

1. Connect to Azure Blob Storage (ABFS) to access ERA5 data
2. Retrieve long-term temperature data for a specific bounding box
3. Extract time series covering multiple years (2020-2024)
4. Create visualizations of the temperature time series

## Installation

### Step 1: Install Required Packages

```bash
pip install -r requirements_era5.txt
```

Or install individually:

```bash
pip install adlfs xarray matplotlib numpy pandas planetary-computer pystac-client zarr fsspec
```

### Step 2: Verify Installation

```python
import adlfs
import xarray as xr
import planetary_computer
print("All packages installed successfully!")
```

## Authentication

**No API keys required!** Planetary Computer provides free access to ERA5 data. The authentication is handled automatically by:

- **planetary-computer** package: Automatically signs URLs with SAS tokens
- **adlfs** library: Uses anonymous access for public Azure Blob Storage

The script handles authentication transparently - you don't need to configure any credentials.

## Usage

### Basic Usage

```python
from era5_abfs_access import ERA5ABFSAccessor

# Define your bounding box [min_lon, min_lat, max_lon, max_lat]
bbox = [17.9, 46.8, 18, 46.9]

# Create accessor
accessor = ERA5ABFSAccessor(bbox=bbox)

# Connect to services
accessor.connect_stac()
accessor.connect_abfs()

# Extract time series for multiple years
time_series = accessor.extract_time_series(
    years=[2020, 2021, 2022, 2023, 2024],
    variable="air_temperature_at_2_metres"
)

# Visualize the data
if time_series is not None:
    accessor.visualize_time_series(time_series)
```

### Run the Complete Script

```bash
python era5_abfs_access.py
```

This will:
1. Connect to Planetary Computer STAC API
2. Search for ERA5 data in your bounding box
3. Load temperature data from ABFS
4. Extract and aggregate time series
5. Create visualizations
6. Print summary statistics

## Configuration

### Bounding Box

The bounding box defines your area of interest:

```python
bbox = [min_longitude, min_latitude, max_longitude, max_latitude]
# Example: [17.9, 46.8, 18, 46.9]  # Small area in Central Europe
```

### Available Variables

Common ERA5 variables include:

- `air_temperature_at_2_metres` - 2m air temperature
- `precipitation_amount_1hour_Accumulation` - Hourly precipitation
- `dewpoint_temperature_at_2_metres` - 2m dewpoint temperature
- `sea_surface_temperature` - Sea surface temperature
- `surface_pressure` - Surface pressure
- `10m_u_component_of_wind` - 10m u-wind component
- `10m_v_component_of_wind` - 10m v-wind component

To find available variables, check the STAC collection:

```python
import pystac_client
import planetary_computer

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace
)

collection = catalog.get_collection("era5-pds")
# Inspect collection metadata for available variables
```

### Time Range

Specify years to extract:

```python
years = [2020, 2021, 2022, 2023, 2024]  # Or any available years
```

ERA5 data is available from 1940 to present (with some delay).

## How It Works

### 1. STAC API Query

The script uses Planetary Computer's STAC API to discover ERA5 data:

```python
search = catalog.search(
    collections=["era5-pds"],
    bbox=[17.9, 46.8, 18, 46.9],
    datetime="2020-01-01/2020-12-31"
)
```

### 2. ABFS URL Extraction

STAC items contain ABFS URLs like:
```
abfs://era5/ERA5/2020/12/air_temperature_at_2_metres.zarr
```

### 3. Zarr Data Loading

The script uses `adlfs` and `xarray` to load Zarr datasets:

```python
# Create filesystem mapper
fs = adlfs.AzureBlobFileSystem(account_name="ai4edataeuwest", anon=True)
mapper = fs.get_mapper("era5/ERA5/2020/12/air_temperature_at_2_metres.zarr")

# Load with xarray
ds = xr.open_zarr(mapper, consolidated=True)
```

### 4. Spatial Subsetting

Data is subset to your bounding box:

```python
ds_subset = ds.sel(
    longitude=slice(min_lon, max_lon),
    latitude=slice(min_lat, max_lat)
)
```

### 5. Time Series Aggregation

Spatial mean is calculated for each time step:

```python
time_series = data.mean(dim=['longitude', 'latitude'], skipna=True)
```

## Output

The script generates:

1. **Console Output**: Progress messages and summary statistics
2. **Visualization**: PNG file with two plots:
   - Full time series with statistics
   - Monthly averages
3. **Summary Statistics**: Mean, std, min, max, time range, data points

Example output file: `era5_temperature_timeseries_20241214_105206.png`

## Troubleshooting

### Issue: "No data could be loaded"

**Possible causes:**
1. Variable name might be incorrect
2. Data might not be available for specified years
3. Bounding box might be outside data coverage
4. Data structure might differ from expected

**Solutions:**
- Check variable names in STAC collection metadata
- Verify data availability for your time range
- Try a different variable or time period
- Inspect STAC items to see actual ABFS paths

### Issue: "Error connecting to ABFS"

**Solutions:**
- Ensure `adlfs` is installed: `pip install adlfs`
- Check internet connection
- Try accessing data directly via STAC items

### Issue: "Authentication error"

**Solutions:**
- Ensure `planetary-computer` package is installed
- The package should handle authentication automatically
- Check that you're not behind a restrictive firewall

### Issue: "Variable not found in dataset"

**Solutions:**
- Check available variables: `print(ds.data_vars)`
- Variable names might differ (e.g., `t2m` vs `air_temperature_at_2_metres`)
- The script will try to find matching variables automatically

## Data Structure

ERA5 data on Planetary Computer is organized as:

```
abfs://era5/ERA5/{year}/{month}/{variable}.zarr
```

Example:
```
abfs://era5/ERA5/2020/12/air_temperature_at_2_metres.zarr
```

Each Zarr dataset contains:
- **Time dimension**: Hourly or sub-hourly data
- **Spatial dimensions**: Longitude and latitude
- **Data variables**: The actual climate variable values

## Advanced Usage

### Custom Processing

```python
# Load data without aggregation
ds = accessor.load_zarr_data(abfs_path)

# Apply custom processing
# e.g., convert from Kelvin to Celsius
if 'air_temperature_at_2_metres' in ds:
    ds['temperature_celsius'] = ds['air_temperature_at_2_metres'] - 273.15

# Calculate daily averages
daily_avg = ds.resample(time='1D').mean()
```

### Multiple Variables

```python
variables = [
    "air_temperature_at_2_metres",
    "precipitation_amount_1hour_Accumulation"
]

for var in variables:
    time_series = accessor.extract_time_series(variable=var)
    if time_series is not None:
        accessor.visualize_time_series(time_series, variable=var)
```

### Export Data

```python
# Export to CSV
df = time_series.to_pandas()
df.to_csv('era5_temperature_timeseries.csv')

# Export to NetCDF
time_series.to_netcdf('era5_temperature_timeseries.nc')
```

## References

- [Planetary Computer Documentation](https://planetarycomputer.microsoft.com/docs/)
- [ERA5 Data Documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [XArray Documentation](https://docs.xarray.dev/)
- [ADLFS Documentation](https://github.com/fsspec/adlfs)
- [Zarr Format](https://zarr.readthedocs.io/)

## License

This script is provided as-is for educational and research purposes. ERA5 data is provided by ECMWF through Planetary Computer under their respective licenses.

## Support

For issues with:
- **Planetary Computer**: Check their [documentation](https://planetarycomputer.microsoft.com/docs/)
- **ERA5 Data**: See [ECMWF documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- **Script Issues**: Review the troubleshooting section above

