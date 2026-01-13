"""
ESG Data Mapping Tool for MCP Framework
Automatically matches SASB metrics with geospatial datasets using expert analysis

Installation:
1. Place this file in your personal directory (e.g., team1a/yourname/esg_mapping_tool.py)
2. Import and register tools in your main script
3. Use via: server.call_tool('tool_name', {'param': 'value'})
"""

import json
import csv
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


EXPERT_ANALYSIS_PROMPT = """ESG Data Mapping Expert Analysis

Role: Act as an experienced ESG data analyst specializing in matching geospatial and environmental datasets to specific sustainability metrics.

Critical Instructions:
1. Match data to WHAT IS ACTUALLY BEING MEASURED: Only assign datasets that directly measure or enable calculation of the specific metric. Climate projections are NOT measurements of current energy use, water consumption, or operational data.

2. Evaluate dataset relevance systematically:
   - What variables/bands does this dataset contain?
   - What does it actually measure vs. project/model?
   - Does it measure the metric's unit (GJ, m³, %, etc.)?
   - What spatial/temporal resolution and coverage?

3. Prioritize measurement datasets over projection datasets:
   - Satellite imagery > Climate models for current conditions
   - Operational data sources > Risk assessments for metrics
   - Direct measurements > Indirect indicators

Relevance Categories - Strict Definitions:
- Direct Measurement: Dataset contains variables that directly quantify the metric in its specified unit
- Risk Assessment: Dataset helps identify locations/facilities at risk related to the metric
- Risk Insights: Dataset provides contextual information that informs understanding of risks
- Trend Analysis: Dataset enables monitoring changes over time in the metric
- Benchmarking: Dataset provides comparative data or enables normalization
- Regulatory Support: Dataset specifically designed for regulatory reporting/compliance
"""


class RelevanceCategory(Enum):
    """Dataset relevance categories for ESG metrics"""
    DIRECT_MEASUREMENT = "Direct Measurement"
    RISK_ASSESSMENT = "Risk Assessment"
    RISK_INSIGHTS = "Risk Insights"
    TREND_ANALYSIS = "Trend Analysis"
    BENCHMARKING = "Benchmarking"
    REGULATORY_SUPPORT = "Regulatory Support"


@dataclass
class SASBMetric:
    """SASB metric structure"""
    sector: str
    topic: str
    metric: str
    category: str
    unit: str
    code: str


@dataclass
class GeospatialDataset:
    """Geospatial dataset structure"""
    id: str
    title: str
    description: str
    keywords: List[str]
    bands: Optional[List[Dict]] = None
    temporal_range: Optional[Dict] = None
    spatial_coverage: Optional[Dict] = None
    resolution: Optional[str] = None


@dataclass
class DatasetMatch:
    """Match between dataset and metric with detailed reasoning"""
    dataset_id: str
    dataset_title: str
    category: RelevanceCategory
    rationale: str
    variables_bands: Optional[str] = None
    measurement_type: Optional[str] = None
    confidence_score: float = 0.0


