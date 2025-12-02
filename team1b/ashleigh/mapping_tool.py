"""
Enhanced ESG Data Mapping Tool - MCP Framework
Maps STAC catalog datasets to SASB sustainability metrics with intelligent analysis.
Outputs Excel-ready CSV format.
"""

import json
import csv
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from datetime import datetime


class DatasetAnalyzer:
    """Analyzes STAC datasets for relevance to ESG metrics."""
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
        # Convert to lowercase and split
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'for', 'to', 'of', 'in', 'on', 'at', 'by'}
        return [w for w in words if w not in stopwords and len(w) > 2]
    
    @staticmethod
    def analyze_temporal_capability(dataset: Dict[str, Any]) -> bool:
        """Check if dataset has good temporal coverage for trend analysis."""
        extent = dataset.get('extent', {})
        temporal = extent.get('temporal', {})
        intervals = temporal.get('interval', [])
        
        if not intervals or not intervals[0]:
            return False
        
        interval = intervals[0]
        if len(interval) >= 2 and interval[0] and interval[1]:
            try:
                # Check if time range is substantial (> 1 year)
                start_str = interval[0]
                end_str = interval[1]
                # Simple year check
                if 'Z' in start_str and 'Z' in end_str:
                    start_year = int(start_str.split('-')[0])
                    end_year = int(end_str.split('-')[0])
                    return (end_year - start_year) >= 1
            except:
                pass
        
        return False
    
    @staticmethod
    def analyze_spatial_resolution(dataset: Dict[str, Any]) -> Optional[str]:
        """Determine spatial resolution if mentioned."""
        title = dataset.get('title', '').lower()
        desc = dataset.get('description', '').lower()
        
        # Look for resolution indicators
        if '20' in title or '20cm' in desc:
            return '20cm'
        elif '10m' in title or '10m' in desc:
            return '10m'
        elif '30m' in title or '30m' in desc:
            return '30m'
        
        return None


