"""
Remove ssp585 files from downloads directory
Keep only ssp245 and historical scenarios
"""
from pathlib import Path

download_dir = Path("downloads/nasa-nex-gddp-cmip6")

# Find all ssp585 files
ssp585_files = [f for f in download_dir.glob("*.nc") if '.ssp585.' in f.name]

print("="*60)
print("Removing ssp585 Files")
print("="*60)
print(f"\nFound {len(ssp585_files)} ssp585 files to remove")

if ssp585_files:
    print("\nSample files to remove:")
    for f in ssp585_files[:10]:
        print(f"  {f.name}")
    if len(ssp585_files) > 10:
        print(f"  ... and {len(ssp585_files) - 10} more")
    
    print(f"\n{'='*60}")
    print("Removing ssp585 files...")
    print("="*60)
    
    deleted_count = 0
    deleted_size = 0
    
    for file in ssp585_files:
        try:
            file_size = file.stat().st_size
            file.unlink()
            deleted_count += 1
            deleted_size += file_size
        except Exception as e:
            print(f"Error deleting {file.name}: {e}")
    
    print(f"\n[SUCCESS] Deleted {deleted_count} files")
    print(f"[SUCCESS] Freed approximately {deleted_size / (1024**3):.2f} GB")
else:
    print("\nNo ssp585 files found. Directory is clean!")

