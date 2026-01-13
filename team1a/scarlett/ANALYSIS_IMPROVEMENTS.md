# Analysis Improvements

## Issues Fixed

### 1. Matching Reasons Parsing

**Problem**: The analysis was too simple and didn't consider different matching reasons for the same collection.

**Solution**:
- Added `_parse_matching_reasons()` method that extracts analysis requirements from matching reason text
- Loads matching reasons from Excel file if available
- Parses requirements like:
  - `analyze_temperature`: Extract from "temperature", "cooling", "energy", "heat"
  - `analyze_precipitation`: Extract from "precipitation", "water", "stress", "drought"
  - `trend_through_2100`: Extract from "2100" in text
  - `trend_through_2050`: Extract from "2050" in text

**Example Matching Reasons**:
- "projects future temperature scenarios through 2100 to assess climate-related risks to cooling energy demands"
  → `analyze_temperature=True`, `analyze_cooling_energy=True`, `trend_through_2100=True`
- "projects future water stress conditions through climate scenarios for long-term facility planning"
  → `analyze_precipitation=True`, `analyze_water_stress=True`

### 2. Trend Analysis

**Problem**: Only analyzed single year (2025) data, didn't analyze trends through 2100.

**Solution**:
- Added `_analyze_trends()` method that:
  - Groups files by year
  - Calculates yearly means
  - Fits linear trend
  - Projects to 2050 and/or 2100 when required
- Updated ESG metric calculations to include trend projections

**Output**:
```json
{
  "trends": {
    "tasmax": {
      "years_analyzed": [2025, 2030, ...],
      "values": [25.5, 26.2, ...],
      "trend_slope": 0.05,
      "projections": {
        "2050": 28.5,
        "2100": 31.2
      }
    }
  }
}
```

### 3. MODIS HDF Reading

**Problem**: MODIS files are HDF-EOS format, not regular GeoTIFF. The script was trying to read .tif files that don't exist.

**Solution**:
- Added `pyhdf` library support for HDF-EOS files
- Updated `_analyze_thermal_data()` to:
  - Use `pyhdf.SD` for MODIS HDF-EOS files
  - Properly extract LST_Day and LST_Night datasets
  - Apply scale factors and offsets
  - Fallback to h5py if pyhdf fails
- Updated `_find_data_files()` to include `.hdf` files

**MODIS Structure**:
- MOD11A2 files contain `LST_Day_1km` and `LST_Night_1km` datasets
- Requires scale factor and offset application
- Units are in Kelvin (scale factor 0.02, offset 0)

### 4. Enhanced ESG Metrics

**Improvements**:
- **Cooling Energy Risk**: Now includes future projections (2050, 2100) with risk levels
- **Temperature Extremes**: Includes trend analysis and projections
- **Precipitation Risk**: Includes trend analysis and water stress assessment
- **Water Stress**: New metric for water stress based on precipitation trends

**Example Output**:
```json
{
  "cooling_energy_risk": {
    "risk_level": "medium",
    "metrics": {
      "mean_temperature_celsius": 25.5,
      "max_temperature_celsius": 35.2
    },
    "future_projection": {
      "2050": {
        "temperature_celsius": 28.5,
        "risk_level": "medium"
      },
      "2100": {
        "temperature_celsius": 31.2,
        "risk_level": "high"
      }
    }
  }
}
```

## Usage

### Install New Dependencies

```bash
pip install pyhdf
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### Run Analysis

```bash
python team1a/scarlett/esg_data_analysis.py
```

The script will:
1. Load matching reasons from Excel file (if available)
2. Parse requirements from each matching reason
3. Analyze trends through 2100 when required
4. Properly read MODIS HDF files
5. Generate comprehensive ESG metrics with projections

## Key Features

### 1. Intelligent Matching Reason Parsing

The script now understands different matching reasons and adapts analysis accordingly:

- **Temperature-focused**: Analyzes tas, tasmax, calculates cooling energy risk
- **Precipitation-focused**: Analyzes pr, calculates water stress
- **Trend-focused**: Analyzes trends through 2050/2100 when mentioned

### 2. Multi-Year Trend Analysis

- Groups files by scenario, model, and year
- Calculates trends across years
- Projects to future years (2050, 2100)
- Includes trend slope and intercept

### 3. Proper MODIS Support

- Uses pyhdf for HDF-EOS format
- Extracts LST_Day and LST_Night
- Applies proper scaling
- Calculates heat island effects

### 4. Enhanced Reporting

- Includes trend projections in reports
- Shows risk levels for future years
- Provides comprehensive statistics
- Maps to ESG requirements

## Example Analysis Output

For a matching reason like:
"projects future temperature scenarios through 2100 to assess climate-related risks to cooling energy demands"

The analysis will:
1. Extract: `analyze_temperature=True`, `analyze_cooling_energy=True`, `trend_through_2100=True`
2. Analyze tas/tasmax variables
3. Calculate trends across available years
4. Project to 2100
5. Assess cooling energy risk for current and future (2100)
6. Report risk levels for both time periods

## Next Steps

After running the improved analysis:

1. **Review Trends**: Check trend projections in `esg_analysis_results.json`
2. **Validate Projections**: Verify 2050/2100 projections make sense
3. **Compare Scenarios**: Compare SSP245 vs SSP585 scenarios
4. **Generate Visualizations**: Create trend charts showing projections
5. **Map to SASB**: Link findings to specific SASB disclosure topics






