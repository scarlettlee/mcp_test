"""
Quick fix script for openpyxl DLL/expat issues.

Run this script to attempt to fix the openpyxl installation.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{description}...")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("="*70)
    print("openpyxl Fix Script")
    print("="*70)
    
    # Check if conda is available
    try:
        subprocess.run(["conda", "--version"], check=True, capture_output=True)
        use_conda = True
        print("✓ Conda detected")
    except:
        use_conda = False
        print("⚠ Conda not detected, will use pip")
    
    fixes = []
    
    if use_conda:
        # Fix 1: Install expat and libxml2 via conda-forge
        fixes.append((
            "conda install -c conda-forge expat libxml2 -y",
            "Installing expat and libxml2 via conda-forge"
        ))
        
        # Fix 2: Reinstall openpyxl via conda-forge
        fixes.append((
            "conda install -c conda-forge openpyxl -y",
            "Reinstalling openpyxl via conda-forge"
        ))
    else:
        # Fix 1: Upgrade pip
        fixes.append((
            f"{sys.executable} -m pip install --upgrade pip",
            "Upgrading pip"
        ))
        
        # Fix 2: Reinstall openpyxl
        fixes.append((
            f"{sys.executable} -m pip install --upgrade --force-reinstall openpyxl",
            "Reinstalling openpyxl"
        ))
    
    # Try fixes
    for cmd, desc in fixes:
        if run_command(cmd, desc):
            # Test if it works
            try:
                import openpyxl
                from openpyxl import Workbook
                wb = Workbook()
                print("✓ openpyxl is now working!")
                return True
            except Exception as e:
                print(f"⚠ openpyxl still has issues: {str(e)[:100]}")
    
    print("\n" + "="*70)
    print("If fixes didn't work, try:")
    print("="*70)
    print("1. Create a fresh conda environment:")
    print("   conda create -n esg_env python=3.10")
    print("   conda activate esg_env")
    print("   conda install -c conda-forge pandas openpyxl")
    print("\n2. Or export Excel to CSV and use CSV parser")
    print("   See TROUBLESHOOTING.md for details")
    print("="*70)
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






