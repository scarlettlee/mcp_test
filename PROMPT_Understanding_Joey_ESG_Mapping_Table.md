# Prompt: Understanding the Joey - ESG Mapping.xlsx Table

## Purpose
This Excel table (`Joey - ESG Mapping.xlsx`) serves as a **mapping between Microsoft Planetary Computer STAC data collections and SASB (Sustainability Accounting Standards Board) ESG risk metrics**. It identifies which geospatial data collections are relevant for ESG risk estimation and explains why each collection matters for specific ESG concerns.

## Table Structure

### Entry Format
Each entry in the table follows this structured format:

```
[catalog-name]-#. Dataset_ID, Dataset_Title (matching reason)
```

**Components:**
- **`[catalog-name]`**: The STAC catalog identifier, derived from the catalog filename without the `.json` extension
  - Example: `stac-tags-planetarycomputer.microsoft.com.json` → `planetarycomputer.microsoft.com`
  - Example: `stac-tags-explorer.digitalearth.africa.json` → `explorer.digitalearth.africa`
- **`#`**: A sequential number (1, 2, 3...) indicating the entry order within that catalog
- **`Dataset_ID`**: The exact STAC collection ID used to search/access the data
  - Example: `nasa-nex-gddp-cmip6`, `modis-11A1-061`, `terraclimate`
- **`Dataset_Title`**: Human-readable name of the dataset
- **`(matching reason)`**: Explanation of why this collection is relevant for ESG risk assessment

### Multiple Entries
When multiple collections are listed for the same ESG metric or category:
- Entries are separated by **semicolons (`;`)** or **`<br>`** tags
- Each entry follows the same format independently

**Example:**
```
planetarycomputer.microsoft.com-1. nasa-nex-gddp-cmip6, NASA NEX-GDDP-CMIP6 Climate Projections (assesses future temperature scenarios through 2100 to assess climate-related risks to cooling energy demands);planetarycomputer.microsoft.com-2. modis-11A1-061, MODIS Land Surface Temperature (monitors heat island effects and thermal stress)
```

## How to Use This Table

### 1. **Identify Collections to Retrieve**
- Extract all `Dataset_ID` values from entries relevant to your ESG analysis
- These IDs are used to search the STAC API: `https://planetarycomputer.microsoft.com/api/stac/v1/collections/{Dataset_ID}`

### 2. **Understand ESG Relevance**
- Read the `(matching reason)` to understand:
  - What ESG risk this collection addresses
  - Which variables/metrics are most relevant
  - How the data should be interpreted for risk scoring

### 3. **Map to SASB Metrics**
- The table columns likely include SASB metric codes (e.g., `TC0102-01`, `TC0102-02`)
- These indicate which SASB disclosure topics each collection supports
- Use these to structure your ESG risk report according to SASB standards

### 4. **Determine Data Variables**
- Based on the matching reason, identify which variables to extract:
  - **Climate collections**: `tasmax` (max temperature), `pr` (precipitation), `tas` (temperature)
  - **Water collections**: `pdsi` (drought index), `def` (water deficit), `aet` (actual evapotranspiration)
  - **Thermal collections**: `LST_Day` (land surface temperature)
  - **Satellite collections**: Thermal bands, vegetation indices

### 5. **Select Time Periods**
- Use the matching reason to determine relevant time periods:
  - **Historical baseline**: Past 10-20 years for trend analysis
  - **Projections**: Future scenarios (2050, 2100) for climate risk
  - **Recent data**: Latest available for current risk assessment

## Key Collections from Planetary Computer

Based on typical ESG mapping tables, common collections include:

| Collection ID | Category | Key Variables | ESG Use Case |
|--------------|----------|---------------|--------------|
| `nasa-nex-gddp-cmip6` | Climate Projection | `tasmax`, `pr`, `tas` | Future temperature/precipitation extremes for infrastructure risk |
| `terraclimate` | Water/Climate | `pdsi`, `def`, `aet`, `soil` | Water stress and drought assessment |
| `modis-11A1-061` | Land Surface Temp | `LST_Day` | Heat island effects, thermal stress |
| `modis-11A2-061` | Land Surface Temp | `LST_Day` | Long-term heat trends |
| `gridmet` | Meteorology | `tmmx`, `pr`, `etr` | Heat and drought patterns |
| `daymet-annual-na` | Climate Annual | `tmax`, `tmin`, `prcp` | Annual climate trends |
| `daymet-monthly-na` | Climate Monthly | `tmax`, `tmin`, `prcp` | Seasonal risk patterns |
| `era5-pds` | Reanalysis | `t2m`, `tp` | Historical weather patterns |

## Workflow for ESG Data Collection

1. **Parse the Excel table** → Extract collection IDs and matching reasons
2. **Query STAC API** → Search for each collection ID
3. **Filter by location** → Use bounding box for company location (e.g., California: `[-124.5, 32.5, -114.0, 42.0]`)
4. **Extract relevant variables** → Based on matching reason and ESG variables list
5. **Calculate statistics** → Mean, max, trends per variable per time period
6. **Generate risk scores** → Based on thresholds and SASB metric requirements
7. **Output JSON** → Structure data for LLM consumption with raw data + risk scores

## Important Notes

- **Catalog name mapping**: Always derive catalog names from filenames by removing `.json` extension
- **Collection availability**: Not all collections may be available on Planetary Computer (some return 404)
- **Data formats**: Collections may use NetCDF, GeoTIFF, or Zarr formats - handle accordingly
- **Authentication**: Planetary Computer requires SAS token authentication for data access
- **Longitude formats**: Some collections use 0-360°, others use -180 to 180° - normalize as needed

## Example Interpretation

**Entry:**
```
planetarycomputer.microsoft.com-1. nasa-nex-gddp-cmip6, NASA NEX-GDDP-CMIP6 Climate Projections (assesses future temperature scenarios through 2100 to assess climate-related risks to cooling energy demands)
```

**Interpretation:**
- **Collection ID**: `nasa-nex-gddp-cmip6`
- **Catalog**: `planetarycomputer.microsoft.com`
- **ESG Relevance**: Cooling energy demand risk (relevant for data centers, offices)
- **Key Variables**: `tasmax` (maximum temperature), `tas` (temperature), `pr` (precipitation)
- **Time Periods**: Historical baseline + projections for 2050, 2100
- **Risk Metric**: Compare future temperatures vs. baseline to assess cooling infrastructure needs
- **SASB Context**: Likely maps to `TC0102-01` (Climate-related risks) for Software & IT Services sector

---

**Use this prompt to guide AI assistants in understanding and processing the Joey - ESG Mapping.xlsx table for ESG risk estimation workflows.**