class ESGDataMatcher:
    """Core matching engine following expert analysis prompt"""
    
    def __init__(self):
        self.metrics: List[SASBMetric] = []
        self.datasets: List[GeospatialDataset] = []
        
    def load_sasb_metrics(self, metrics_data: List[Dict]) -> None:
        """Load SASB metrics from JSON/dict format"""
        self.metrics = []
        for m in metrics_data:
            # Handle comma-separated metrics - split into separate rows
            metric_text = m.get("Metric", "")
            if "," in metric_text and m.get("Category") == "Quantitative":
                individual_metrics = [mt.strip() for mt in metric_text.split(",")]
                for individual_metric in individual_metrics:
                    self.metrics.append(SASBMetric(
                        sector=m.get("Sector", ""),
                        topic=m.get("Topic", ""),
                        metric=individual_metric,
                        category=m.get("Category", ""),
                        unit=m.get("Unit of Measure", ""),
                        code=m.get("Code", "")
                    ))
            else:
                self.metrics.append(SASBMetric(
                    sector=m.get("Sector", ""),
                    topic=m.get("Topic", ""),
                    metric=metric_text,
                    category=m.get("Category", ""),
                    unit=m.get("Unit of Measure", ""),
                    code=m.get("Code", "")
                ))
    
    def load_geospatial_datasets(self, datasets_data: List[Dict]) -> None:
        """Load geospatial datasets from STAC JSON or similar format"""
        self.datasets = []
        for d in datasets_data:
            bands = None
            if "summaries" in d and "eo:bands" in d["summaries"]:
                bands = d["summaries"]["eo:bands"]
            
            temporal = None
            if "extent" in d and "temporal" in d["extent"]:
                temporal = d["extent"]["temporal"]
            
            spatial = None
            if "extent" in d and "spatial" in d["extent"]:
                spatial = d["extent"]["spatial"]
            
            resolution = None
            if "summaries" in d and "gsd" in d["summaries"]:
                gsd = d["summaries"]["gsd"]
                resolution = f"{gsd}m" if isinstance(gsd, (int, float)) else str(gsd)
            
            self.datasets.append(GeospatialDataset(
                id=d.get("id", ""),
                title=d.get("title", ""),
                description=d.get("description", ""),
                keywords=d.get("keywords", []),
                bands=bands,
                temporal_range=temporal,
                spatial_coverage=spatial,
                resolution=resolution
            ))
    
    def _is_projection_dataset(self, dataset: GeospatialDataset) -> bool:
        """Determine if dataset is projection/model vs actual measurement"""
        projection_indicators = [
            "projection", "scenario", "forecast", "future", "cmip", "downscaled",
            "model", "predicted", "simulated"
        ]
        text = f"{dataset.title} {dataset.description}".lower()
        return any(indicator in text for indicator in projection_indicators)
    
    def _extract_measurement_capability(self, dataset: GeospatialDataset) -> str:
        """Determine what the dataset actually measures"""
        desc_lower = f"{dataset.title} {dataset.description}".lower()
        capabilities = []
        
        if any(term in desc_lower for term in ["temperature", "thermal", "lst", "heat"]):
            capabilities.append("temperature/thermal")
        if any(term in desc_lower for term in ["water", "precipitation", "moisture", "hydrological"]):
            capabilities.append("water/precipitation")
        if any(term in desc_lower for term in ["vegetation", "ndvi", "evi", "photosynthesis"]):
            capabilities.append("vegetation indices")
        if any(term in desc_lower for term in ["land cover", "land use", "lulc"]):
            capabilities.append("land cover/use")
        if any(term in desc_lower for term in ["building", "infrastructure", "footprint"]):
            capabilities.append("infrastructure mapping")
        if any(term in desc_lower for term in ["elevation", "dem", "dtm", "terrain"]):
            capabilities.append("elevation/terrain")
        if any(term in desc_lower for term in ["fire", "thermal anomaly", "wildfire"]):
            capabilities.append("fire detection")
        if any(term in desc_lower for term in ["flood", "inundation", "sea level"]):
            capabilities.append("flood modeling")
        
        return "; ".join(capabilities) if capabilities else "general imagery"
    
    def _analyze_metric_dataset_match(self, metric: SASBMetric, dataset: GeospatialDataset) -> Optional[DatasetMatch]:
        """Perform detailed analysis following expert prompt logic"""
        
        is_projection = self._is_projection_dataset(dataset)
        measurement_capability = self._extract_measurement_capability(dataset)
        
        metric_lower = metric.metric.lower()
        desc_lower = f"{dataset.title} {dataset.description}".lower()
        
        category = None
        rationale = ""
        confidence = 0.0
        
        # Rule 1: Climate projections NEVER for Direct Measurement
        if is_projection:
            if "risk" in metric_lower or "stress" in metric_lower:
                category = RelevanceCategory.RISK_ASSESSMENT
                rationale = f"{measurement_capability} projections for future risk assessment"
                confidence = 0.8
            else:
                category = RelevanceCategory.TREND_ANALYSIS
                rationale = f"long-term {measurement_capability} patterns"
                confidence = 0.7
        
        # Rule 2: Direct Measurement - actual measurements only
        elif not is_projection:
            if "energy" in metric_lower and "thermal" in measurement_capability:
                category = RelevanceCategory.DIRECT_MEASUREMENT
                rationale = f"thermal signatures from facilities"
                confidence = 0.9
            elif "water" in metric_lower and "water" in measurement_capability:
                category = RelevanceCategory.DIRECT_MEASUREMENT
                rationale = f"surface water monitoring"
                confidence = 0.9
            elif "renewable" in metric_lower and ("land cover" in measurement_capability or "infrastructure" in measurement_capability):
                category = RelevanceCategory.DIRECT_MEASUREMENT
                rationale = f"renewable infrastructure identification"
                confidence = 0.85
        
        # Rule 3: Risk Assessment - hazard identification
        if not category:
            risk_keywords = ["flood", "fire", "drought", "stress", "hazard"]
            if any(kw in metric_lower for kw in risk_keywords) and any(kw in desc_lower for kw in risk_keywords):
                category = RelevanceCategory.RISK_ASSESSMENT
                rationale = f"{measurement_capability} for risk identification"
                confidence = 0.75
        
        # Rule 4: Risk Insights - contextual information
        if not category:
            context_keywords = ["land cover", "land use", "building", "infrastructure", "terrain", "elevation"]
            if any(kw in measurement_capability for kw in context_keywords):
                category = RelevanceCategory.RISK_INSIGHTS
                rationale = f"{measurement_capability} provides facility location and environmental context"
                confidence = 0.7
        
        # Rule 5: Trend Analysis - temporal component
        if not category and dataset.temporal_range:
            category = RelevanceCategory.TREND_ANALYSIS
            rationale = f"temporal series enables monitoring changes"
            confidence = 0.65
        
        if category and confidence >= 0.5:
            bands_info = None
            if dataset.bands:
                band_names = [b.get("name") or b.get("common_name") for b in dataset.bands[:5]]
                bands_info = f"bands: {', '.join([b for b in band_names if b])}"
            
            return DatasetMatch(
                dataset_id=dataset.id,
                dataset_title=dataset.title,
                category=category,
                rationale=rationale,
                variables_bands=bands_info,
                measurement_type="actual measurement" if not is_projection else "projection/model",
                confidence_score=confidence
            )
        
        return None
    
    def match_metric_to_datasets(self, metric: SASBMetric) -> Dict[RelevanceCategory, List[DatasetMatch]]:
        """Match a single metric to all relevant datasets"""
        matches_by_category: Dict[RelevanceCategory, List[DatasetMatch]] = {
            cat: [] for cat in RelevanceCategory
        }
        
        for dataset in self.datasets:
            match = self._analyze_metric_dataset_match(metric, dataset)
            if match:
                matches_by_category[match.category].append(match)
        
        for category in matches_by_category:
            matches_by_category[category].sort(key=lambda m: m.confidence_score, reverse=True)
        
        return matches_by_category
    
    def generate_excel_row(self, metric: SASBMetric, matches: Dict[RelevanceCategory, List[DatasetMatch]]) -> Dict[str, str]:
        """Generate Excel-formatted row"""
        output = {
            "Sector": metric.sector,
            "Topic": metric.topic,
            "Metric": metric.metric,
            "Category": metric.category,
            "Unit of Measure": metric.unit,
            "Code": metric.code
        }
        
        for category in RelevanceCategory:
            category_matches = matches.get(category, [])
            if category_matches:
                formatted_matches = []
                for i, match in enumerate(category_matches[:10], 1):
                    details = [match.rationale]
                    if match.variables_bands:
                        details.append(match.variables_bands)
                    detail_str = "; ".join(details)
                    formatted_matches.append(f"{i}. {match.dataset_id}, {match.dataset_title} ({detail_str})")
                output[category.value] = "\n".join(formatted_matches)
            else:
                output[category.value] = ""
        
        return output
    
    def process_all_metrics(self) -> List[Dict[str, str]]:
        """Process all metrics and generate complete mapping table"""
        results = []
        for metric in self.metrics:
            matches = self.match_metric_to_datasets(metric)
            excel_row = self.generate_excel_row(metric, matches)
            results.append(excel_row)
        return results


