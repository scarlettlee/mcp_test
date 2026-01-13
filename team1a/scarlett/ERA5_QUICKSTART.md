# ERA5 ABFS Access - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements_era5.txt
```

Or install manually:
```bash
pip install adlfs xarray matplotlib numpy pandas planetary-computer pystac-client zarr fsspec
```

### 2. Run the Script

```bash
python era5_abfs_access.py
```

That's it! The script will:
- ✅ Connect to Planetary Computer STAC API
- ✅ Search for ERA5 temperature data in your bounding box [17.9, 46.8, 18, 46.9]
- ✅ Load data from Azure Blob Storage (ABFS)
- ✅ Extract time series for 2020-2024
- ✅ Create visualizations
- ✅ Print summary statistics

### 3. Customize (Optional)

Edit the script to change:
- **Bounding box**: Modify `bbox = [17.9, 46.8, 18, 46.9]` in `main()`
- **Years**: Change `years = [2020, 2021, 2022, 2023, 2024]`
- **Variable**: Change `variable = "air_temperature_at_2_metres"`

## 📁 Files Created

- **`era5_abfs_access.py`** - Complete script with full functionality
- **`era5_example_simple.py`** - Minimal example (good for learning)
- **`requirements_era5.txt`** - Package dependencies
- **`ERA5_ABFS_README.md`** - Comprehensive documentation
- **`ERA5_QUICKSTART.md`** - This file

## 🔍 What You'll Get

### Console Output
```
============================================================
ERA5 Climate Data Access via Azure Blob File System
============================================================
Connecting to Planetary Computer STAC API...
✓ Successfully connected to STAC API
Connecting to Azure Blob File System...
✓ Successfully connected to ABFS

Searching for ERA5 air_temperature_at_2_metres data...
Bounding box: [17.9, 46.8, 18, 46.9]
Years: [2020, 2021, 2022, 2023, 2024]
...
```

### Visualization
A PNG file with two plots:
1. Full time series with statistics
2. Monthly averages

### Summary Statistics
```
Time Series Summary Statistics
============================================================
Mean: 285.23 K
Standard Deviation: 8.45 K
Minimum: 268.12 K
Maximum: 302.34 K
Time Range: 2020-01-01 to 2024-12-31
Total Data Points: 43824
```

## 🛠️ Troubleshooting

### "No data could be loaded"
- Check that the variable name is correct
- Verify data availability for your time range
- Try a different bounding box

### "Error connecting to ABFS"
- Ensure `adlfs` is installed: `pip install adlfs`
- Check internet connection
- The script tries multiple access methods automatically

### "Module not found"
- Install missing packages: `pip install -r requirements_era5.txt`

## 📚 Next Steps

1. **Read the full documentation**: See `ERA5_ABFS_README.md`
2. **Try the simple example**: Run `era5_example_simple.py`
3. **Explore other variables**: Change the variable name in the script
4. **Process multiple variables**: Loop through different variables

## 💡 Example: Access Different Variables

```python
variables = [
    "air_temperature_at_2_metres",
    "precipitation_amount_1hour_Accumulation",
    "dewpoint_temperature_at_2_metres"
]

for var in variables:
    time_series = accessor.extract_time_series(variable=var)
    if time_series is not None:
        accessor.visualize_time_series(time_series, variable=var)
```

## 🔗 Resources

- [Planetary Computer Docs](https://planetarycomputer.microsoft.com/docs/)
- [ERA5 Documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [XArray Tutorial](https://docs.xarray.dev/en/stable/user-guide/quick-overview.html)

## ❓ Need Help?

1. Check `ERA5_ABFS_README.md` for detailed troubleshooting
2. Review error messages in console output
3. Verify your bounding box and time range
4. Ensure all packages are installed correctly

---

**Happy analyzing! 🌍📊**

