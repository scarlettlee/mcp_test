"""
Cleanup script for NASA NEX-GDDP-CMIP6 data
Keeps only one typical model and scenario for long-term ESG risk mapping
"""
import re
from pathlib import Path
from collections import Counter

def analyze_files(directory):
    """Analyze what models, scenarios, and years are in the directory"""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Directory not found: {directory}")
        return None
    
    files = list(dir_path.glob("*.nc"))
    print(f"\nTotal files found: {len(files)}")
    
    models = Counter()
    scenarios = Counter()
    years = set()
    
    for file in files:
        # Parse filename: nasa-nex-gddp-cmip6_MODEL.SCENARIO.YEAR.nc
        match = re.search(r'nasa-nex-gddp-cmip6_(.+?)\.(ssp\d+)\.(\d{4})\.nc', file.name)
        if match:
            model = match.group(1)
            scenario = match.group(2)
            year = match.group(3)
            
            models[model] += 1
            scenarios[scenario] += 1
            years.add(year)
    
    print(f"\nModels found ({len(models)}):")
    for model, count in models.most_common(10):
        print(f"  {model}: {count} files")
    
    print(f"\nScenarios found ({len(scenarios)}):")
    for scenario, count in scenarios.most_common():
        print(f"  {scenario}: {count} files")
    
    years_sorted = sorted([int(y) for y in years])
    print(f"\nYears range: {min(years_sorted)} to {max(years_sorted)} ({len(years_sorted)} years)")
    
    return {
        'files': files,
        'models': models,
        'scenarios': scenarios,
        'years': years_sorted
    }

def cleanup_directory(directory, keep_model="UKESM1-0-LL", keep_scenario="ssp245", auto_confirm=False):
    """
    Keep only files matching the specified model and scenario, delete the rest
    
    Args:
        directory: Path to the directory
        keep_model: Model to keep (default: UKESM1-0-LL - a well-regarded model)
        keep_scenario: Scenario to keep (default: ssp245 - moderate emissions)
        auto_confirm: If True, skip confirmation prompt
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Directory not found: {directory}")
        return
    
    files = list(dir_path.glob("*.nc"))
    print(f"\nAnalyzing {len(files)} files...")
    
    files_to_keep = []
    files_to_delete = []
    
    for file in files:
        # Check if file matches the model and scenario we want to keep
        match = re.search(r'nasa-nex-gddp-cmip6_(.+?)\.(ssp\d+)\.(\d{4})\.nc', file.name)
        if match:
            model = match.group(1)
            scenario = match.group(2)
            
            if model == keep_model and scenario == keep_scenario:
                files_to_keep.append(file)
            else:
                files_to_delete.append(file)
        else:
            # If filename doesn't match pattern, keep it to be safe
            files_to_keep.append(file)
    
    print(f"\nFiles to keep: {len(files_to_keep)}")
    print(f"Files to delete: {len(files_to_delete)}")
    
    if len(files_to_keep) == 0:
        print(f"\nWARNING: No files match model '{keep_model}' and scenario '{keep_scenario}'!")
        print("Available models and scenarios:")
        analysis = analyze_files(directory)
        return
    
    # Show what will be kept
    if files_to_keep:
        print(f"\nSample files to keep:")
        for f in files_to_keep[:5]:
            print(f"  {f.name}")
        if len(files_to_keep) > 5:
            print(f"  ... and {len(files_to_keep) - 5} more")
    
    # Confirm deletion
    print(f"\n{'='*60}")
    print(f"Will DELETE {len(files_to_delete)} files")
    print(f"Will KEEP {len(files_to_keep)} files")
    print(f"Model: {keep_model}, Scenario: {keep_scenario}")
    print(f"{'='*60}")
    
    if not auto_confirm:
        try:
            response = input("\nProceed with deletion? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Cancelled. No files deleted.")
                return
        except EOFError:
            print("\nNon-interactive mode detected. Use auto_confirm=True to proceed.")
            return
    else:
        print("\nAuto-confirm enabled. Proceeding with deletion...")
    
    # Delete files
    deleted_count = 0
    deleted_size = 0
    
    for file in files_to_delete:
        try:
            file_size = file.stat().st_size
            file.unlink()
            deleted_count += 1
            deleted_size += file_size
        except Exception as e:
            print(f"Error deleting {file.name}: {e}")
    
    print(f"\n[SUCCESS] Deleted {deleted_count} files")
    print(f"[SUCCESS] Freed approximately {deleted_size / (1024**3):.2f} GB")
    print(f"[SUCCESS] Kept {len(files_to_keep)} files")

if __name__ == "__main__":
    directory = "downloads/nasa-nex-gddp-cmip6"
    
    print("="*60)
    print("NASA NEX-GDDP-CMIP6 Data Cleanup")
    print("="*60)
    
    # First, analyze what's in the directory
    analysis = analyze_files(directory)
    
    if analysis:
        print("\n" + "="*60)
        print("RECOMMENDATION:")
        print("="*60)
        print("For ESG risk mapping, keeping:")
        print("  Model: UKESM1-0-LL (well-regarded UK model)")
        print("  Scenario: ssp245 (moderate emissions - SSP2-4.5)")
        print("\nThis provides long-term projections (2039-2100) for climate risk assessment")
        print("="*60)
        
        # Run cleanup
        import sys
        auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
        cleanup_directory(directory, keep_model="UKESM1-0-LL", keep_scenario="ssp245", auto_confirm=auto_confirm)