# Global matcher instance
_matcher = ESGDataMatcher()


# Tool Functions (following MCP framework signature)

def load_sasb_framework(args: Dict, context: Dict) -> str:
    """
    Load SASB metrics framework
    
    Args:
        metrics_data: List of SASB metric dictionaries
    
    Returns:
        Status message
    """
    metrics_data = args.get("metrics_data", [])
    _matcher.load_sasb_metrics(metrics_data)
    
    original_count = len(metrics_data)
    final_count = len(_matcher.metrics)
    split_info = f" ({final_count - original_count} metrics split from comma-separated values)" if final_count > original_count else ""
    
    return f"✓ Successfully loaded {final_count} SASB metrics{split_info}"


def load_geospatial_datasets(args: Dict, context: Dict) -> str:
    """
    Load geospatial datasets from STAC JSON
    
    Args:
        datasets_data: List of STAC collection dictionaries
    
    Returns:
        Status message
    """
    datasets_data = args.get("datasets_data", [])
    _matcher.load_geospatial_datasets(datasets_data)
    
    projection_count = sum(1 for d in _matcher.datasets if _matcher._is_projection_dataset(d))
    measurement_count = len(_matcher.datasets) - projection_count
    
    return f"✓ Successfully loaded {len(_matcher.datasets)} geospatial datasets\n" + \
           f"  - Actual measurements: {measurement_count}\n" + \
           f"  - Projections/models: {projection_count}"


