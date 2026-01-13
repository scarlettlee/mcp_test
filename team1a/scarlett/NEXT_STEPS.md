# Next Steps: ESG Data Analysis

## Current Status

✅ **Data Retrieval Complete**
- Successfully retrieved 3 collections
- Downloaded data for 2 collections:
  - `nasa-nex-gddp-cmip6`: Climate projection NetCDF files
  - `modis-11A2-061`: MODIS thermal HDF files
- `era5-pds`: Found but not downloaded (see explanation below)

## About era5-pds

The `era5-pds` collection was found but not downloaded because:

- **Format**: Uses Zarr format stored in Azure Blob File System (`abfs://`)
- **Current Limitation**: The downloader handles HTTP URLs but not Azure Blob File System paths
- **Solution**: Requires `adlfs` library for Azure Blob access

To download era5-pds data in the future:
```python
import adlfs
import xarray as xr

fs = adlfs.AzureBlobFileSystem(...)
# Access Zarr datasets directly
```

## Downloaded Data Summary

### nasa-nex-gddp-cmip6 (Climate Projections)
- **Location**: `esg_data_retrieval/vectors/nasa-nex-gddp-cmip6/`
- **Files**: 35 NetCDF (.nc) files
- **Variables**: `tas`, `tasmax`, `tasmin`, `pr`, `hurs`, `huss`, `rlds`, `rsds`, `sfcWind`
- **Scenarios**: SSP245, SSP585
- **Models**: IITM-ESM, UKESM1-0-LL, TaiESM1
- **Year**: 2025 projections

### modis-11A2-061 (Land Surface Temperature)
- **Location**: `esg_data_retrieval/vectors/modus-11A2-061/`
- **Files**: 5 HDF files
- **Variables**: LST_Day, LST_Night (in HDF structure)
- **Period**: 2025 (recent data)

## Step 2: Run Analysis

Now that data is downloaded, analyze it:

```bash
# Install analysis dependencies
pip install xarray h5py netcdf4

# Run analysis
python team1a/scarlett/esg_data_analysis.py
```

This will:
1. Read NetCDF files and extract climate variables
2. Calculate statistics (mean, max, min, percentiles)
3. Assess ESG risks based on matching reasons:
   - Cooling energy demand risk (from temperature)
   - Temperature extremes
   - Precipitation patterns
4. Generate analysis report

## Expected Analysis Output

After running the analysis, you'll get:

```
esg_data_retrieval/
└── esg_analysis/
    ├── esg_analysis_results.json  # Detailed JSON results
    └── esg_analysis_report.txt      # Human-readable report
```

The report will include:
- Variable statistics for each collection
- ESG risk assessments
- Risk level classifications
- Key findings summary

## Step 3: Interpret Results

### Climate Projections (nasa-nex-gddp-cmip6)

**For Cooling Energy Risk:**
- Check `cooling_energy_risk` metric
- Risk levels: High (>30°C), Medium (>25°C), Low (≤25°C)
- Compare SSP245 vs SSP585 scenarios
- Compare different climate models

**For Temperature Extremes:**
- Review `temperature_extremes` metrics
- Check p95 (95th percentile) for extreme heat events
- Compare tasmax across scenarios

**For Precipitation:**
- Review `precipitation_risk` metrics
- Check variability (std) for drought/flood risk

### Thermal Data (modis-11A2-061)

**For Heat Island Effects:**
- Compare LST_Day vs LST_Night
- Identify urban heat island intensity
- Assess thermal stress patterns

## Step 4: Map to SASB Metrics

Based on the matching reasons from the Excel file:

1. **Cooling Energy Demand** → SASB TC0102-01 (Climate-related risks)
2. **Temperature Extremes** → TC0102-01 (Climate-related risks)
3. **Precipitation Patterns** → TC0102-02 (Water management)
4. **Heat Island Effects** → TC0102-01 (Climate-related risks)

## Step 5: Generate ESG Report

Create a structured report:

1. **Executive Summary**: Key findings
2. **Climate Risk Assessment**: 
   - Current conditions
   - Future projections (2025, 2050, 2100)
   - Risk levels
3. **Water Risk Assessment**:
   - Precipitation patterns
   - Drought risk
4. **Thermal Risk Assessment**:
   - Heat island effects
   - Thermal stress
5. **Recommendations**: Based on risk levels

## Files Created

- ✅ `esg_data_retrieval.py`: Data retrieval script
- ✅ `esg_data_analysis.py`: Data analysis script
- ✅ `planetary_computer_framework.py`: Core framework
- ✅ `ESG_RETRIEVAL_GUIDE.md`: Retrieval documentation
- ✅ `ANALYSIS_GUIDE.md`: Analysis documentation
- ✅ `TROUBLESHOOTING.md`: Troubleshooting guide

## Quick Reference

```bash
# Step 1: Retrieve data (already done)
python team1a/scarlett/esg_data_retrieval.py

# Step 2: Analyze data
python team1a/scarlett/esg_data_analysis.py

# Step 3: Review results
# Check: esg_data_retrieval/esg_analysis/esg_analysis_report.txt
```

## Need Help?

- See `ANALYSIS_GUIDE.md` for detailed analysis documentation
- See `TROUBLESHOOTING.md` for common issues
- Check analysis results JSON for detailed metrics