class ESGDataMapper:
    """Maps geospatial datasets to SASB ESG metrics with intelligent categorization."""
    
    RELEVANCE_CATEGORIES = [
        "Direct Measurement",
        "Risk Assessment",
        "Risk Insights",
        "Trend Analysis",
        "Benchmarking",
        "Regulatory Support"
    ]
    
    def __init__(self):
        self.sasb_metrics = []
        self.stac_collections = []
        self.mappings = {}
        self.analyzer = DatasetAnalyzer()
        
    def load_sasb_metrics(self, csv_path: str) -> List[Dict[str, str]]:
        """Load SASB metrics from CSV file with improved parsing."""
        metrics = []
        
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            # Skip first line (Topics header)
            first_line = f.readline()
            
            # Now read with DictReader
            reader = csv.DictReader(f)
            
            current_sector = "Software & IT Services"  # Default from your file
            current_topic = ""
            
            for row in reader:
                # Get sector (use previous if empty)
                sector = row.get('Sector', '').strip()
                if sector and 'Metric' not in sector:  # Avoid header-like rows
                    current_sector = sector
                else:
                    sector = current_sector
                
                # Get topic (use previous if empty)
                topic = row.get('Topic', '').strip()
                if topic:
                    current_topic = topic
                else:
                    topic = current_topic
                
                # Get metric
                metric_text = row.get('Accounting Metric', '').strip()
                
                # Skip if no meaningful data
                if not metric_text or not topic:
                    continue
                    
                # Skip activity metrics section
                if 'Activity Metric' in metric_text or 'Activity Metric' in topic:
                    continue
                    
                # Clean up multi-line text (replace newlines with spaces)
                metric_clean = ' '.join(metric_text.replace('\n', ' ').split())
                category = row.get('Category', '').strip()
                unit = ' '.join(row.get('Unit of Measure', '').replace('\n', ' ').split())
                code = row.get('Code', '').strip().replace('\n', '').replace('\r', '')
                
                # Must have at minimum a code and metric
                if not code or not metric_clean:
                    continue
                
                metric = {
                    'Sector': sector,
                    'Topic': topic,
                    'Metric': metric_clean,
                    'Category': category,
                    'Unit of Measure': unit,
                    'Code': code
                }
                
                metrics.append(metric)
        
        self.sasb_metrics = metrics
        print(f"Loaded {len(metrics)} SASB metrics")
        return metrics
    
    def load_stac_catalog(self, json_path: str) -> List[Dict[str, Any]]:
        """Load STAC catalog from JSON file."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        collections = data.get('collections', [])
        self.stac_collections = collections
        print(f"Loaded {len(collections)} STAC collections")
        return collections
    
    def determine_relevance(self, dataset: Dict[str, Any], metric: Dict[str, str]) -> Tuple[str, str]:
        """
        Determine the most appropriate relevance category for a dataset-metric pair.
        Returns: (category, reasoning)
        """
        dataset_id = dataset.get('id', '').lower()
        dataset_title = dataset.get('title', '').lower()
        dataset_desc = dataset.get('description', '').lower()
        
        metric_name = metric['Metric'].lower()
        metric_topic = metric['Topic'].lower()
        unit = metric['Unit of Measure'].lower()
        
        # Combine dataset text for keyword matching
        dataset_text = f"{dataset_id} {dataset_title} {dataset_desc}"
        
        # Extract keywords
        dataset_keywords = self.analyzer.extract_keywords(dataset_text)
        metric_keywords = self.analyzer.extract_keywords(f"{metric_name} {metric_topic}")
        
        # DOP / Orthophoto Analysis
        if 'dop' in dataset_id or 'orthophoto' in dataset_title or 'orthophoto' in dataset_desc:
            resolution = self.analyzer.analyze_spatial_resolution(dataset)
            has_temporal = self.analyzer.analyze_temporal_capability(dataset)
            
            # High-resolution aerial imagery - excellent for visual analysis
            if 'infrastructure' in metric_topic or 'hardware' in metric_topic or 'data center' in metric_name:
                if has_temporal:
                    return ("Trend Analysis", 
                           f"High-resolution orthophoto imagery ({resolution or 'high-res'}) with multi-year coverage enables monitoring infrastructure changes and environmental impacts over time")
                else:
                    return ("Risk Insights",
                           f"High-resolution orthophoto imagery ({resolution or 'high-res'}) provides detailed visual context for infrastructure locations, land use, and environmental surroundings")
            
            elif 'water' in metric_name or 'water' in metric_topic:
                if has_temporal:
                    return ("Trend Analysis",
                           "Multi-temporal aerial imagery can track changes in water bodies, watershed conditions, and land use impacts on water resources")
                else:
                    return ("Risk Insights",
                           "Aerial imagery identifies nearby water bodies, watershed boundaries, and potential water source locations")
            
            elif 'environmental' in metric_name:
                if has_temporal:
                    return ("Trend Analysis",
                           "Time-series aerial imagery tracks environmental changes, land cover transitions, and ecosystem impacts")
                else:
                    return ("Risk Insights",
                           "Detailed aerial imagery provides land cover classification, vegetation assessment, and environmental context")
            
            elif 'energy' in metric_name:
                if has_temporal:
                    return ("Trend Analysis",
                           "Multi-year imagery can track solar panel installations, renewable energy infrastructure development")
                else:
                    return ("Risk Insights",
                           "Visual identification of energy infrastructure, solar potential assessment, and site context")
            
            else:
                # General catchall for other metrics
                if has_temporal:
                    return ("Trend Analysis",
                           "Multi-temporal high-resolution imagery enables monitoring site conditions and changes over time")
                else:
                    return ("Risk Insights",
                           "High-resolution visual context for facility locations and operational environment")
        
        # Energy metrics
        if any(kw in metric_name for kw in ['energy', 'electricity', 'renewable', 'grid']):
            if 'satellite' in dataset_text or 'sensor' in dataset_text:
                return ("Risk Insights",
                       "Satellite data can provide context on renewable energy potential and infrastructure")
            return ("Risk Insights",
                   "Geospatial context for energy-related assessments")
        
        # Water metrics
        if any(kw in metric_name for kw in ['water', 'aqua', 'hydro']):
            if 'stress' in dataset_text or 'risk' in dataset_text:
                return ("Risk Assessment",
                       "Dataset helps identify water stress zones and water-related risks")
            return ("Risk Insights",
                   "Contextual information about water resources and watershed conditions")
        
        # Privacy & Security metrics
        if 'privacy' in metric_topic or 'security' in metric_topic or 'data security' in metric_topic:
            return ("Risk Insights",
                   "Geographic context for data center locations and infrastructure security considerations")
        
        # Default: Risk Insights (most geospatial data provides context)
        return ("Risk Insights",
               "Geospatial data provides general environmental and operational context")
    
    def map_datasets_to_metrics(self) -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
        """
        Map all STAC datasets to SASB metrics.
        Returns: Dictionary mapping metric codes to categories to (dataset_info, reasoning) tuples
        """
        mappings = {}
        
        for metric in self.sasb_metrics:
            metric_code = metric['Code']
            if not metric_code:
                continue
                
            mappings[metric_code] = {cat: [] for cat in self.RELEVANCE_CATEGORIES}
            
            for dataset in self.stac_collections:
                dataset_id = dataset.get('id', 'unknown')
                dataset_title = dataset.get('title', dataset_id)
                
                # Determine relevance
                category, reasoning = self.determine_relevance(dataset, metric)
                
                # Format: [dataset-id], [Dataset Title]
                entry = f"{dataset_id}, {dataset_title}"
                
                # Store with reasoning for debugging
                mappings[metric_code][category].append((entry, reasoning))
        
        self.mappings = mappings
        return mappings
    
    def export_to_csv(self, output_path: str, include_reasoning: bool = False):
        """
        Export mappings to CSV file in Excel-ready format.
        
        Args:
            output_path: Path to output CSV file
            include_reasoning: If True, add reasoning as comments (not in final format)
        """
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            header = [
                'Sector',
                'Topic',
                'Metric',
                'Category',
                'Unit of Measure',
                'Code',
                'Direct Measurement',
                'Risk Assessment',
                'Risk Insights',
                'Trend Analysis',
                'Benchmarking',
                'Regulatory Support'
            ]
            writer.writerow(header)
            
            # Write data rows
            for metric in self.sasb_metrics:
                metric_code = metric['Code']
                
                # Get mappings for this metric
                metric_mappings = self.mappings.get(metric_code, {cat: [] for cat in self.RELEVANCE_CATEGORIES})
                
                # Format dataset lists with numbering
                formatted_mappings = {}
                for category in self.RELEVANCE_CATEGORIES:
                    datasets_with_reasoning = metric_mappings.get(category, [])
                    
                    if datasets_with_reasoning:
                        # Extract just the dataset info (not reasoning)
                        datasets = [ds[0] if isinstance(ds, tuple) else ds for ds in datasets_with_reasoning]
                        # Number the datasets starting from 1
                        numbered = [f"{i+1}. {ds}" for i, ds in enumerate(datasets)]
                        formatted_mappings[category] = '\n'.join(numbered)
                    else:
                        formatted_mappings[category] = ''
                
                # Write row
                row = [
                    metric['Sector'],
                    metric['Topic'],
                    metric['Metric'],
                    metric['Category'],
                    metric['Unit of Measure'],
                    metric['Code'],
                    formatted_mappings.get('Direct Measurement', ''),
                    formatted_mappings.get('Risk Assessment', ''),
                    formatted_mappings.get('Risk Insights', ''),
                    formatted_mappings.get('Trend Analysis', ''),
                    formatted_mappings.get('Benchmarking', ''),
                    formatted_mappings.get('Regulatory Support', '')
                ]
                writer.writerow(row)
        
        print(f"Exported to: {output_path}")
        return output_path


def esg_mapping_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    MCP Tool: Map STAC catalog data to SASB ESG metrics and export to CSV.
    
    Args:
        sasb_csv_path: Path to SASB metrics CSV file
        stac_json_path: Path to STAC catalog JSON file  
        output_csv_path: Path for output CSV file (default: esg_mapping_output.csv)
    
    Returns:
        Success message with output file path and summary statistics
    """
    try:
        # Get arguments
        sasb_csv = args.get('sasb_csv_path')
        stac_json = args.get('stac_json_path')
        output_csv = args.get('output_csv_path', 'esg_mapping_output.csv')
        
        if not sasb_csv or not stac_json:
            return "Error: Both 'sasb_csv_path' and 'stac_json_path' are required."
        
        # Validate file paths
        if not Path(sasb_csv).exists():
            return f"Error: SASB CSV file not found: {sasb_csv}"
        if not Path(stac_json).exists():
            return f"Error: STAC JSON file not found: {stac_json}"
        
        print(f"\n{'='*70}")
        print("ESG DATA MAPPING TOOL")
        print(f"{'='*70}\n")
        
        # Create mapper and process
        mapper = ESGDataMapper()
        
        # Load data
        print("Loading data...")
        metrics = mapper.load_sasb_metrics(sasb_csv)
        collections = mapper.load_stac_catalog(stac_json)
        print()
        
        # Perform mapping
        print("Analyzing dataset relevance to metrics...")
        mappings = mapper.map_datasets_to_metrics()
        print()
        
        # Export to CSV
        print("Generating CSV output...")
        output_path = mapper.export_to_csv(output_csv)
        print()
        
        # Generate statistics
        total_mappings = 0
        category_counts = {cat: 0 for cat in mapper.RELEVANCE_CATEGORIES}
        
        for metric_code, categories in mappings.items():
            for category, datasets in categories.items():
                count = len(datasets)
                total_mappings += count
                category_counts[category] += count
        
        # Generate summary report
        result = f"""{'='*70}
ESG DATA MAPPING COMPLETE
{'='*70}

INPUT FILES:
  • SASB Metrics:  {sasb_csv}
                  ({len(metrics)} sustainability metrics)
  
  • STAC Catalog: {stac_json}
                  ({len(collections)} geospatial collections)

OUTPUT FILE:
  • {output_path}
    (Excel-ready CSV format)

MAPPING SUMMARY:
  • Total Mappings: {total_mappings}
  • Metrics Analyzed: {len(metrics)}
  • Datasets Analyzed: {len(collections)}

BREAKDOWN BY RELEVANCE CATEGORY:
"""
        
        for category, count in category_counts.items():
            if count > 0:
                result += f"  • {category}: {count}\n"
        
        result += f"""
{'='*70}
NEXT STEPS:
1. Open {output_path} in Excel
2. Review dataset mappings by relevance category
3. Validate mappings against your specific use cases
4. Add additional STAC catalogs for more comprehensive coverage
{'='*70}
"""
        
        # Store output path in context for reference
        context['last_esg_output'] = output_path
        context['last_esg_metrics_count'] = len(metrics)
        context['last_esg_datasets_count'] = len(collections)
        
        return result
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"Error processing ESG mapping:\n{str(e)}\n\nDetails:\n{error_detail}"


# For standalone testing
if __name__ == "__main__":
    print("ESG Data Mapping Tool - Standalone Test Mode")
    print("=" * 70)
    print()
    
    # Test the mapper directly
    mapper = ESGDataMapper()
    
    sasb_file = "SASB_RIsk_-_Sheet1.csv"
    stac_file = "stac-tags-dop_stac_lgln_niedersachsen_de.json"
    
    if Path(sasb_file).exists() and Path(stac_file).exists():
        print("Files found! Running mapping...\n")
        mapper.load_sasb_metrics(sasb_file)
        mapper.load_stac_catalog(stac_file)
        mapper.map_datasets_to_metrics()
        mapper.export_to_csv("test_output.csv")
        print("\n✓ Test mapping generated: test_output.csv")
        print("\nYou can now open test_output.csv in Excel!")
    else:
        print("Test files not found.")
        print(f"  Looking for: {sasb_file}")
        print(f"  Looking for: {stac_file}")
        print("\nProvide these files to test the tool.")