def generate_esg_mapping(args: Dict, context: Dict) -> str:
    """
    Generate complete ESG data mapping
    
    Args:
        output_format: 'tsv', 'csv', or 'json' (default: 'tsv')
        output_file: Optional file path to save output
        include_analysis_summary: Include detailed summary (default: False)
    
    Returns:
        Formatted mapping table or file path
    """
    if not _matcher.metrics:
        return "❌ Error: No SASB metrics loaded. Use 'load_sasb_framework' first."
    if not _matcher.datasets:
        return "❌ Error: No datasets loaded. Use 'load_geospatial_datasets' first."
    
    output_format = args.get("output_format", "tsv")
    output_file = args.get("output_file", None)
    include_summary = args.get("include_analysis_summary", False)
    
    # Generate mapping
    results = _matcher.process_all_metrics()
    
    # Format output
    headers = ["Sector", "Topic", "Metric", "Category", "Unit of Measure", "Code",
              "Direct Measurement", "Risk Assessment", "Risk Insights", 
              "Trend Analysis", "Benchmarking", "Regulatory Support"]
    
    if output_format == "json":
        output_text = json.dumps(results, indent=2)
    elif output_format == "csv":
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in results:
            writer.writerow({h: row.get(h, "") for h in headers})
        output_text = output.getvalue()
    else:  # tsv
        lines = ["\t".join(headers)]
        for row in results:
            lines.append("\t".join(row.get(h, "") for h in headers))
        output_text = "\n".join(lines)
    
    # Save to file if requested
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            file_msg = f"✓ Successfully saved to: {os.path.abspath(output_file)}"
        except Exception as e:
            file_msg = f"❌ Error saving file: {str(e)}"
        
        return f"{file_msg}\n\nPreview (first 500 characters):\n{output_text[:500]}..."
    
    # Add summary if requested
    if include_summary:
        covered = sum(1 for r in results if any(r.get(cat.value) for cat in RelevanceCategory))
        summary = f"{'='*60}\nANALYSIS SUMMARY\n{'='*60}\n"
        summary += f"Total metrics: {len(results)}\n"
        summary += f"Covered metrics: {covered} ({covered/len(results)*100:.1f}%)\n"
        summary += f"Uncovered metrics: {len(results) - covered}\n\n"
        return summary + output_text
    
    return output_text


