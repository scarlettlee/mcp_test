# Troubleshooting Guide for ESG Data Retrieval

## Common Issues and Solutions

### Issue: DLL/expat Error with openpyxl

**Error Message:**
```
ImportError: DLL load failed while importing pyexpat: The operating system cannot run %1.
```

**Cause:**
This is a common issue on Windows with Anaconda environments where the XML/expat module is corrupted or incompatible.

**Solutions (try in order):**

#### Solution 1: Reinstall openpyxl via conda-forge (Recommended)
```bash
conda install -c conda-forge openpyxl
```

#### Solution 2: Reinstall Python XML libraries
```bash
conda install -c conda-forge expat
conda install -c conda-forge libxml2
pip install --upgrade --force-reinstall openpyxl
```

#### Solution 3: Use a fresh conda environment
```bash
# Create new environment
conda create -n esg_env python=3.10
conda activate esg_env

# Install dependencies
conda install -c conda-forge pandas openpyxl
pip install planetary-computer requests rasterio numpy
```

#### Solution 4: Use pip instead of conda
```bash
# Deactivate conda environment
conda deactivate

# Use system Python or create venv
python -m venv esg_venv
esg_venv\Scripts\activate  # On Windows
# or
source esg_venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install pandas openpyxl planetary-computer requests rasterio numpy
```

#### Solution 5: Export Excel to CSV (Workaround)
If you can't fix the openpyxl issue, you can export the Excel file to CSV:

1. Open `Joey - ESG Mapping.xlsx` in Excel
2. Save As → CSV format
3. Modify the script to read CSV instead (see below)

### Issue: Missing pandas or openpyxl

**Error:** `Missing optional dependency 'openpyxl'`

**Solution:**
```bash
pip install pandas openpyxl
# OR
conda install -c conda-forge pandas openpyxl
```

### Issue: Collection Not Found in STAC API

**Error:** `Failed to fetch collection {collection_id}`

**Solutions:**
1. Verify collection ID spelling
2. Check if collection exists: `https://planetarycomputer.microsoft.com/api/stac/v1/collections/{collection_id}`
3. Some collections may be deprecated or unavailable

### Issue: No Items Found

**Error:** `No items found for collection`

**Solutions:**
1. Expand the bounding box (collection may not cover San Francisco area)
2. Check collection's spatial extent
3. Try a different time period
4. Some collections are regional and may not have global coverage

### Issue: Network/Timeout Errors

**Error:** `Failed to search items` or timeout errors

**Solutions:**
1. Check internet connection
2. Increase timeout values in the code
3. Try again later (Planetary Computer may be experiencing high load)

## Alternative: Using CSV Instead of Excel

If you continue having issues with Excel reading, you can export to CSV:

### Step 1: Export Excel to CSV
1. Open `Joey - ESG Mapping.xlsx` in Excel
2. File → Save As → Choose CSV format
3. Save as `Joey - ESG Mapping.csv`

### Step 2: Modify Script to Read CSV

Add this function to `esg_data_retrieval.py`:

```python
def parse_csv(self, csv_path: str) -> List[Dict[str, Any]]:
    """Parse CSV file instead of Excel."""
    import pandas as pd
    
    print(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    collections = []
    for col_idx, col_name in enumerate(df.columns):
        for row_idx, cell_value in enumerate(df[col_name]):
            if pd.isna(cell_value):
                continue
            
            cell_str = str(cell_value)
            parsed = self._parse_cell(cell_str, col_name, row_idx)
            if parsed:
                collections.extend(parsed)
    
    return collections
```

Then in `main()`, change:
```python
# From:
collections = parser.parse_excel()

# To:
csv_file = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.csv')
collections = parser.parse_csv(csv_file)
```

## Getting Help

If none of these solutions work:

1. Check your Python version: `python --version` (should be 3.7+)
2. Check your conda/pip version: `conda --version` or `pip --version`
3. Try in a fresh environment
4. Check the full error traceback for more details

## Environment Verification

Run this to verify your environment:

```python
import sys
print(f"Python: {sys.version}")

try:
    import pandas as pd
    print(f"✓ pandas: {pd.__version__}")
except ImportError:
    print("✗ pandas not installed")

try:
    import openpyxl
    print(f"✓ openpyxl: {openpyxl.__version__}")
except ImportError:
    print("✗ openpyxl not installed")
except Exception as e:
    print(f"✗ openpyxl has issues: {str(e)[:100]}")

try:
    import planetary_computer
    print("✓ planetary-computer installed")
except ImportError:
    print("✗ planetary-computer not installed")
```






