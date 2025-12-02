import json
import csv
from typing import Dict, List
from pathlib import Path


def esg_mapping_tool(args: Dict, context: Dict) -> str:
    input_file = args.get('input_file')
    output_file = args.get('output_file')
    
    if not input_file:
        return "Error: 'input_file' parameter is required"
    
    if not output_file:
        output_file = str(Path(input_file).with_suffix('.csv'))
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return "Error: JSON must be an array of metric objects"
        
        headers = [
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
        
        rows = []
        for item in data:
            row = {
                'Sector': item.get('sector', ''),
                'Topic': item.get('topic', ''),
                'Metric': item.get('metric', ''),
                'Category': item.get('category', ''),
                'Unit of Measure': item.get('unit_of_measure', ''),
                'Code': item.get('code', ''),
                'Direct Measurement': format_data_points(item.get('direct_measurement', [])),
                'Risk Assessment': format_data_points(item.get('risk_assessment', [])),
                'Risk Insights': format_data_points(item.get('risk_insights', [])),
                'Trend Analysis': format_data_points(item.get('trend_analysis', [])),
                'Benchmarking': format_data_points(item.get('benchmarking', [])),
                'Regulatory Support': format_data_points(item.get('regulatory_support', []))
            }
            rows.append(row)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        
        return f"Success: Converted {len(rows)} metrics from '{input_file}' to '{output_file}'"
    
    except FileNotFoundError:
        return f"Error: Input file '{input_file}' not found"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def format_data_points(data_points: List[Dict[str, str]]) -> str:
    if not data_points:
        return ''
    
    formatted = []
    for idx, dp in enumerate(data_points, 1):
        dataset_id = dp.get('dataset_id', '')
        title = dp.get('title', '')
        reason = dp.get('reason', '')
        
        if dataset_id and title:
            entry = f"{idx}. {dataset_id}, {title}"
            if reason:
                entry += f" ({reason})"
            formatted.append(entry)
    
    return '<br>'.join(formatted)