def analyze_single_metric(args: Dict, context: Dict) -> str:
    """
    Analyze a single SASB metric in detail
    
    Args:
        metric_code: SASB metric code (e.g., 'TA03-04-01')
    
    Returns:
        Detailed analysis report
    """
    metric_code = args.get("metric_code")
    
    metrics = [m for m in _matcher.metrics if m.code == metric_code]
    if not metrics:
        return f"❌ Metric with code {metric_code} not found"
    
    output_lines = [f"DETAILED ANALYSIS: {metric_code}", "="*60, ""]
    
    for metric in metrics:
        output_lines.append(f"Metric: {metric.metric}")
        output_lines.append(f"Topic: {metric.topic}")
        output_lines.append(f"Unit: {metric.unit}")
        output_lines.append("")
        
        matches = _matcher.match_metric_to_datasets(metric)
        
        for category in RelevanceCategory:
            category_matches = matches.get(category, [])
            if category_matches:
                output_lines.append(f"\n{category.value}:")
                output_lines.append("-" * 40)
                for match in category_matches:
                    output_lines.append(f"\n  Dataset: {match.dataset_id}")
                    output_lines.append(f"  Title: {match.dataset_title}")
                    output_lines.append(f"  Type: {match.measurement_type}")
                    output_lines.append(f"  Rationale: {match.rationale}")
                    if match.variables_bands:
                        output_lines.append(f"  {match.variables_bands}")
                    output_lines.append(f"  Confidence: {match.confidence_score:.2f}")
        
        output_lines.append("\n" + "="*60 + "\n")
    
    return "\n".join(output_lines)


def get_coverage_report(args: Dict, context: Dict) -> str:
    """
    Generate coverage report
    
    Args:
        group_by: 'topic', 'sector', or 'category' (default: 'topic')
    
    Returns:
        Coverage statistics report
    """
    group_by = args.get("group_by", "topic")
    
    if not _matcher.metrics or not _matcher.datasets:
        return "❌ Error: Load both SASB metrics and datasets first"
    
    coverage_stats = {}
    for metric in _matcher.metrics:
        matches = _matcher.match_metric_to_datasets(metric)
        total_matches = sum(len(m) for m in matches.values())
        
        key = getattr(metric, group_by)
        if key not in coverage_stats:
            coverage_stats[key] = {"total_metrics": 0, "covered_metrics": 0, "total_matches": 0}
        
        coverage_stats[key]["total_metrics"] += 1
        if total_matches > 0:
            coverage_stats[key]["covered_metrics"] += 1
        coverage_stats[key]["total_matches"] += total_matches
    
    report_lines = ["ESG DATA COVERAGE REPORT", "="*70, f"Grouped by: {group_by.title()}", ""]
    
    for key, stats in sorted(coverage_stats.items()):
        coverage_pct = (stats["covered_metrics"] / stats["total_metrics"] * 100) if stats["total_metrics"] > 0 else 0
        report_lines.append(f"\n{key}")
        report_lines.append("-" * 70)
        report_lines.append(f"  Metrics: {stats['covered_metrics']}/{stats['total_metrics']} ({coverage_pct:.1f}% coverage)")
        report_lines.append(f"  Total matches: {stats['total_matches']}")
    
    total = sum(s["total_metrics"] for s in coverage_stats.values())
    covered = sum(s["covered_metrics"] for s in coverage_stats.values())
    
    report_lines.extend([
        "",
        "="*70,
        "OVERALL SUMMARY",
        "="*70,
        f"Total Metrics: {total}",
        f"Covered Metrics: {covered}",
        f"Overall Coverage: {covered/total*100:.1f}%",
    ])
    
    return "\n".join(report_lines)


# Tool registration helper
def register_esg_tools(server):
    """
    Register all ESG mapping tools with the MCP server
    
    Usage:
        from team1a.yourname.esg_mapping_tool import register_esg_tools
        register_esg_tools(server)
    """
    server.register_tool('load_sasb_framework', load_sasb_framework)
    server.register_tool('load_geospatial_datasets', load_geospatial_datasets)
    server.register_tool('generate_esg_mapping', generate_esg_mapping)
    server.register_tool('analyze_single_metric', analyze_single_metric)
    server.register_tool('get_coverage_report', get_coverage_report)
    
    print("✓ Registered 5 ESG mapping tools:")
    print("  - load_sasb_framework")
    print("  - load_geospatial_datasets")
    print("  - generate_esg_mapping")
    print("  - analyze_single_metric")
    print("  - get_coverage_report")