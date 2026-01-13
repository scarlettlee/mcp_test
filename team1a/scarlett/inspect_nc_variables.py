"""
Inspect variables available in downloaded NEX-GDDP-CMIP6 NetCDF files
"""
import xarray as xr
from pathlib import Path

# Check a few sample files
download_dir = Path("downloads/nasa-nex-gddp-cmip6")
files = list(download_dir.glob("*.nc"))

if not files:
    print("No NetCDF files found!")
    exit()

print("="*60)
print("Inspecting NetCDF File Variables")
print("="*60)

# Check historical file
historical_files = [f for f in files if '.historical.' in f.name]
if historical_files:
    print(f"\nChecking historical file: {historical_files[0].name}")
    try:
        ds = xr.open_dataset(historical_files[0])
        print(f"\nVariables in file:")
        for var_name in ds.data_vars:
            var = ds[var_name]
            print(f"  - {var_name}")
            print(f"    Shape: {var.shape}")
            print(f"    Dimensions: {var.dims}")
            if hasattr(var, 'long_name'):
                print(f"    Long name: {var.long_name}")
            if hasattr(var, 'units'):
                print(f"    Units: {var.units}")
            print()
        
        print(f"\nCoordinates:")
        for coord_name in ds.coords:
            coord = ds[coord_name]
            print(f"  - {coord_name}: {coord.shape}")
            if len(coord) > 0:
                print(f"    Range: {float(coord.min().values):.2f} to {float(coord.max().values):.2f}")
        
        print(f"\nGlobal attributes:")
        for attr in ds.attrs:
            print(f"  {attr}: {ds.attrs[attr]}")
        
        ds.close()
    except Exception as e:
        print(f"Error opening file: {e}")

# Check future file
future_files = [f for f in files if '.ssp245.' in f.name]
if future_files:
    print(f"\n{'='*60}")
    print(f"Checking future file: {future_files[0].name}")
    try:
        ds = xr.open_dataset(future_files[0])
        print(f"\nVariables in file:")
        for var_name in ds.data_vars:
            var = ds[var_name]
            print(f"  - {var_name}")
            print(f"    Shape: {var.shape}")
            print(f"    Dimensions: {var.dims}")
            if hasattr(var, 'long_name'):
                print(f"    Long name: {var.long_name}")
            if hasattr(var, 'units'):
                print(f"    Units: {var.units}")
            print()
        
        print(f"\nCoordinates:")
        for coord_name in ds.coords:
            coord = ds[coord_name]
            print(f"  - {coord_name}: {coord.shape}")
            if len(coord) > 0:
                try:
                    print(f"    Range: {float(coord.min().values):.2f} to {float(coord.max().values):.2f}")
                except:
                    print(f"    Values: {coord.values[:5]}...")
        
        ds.close()
    except Exception as e:
        print(f"Error opening file: {e}")

# Check all files to see if they have different variables
print(f"\n{'='*60}")
print("Checking variable consistency across files...")
print("="*60)

all_variables = set()
for file in files[:10]:  # Check first 10 files
    try:
        ds = xr.open_dataset(file)
        all_variables.update(ds.data_vars.keys())
        ds.close()
    except Exception as e:
        print(f"Error reading {file.name}: {e}")

print(f"\nAll variables found across sample files:")
for var in sorted(all_variables):
    print(f"  - {var}")




