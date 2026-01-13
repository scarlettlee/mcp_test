# ESG Data Analysis Guide

## Overview

After downloading ESG data using `esg_data_retrieval.py`, use `esg_data_analysis.py` to analyze the data according to matching reasons and generate ESG risk metrics.

## Quick Start

### 1. Install Additional Dependencies

```bash
pip install xarray h5py netcdf4
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Run Analysis

```bash
python team1a/scarlett/esg_data_analysis.py
```

This will:
- Read the retrieval results JSON
- Analyze downloaded NetCDF files (climate projections)
- Analyze MODIS HDF files (thermal data)
- Calculate ESG risk metrics
- Generate analysis report

## What Gets Analyzed

### 1. Climate Projections (nasa-nex-gddp-cmip6)

**Variables Analyzed:**
- `tas`: Average temperature
- `tasmax`: Maximum temperature
- `tasmin`: Minimum temperature
- `pr`: Precipitation

**ESG Metrics Calculated:**
- **Cooling Energy Risk**: Based on temperature thresholds
  - High risk: Mean temperature > 30°C
  - Medium risk: Mean temperature > 25°C
  - Low risk: Mean temperature ≤ 25°C

- **Temperature Extremes**: Percentiles and extremes
- **Precipitation Risk**: Mean, max, and variability

**Output:**
- Statistics for each variable (mean, max, min, std, percentiles)
- ESG risk assessments
- Risk level classifications

### 2. Thermal Data (modis-11A2-061)

**Variables Analyzed:**
- `LST_Day`: Land Surface Temperature (Day)
- `LST_Night`: Land Surface Temperature (Night)

**ESG Metrics Calculated:**
- **Heat Island Effect**: Urban heat island intensity
- **Thermal Stress**: Day/night temperature differences

**Note:** MODIS HDF file parsing requires proper structure understanding. The current implementation provides a framework that can be extended.

## Output Structure

```
esg_data_retrieval/
├── esg_retrieval_results.json    # Original retrieval results
└── esg_analysis/                  # Analysis results
    ├── esg_analysis_results.json  # Detailed analysis (JSON)
    └── esg_analysis_report.txt    # Human-readable report
```

## Understanding the Analysis Results

### JSON Output Structure

```json
{
  "analysis_date": "2025-12-05T...",
  "bbox": [-122.5, 37.7, -122.3, 37.8],
  "collections_analyzed": [
    {
      "dataset_id": "nasa-nex-gddp-cmip6",
      "matching_reason": "...",
      "variables_analyzed": {
        "tasmax": {
          "status": "success",
          "statistics": {
            "mean": 25.5,
            "max": 35.2,
            "min": 15.8,
            "std": 4.2,
            "units": "celsius"
          }
        }
      },
      "esg_metrics": {
        "cooling_energy_risk": {
          "risk_level": "medium",
          "metrics": {
            "mean_temperature": 25.5,
            "max_temperature": 35.2
          }
        }
      }
    }
  ],
  "summary": {
    "total_collections": 2,
    "successful_analyses": 2,
    "key_findings": [...]
  }
}
```

### Report Output

The text report includes:
- Summary statistics
- Variable-by-variable analysis
- ESG risk metrics
- Risk level assessments

## Customization

### Modify Risk Thresholds

Edit `esg_data_analysis.py`:

```python
def _calculate_cooling_energy_risk(self, variables):
    # Modify thresholds
    if mean_temp > 32:  # Change from 30
        risk['risk_level'] = 'high'
    # ...
```

### Add New Metrics

Add new calculation methods:

```python
def _calculate_custom_metric(self, variables):
    # Your custom calculation
    return {'status': 'calculated', 'value': ...}
```

Then call it in `_analyze_collection()`:

```python
analysis['esg_metrics']['custom_metric'] = self._calculate_custom_metric(
    analysis['variables_analyzed']
)
```

## About era5-pds

The era5-pds collection uses Zarr format stored in Azure Blob File System (`abfs://`), which requires special handling. The current downloader doesn't handle Zarr files directly. To analyze era5-pds data:

1. Use `adlfs` library to access Azure Blob File System
2. Use `xarray` with `zarr` backend to read Zarr datasets
3. Process the data similar to NetCDF files

Example:
```python
import adlfs
import xarray as xr

fs = adlfs.AzureBlobFileSystem(...)
ds = xr.open_zarr(fs.get_mapper('era5/ERA5/2020/12/precipitation_amount_1hour_Accumulation.zarr'))
```

## Next Steps

After analysis:

1. **Review Results**: Check `esg_analysis_report.txt` for key findings
2. **Validate Metrics**: Verify risk assessments make sense for your location
3. **Generate Visualizations**: Create charts/maps from the analysis results
4. **Map to SASB Metrics**: Link findings to specific SASB disclosure topics
5. **Create ESG Report**: Structure findings according to SASB standards

## Troubleshooting

### "xarray not available"
```bash
pip install xarray netcdf4
```

### "h5py not available"
```bash
pip install h5py
```

### "No data found for collection"
- Check that files were downloaded in `esg_data_retrieval/vectors/` or `esg_data_retrieval/rasters/`
- Verify file formats match expected types (.nc for NetCDF, .hdf for MODIS)

### "Error reading NetCDF file"
- Check file is not corrupted
- Verify file has expected variables
- Check coordinate system matches bounding box

## References

- [xarray Documentation](https://docs.xarray.dev/)
- [NetCDF Documentation](https://www.unidata.ucar.edu/software/netcdf/)
- [MODIS Data Products](https://modis.gsfc.nasa.gov/data/)






