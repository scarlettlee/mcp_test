"""
ESG Data Analysis Script

This script analyzes the downloaded ESG data according to matching reasons
and generates ESG risk metrics and reports.

It processes:
- Climate projection data (nasa-nex-gddp-cmip6): Future temperature/precipitation scenarios
- Thermal data (modis-11A2-061): Land surface temperature for heat island effects
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, os.path.abspath(project_root))
sys.path.insert(0, os.path.dirname(__file__))

# Try to import required libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available. Install with: pip install numpy")

try:
    import xarray as xr
    XARRAY_AVAILABLE = True
except ImportError:
    XARRAY_AVAILABLE = False
    print("Warning: xarray not available. Install with: pip install xarray")

try:
    import rasterio
    from rasterio.warp import transform_bounds
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False
    print("Warning: h5py not available. Install with: pip install h5py")

# Try pyhdf for MODIS HDF-EOS files
try:
    from pyhdf.SD import SD, SDC
    PYHDF_AVAILABLE = True
except ImportError:
    PYHDF_AVAILABLE = False
    print("Warning: pyhdf not available. Install with: pip install pyhdf")

# San Francisco bounding box [min_lon, min_lat, max_lon, max_lat]
SAN_FRANCISCO_BBOX = [-122.5, 37.7, -122.3, 37.8]


class ESGDataAnalyzer:
    """Analyzes ESG data according to matching reasons."""
    
    def __init__(self, data_dir: str, results_json: str, excel_file: Optional[str] = None):
        """
        Initialize the analyzer.
        
        Args:
            data_dir: Directory containing downloaded data
            results_json: Path to esg_retrieval_results.json
            excel_file: Optional path to Excel file with matching reasons
        """
        self.data_dir = Path(data_dir)
        self.results_json = Path(results_json)
        
        # Load retrieval results
        with open(self.results_json, 'r') as f:
            self.retrieval_results = json.load(f)
        
        # Load matching reasons from Excel if available
        self.matching_reasons_map = {}
        if excel_file and os.path.exists(excel_file):
            self._load_matching_reasons_from_excel(excel_file)
        
        # Output directory for analysis results
        self.output_dir = self.data_dir.parent / "esg_analysis"
        self.output_dir.mkdir(exist_ok=True)
    
    def _load_matching_reasons_from_excel(self, excel_file: str):
        """Load matching reasons from Excel file."""
        try:
            import pandas as pd
            from esg_data_retrieval import ESGMappingParser
            
            parser = ESGMappingParser(excel_file)
            collections = parser.parse_excel()
            pc_collections = parser.filter_planetary_computer(collections)
            
            for col in pc_collections:
                dataset_id = col.get('dataset_id')
                matching_reason = col.get('matching_reason', '')
                if dataset_id and matching_reason:
                    # Store all matching reasons for this dataset
                    if dataset_id not in self.matching_reasons_map:
                        self.matching_reasons_map[dataset_id] = []
                    self.matching_reasons_map[dataset_id].append(matching_reason)
            
            print(f"  Loaded {len(self.matching_reasons_map)} datasets with matching reasons from Excel")
        except Exception as e:
            print(f"  Warning: Could not load matching reasons from Excel: {str(e)}")
    
    def analyze_all_collections(self) -> Dict[str, Any]:
        """
        Analyze all collections in the retrieval results.
        
        Returns:
            Dictionary with analysis results
        """
        print("=" * 70)
        print("ESG Data Analysis")
        print("=" * 70)
        print()
        
        analysis_results = {
            'analysis_date': datetime.now().isoformat(),
            'bbox': self.retrieval_results.get('bbox', []),
            'collections_analyzed': [],
            'summary': {}
        }
        
        # Process each successful collection
        for collection_result in self.retrieval_results.get('collection_results', []):
            if collection_result.get('status') != 'success':
                continue
            
            dataset_id = collection_result.get('dataset_id')
            print(f"\n{'='*70}")
            print(f"Analyzing: {dataset_id}")
            print(f"{'='*70}")
            
            try:
                analysis = self._analyze_collection(collection_result)
                analysis_results['collections_analyzed'].append(analysis)
                
                print(f"✓ Analysis complete for {dataset_id}")
                
            except Exception as e:
                print(f"✗ Error analyzing {dataset_id}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Generate summary
        analysis_results['summary'] = self._generate_summary(analysis_results['collections_analyzed'])
        
        # Save results
        output_file = self.output_dir / "esg_analysis_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Analysis results saved to: {output_file}")
        
        # Generate report
        self._generate_report(analysis_results)
        
        return analysis_results
    
    def _analyze_collection(self, collection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single collection.
        
        Args:
            collection_result: Collection result from retrieval
            
        Returns:
            Analysis results dictionary
        """
        dataset_id = collection_result.get('dataset_id')
        matching_reason = collection_result.get('matching_reason', '')
        relevant_variables = collection_result.get('relevant_variables', [])
        
        # Get matching reasons from Excel if available
        if dataset_id in self.matching_reasons_map:
            # Use all matching reasons from Excel
            matching_reasons = self.matching_reasons_map[dataset_id]
            matching_reason = '; '.join(matching_reasons) if matching_reasons else matching_reason
            print(f"  Using matching reasons from Excel: {len(matching_reasons)} reasons")
        
        analysis = {
            'dataset_id': dataset_id,
            'dataset_title': collection_result.get('dataset_title', ''),
            'matching_reason': matching_reason,
            'matching_reasons': self.matching_reasons_map.get(dataset_id, []) if dataset_id in self.matching_reasons_map else [matching_reason],
            'relevant_variables': relevant_variables,
            'variables_analyzed': {},
            'esg_metrics': {},
            'risk_assessment': {}
        }
        
        # Find downloaded files
        data_files = self._find_data_files(dataset_id)
        
        if not data_files:
            analysis['status'] = 'no_files'
            analysis['message'] = 'No downloaded files found'
            return analysis
        
        # Analyze based on dataset type
        if dataset_id == 'nasa-nex-gddp-cmip6':
            # Handle multiple matching reasons
            if 'matching_reasons' in analysis and len(analysis['matching_reasons']) > 1:
                # Analyze for each matching reason
                all_analyses = []
                for mr in analysis['matching_reasons']:
                    mr_analysis = self._analyze_climate_projections(data_files, mr)
                    mr_analysis['matching_reason'] = mr
                    all_analyses.append(mr_analysis)
                
                # Merge analyses
                merged_analysis = {
                    'status': 'success',
                    'data_type': 'climate_projections',
                    'matching_reasons': analysis['matching_reasons'],
                    'analyses_by_reason': all_analyses,
                    'variables_analyzed': {},
                    'esg_metrics': {},
                    'trends': {}
                }
                
                # Merge variables and metrics
                for a in all_analyses:
                    merged_analysis['variables_analyzed'].update(a.get('variables_analyzed', {}))
                    merged_analysis['esg_metrics'].update(a.get('esg_metrics', {}))
                    if 'trends' in a:
                        merged_analysis['trends'].update(a['trends'])
                
                analysis.update(merged_analysis)
            else:
                analysis.update(self._analyze_climate_projections(data_files, matching_reason))
                
        elif dataset_id == 'modis-11A2-061':
            # Prioritize HDF files for MODIS
            hdf_files = [f for f in data_files if f.suffix.lower() == '.hdf']
            if hdf_files:
                analysis.update(self._analyze_thermal_data(hdf_files, matching_reason))
            else:
                analysis['status'] = 'no_hdf_files'
                analysis['message'] = 'No HDF files found for MODIS analysis'
        # DLR Geoservice collections
        elif dataset_id == 'TIMELINE_AVHRR_P1M_LSTD':
            analysis.update(self._analyze_timeline_lstd(data_files, matching_reason))
        elif dataset_id.startswith('GWP_'):
            analysis.update(self._analyze_waterpack(data_files, dataset_id, matching_reason))
        elif dataset_id.startswith('GSP_'):
            analysis.update(self._analyze_snowpack(data_files, dataset_id, matching_reason))
        elif dataset_id == 'SWIM_WE':
            analysis.update(self._analyze_waterpack(data_files, dataset_id, matching_reason))
        elif dataset_id == 'TDM_DEM_90':
            analysis.update(self._analyze_elevation_hazards(data_files, matching_reason))
        elif dataset_id.startswith('WSF_'):
            analysis.update(self._analyze_settlement(data_files, dataset_id, matching_reason))
        elif dataset_id in ['SUPERSITES', 'D4H']:
            analysis.update(self._analyze_geohazards(data_files, dataset_id, matching_reason))
        else:
            analysis['status'] = 'not_implemented'
            analysis['message'] = f'Analysis not implemented for {dataset_id}'
        
        return analysis
    
    def _find_data_files(self, dataset_id: str) -> List[Path]:
        """Find downloaded data files for a collection."""
        files = []
        
        # Check vectors directory (NetCDF files, HDF files)
        vectors_dir = self.data_dir / 'vectors' / dataset_id
        if vectors_dir.exists():
            files.extend(list(vectors_dir.glob('*.nc')))
            files.extend(list(vectors_dir.glob('*.hdf')))
        
        # Check rasters directory
        rasters_dir = self.data_dir / 'rasters' / dataset_id
        if rasters_dir.exists():
            files.extend(list(rasters_dir.glob('*.tif')))
            files.extend(list(rasters_dir.glob('*.nc')))
            files.extend(list(rasters_dir.glob('*.hdf')))
        
        # Check DLR Geoservice data directory (direct collection folders)
        dlr_dir = self.data_dir.parent / 'dlr_geoservice_data' / dataset_id
        if dlr_dir.exists():
            files.extend(list(dlr_dir.glob('*.tif')))
            files.extend(list(dlr_dir.glob('*.nc')))
            files.extend(list(dlr_dir.glob('*.hdf')))
            files.extend(list(dlr_dir.glob('*.geojson')))
        
        # Also check if data_dir itself contains DLR data
        dlr_collection_dir = self.data_dir / dataset_id
        if dlr_collection_dir.exists():
            files.extend(list(dlr_collection_dir.glob('*.tif')))
            files.extend(list(dlr_collection_dir.glob('*.nc')))
            files.extend(list(dlr_collection_dir.glob('*.hdf')))
            files.extend(list(dlr_collection_dir.glob('*.geojson')))
        
        return files
    
    def _parse_matching_reasons(self, matching_reason: str) -> Dict[str, Any]:
        """
        Parse matching reason to extract analysis requirements.
        
        Args:
            matching_reason: Matching reason text
            
        Returns:
            Dictionary with analysis requirements
        """
        reason_lower = matching_reason.lower()
        requirements = {
            'analyze_temperature': False,
            'analyze_precipitation': False,
            'analyze_water_stress': False,
            'analyze_cooling_energy': False,
            'trend_through_2100': False,
            'trend_through_2050': False,
            'focus_variables': []
        }
        
        # Check for temperature-related analysis
        if any(term in reason_lower for term in ['temperature', 'temp', 'cooling', 'energy', 'heat']):
            requirements['analyze_temperature'] = True
            requirements['focus_variables'].extend(['tas', 'tasmax', 'tasmin'])
        
        # Check for precipitation/water analysis
        if any(term in reason_lower for term in ['precipitation', 'water', 'stress', 'drought']):
            requirements['analyze_precipitation'] = True
            requirements['focus_variables'].extend(['pr'])
        
        # Check for water stress
        if 'water stress' in reason_lower or 'drought' in reason_lower:
            requirements['analyze_water_stress'] = True
        
        # Check for cooling energy
        if 'cooling' in reason_lower and 'energy' in reason_lower:
            requirements['analyze_cooling_energy'] = True
        
        # Check for time horizons
        if '2100' in matching_reason:
            requirements['trend_through_2100'] = True
        if '2050' in matching_reason:
            requirements['trend_through_2050'] = True
        
        return requirements
    
    def _analyze_climate_projections(
        self,
        data_files: List[Path],
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze climate projection data (NEX-GDDP-CMIP6).
        
        Args:
            data_files: List of NetCDF files
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not XARRAY_AVAILABLE:
            return {'status': 'error', 'message': 'xarray not available'}
        
        # Parse matching reason to understand requirements
        requirements = self._parse_matching_reasons(matching_reason)
        print(f"  Matching reason: {matching_reason}")
        print(f"  Analysis requirements: {requirements}")
        
        analysis = {
            'status': 'success',
            'data_type': 'climate_projections',
            'matching_reason': matching_reason,
            'requirements': requirements,
            'variables_analyzed': {},
            'esg_metrics': {},
            'trends': {},
            'risk_assessment': {}
        }
        
        # Group files by variable, scenario, model, and year
        file_groups = {}
        for file_path in data_files:
            filename = file_path.stem
            # Parse filename: e.g., "IITM-ESM.ssp585.2025_tas"
            parts = filename.split('.')
            if len(parts) >= 3:
                model = parts[0]
                scenario = parts[1] if 'ssp' in parts[1].lower() else None
                year = parts[2] if parts[2].isdigit() else None
                
                # Extract variable
                var_name = None
                for var in ['tas', 'tasmax', 'tasmin', 'pr', 'hurs', 'huss']:
                    if f'_{var}' in filename or filename.endswith(var):
                        var_name = var
                        break
                
                if var_name:
                    key = (var_name, scenario, model, year)
                    if key not in file_groups:
                        file_groups[key] = []
                    file_groups[key].append(file_path)
        
        print(f"  Found {len(file_groups)} file groups")
        
        # Group by variable for analysis
        variable_files = {}
        for (var_name, scenario, model, year), files in file_groups.items():
            if var_name not in variable_files:
                variable_files[var_name] = []
            variable_files[var_name].extend(files)
        
        print(f"  Variables to analyze: {list(variable_files.keys())}")
        
        # Analyze each variable
        for var_name, files in variable_files.items():
            # Skip if not in focus variables (if specified)
            if requirements['focus_variables'] and var_name not in requirements['focus_variables']:
                continue
            
            print(f"  Analyzing {var_name} ({len(files)} files)...")
            
            try:
                # Analyze current values
                var_analysis = self._analyze_netcdf_variable(files, var_name)
                analysis['variables_analyzed'][var_name] = var_analysis
                
                # Analyze trends if required
                if requirements['trend_through_2100'] or requirements['trend_through_2050']:
                    trend_analysis = self._analyze_trends(file_groups, var_name, requirements)
                    if trend_analysis:
                        if 'trends' not in analysis:
                            analysis['trends'] = {}
                        analysis['trends'][var_name] = trend_analysis
                        
            except Exception as e:
                print(f"    ✗ Error analyzing {var_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                analysis['variables_analyzed'][var_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate ESG metrics based on requirements
        if requirements['analyze_cooling_energy']:
            analysis['esg_metrics']['cooling_energy_risk'] = self._calculate_cooling_energy_risk(
                analysis['variables_analyzed'], analysis.get('trends', {})
            )
        
        if requirements['analyze_temperature']:
            analysis['esg_metrics']['temperature_extremes'] = self._calculate_temperature_extremes(
                analysis['variables_analyzed'], analysis.get('trends', {})
            )
        
        if requirements['analyze_precipitation'] or requirements['analyze_water_stress']:
            analysis['esg_metrics']['precipitation_risk'] = self._calculate_precipitation_risk(
                analysis['variables_analyzed'], analysis.get('trends', {})
            )
        
        if requirements['analyze_water_stress']:
            analysis['esg_metrics']['water_stress'] = self._calculate_water_stress(
                analysis['variables_analyzed'], analysis.get('trends', {})
            )
        
        return analysis
    
    def _analyze_netcdf_variable(
        self,
        files: List[Path],
        var_name: str
    ) -> Dict[str, Any]:
        """
        Analyze a NetCDF variable across multiple files.
        
        Args:
            files: List of NetCDF file paths
            var_name: Variable name
            
        Returns:
            Analysis results
        """
        # Open and concatenate datasets
        datasets = []
        for file_path in files[:5]:  # Limit to first 5 files
            try:
                ds = xr.open_dataset(str(file_path))
                if var_name in ds.data_vars:
                    datasets.append(ds[var_name])
                ds.close()
            except Exception as e:
                print(f"      Warning: Could not read {file_path.name}: {str(e)}")
                continue
        
        if not datasets:
            return {'status': 'error', 'message': 'No valid data found'}
        
        # Concatenate along time dimension if possible
        try:
            combined = xr.concat(datasets, dim='time') if len(datasets) > 1 else datasets[0]
        except:
            combined = datasets[0]
        
        # Extract San Francisco area (approximate)
        # Note: NetCDF files may use different coordinate systems
        try:
            # Try to subset to San Francisco area
            sf_data = combined.sel(
                lon=slice(SAN_FRANCISCO_BBOX[0], SAN_FRANCISCO_BBOX[2]),
                lat=slice(SAN_FRANCISCO_BBOX[1], SAN_FRANCISCO_BBOX[3]),
                method='nearest'
            )
        except:
            # If subsetting fails, use global data
            sf_data = combined
        
        # Calculate statistics
        stats = {
            'mean': float(sf_data.mean().values) if hasattr(sf_data.mean(), 'values') else None,
            'max': float(sf_data.max().values) if hasattr(sf_data.max(), 'values') else None,
            'min': float(sf_data.min().values) if hasattr(sf_data.min(), 'values') else None,
            'std': float(sf_data.std().values) if hasattr(sf_data.std(), 'values') else None,
            'units': str(sf_data.attrs.get('units', 'unknown')) if hasattr(sf_data, 'attrs') else 'unknown'
        }
        
        # Calculate percentiles
        try:
            stats['p95'] = float(np.nanpercentile(sf_data.values, 95))
            stats['p5'] = float(np.nanpercentile(sf_data.values, 5))
        except:
            pass
        
        return {
            'status': 'success',
            'files_analyzed': len(files),
            'data_shape': list(sf_data.shape) if hasattr(sf_data, 'shape') else None,
            'statistics': stats
        }
    
    def _analyze_trends(
        self,
        file_groups: Dict[Tuple, List[Path]],
        var_name: str,
        requirements: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze trends over time for a variable.
        
        Args:
            file_groups: Dictionary of (var, scenario, model, year) -> files
            var_name: Variable name
            requirements: Analysis requirements
            
        Returns:
            Trend analysis results
        """
        # Group files by year
        year_data = {}
        for (var, scenario, model, year), files in file_groups.items():
            if var != var_name or not year:
                continue
            
            year = int(year)
            if year not in year_data:
                year_data[year] = []
            year_data[year].extend(files)
        
        if len(year_data) < 2:
            return None  # Need at least 2 years for trend
        
        # Extract mean values by year
        yearly_means = {}
        for year, files in sorted(year_data.items()):
            try:
                # Read and calculate mean for this year
                datasets = []
                for file_path in files[:3]:  # Limit files per year
                    try:
                        ds = xr.open_dataset(str(file_path))
                        if var_name in ds.data_vars:
                            datasets.append(ds[var_name])
                        ds.close()
                    except:
                        continue
                
                if datasets:
                    combined = xr.concat(datasets, dim='time') if len(datasets) > 1 else datasets[0]
                    try:
                        sf_data = combined.sel(
                            lon=slice(SAN_FRANCISCO_BBOX[0], SAN_FRANCISCO_BBOX[2]),
                            lat=slice(SAN_FRANCISCO_BBOX[1], SAN_FRANCISCO_BBOX[3]),
                            method='nearest'
                        )
                    except:
                        sf_data = combined
                    
                    mean_val = float(sf_data.mean().values) if hasattr(sf_data.mean(), 'values') else None
                    if mean_val is not None:
                        yearly_means[year] = mean_val
            except Exception as e:
                print(f"      Warning: Could not analyze trend for year {year}: {str(e)}")
                continue
        
        if len(yearly_means) < 2:
            return None
        
        # Calculate trend
        years = sorted(yearly_means.keys())
        values = [yearly_means[y] for y in years]
        
        # Simple linear trend
        if len(years) >= 2:
            trend_slope = np.polyfit(years, values, 1)[0]
            trend_intercept = np.polyfit(years, values, 1)[1]
            
            # Project to 2050 and 2100 if needed
            projections = {}
            if requirements.get('trend_through_2050'):
                projections[2050] = trend_slope * 2050 + trend_intercept
            if requirements.get('trend_through_2100'):
                projections[2100] = trend_slope * 2100 + trend_intercept
            
            return {
                'years_analyzed': years,
                'values': values,
                'trend_slope': float(trend_slope),
                'trend_intercept': float(trend_intercept),
                'projections': projections,
                'current_mean': values[-1] if values else None,
                'baseline_mean': values[0] if values else None
            }
        
        return None
    
    def _analyze_thermal_data(
        self,
        data_files: List[Path],
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze MODIS thermal data (land surface temperature).
        
        Args:
            data_files: List of HDF files
            matching_reason: Matching reason
            
        Returns:
            Analysis results
        """
        analysis = {
            'status': 'success',
            'data_type': 'thermal',
            'variables_analyzed': {},
            'esg_metrics': {}
        }
        
        # MODIS HDF files contain LST_Day and LST_Night
        lst_day_data = []
        lst_night_data = []
        
        for file_path in data_files:
            # Skip non-HDF files
            if file_path.suffix.lower() != '.hdf':
                print(f"    Skipping {file_path.name} (not HDF file)")
                continue
            
            print(f"    Reading HDF file: {file_path.name}...")
            
            # Try pyhdf first (for HDF-EOS format)
            if PYHDF_AVAILABLE:
                try:
                    hdf = SD(str(file_path), SDC.READ)
                    datasets = hdf.datasets()
                    
                    print(f"      Available datasets: {list(datasets.keys())[:10]}...")
                    
                    # Look for LST datasets
                    for ds_name in datasets.keys():
                        if 'LST_Day' in ds_name or 'LST_Day_1km' in ds_name or 'LST_Day_CMG' in ds_name:
                            try:
                                lst_ds = hdf.select(ds_name)
                                lst_data = lst_ds.get()
                                
                                # Apply scale factor and offset if available
                                attrs = lst_ds.attributes()
                                
                                # Handle scale_factor (can be float or list)
                                # pyhdf may return attributes in different formats
                                try:
                                    scale_factor = attrs.get('scale_factor', 0.02)
                                    # Check if it's subscriptable (list/tuple/array) vs scalar
                                    try:
                                        scale = float(scale_factor[0])
                                    except (TypeError, IndexError):
                                        scale = float(scale_factor)
                                except Exception:
                                    scale = 0.02  # Default MODIS scale factor
                                
                                # Handle add_offset (can be float or list)
                                try:
                                    add_offset = attrs.get('add_offset', 0.0)
                                    try:
                                        offset = float(add_offset[0])
                                    except (TypeError, IndexError):
                                        offset = float(add_offset)
                                except Exception:
                                    offset = 0.0
                                
                                # Apply valid range mask if available
                                valid_range = attrs.get('valid_range', None)
                                if valid_range is not None:
                                    # Handle valid_range (can be list or tuple)
                                    if isinstance(valid_range, (list, tuple, np.ndarray)):
                                        vmin, vmax = float(valid_range[0]), float(valid_range[1])
                                    else:
                                        # If single value, use it as max
                                        vmax = float(valid_range)
                                        vmin = 0.0
                                    
                                    # MODIS uses fill values (typically 0) for invalid pixels
                                    # Valid LST range is usually > 0 and < 65535
                                    lst_data = np.where(
                                        (lst_data > vmin) & (lst_data < vmax) & (lst_data > 0),
                                        lst_data * scale + offset,
                                        np.nan
                                    )
                                else:
                                    # Apply scaling and mask fill values (0)
                                    lst_data = np.where(
                                        lst_data > 0,
                                        lst_data * scale + offset,
                                        np.nan
                                    )
                                
                                lst_day_data.append(lst_data)
                                lst_ds.endaccess()
                                print(f"      ✓ Extracted {ds_name}: shape {lst_data.shape}, scale={scale}, offset={offset}")
                            except Exception as e:
                                print(f"      Warning: Could not extract {ds_name}: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        
                        if 'LST_Night' in ds_name or 'LST_Night_1km' in ds_name or 'LST_Night_CMG' in ds_name:
                            try:
                                lst_ds = hdf.select(ds_name)
                                lst_data = lst_ds.get()
                                
                                attrs = lst_ds.attributes()
                                
                                # Handle scale_factor (can be float or list)
                                try:
                                    scale_factor = attrs.get('scale_factor', 0.02)
                                    try:
                                        scale = float(scale_factor[0])
                                    except (TypeError, IndexError):
                                        scale = float(scale_factor)
                                except Exception:
                                    scale = 0.02  # Default MODIS scale factor
                                
                                # Handle add_offset (can be float or list)
                                try:
                                    add_offset = attrs.get('add_offset', 0.0)
                                    try:
                                        offset = float(add_offset[0])
                                    except (TypeError, IndexError):
                                        offset = float(add_offset)
                                except Exception:
                                    offset = 0.0
                                
                                valid_range = attrs.get('valid_range', None)
                                if valid_range is not None:
                                    if isinstance(valid_range, (list, tuple, np.ndarray)):
                                        vmin, vmax = float(valid_range[0]), float(valid_range[1])
                                    else:
                                        vmax = float(valid_range)
                                        vmin = 0.0
                                    
                                    lst_data = np.where(
                                        (lst_data > vmin) & (lst_data < vmax) & (lst_data > 0),
                                        lst_data * scale + offset,
                                        np.nan
                                    )
                                else:
                                    lst_data = np.where(
                                        lst_data > 0,
                                        lst_data * scale + offset,
                                        np.nan
                                    )
                                
                                lst_night_data.append(lst_data)
                                lst_ds.endaccess()
                                print(f"      ✓ Extracted {ds_name}: shape {lst_data.shape}, scale={scale}, offset={offset}")
                            except Exception as e:
                                print(f"      Warning: Could not extract {ds_name}: {str(e)}")
                                import traceback
                                traceback.print_exc()
                    
                    hdf.end()
                    print(f"      ✓ Successfully read HDF file")
                    continue
                except Exception as e:
                    print(f"      ✗ pyhdf failed: {str(e)}")
            
            # Fallback to h5py (may not work for HDF-EOS)
            if H5PY_AVAILABLE and not lst_day_data and not lst_night_data:
                try:
                    with h5py.File(str(file_path), 'r') as f:
                        print(f"      H5PY: Found keys: {list(f.keys())[:10]}")
                        # MODIS HDF-EOS structure is complex and h5py may not work
                        # This is a fallback attempt
                except Exception as e:
                    print(f"      ✗ h5py also failed: {str(e)}")
            
            if not lst_day_data and not lst_night_data:
                print(f"      ⚠ No LST data extracted from {file_path.name}")
        
        # Analyze LST data
        print(f"  LST Day datasets extracted: {len(lst_day_data)}")
        print(f"  LST Night datasets extracted: {len(lst_night_data)}")
        
        if lst_day_data:
            try:
                lst_day_array = np.concatenate([np.array(d).flatten() for d in lst_day_data])
                lst_day_array = lst_day_array[~np.isnan(lst_day_array)]
                if len(lst_day_array) > 0:
                    analysis['variables_analyzed']['LST_Day'] = {
                        'status': 'success',
                        'files_analyzed': len(lst_day_data),
                        'data_points': len(lst_day_array),
                        'statistics': {
                            'mean': float(np.nanmean(lst_day_array)),
                            'max': float(np.nanmax(lst_day_array)),
                            'min': float(np.nanmin(lst_day_array)),
                            'std': float(np.nanstd(lst_day_array)),
                            'mean_celsius': float(np.nanmean(lst_day_array) - 273.15),
                            'max_celsius': float(np.nanmax(lst_day_array) - 273.15),
                            'min_celsius': float(np.nanmin(lst_day_array) - 273.15),
                            'units': 'Kelvin'
                        }
                    }
                    print(f"    ✓ LST_Day: mean={np.nanmean(lst_day_array):.2f}K ({np.nanmean(lst_day_array)-273.15:.2f}°C)")
                else:
                    print(f"    ⚠ LST_Day: No valid data points after filtering")
            except Exception as e:
                print(f"    ✗ Error processing LST_Day data: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if lst_night_data:
            try:
                lst_night_array = np.concatenate([np.array(d).flatten() for d in lst_night_data])
                lst_night_array = lst_night_array[~np.isnan(lst_night_array)]
                if len(lst_night_array) > 0:
                    analysis['variables_analyzed']['LST_Night'] = {
                        'status': 'success',
                        'files_analyzed': len(lst_night_data),
                        'data_points': len(lst_night_array),
                        'statistics': {
                            'mean': float(np.nanmean(lst_night_array)),
                            'max': float(np.nanmax(lst_night_array)),
                            'min': float(np.nanmin(lst_night_array)),
                            'std': float(np.nanstd(lst_night_array)),
                            'mean_celsius': float(np.nanmean(lst_night_array) - 273.15),
                            'max_celsius': float(np.nanmax(lst_night_array) - 273.15),
                            'min_celsius': float(np.nanmin(lst_night_array) - 273.15),
                            'units': 'Kelvin'
                        }
                    }
                    print(f"    ✓ LST_Night: mean={np.nanmean(lst_night_array):.2f}K ({np.nanmean(lst_night_array)-273.15:.2f}°C)")
                else:
                    print(f"    ⚠ LST_Night: No valid data points after filtering")
            except Exception as e:
                print(f"    ✗ Error processing LST_Night data: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Calculate heat island metrics
        if 'heat island' in matching_reason.lower() or 'thermal' in matching_reason.lower():
            day_stats = analysis['variables_analyzed'].get('LST_Day', {}).get('statistics', {})
            night_stats = analysis['variables_analyzed'].get('LST_Night', {}).get('statistics', {})
            
            if day_stats and night_stats:
                day_mean = day_stats.get('mean')
                night_mean = night_stats.get('mean')
                
                if day_mean and night_mean:
                    day_night_diff = float(day_mean - night_mean)
                    day_mean_c = day_stats.get('mean_celsius', day_mean - 273.15)
                    night_mean_c = night_stats.get('mean_celsius', night_mean - 273.15)
                    
                    analysis['esg_metrics']['heat_island_effect'] = {
                        'status': 'calculated',
                        'day_night_difference_kelvin': day_night_diff,
                        'day_night_difference_celsius': float(day_mean_c - night_mean_c),
                        'day_mean_kelvin': day_mean,
                        'night_mean_kelvin': night_mean,
                        'day_mean_celsius': day_mean_c,
                        'night_mean_celsius': night_mean_c,
                        'intensity': 'high' if day_night_diff > 5 else ('medium' if day_night_diff > 2 else 'low')
                    }
                    print(f"    ✓ Heat island effect: {day_night_diff:.2f}K difference")
        
        # Also calculate cooling energy risk from LST if available
        if 'cooling' in matching_reason.lower() or 'energy' in matching_reason.lower():
            lst_day_stats = analysis['variables_analyzed'].get('LST_Day', {}).get('statistics', {})
            if lst_day_stats:
                mean_lst_c = lst_day_stats.get('mean_celsius')
                if mean_lst_c:
                    if mean_lst_c > 30:
                        risk_level = 'high'
                    elif mean_lst_c > 25:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                    
                    analysis['esg_metrics']['cooling_energy_risk'] = {
                        'status': 'calculated',
                        'risk_level': risk_level,
                        'metrics': {
                            'mean_lst_celsius': mean_lst_c,
                            'max_lst_celsius': lst_day_stats.get('max_celsius')
                        }
                    }
        
        return analysis
    
    def _calculate_cooling_energy_risk(
        self,
        variables: Dict[str, Any],
        trends: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Calculate cooling energy demand risk from temperature data."""
        risk = {
            'status': 'calculated',
            'risk_level': 'unknown',
            'metrics': {},
            'future_projection': {}
        }
        
        trends = trends or {}
        
        # Check tasmax first, then tas
        temp_var = None
        if 'tasmax' in variables and variables['tasmax'].get('status') == 'success':
            temp_var = 'tasmax'
        elif 'tas' in variables and variables['tas'].get('status') == 'success':
            temp_var = 'tas'
        
        if temp_var:
            stats = variables[temp_var].get('statistics', {})
            mean_temp = stats.get('mean')
            max_temp = stats.get('max')
            units = stats.get('units', '')
            
            # Convert from Kelvin to Celsius if needed
            if 'kelvin' in units.lower() or 'k' == units.lower():
                mean_temp_c = mean_temp - 273.15 if mean_temp else None
                max_temp_c = max_temp - 273.15 if max_temp else None
            else:
                mean_temp_c = mean_temp
                max_temp_c = max_temp
            
            if mean_temp_c is not None:
                # Risk assessment based on temperature thresholds
                if mean_temp_c > 30:
                    risk['risk_level'] = 'high'
                elif mean_temp_c > 25:
                    risk['risk_level'] = 'medium'
                else:
                    risk['risk_level'] = 'low'
                
                risk['metrics']['mean_temperature_celsius'] = mean_temp_c
                risk['metrics']['max_temperature_celsius'] = max_temp_c
                risk['metrics']['mean_temperature_kelvin'] = mean_temp
                
                # Add trend projections if available
                if temp_var in trends:
                    trend = trends[temp_var]
                    if 'projections' in trend:
                        for year, projected_temp in trend['projections'].items():
                            # Convert to Celsius
                            if 'kelvin' in units.lower():
                                projected_temp_c = projected_temp - 273.15
                            else:
                                projected_temp_c = projected_temp
                            
                            risk['future_projection'][year] = {
                                'temperature_celsius': projected_temp_c,
                                'temperature_kelvin': projected_temp,
                                'risk_level': 'high' if projected_temp_c > 30 else ('medium' if projected_temp_c > 25 else 'low')
                            }
        
        return risk
    
    def _calculate_temperature_extremes(
        self,
        variables: Dict[str, Any],
        trends: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Calculate temperature extremes risk."""
        risk = {
            'status': 'calculated',
            'extremes': {},
            'trends': {}
        }
        
        trends = trends or {}
        
        for var_name in ['tasmax', 'tas', 'tasmin']:
            if var_name in variables and variables[var_name].get('status') == 'success':
                stats = variables[var_name].get('statistics', {})
                units = stats.get('units', '')
                
                # Convert to Celsius for reporting
                extremes = {}
                for key in ['max', 'min', 'p95', 'p5']:
                    val = stats.get(key)
                    if val is not None:
                        if 'kelvin' in units.lower() or 'k' == units.lower():
                            extremes[f'{key}_celsius'] = val - 273.15
                            extremes[f'{key}_kelvin'] = val
                        else:
                            extremes[f'{key}_celsius'] = val
                
                risk['extremes'][var_name] = extremes
                
                # Add trend if available
                if var_name in trends:
                    risk['trends'][var_name] = trends[var_name]
        
        return risk
    
    def _calculate_precipitation_risk(
        self,
        variables: Dict[str, Any],
        trends: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Calculate precipitation-related risks."""
        risk = {
            'status': 'calculated',
            'metrics': {},
            'trends': {}
        }
        
        trends = trends or {}
        
        if 'pr' in variables and variables['pr'].get('status') == 'success':
            stats = variables['pr'].get('statistics', {})
            units = stats.get('units', '')
            
            # Convert from kg m-2 s-1 to mm/day if needed
            mean_pr = stats.get('mean')
            if mean_pr is not None and 'kg m-2 s-1' in units:
                # Convert: 1 kg m-2 s-1 = 86400 mm/day
                mean_pr_mm_day = mean_pr * 86400
                risk['metrics']['mean_precipitation_mm_per_day'] = mean_pr_mm_day
                risk['metrics']['mean_precipitation_original'] = mean_pr
            else:
                risk['metrics']['mean_precipitation'] = mean_pr
            
            risk['metrics']['max_precipitation'] = stats.get('max')
            risk['metrics']['precipitation_variability'] = stats.get('std')
            
            # Add trend if available
            if 'pr' in trends:
                risk['trends']['pr'] = trends['pr']
        
        return risk
    
    def _calculate_water_stress(
        self,
        variables: Dict[str, Any],
        trends: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Calculate water stress risk from precipitation trends."""
        risk = {
            'status': 'calculated',
            'water_stress_level': 'unknown',
            'metrics': {}
        }
        
        trends = trends or {}
        
        if 'pr' in variables and variables['pr'].get('status') == 'success':
            stats = variables['pr'].get('statistics', {})
            mean_pr = stats.get('mean')
            
            # Assess water stress based on precipitation
            # This is simplified - real water stress needs more variables
            if mean_pr is not None:
                # Convert to mm/day for assessment
                units = stats.get('units', '')
                if 'kg m-2 s-1' in units:
                    mean_pr_mm_day = mean_pr * 86400
                else:
                    mean_pr_mm_day = mean_pr
                
                # Simple thresholds (mm/day)
                if mean_pr_mm_day < 0.5:
                    risk['water_stress_level'] = 'high'
                elif mean_pr_mm_day < 1.0:
                    risk['water_stress_level'] = 'medium'
                else:
                    risk['water_stress_level'] = 'low'
                
                risk['metrics']['mean_precipitation_mm_per_day'] = mean_pr_mm_day
                
                # Add trend projections
                if 'pr' in trends and 'projections' in trends['pr']:
                    risk['future_projection'] = {}
                    for year, projected_pr in trends['pr']['projections'].items():
                        if 'kg m-2 s-1' in units:
                            projected_pr_mm_day = projected_pr * 86400
                        else:
                            projected_pr_mm_day = projected_pr
                        
                        risk['future_projection'][year] = {
                            'precipitation_mm_per_day': projected_pr_mm_day,
                            'water_stress_level': 'high' if projected_pr_mm_day < 0.5 else ('medium' if projected_pr_mm_day < 1.0 else 'low')
                        }
        
        return risk
    
    def _analyze_timeline_lstd(
        self,
        data_files: List[Path],
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze TIMELINE AVHRR L3 Monthly LSTD data for temperature trends.
        
        Args:
            data_files: List of data files
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not XARRAY_AVAILABLE or not NUMPY_AVAILABLE:
            return {'status': 'error', 'message': 'xarray or numpy not available'}
        
        analysis = {
            'status': 'success',
            'data_type': 'timeline_lstd',
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {},
            'trends': {}
        }
        
        print(f"  Analyzing TIMELINE LSTD data ({len(data_files)} files)...")
        
        try:
            # Load and analyze NetCDF files
            lst_values = []
            dates = []
            
            for file_path in data_files:
                try:
                    ds = xr.open_dataset(file_path)
                    
                    # Find LSTD variable (may vary)
                    lst_var = None
                    for var in ds.data_vars:
                        if 'lst' in var.lower() or 'temp' in var.lower() or 'temperature' in var.lower():
                            lst_var = var
                            break
                    
                    if lst_var is None and len(ds.data_vars) > 0:
                        lst_var = list(ds.data_vars)[0]
                    
                    if lst_var:
                        data = ds[lst_var].values
                        lst_values.extend(data.flatten())
                        
                        # Extract dates if available
                        if 'time' in ds.coords:
                            dates.extend([ds.time.values] * data.size)
                    
                    ds.close()
                except Exception as e:
                    print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                    continue
            
            if lst_values:
                lst_array = np.array(lst_values)
                lst_array = lst_array[~np.isnan(lst_array)]
                
                if len(lst_array) > 0:
                    analysis['variables_analyzed']['LSTD'] = {
                        'status': 'success',
                        'files_analyzed': len(data_files),
                        'data_points': len(lst_array),
                        'statistics': {
                            'mean': float(np.nanmean(lst_array)),
                            'max': float(np.nanmax(lst_array)),
                            'min': float(np.nanmin(lst_array)),
                            'std': float(np.nanstd(lst_array))
                        }
                    }
                    
                    # Calculate cooling energy risk
                    mean_lst = np.nanmean(lst_array)
                    if mean_lst > 30:
                        risk_level = 'high'
                    elif mean_lst > 25:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                    
                    analysis['esg_metrics']['cooling_energy_risk'] = {
                        'status': 'calculated',
                        'risk_level': risk_level,
                        'mean_temperature_celsius': float(mean_lst),
                        'trend_period': '40+ years'
                    }
                    
                    print(f"    ✓ LSTD analysis complete: mean={mean_lst:.2f}°C, risk={risk_level}")
        
        except Exception as e:
            print(f"    ✗ Error analyzing TIMELINE LSTD: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_waterpack(
        self,
        data_files: List[Path],
        dataset_id: str,
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze Global WaterPack data for water availability and stress.
        
        Args:
            data_files: List of data files
            dataset_id: Collection ID
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not XARRAY_AVAILABLE or not NUMPY_AVAILABLE:
            return {'status': 'error', 'message': 'xarray or numpy not available'}
        
        analysis = {
            'status': 'success',
            'data_type': 'waterpack',
            'dataset_id': dataset_id,
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {},
            'trends': {}
        }
        
        print(f"  Analyzing WaterPack data ({len(data_files)} files)...")
        
        try:
            water_extent_values = []
            water_occurrence_values = []
            
            for file_path in data_files:
                try:
                    ds = xr.open_dataset(file_path)
                    
                    # Find water-related variables
                    for var in ds.data_vars:
                        var_lower = var.lower()
                        if 'water' in var_lower or 'extent' in var_lower:
                            data = ds[var].values
                            water_extent_values.extend(data.flatten())
                        elif 'occurrence' in var_lower:
                            data = ds[var].values
                            water_occurrence_values.extend(data.flatten())
                    
                    ds.close()
                except Exception as e:
                    print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                    continue
            
            # Analyze water extent
            if water_extent_values:
                extent_array = np.array(water_extent_values)
                extent_array = extent_array[~np.isnan(extent_array)]
                
                if len(extent_array) > 0:
                    analysis['variables_analyzed']['water_extent'] = {
                        'status': 'success',
                        'statistics': {
                            'mean': float(np.nanmean(extent_array)),
                            'max': float(np.nanmax(extent_array)),
                            'min': float(np.nanmin(extent_array)),
                            'std': float(np.nanstd(extent_array))
                        }
                    }
            
            # Analyze water occurrence
            if water_occurrence_values:
                occurrence_array = np.array(water_occurrence_values)
                occurrence_array = occurrence_array[~np.isnan(occurrence_array)]
                
                if len(occurrence_array) > 0:
                    analysis['variables_analyzed']['water_occurrence'] = {
                        'status': 'success',
                        'statistics': {
                            'mean': float(np.nanmean(occurrence_array)),
                            'max': float(np.nanmax(occurrence_array)),
                            'min': float(np.nanmin(occurrence_array))
                        }
                    }
            
            # Calculate water stress risk
            if 'water_extent' in analysis['variables_analyzed']:
                mean_extent = analysis['variables_analyzed']['water_extent']['statistics']['mean']
                
                # Low water extent indicates water stress
                if mean_extent < 5:
                    risk_level = 'high'
                elif mean_extent < 15:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                analysis['esg_metrics']['water_stress'] = {
                    'status': 'calculated',
                    'risk_level': risk_level,
                    'mean_water_extent_percent': float(mean_extent),
                    'assessment': 'Low water extent indicates potential water stress'
                }
                
                print(f"    ✓ WaterPack analysis: mean extent={mean_extent:.2f}%, risk={risk_level}")
        
        except Exception as e:
            print(f"    ✗ Error analyzing WaterPack: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_snowpack(
        self,
        data_files: List[Path],
        dataset_id: str,
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze Global SnowPack data for snow cover and water storage.
        
        Args:
            data_files: List of data files
            dataset_id: Collection ID
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not XARRAY_AVAILABLE or not NUMPY_AVAILABLE:
            return {'status': 'error', 'message': 'xarray or numpy not available'}
        
        analysis = {
            'status': 'success',
            'data_type': 'snowpack',
            'dataset_id': dataset_id,
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {}
        }
        
        print(f"  Analyzing SnowPack data ({len(data_files)} files)...")
        
        try:
            snow_cover_values = []
            snow_duration_values = []
            
            for file_path in data_files:
                try:
                    ds = xr.open_dataset(file_path)
                    
                    # Find snow-related variables
                    for var in ds.data_vars:
                        var_lower = var.lower()
                        if 'snow' in var_lower and 'cover' in var_lower:
                            data = ds[var].values
                            snow_cover_values.extend(data.flatten())
                        elif 'duration' in var_lower:
                            data = ds[var].values
                            snow_duration_values.extend(data.flatten())
                    
                    ds.close()
                except Exception as e:
                    print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                    continue
            
            # Analyze snow cover
            if snow_cover_values:
                cover_array = np.array(snow_cover_values)
                cover_array = cover_array[~np.isnan(cover_array)]
                
                if len(cover_array) > 0:
                    analysis['variables_analyzed']['snow_cover'] = {
                        'status': 'success',
                        'statistics': {
                            'mean': float(np.nanmean(cover_array)),
                            'max': float(np.nanmax(cover_array)),
                            'min': float(np.nanmin(cover_array))
                        }
                    }
            
            # Analyze snow duration
            if snow_duration_values:
                duration_array = np.array(snow_duration_values)
                duration_array = duration_array[~np.isnan(duration_array)]
                
                if len(duration_array) > 0:
                    analysis['variables_analyzed']['snow_duration'] = {
                        'status': 'success',
                        'statistics': {
                            'mean': float(np.nanmean(duration_array)),
                            'max': float(np.nanmax(duration_array)),
                            'min': float(np.nanmin(duration_array))
                        }
                    }
            
            # Calculate water storage risk (low snow = low water storage)
            if 'snow_cover' in analysis['variables_analyzed']:
                mean_cover = analysis['variables_analyzed']['snow_cover']['statistics']['mean']
                
                if mean_cover < 20:
                    risk_level = 'high'
                elif mean_cover < 40:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                analysis['esg_metrics']['water_storage_risk'] = {
                    'status': 'calculated',
                    'risk_level': risk_level,
                    'mean_snow_cover_percent': float(mean_cover),
                    'assessment': 'Low snow cover indicates reduced water storage capacity'
                }
                
                print(f"    ✓ SnowPack analysis: mean cover={mean_cover:.2f}%, risk={risk_level}")
        
        except Exception as e:
            print(f"    ✗ Error analyzing SnowPack: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_elevation_hazards(
        self,
        data_files: List[Path],
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze elevation data (TDM_DEM_90) for flood and terrain hazards.
        
        Args:
            data_files: List of data files
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            return {'status': 'error', 'message': 'rasterio or numpy not available'}
        
        analysis = {
            'status': 'success',
            'data_type': 'elevation_hazards',
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {}
        }
        
        print(f"  Analyzing elevation data ({len(data_files)} files)...")
        
        try:
            elevation_values = []
            
            for file_path in data_files:
                try:
                    with rasterio.open(file_path) as src:
                        data = src.read(1)
                        elevation_values.extend(data.flatten())
                except Exception as e:
                    print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                    continue
            
            if elevation_values:
                elev_array = np.array(elevation_values)
                elev_array = elev_array[~np.isnan(elev_array)]
                
                if len(elev_array) > 0:
                    analysis['variables_analyzed']['elevation'] = {
                        'status': 'success',
                        'statistics': {
                            'mean': float(np.nanmean(elev_array)),
                            'max': float(np.nanmax(elev_array)),
                            'min': float(np.nanmin(elev_array)),
                            'std': float(np.nanstd(elev_array))
                        }
                    }
                    
                    # Calculate flood risk (low elevation = higher flood risk)
                    mean_elev = np.nanmean(elev_array)
                    min_elev = np.nanmin(elev_array)
                    
                    # For San Francisco area, elevations typically > 0m
                    # Low elevation areas (< 10m) are at higher flood risk
                    if min_elev < 5:
                        flood_risk = 'high'
                    elif min_elev < 10:
                        flood_risk = 'medium'
                    else:
                        flood_risk = 'low'
                    
                    analysis['esg_metrics']['flood_risk'] = {
                        'status': 'calculated',
                        'risk_level': flood_risk,
                        'min_elevation_meters': float(min_elev),
                        'mean_elevation_meters': float(mean_elev),
                        'assessment': 'Low elevation areas are at higher flood risk'
                    }
                    
                    print(f"    ✓ Elevation analysis: mean={mean_elev:.2f}m, min={min_elev:.2f}m, flood_risk={flood_risk}")
        
        except Exception as e:
            print(f"    ✗ Error analyzing elevation: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_settlement(
        self,
        data_files: List[Path],
        dataset_id: str,
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze World Settlement Footprint data for infrastructure context.
        
        Args:
            data_files: List of data files
            dataset_id: Collection ID
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        if not RASTERIO_AVAILABLE or not NUMPY_AVAILABLE:
            return {'status': 'error', 'message': 'rasterio or numpy not available'}
        
        analysis = {
            'status': 'success',
            'data_type': 'settlement',
            'dataset_id': dataset_id,
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {}
        }
        
        print(f"  Analyzing settlement data ({len(data_files)} files)...")
        
        try:
            settlement_values = []
            
            for file_path in data_files:
                try:
                    with rasterio.open(file_path) as src:
                        data = src.read(1)
                        settlement_values.extend(data.flatten())
                except Exception as e:
                    print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                    continue
            
            if settlement_values:
                sett_array = np.array(settlement_values)
                sett_array = sett_array[~np.isnan(sett_array)]
                
                if len(sett_array) > 0:
                    # Settlement is typically binary (0=no settlement, 1=settlement)
                    settlement_percent = np.nanmean(sett_array) * 100
                    
                    analysis['variables_analyzed']['settlement'] = {
                        'status': 'success',
                        'statistics': {
                            'settlement_percent': float(settlement_percent),
                            'total_pixels': len(sett_array)
                        }
                    }
                    
                    analysis['esg_metrics']['infrastructure_context'] = {
                        'status': 'calculated',
                        'settlement_percent': float(settlement_percent),
                        'assessment': 'Settlement extent indicates infrastructure density'
                    }
                    
                    print(f"    ✓ Settlement analysis: {settlement_percent:.2f}% settlement")
        
        except Exception as e:
            print(f"    ✗ Error analyzing settlement: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_geohazards(
        self,
        data_files: List[Path],
        dataset_id: str,
        matching_reason: str
    ) -> Dict[str, Any]:
        """
        Analyze geohazard data (SUPERSITES, D4H) for natural hazard risks.
        
        Args:
            data_files: List of data files
            dataset_id: Collection ID
            matching_reason: Matching reason for ESG context
            
        Returns:
            Analysis results
        """
        analysis = {
            'status': 'success',
            'data_type': 'geohazards',
            'dataset_id': dataset_id,
            'matching_reason': matching_reason,
            'variables_analyzed': {},
            'esg_metrics': {}
        }
        
        print(f"  Analyzing geohazard data ({len(data_files)} files)...")
        
        try:
            # For D4H (flood masks), analyze flood extent
            if dataset_id == 'D4H':
                if RASTERIO_AVAILABLE and NUMPY_AVAILABLE:
                    flood_values = []
                    for file_path in data_files:
                        try:
                            with rasterio.open(file_path) as src:
                                data = src.read(1)
                                flood_values.extend(data.flatten())
                        except Exception as e:
                            print(f"    ⚠ Error reading {file_path.name}: {str(e)}")
                            continue
                    
                    if flood_values:
                        flood_array = np.array(flood_values)
                        flood_array = flood_array[~np.isnan(flood_array)]
                        
                        if len(flood_array) > 0:
                            flood_percent = np.nanmean(flood_array) * 100
                            
                            analysis['variables_analyzed']['flood_extent'] = {
                                'status': 'success',
                                'flood_percent': float(flood_percent)
                            }
                            
                            if flood_percent > 10:
                                risk_level = 'high'
                            elif flood_percent > 5:
                                risk_level = 'medium'
                            else:
                                risk_level = 'low'
                            
                            analysis['esg_metrics']['flood_hazard_risk'] = {
                                'status': 'calculated',
                                'risk_level': risk_level,
                                'flood_percent': float(flood_percent)
                            }
                            
                            print(f"    ✓ Flood hazard analysis: {flood_percent:.2f}% flood extent, risk={risk_level}")
            
            # For SUPERSITES (ground deformation), analyze deformation
            elif dataset_id == 'SUPERSITES':
                analysis['esg_metrics']['geohazard_risk'] = {
                    'status': 'calculated',
                    'risk_level': 'medium',  # Default for geohazard areas
                    'assessment': 'Geohazard supersite indicates active ground deformation monitoring'
                }
                print(f"    ✓ Geohazard analysis: Active monitoring area")
        
        except Exception as e:
            print(f"    ✗ Error analyzing geohazards: {str(e)}")
            import traceback
            traceback.print_exc()
            analysis['status'] = 'error'
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_composite_risk_metrics(self, collections_analyzed: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate composite ESG risk metrics from all analyses.
        
        Args:
            collections_analyzed: List of collection analysis results
            
        Returns:
            Composite risk metrics dictionary
        """
        composite_risks = {
            'temperature_risk': {'level': 'unknown', 'score': 0, 'sources': []},
            'water_risk': {'level': 'unknown', 'score': 0, 'sources': []},
            'hazard_risk': {'level': 'unknown', 'score': 0, 'sources': []},
            'overall_risk': {'level': 'unknown', 'score': 0}
        }
        
        risk_scores = {'low': 1, 'medium': 2, 'high': 3, 'unknown': 0}
        
        # Aggregate temperature risks
        temp_risks = []
        for collection in collections_analyzed:
            if collection.get('status') == 'success':
                esg_metrics = collection.get('esg_metrics', {})
                
                # Cooling energy risk
                if 'cooling_energy_risk' in esg_metrics:
                    risk_data = esg_metrics['cooling_energy_risk']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    temp_risks.append(risk_level)
                    composite_risks['temperature_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
        
        if temp_risks:
            avg_temp_score = sum(risk_scores.get(r, 0) for r in temp_risks) / len(temp_risks)
            if avg_temp_score >= 2.5:
                composite_risks['temperature_risk']['level'] = 'high'
            elif avg_temp_score >= 1.5:
                composite_risks['temperature_risk']['level'] = 'medium'
            else:
                composite_risks['temperature_risk']['level'] = 'low'
            composite_risks['temperature_risk']['score'] = avg_temp_score
        
        # Aggregate water risks
        water_risks = []
        for collection in collections_analyzed:
            if collection.get('status') == 'success':
                esg_metrics = collection.get('esg_metrics', {})
                
                # Water stress
                if 'water_stress' in esg_metrics:
                    risk_data = esg_metrics['water_stress']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    water_risks.append(risk_level)
                    composite_risks['water_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
                
                # Water storage risk
                if 'water_storage_risk' in esg_metrics:
                    risk_data = esg_metrics['water_storage_risk']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    water_risks.append(risk_level)
                    composite_risks['water_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
        
        if water_risks:
            avg_water_score = sum(risk_scores.get(r, 0) for r in water_risks) / len(water_risks)
            if avg_water_score >= 2.5:
                composite_risks['water_risk']['level'] = 'high'
            elif avg_water_score >= 1.5:
                composite_risks['water_risk']['level'] = 'medium'
            else:
                composite_risks['water_risk']['level'] = 'low'
            composite_risks['water_risk']['score'] = avg_water_score
        
        # Aggregate hazard risks
        hazard_risks = []
        for collection in collections_analyzed:
            if collection.get('status') == 'success':
                esg_metrics = collection.get('esg_metrics', {})
                
                # Flood risk
                if 'flood_risk' in esg_metrics:
                    risk_data = esg_metrics['flood_risk']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    hazard_risks.append(risk_level)
                    composite_risks['hazard_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
                
                # Flood hazard risk
                if 'flood_hazard_risk' in esg_metrics:
                    risk_data = esg_metrics['flood_hazard_risk']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    hazard_risks.append(risk_level)
                    composite_risks['hazard_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
                
                # Geohazard risk
                if 'geohazard_risk' in esg_metrics:
                    risk_data = esg_metrics['geohazard_risk']
                    risk_level = risk_data.get('risk_level', 'unknown')
                    hazard_risks.append(risk_level)
                    composite_risks['hazard_risk']['sources'].append({
                        'dataset': collection.get('dataset_id'),
                        'risk_level': risk_level
                    })
        
        if hazard_risks:
            avg_hazard_score = sum(risk_scores.get(r, 0) for r in hazard_risks) / len(hazard_risks)
            if avg_hazard_score >= 2.5:
                composite_risks['hazard_risk']['level'] = 'high'
            elif avg_hazard_score >= 1.5:
                composite_risks['hazard_risk']['level'] = 'medium'
            else:
                composite_risks['hazard_risk']['level'] = 'low'
            composite_risks['hazard_risk']['score'] = avg_hazard_score
        
        # Calculate overall risk (weighted average)
        risk_scores_list = [
            composite_risks['temperature_risk']['score'],
            composite_risks['water_risk']['score'],
            composite_risks['hazard_risk']['score']
        ]
        valid_scores = [s for s in risk_scores_list if s > 0]
        
        if valid_scores:
            overall_score = sum(valid_scores) / len(valid_scores)
            if overall_score >= 2.5:
                composite_risks['overall_risk']['level'] = 'high'
            elif overall_score >= 1.5:
                composite_risks['overall_risk']['level'] = 'medium'
            else:
                composite_risks['overall_risk']['level'] = 'low'
            composite_risks['overall_risk']['score'] = overall_score
        
        return composite_risks
    
    def _generate_summary(self, collections_analyzed: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of all analyses."""
        summary = {
            'total_collections': len(collections_analyzed),
            'successful_analyses': sum(1 for c in collections_analyzed if c.get('status') == 'success'),
            'key_findings': [],
            'risk_summary': {}
        }
        
        # Extract key findings
        for collection in collections_analyzed:
            if collection.get('status') == 'success':
                dataset_id = collection.get('dataset_id')
                esg_metrics = collection.get('esg_metrics', {})
                
                if esg_metrics:
                    summary['key_findings'].append({
                        'dataset': dataset_id,
                        'metrics': list(esg_metrics.keys())
                    })
        
        # Calculate composite risk metrics
        summary['risk_summary'] = self._calculate_composite_risk_metrics(collections_analyzed)
        
        return summary
    
    def _generate_report(self, analysis_results: Dict[str, Any]):
        """Generate a human-readable report."""
        report_file = self.output_dir / "esg_analysis_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ESG Data Analysis Report\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Analysis Date: {analysis_results['analysis_date']}\n")
            f.write(f"Location: San Francisco Area\n")
            f.write(f"Bounding Box: {analysis_results['bbox']}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("Summary\n")
            f.write("=" * 70 + "\n")
            summary = analysis_results['summary']
            f.write(f"Collections Analyzed: {summary['total_collections']}\n")
            f.write(f"Successful Analyses: {summary['successful_analyses']}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("Detailed Analysis\n")
            f.write("=" * 70 + "\n\n")
            
            for collection in analysis_results['collections_analyzed']:
                f.write(f"\nCollection: {collection.get('dataset_id')}\n")
                f.write(f"Title: {collection.get('dataset_title', 'N/A')}\n")
                f.write(f"ESG Relevance: {collection.get('matching_reason', 'N/A')}\n")
                f.write("-" * 70 + "\n")
                
                variables = collection.get('variables_analyzed', {})
                if variables:
                    f.write("Variables Analyzed:\n")
                    for var_name, var_data in variables.items():
                        if var_data.get('status') == 'success':
                            stats = var_data.get('statistics', {})
                            f.write(f"  • {var_name}:\n")
                            f.write(f"    Mean: {stats.get('mean', 'N/A')} {stats.get('units', '')}\n")
                            f.write(f"    Max: {stats.get('max', 'N/A')}\n")
                            f.write(f"    Min: {stats.get('min', 'N/A')}\n")
                
                esg_metrics = collection.get('esg_metrics', {})
                if esg_metrics:
                    f.write("\nESG Metrics:\n")
                    for metric_name, metric_data in esg_metrics.items():
                        f.write(f"  • {metric_name}: {json.dumps(metric_data, indent=4)}\n")
                
                f.write("\n")
        
        print(f"✓ Report saved to: {report_file}")


def main():
    """Main function."""
    script_dir = os.path.dirname(__file__)
    project_root = os.path.join(script_dir, '../..')
    data_dir = os.path.join(script_dir, "esg_data_retrieval")
    results_json = os.path.join(data_dir, "esg_retrieval_results.json")
    excel_file = os.path.join(project_root, 'data', 'TablesMatched', 'Joey - ESG Mapping.xlsx')
    
    if not os.path.exists(results_json):
        print(f"✗ Retrieval results not found: {results_json}")
        print("  Please run esg_data_retrieval.py first")
        return
    
    # Try to load Excel file for matching reasons
    excel_path = excel_file if os.path.exists(excel_file) else None
    if excel_path:
        print(f"  Loading matching reasons from: {excel_path}")
    else:
        print(f"  Excel file not found, using matching reasons from retrieval results")
    
    analyzer = ESGDataAnalyzer(data_dir, results_json, excel_path)
    results = analyzer.analyze_all_collections()
    
    print("\n" + "=" * 70)
    print("Analysis Complete!")
    print("=" * 70)
    print(f"\nResults saved to: {analyzer.output_dir}")


if __name__ == "__main__":
    main()

