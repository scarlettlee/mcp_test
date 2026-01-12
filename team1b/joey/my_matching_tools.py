from typing import Dict, Any
import json
import os
import csv
import io
from openai import OpenAI
from anthropic import Anthropic
from config import get_api_key 

def esg_data_mapping_tool(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Maps geospatial datasets to SASB ESG metrics using OpenAI.
    """
    
    # Extract arguments
    catalog_data = args.get("catalog_data")
    model = args.get("model", "gpt-4")
    output_file = args.get("output_file", "esg_mapping_output.csv")
    provider = args.get("provider", "openai")
    
    # ═══════════════════════════════════════════════════════
    # LOAD OPENAI KEY FROM CONFIG.JSON (instead of from args)
    # ═══════════════════════════════════════════════════════
    try:
        api_key = get_api_key(provider)   # "openai" or "anthropic"
    except Exception as e:
        return f"Error loading {provider} API key from config.json: {str(e)}"

    if not catalog_data:
        return "Error: catalog_data is required"
    if not api_key:
        return f"Error: {provider} API key not found in config.json"
    
    # Validate inputs
    if not catalog_data:
        return "Error: catalog_data is required"
    if not api_key:
        return "Error: OpenAI API key not found in config.json"
    
    # Load catalog data
    if isinstance(catalog_data, str) and os.path.exists(catalog_data):
        with open(catalog_data, 'r') as f:
            catalog_json = json.load(f)
    elif isinstance(catalog_data, dict):
        catalog_json = catalog_data
    elif isinstance(catalog_data, str):
        catalog_json = json.loads(catalog_data)
    else:
        return "Error: catalog_data must be JSON string, dict, or file path"
    
    # Load the system prompt
    system_prompt = get_esg_mapping_prompt()
    
    # Prepare user message
    user_message = f"""
        Analyze the following geospatial dataset catalog and create a 33-row mapping table matching datasets to SASB Software & IT Services metrics.

        **CRITICAL FORMAT REQUIREMENTS:**

        1. **Dataset Match Format**: Each dataset must follow this EXACT format:
        catalog-domain-#. dataset_id, Dataset Title (detailed reasoning explaining the match)
        
        Example: planetarycomputer.microsoft.com-1. terraclimate, TerraClimate (contains climate water deficit, soil moisture, actual evapotranspiration, and runoff variables for assessing regional water stress and availability risks at facility locations)

        2. **Multiple Datasets**: When multiple datasets match a column, separate them with semicolons:
        catalog1-1. id1, Title1 (reason);
        catalog2-1. id2, Title2 (reason);
        catalog3-2. id3, Title3 (reason)

        3. **Numbering**: Restart numbering at 1 for EACH NEW CATALOG within each relevance category (column). If the same catalog appears multiple times in one column, increment the number.

        4. **All 33 Metrics**: You must provide exactly these 33 rows in order:
        Row 1: Total energy consumed
        Row 2: Percentage grid electricity
        Row 3: Percentage renewable energy
        Row 4: Total water withdrawn
        Row 5: Percentage recycled
        Row 6: Percentage in regions with High or Extremely High Baseline Water Stress
        Row 7: Description of the integration of environmental considerations...
        Row 8: Discussion of policies and practices relating to collection, usage...
        Row 9: Percentage of users whose customer information is collected for secondary purpose
        Row 10: Percentage who have opted-in
        Row 11: Amount of legal and regulatory fines and settlements associated with customer privacy
        Row 12: Number of government or law enforcement requests for customer information
        Row 13: Number of records requested
        Row 14: Percentage resulting in disclosure
        Row 15: List of countries where core products or services are subject to government-required monitoring...
        Row 16: Number of data security breaches
        Row 17: Percentage involving customers' personally identifiable information (PII)
        Row 18: Number of customers affected
        Row 19: Discussion of management approach to identifying and addressing data security risks
        Row 20: Percentage of operations, by revenue, independently certified...
        Row 21: Percentage of employees that are foreign nationals
        Row 22: Percentage of employees located offshore
        Row 23: Employee engagement as a percentage
        Row 24: Percentage of gender and racial/ethnic group representation for executives
        Row 25: Percentage of gender and racial/ethnic group representation for all others
        Row 26: Number of performance issues
        Row 27: Number of service disruptions
        Row 28: Total customer downtime
        Row 29: Discussion of business continuity risks related to disruptions of operations
        Row 30: Number of patent litigation cases
        Row 31: Number successful
        Row 32: Number as patent holder
        Row 33: Amount of legal and regulatory fines and settlements associated with anti-competitive practices

        5. **Empty Cells**: If no datasets match a specific category for a metric, leave that field as an empty string "".

        6. **Return JSON**: Return valid JSON with this structure:
        {{
        "rows": [
            {{
            "sector": "Software & IT Services",
            "topic": "Environmental Footprint of Hardware Infrastructure",
            "metric": "Total water withdrawn",
            "category": "Quantitative",
            "unit_of_measure": "Cubic meters (m³)",
            "code": "TC0102-02",
            "direct_measurement": "catalog-1. id, Title (reason)",
            "risk_assessment": "catalog-1. id, Title (reason); catalog-2. id, Title (reason)",
            "risk_insights": "",
            "trend_analysis": "catalog-1. id, Title (reason)",
            "benchmarking": "",
            "regulatory_support": ""
            }},
            ... (32 more rows)
        ]
        }}

        Dataset Catalog to Analyze:
        {json.dumps(catalog_json, indent=2)}

        Remember: Match datasets based on what they ACTUALLY MEASURE vs what the metric requires.
    """

    try:
        if provider == "openai":
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,   # ← now uses args["model"]
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "esg_mapping",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "rows": {
                                    "type": "array",
                                    "minItems": 33,
                                    "maxItems": 33,
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "sector": {"type": "string"},
                                            "topic": {"type": "string"},
                                            "metric": {"type": "string"},
                                            "category": {"type": "string"},
                                            "unit_of_measure": {"type": "string"},
                                            "code": {"type": "string"},
                                            "direct_measurement": {"type": "string"},  # Can contain multiple datasets separated by ;
                                            "risk_assessment": {"type": "string"},
                                            "risk_insights": {"type": "string"},
                                            "trend_analysis": {"type": "string"},
                                            "benchmarking": {"type": "string"},
                                            "regulatory_support": {"type": "string"}
                                        },
                                        "required": ["sector", "topic", "metric", "category", "unit_of_measure", "code"]
                                    }
                                }
                            },
                            "required": ["rows"]
                        }
                    }
                },
                temperature=0.3,
            )
            mapping_result = response.choices[0].message.content

        elif provider == "anthropic":
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,              # e.g. "claude-3-5-sonnet-20241022"
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                extra_body={
                    "output_format": {          # Anthropic structured JSON output
                        "type": "json_schema",
                        "json_schema": {        # same schema you used in response_format
                            "name": "esg_mapping",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "rows": {
                                        "type": "array",
                                        "minItems": 33,
                                        "maxItems": 33,
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "sector": {"type": "string"},
                                                "topic": {"type": "string"},
                                                "metric": {"type": "string"},
                                                "category": {"type": "string"},
                                                "unit_of_measure": {"type": "string"},
                                                "code": {"type": "string"},
                                                "direct_measurement": {"type": "string"},
                                                "risk_assessment": {"type": "string"},
                                                "risk_insights": {"type": "string"},
                                                "trend_analysis": {"type": "string"},
                                                "benchmarking": {"type": "string"},
                                                "regulatory_support": {"type": "string"}
                                            },
                                            "required": ["sector", "topic", "metric", "category", "unit_of_measure", "code"]
                                        }
                                    }
                                },
                                "required": ["rows"]
                            }
                        }
                    }
                },
                temperature=0.3,
            )
            # Anthropic returns content as a list of text blocks
            mapping_result = response.content[0].text  # JSON string
        else:
            return f"Error: Unknown provider '{provider}'"

        csv_output = convert_to_csv(mapping_result)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(csv_output)
        
        # Store result in context
        context['last_esg_mapping'] = {
            'output_file': output_file,
            'row_count': len(csv_output.split('\n')) - 1
        }
        
        return f"Success! ESG mapping completed. Output saved to: {output_file}"
        
    except Exception as e:
        return f"Error: {str(e)}"


def convert_to_csv(mapping_result: str) -> str:
    """
    Converts OpenAI JSON output to CSV with 33 rows.
    """
    # Parse JSON response
    data = json.loads(mapping_result)
    rows = data.get('rows', [])
    
    # Validate 33 rows
    if len(rows) != 33:
        raise ValueError(f"Expected 33 rows, got {len(rows)}")
    
    # Define CSV columns
    columns = [
        'Sector', 'Topic', 'Metric', 'Category', 
        'Unit of Measure', 'Code', 'Direct Measurement',
        'Risk Assessment', 'Risk Insights', 'Trend Analysis',
        'Benchmarking', 'Regulatory Support'
    ]
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    
    for row in rows:
        writer.writerow({
            'Sector': row.get('sector', ''),
            'Topic': row.get('topic', ''),
            'Metric': row.get('metric', ''),
            'Category': row.get('category', ''),
            'Unit of Measure': row.get('unit_of_measure', ''),
            'Code': row.get('code', ''),
            'Direct Measurement': row.get('direct_measurement', ''),
            'Risk Assessment': row.get('risk_assessment', ''),
            'Risk Insights': row.get('risk_insights', ''),
            'Trend Analysis': row.get('trend_analysis', ''),
            'Benchmarking': row.get('benchmarking', ''),
            'Regulatory Support': row.get('regulatory_support', '')
        })
    
    return output.getvalue()



def get_esg_mapping_prompt() -> str:
    """Returns the full system prompt for ESG data mapping."""
    # Read from file or paste full content
    prompt_file = os.path.join(os.path.dirname(__file__), "ESG_Data_Mapping_Prompt_REVISED.txt")
    
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return """ ESG Data Mapping Prompt - Excel Output Format

        Role: Act as an experienced ESG data analyst specializing in matching geospatial and environmental datasets to specific sustainability metrics.

        Critical Instructions
        1. Match data to WHAT IS ACTUALLY BEING MEASURED: Only assign datasets that directly measure or enable calculation of the specific metric. Climate projections are NOT measurements of current energy use, water consumption, or operational data.

        2. Evaluate dataset relevance systematically:
        • What variables/bands does this dataset contain?
        • What does it actually measure vs. project/model?
        • Does it measure the metric's unit (GJ, m³, %, etc.)?
        • What spatial/temporal resolution and coverage?

        3. Prioritize measurement datasets over projection datasets:
        • Satellite imagery > Climate models for current conditions
        • Operational data sources > Risk assessments for metrics
        • Direct measurements > Indirect indicators

        4. Put each metric that is separated by commas into its own row

        Task
        Create a comprehensive mapping showing which datasets support each SASB metric, organized by relevance category. Include ALL 33 metrics even if no supporting data is found. Use ONE consolidated table for all catalogs.

        Template Structure - MANDATORY
        Your output MUST contain exactly these 33 rows in this exact order with these exact columns:

        Row | Sector | Topic | Metric | Category | Unit of Measure | Code
        ----|--------|-------|--------|----------|-----------------|------
        1 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Total energy consumed | Quantitative | Gigajoules | TC0102-01
        2 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Percentage grid electricity | Quantitative | Percentage (%) | TC0102-01
        3 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Percentage renewable energy | Quantitative | Percentage (%) | TC0102-01
        4 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Total water withdrawn | Quantitative | Cubic meters (m³) | TC0102-02
        5 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Percentage recycled | Quantitative | Percentage (%) | TC0102-02
        6 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Percentage in regions with High or Extremely High Baseline Water Stress | Quantitative | Percentage (%) | TC0102-02
        7 | Software & IT Services | Environmental Footprint of Hardware Infrastructure | Description of the integration of environmental considerations to strategic planning for data center needs | Discussion and Analysis | n/a | TC0102-03
        8 | Software & IT Services | Data Privacy & Freedom of Expression | Discussion of policies and practices relating to collection, usage, and retention of customers' information and personally identifiable information | Discussion and Analysis | n/a | TC0102-04
        9 | Software & IT Services | Data Privacy & Freedom of Expression | Percentage of users whose customer information is collected for secondary purpose | Quantitative | Percentage (%) | TC0102-05
        10 | Software & IT Services | Data Privacy & Freedom of Expression | Percentage who have opted-in | Quantitative | Percentage (%) | TC0102-05
        11 | Software & IT Services | Data Privacy & Freedom of Expression | Amount of legal and regulatory fines and settlements associated with customer privacy | Quantitative | U.S. dollars ($) | TC0102-06
        12 | Software & IT Services | Data Privacy & Freedom of Expression | Number of government or law enforcement requests for customer information | Quantitative | Number | TA03-04-01
        13 | Software & IT Services | Data Privacy & Freedom of Expression | Number of records requested | Quantitative | Number | TA03-04-01
        14 | Software & IT Services | Data Privacy & Freedom of Expression | Percentage resulting in disclosure | Quantitative | Percentage (%) | TA03-04-01
        15 | Software & IT Services | Data Privacy & Freedom of Expression | List of countries where core products or services are subject to government-required monitoring, blocking, content filtering, or censoring | Discussion and Analysis | n/a | TC0102-08
        16 | Software & IT Services | Data Security | Number of data security breaches | Quantitative | Number | TA03-06-01
        17 | Software & IT Services | Data Security | Percentage involving customers' personally identifiable information (PII) | Quantitative | Percentage (%) | TA03-06-01
        18 | Software & IT Services | Data Security | Number of customers affected | Quantitative | Number | TA03-06-01
        19 | Software & IT Services | Data Security | Discussion of management approach to identifying and addressing data security risks | Discussion and Analysis | n/a | TC0102-10
        20 | Software & IT Services | Data Security | Percentage of operations, by revenue, independently certified to a suitable third-party cybersecurity management standard | Quantitative | Percentage (%) | TA03-05-01
        21 | Software & IT Services | Recruiting & Managing a Global, Diverse Skilled Workforce | Percentage of employees that are foreign nationals | Quantitative | Percentage (%) | TC0102-11
        22 | Software & IT Services | Recruiting & Managing a Global, Diverse Skilled Workforce | Percentage of employees located offshore | Quantitative | Percentage (%) | TC0102-11
        23 | Software & IT Services | Recruiting & Managing a Global, Diverse Skilled Workforce | Employee engagement as a percentage | Quantitative | Percentage (%) | TC0102-12
        24 | Software & IT Services | Recruiting & Managing a Global, Diverse Skilled Workforce | Percentage of gender and racial/ethnic group representation for executives | Quantitative | Percentage (%) | TC0102-13
        25 | Software & IT Services | Recruiting & Managing a Global, Diverse Skilled Workforce | Percentage of gender and racial/ethnic group representation for all others | Quantitative | Percentage (%) | TC0102-13
        26 | Software & IT Services | Managing Systemic Risks from Technology Disruptions | Number of performance issues | Quantitative | Number | TC0102-14
        27 | Software & IT Services | Managing Systemic Risks from Technology Disruptions | Number of service disruptions | Quantitative | Number | TC0102-14
        28 | Software & IT Services | Managing Systemic Risks from Technology Disruptions | Total customer downtime | Quantitative | Days | TC0102-14
        29 | Software & IT Services | Managing Systemic Risks from Technology Disruptions | Discussion of business continuity risks related to disruptions of operations | Discussion and Analysis | n/a | TC0102-15
        30 | Software & IT Services | Intellectual Property Protection & Competitive Behavior | Number of patent litigation cases | Quantitative | Number | TC0102-16
        31 | Software & IT Services | Intellectual Property Protection & Competitive Behavior | Number successful | Quantitative | Number | TC0102-16
        32 | Software & IT Services | Intellectual Property Protection & Competitive Behavior | Number as patent holder | Quantitative | Number | TC0102-16
        33 | Software & IT Services | Intellectual Property Protection & Competitive Behavior | Amount of legal and regulatory fines and settlements associated with anti-competitive practices | Quantitative | U.S. dollars ($) | TC0102-17

        Additional columns for dataset mappings:
        • Direct Measurement
        • Risk Assessment
        • Risk Insights
        • Trend Analysis
        • Benchmarking
        • Regulatory Support

        Relevance Categories - Strict Definitions
        Assign each dataset to ONLY ONE category based on the strongest relationship:

        • Direct Measurement: Dataset contains variables that directly quantify the metric in its specified unit of measure (e.g., energy in GJ, water in m³). Must be actual measurements, not projections.

        • Risk Assessment: Dataset helps identify locations/facilities at risk related to the metric (e.g., water stress indices, climate hazard maps, biodiversity risk zones)

        • Risk Insights: Dataset provides contextual information that informs understanding of risks but doesn't directly assess them (e.g., land cover for understanding site context)

        • Trend Analysis: Dataset enables monitoring changes over time in the metric or related conditions. Must have temporal component suitable for tracking (daily/monthly/yearly observations)

        • Benchmarking: Dataset provides comparative data (industry standards, regional averages, peer comparisons) or enables normalization

        • Regulatory Support: Dataset specifically designed for or commonly used in regulatory reporting/compliance for this metric type

        Data Point Formatting Requirements - CRITICAL
        For each cell containing datasets:

        1. Format: [catalog-name]-#. Dataset_ID, Dataset_Title (matching reason)

        2. Catalog naming: Use the filename without .json:
        • stac-tags-explorer.digitalearth.africa.json → explorer.digitalearth.africa
        • stac-tags-stac.geobon.org.json → stac.geobon.org
        • etc.

        3. Numbering - CRITICAL CORRECTION:
        The number after [catalog-name]- should restart at 1 for each new catalog source within each relevance category column.

        ❌ INCORRECT Example:
        gep-supersites-stac.terradue.com-1. csk-nicaragua-supersite...
        gep-supersites-stac.terradue.com-2. csk-san-andrea-supersite...
        gep-supersites-stac.terradue.com-3. csk-turkey-event-supersite...
        geoservice.dlr.de-4. TIMELINE_AVHRR_P1M_LSTD...
        planetarycomputer.microsoft.com-5. modis-11A2-061...
        planetarycomputer.microsoft.com-6. modis-11A1-061...

        ✓ CORRECT Example:
        gep-supersites-stac.terradue.com-1. csk-nicaragua-supersite...
        gep-supersites-stac.terradue.com-2. csk-san-andrea-supersite...
        gep-supersites-stac.terradue.com-3. csk-turkey-event-supersite...
        geoservice.dlr.de-1. TIMELINE_AVHRR_P1M_LSTD...
        planetarycomputer.microsoft.com-1. modis-11A2-061...
        planetarycomputer.microsoft.com-2. modis-11A1-061...
        planetarycomputer.microsoft.com-3. era5-pds...
        planetarycomputer.microsoft.com-4. terraclimate...
        eocat.esa.int-1. Swarm.Geodesy_Gravity...

        4. Multiple datasets: Separate entries with ; (semicolon) or line break

        5. Include matching reason: Add brief explanation in parentheses explaining why the dataset matches

        6. Single consolidated table: Do NOT create separate tables for each STAC catalog

        Complete Example for One Cell:
        explorer.digitalearth.africa-1. cmip6-annual-precipitation, CMIP6 Annual Precipitation (assesses projected changes in precipitation and temperature extremes that may influence cooling energy demand); explorer.digitalearth.africa-2. sentinel-2-l2a, Sentinel-2 Level-2A (monitors land surface changes around data centers); stac.geobon.org-1. chelsa-clim-proj, CHELSA Climatologies Projections (assesses future climate shifts that may drive habitat degradation)

        Analysis Process for Each Metric
        For every metric, systematically evaluate:

        1. What is being measured? [metric name and unit]

        2. Available datasets that could measure this:
        • List datasets containing relevant variables from ALL catalogs
        • Specify which variables/bands are relevant
        • Note spatial/temporal characteristics

        3. Best relevance category for each dataset:
        • Apply strict category definitions
        • Choose ONE category per dataset
        • Justify the selection briefly in your working

        Special Considerations
        • Climate projections (CMIP6, downscaled data): Use for Risk Assessment (future climate risks) or Trend Analysis (long-term patterns), NOT for measuring current operations

        • Satellite imagery: Prioritize for Direct Measurement when variables match metric units

        • Ocean/atmospheric data: Relevant for environmental context and risk assessment

        • Land cover/biodiversity: Use for Risk Insights and contextual understanding

        • Historical archives: Strong for Trend Analysis if temporal coverage adequate

        Output Requirements
        1. Preserve ALL original metric information exactly from the template (all 33 rows)
        2. Include ALL metrics even with no matches (leave cells blank)
        3. Consolidate all datasets from all catalogs into ONE table
        4. Format dataset entries as: [catalog-name]-#. Dataset_ID, Dataset_Title (matching reason)
        5. Number datasets starting from 1 for EACH catalog within each relevance category column (restart numbering when switching to a new catalog)
        6. Separate multiple entries with ; or line break
        7. Each dataset appears in ONLY ONE category per metric
        8. Empty cells remain truly empty (no placeholder text)
        9. Format table for direct Excel import

        Quality Checks Before Finalizing
        ✓ Does your table contain exactly 33 rows matching the template structure?
        ✓ Are all Sector, Topic, Metric, Category, Unit of Measure, and Code values exactly as shown in the template?
        ✓ Does numbering restart at 1 for each new catalog within each relevance category column?
        ✓ Are climate models used appropriately (risk/trends, not direct measurement)?
        ✓ Do Direct Measurement datasets actually measure the metric's unit?
        ✓ Are satellite/sensor datasets prioritized for current conditions?
        ✓ Is each dataset in its single most relevant category?
        ✓ Are all original metric details preserved exactly?
        ✓ Are dataset IDs and titles exactly as provided in source JSON?
        ✓ Is there ONE consolidated table (not separate tables per catalog)?
        ✓ Are all dataset entries properly formatted with catalog prefix and matching reason?

        Key Changes in This Revision:
        1. Explicitly listed all 33 template rows with exact values for Sector, Topic, Metric, Category, Unit of Measure, and Code
        2. Clarified numbering format with visual examples (❌ incorrect vs. ✓ correct)
        3. Emphasized that numbering restarts at 1 for each new catalog within each relevance category column
        4. Added template compliance as first quality check
        5. Added numbering format check to quality checks
        6. Made template structure non-negotiable and clearly visible
        
        """

