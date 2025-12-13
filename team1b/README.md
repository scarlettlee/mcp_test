# ESG Data Mapping Tool

This project provides an LLM-powered tool for mapping geospatial and environmental datasets (e.g. STAC catalogs) to **SASB ESG metrics** for the **Software & IT Services** sector.  
It produces a **single, structured 33-row CSV** suitable for Excel-based ESG analysis and reporting.

The system supports both **OpenAI** and **Anthropic** models and enforces strict formatting, relevance, and data-quality rules through a detailed system prompt.

---

## Repository Contents
.
├── my_matching_tools.py
├── test_my_matching_tools.py
└── ESG_Data_Mapping_Prompt_REVISED.txt


### 1. `my_matching_tools.py`

Core implementation of the ESG data mapping tool.

**Key components:**

- `esg_data_mapping_tool(args, context)`
  - Main entry point for mapping dataset catalogs to SASB ESG metrics.
  - Accepts STAC catalogs as:
    - a file path
    - a Python dictionary
    - a JSON string
  - Calls an LLM (OpenAI or Anthropic) to generate a structured JSON mapping.
  - Converts the result into a CSV with exactly **33 rows**.
  - Saves output to disk and stores metadata in the execution context.

- `convert_to_csv(mapping_result)`
  - Validates that exactly 33 metrics are returned.
  - Converts structured JSON into a CSV formatted for Excel import.

- `get_esg_mapping_prompt()`
  - Loads the ESG system prompt from `ESG_Data_Mapping_Prompt_REVISED.txt`.
  - Falls back to an embedded prompt if the file is missing.

**Supported providers**
- OpenAI (`openai`)
- Anthropic (`anthropic`)

API keys are loaded via a `config.json` file using `get_api_key(provider)`.

---

### 2. `ESG_Data_Mapping_Prompt_REVISED.txt`

The authoritative **system prompt** used by the LLM.

**What this prompt enforces:**
- Exact compliance with **33 SASB metrics** (no more, no less)
- Strict definitions for relevance categories:
  - Direct Measurement
  - Risk Assessment
  - Risk Insights
  - Trend Analysis
  - Benchmarking
  - Regulatory Support
- Correct dataset formatting: catalog-name-#. dataset_id, Dataset Title (matching reason)
- Restarting dataset numbering **per catalog per column**
- Proper use of climate models (risk/trends only, not direct measurement)
- A single consolidated table across all catalogs

This file defines the ESG logic and quality controls for the entire system.

---

### 3. `test_my_matching_tools.py`

Test and demonstration script for running the ESG mapping tool end-to-end.

**Includes:**

- Utilities for:
- Slimming large STAC catalogs to reduce token usage
- Previewing generated CSV output
- Two test scenarios:
1. **Single catalog test**
   - `fedeo.ceos.org`
2. **Multi-catalog test**
   - `fedeo.ceos.org`
   - `planetarycomputer.microsoft.com`
- Automatic validation:
- Confirms exactly **33 rows** are generated
- Prints sample output for inspection

Tests are run via an `MCPServer` and demonstrate realistic usage of the tool.

---

## Quick Start

Follow these steps to run the ESG Data Mapping Tool end-to-end and generate a 33-row SASB-aligned ESG mapping CSV.

---

### 1. Install Dependencies

Ensure you are using **Python 3.9+**.

```bash
pip install openai anthropic
```

### 2. Configure API Keys

Create a config.json file at the project root:

```bash
{
  "openai": "YOUR_OPENAI_API_KEY",
  "anthropic": "YOUR_ANTHROPIC_API_KEY"
}
```

The tool automatically loads keys using:

provider=`openai`
provider=`anthropic`


### 3. Prepare a STAC Catalog

You can pass catalog data in one of three formats:

Option A: File path (recommended)

```bash
"catalog_data": "stac-tags-fedeo.ceos.org.json"
```

Option B: Python dictionary

```bash
"catalog_data": catalog_dict
```
Option C: JSON string

```bash
"catalog_data": json.dumps(catalog_dict)
```

For large catalogs, consider trimming descriptions or collections to reduce token usage.

### 4. Run the Mapping Tool

```bash
from my_matching_tools import esg_data_mapping_tool

context = {}

result = esg_data_mapping_tool(
    {
        "catalog_data": "stac-tags-fedeo.ceos.org.json",
        "provider": "openai",
        "model": "gpt-5.1",
        "output_file": "esg_mapping_output.csv"
    },
    context
)

print(result)
```

On success, a CSV file will be written to disk and metadata will be stored in context["last_esg_mapping"].