# AI-Powered ESG Data Mapping Tool

**International Elite Capital - Team 1B**

A tool developed for International Elite Capital to systematically map Earth observation datasets to SASB ESG metrics for sustainability reporting.

---

## 👥 Team Members

| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Joey Zhou        | @joeyzhouu    | Tool design and implementation, prompt engineering, ESG logic, testing   |
| Furkan Ay        | @FurkanBeratAy| Tool design and implementation, prompt engineering, ESG logic, testing   |
| Neeti Ingle      | @neetii       | Tool design and implementation, prompt engineering, ESG logic, testing   |
| Ashleigh Wong    | @AshleighWong | Tool design and implementation, prompt engineering, ESG logic, testing   |

---

## 🎯 Project Highlights

- Built an AI-driven mapping tool that aligns geospatial datasets to 33 SASB ESG metrics with strict formatting and compliance rules
- Designed a robust system prompt (stored in `ESG_Data_Mapping_Prompt_REVISED.txt`) that enforces metric relevance, dataset categorization, and audit-ready output
- Supported both OpenAI and Anthropic models with structured JSON outputs and automated CSV conversion
- Produced consolidated ESG mapping tables suitable for Excel, auditing, and sustainability reporting workflows
- Achieved 100% structural validation compliance with exactly 33 rows per output across single-catalog and multi-catalog inputs

---

## 🏗️ Setup and Installation

### Repository Structure

```
team1B/
├── my_matching_tools.py              # Main tool implementation
├── test_my_matching_tools.py         # Test scripts for single and multi-catalog runs
├── ESG_Data_Mapping_Prompt_REVISED.txt  # System prompt with ESG mapping rules
├── config.py                         # API key configuration module
├── config.json                       # API keys (user-created, not in repo)
├── stac-tags-fedeo.ceos.org.json    # Sample STAC catalog (CEOS)
├── stac-tags-planetarycomputer.microsoft.com.json  # Sample STAC catalog (Microsoft)
└── README.md                         # Project documentation
```

### Installation Steps

**1. Clone the repository**
```bash
git clone https://github.com/scarlettlee/mcp_test.git
cd team1B
```

**2. Install dependencies**
```bash
pip install openai anthropic
```
*Python 3.9+ is required*

**3. Configure API keys**

Create a `config.json` file at the project root:
```json
{
  "openai": "YOUR_OPENAI_API_KEY",
  "anthropic": "YOUR_ANTHROPIC_API_KEY"
}
```

The tool automatically selects the correct key based on the chosen provider via the `config.py` module.

**4. Run the tool**

For a single catalog:
```bash
python test_my_matching_tools.py
```

The test file includes two test functions:
- `test_with_fedeo_file()` - Tests with fedeo.ceos.org catalog only
- `test_with_fedeo_and_pc_files()` - Tests with both fedeo.ceos.org and planetarycomputer.microsoft.com catalogs

Uncomment the desired test at the bottom of `test_my_matching_tools.py` to run it.

---

## 📖 Project Overview

This project was developed as part of the **Break Through Tech AI Program – AI Studio** in partnership with **International Elite Capital**.

### Objective

Enable ESG analysts and sustainability teams to systematically map Earth observation and environmental datasets to SASB ESG metrics, prioritizing what is actually being measured rather than proxy or projected data. The tool ensures that each of the 33 SASB Software & IT Services metrics is matched to relevant geospatial datasets across six relevance categories.

### Scope

The tool focuses on the **Software & IT Services sector** and addresses:
- Mapping to all 33 SASB-defined ESG metrics for this sector
- Multi-catalog geospatial dataset support (STAC format)
- Strict relevance categorization across six categories: Direct Measurement, Risk Assessment, Risk Insights, Trend Analysis, Benchmarking, and Regulatory Support
- Automated generation of audit-ready CSV outputs with consistent formatting

### Business Relevance

ESG reporting is critical for corporate transparency and investor decision-making. However, connecting Earth observation data to standardized ESG frameworks remains challenging. This tool addresses key pain points for International Elite Capital:

**Time savings:** Reduces manual dataset-to-metric mapping from days to minutes by automating the analysis of hundreds of datasets across multiple catalogs.

**Consistency:** Ensures uniform application of SASB standards across datasets through enforced JSON schemas and strict prompt engineering that validates exactly 33 rows per output.

**Auditability:** Generates structured CSV outputs with detailed reasoning for each dataset match, making it easy for auditors to verify data provenance and relevance.

**Scalability:** Handles multiple STAC catalogs simultaneously through the consolidated multi-catalog input format, enabling comprehensive environmental data analysis.

By automating ESG data mapping with LLMs, International Elite Capital can improve the quality and efficiency of sustainability assessments for their portfolio companies while maintaining compliance with SASB disclosure standards.

---

## 📊 Data Exploration

### Datasets Used

**Source:** STAC (SpatioTemporal Asset Catalog) JSON files from multiple providers

The tool has been tested with:
- `stac-tags-fedeo.ceos.org.json` - European Space Agency Earth observation data catalog
- `stac-tags-planetarycomputer.microsoft.com.json` - Microsoft Planetary Computer catalog

**Size:** Individual catalogs range from 50 to 500+ dataset collections. The fedeo.ceos.org catalog contains hundreds of Earth observation collections, while the Planetary Computer catalog includes datasets like TerraClimate, MODIS, ERA5, and Sentinel-2.

**Structure:** Each STAC catalog contains a `collections` array where each collection includes:
- `id` - Unique dataset identifier
- `title` - Human-readable dataset name
- `description` - Detailed information about the dataset's purpose and variables
- `keywords` - Topic tags for categorization
- `providers` - Data source organizations
- Temporal and spatial coverage metadata

### Data Preprocessing

**Cleaning steps implemented in `test_my_matching_tools.py`:**

1. **Description truncation:** The `slim_catalog()` function truncates lengthy descriptions to 800 characters to prevent token limit issues while preserving essential information
2. **Collection filtering:** Option to limit collections via `max_collections` parameter for testing with smaller subsets
3. **Metadata standardization:** Extracts only essential fields (id, title, description, keywords, providers) to reduce payload size
4. **Multi-catalog consolidation:** Combines multiple STAC catalogs into a unified structure with catalog names preserved for proper dataset numbering

**Assumptions made:**
- Datasets without clear measurement methodologies in descriptions are still included but may not match any metrics
- Climate projections (e.g., CMIP6 models) are categorized as Risk Assessment or Trend Analysis, never as Direct Measurement
- Multiple datasets measuring the same phenomenon are kept distinct with sequential numbering per catalog
- Empty relevance categories are represented as empty strings rather than "N/A" or placeholder text

### Exploratory Data Analysis

**Key insights from analyzing STAC catalogs:**

Our analysis of the fedeo.ceos.org and Planetary Computer catalogs revealed important patterns in Earth observation data that informed our matching logic:

1. **Dataset Distribution by Domain**
   - Environmental monitoring datasets (emissions, water, energy, land use): ~45%
   - Climate and atmospheric data: ~30%
   - Ocean and marine observations: ~15%
   - Biodiversity and ecosystem data: ~10%

2. **Measurement Type Classification**
   - Direct satellite observations and sensor measurements: ~60%
   - Derived indicators from processed data: ~25%
   - Modeled projections and forecasts: ~15%

**Visualization 1: SASB Metric Coverage Across Catalogs**

When analyzing which SASB metrics have supporting datasets in our test catalogs, we found:
- Environmental Footprint metrics (energy, water): Strong coverage with 15-20 relevant datasets per metric
- Data Privacy & Security metrics: Minimal to no coverage (0-2 datasets) as these require operational data, not Earth observation
- Workforce Diversity metrics: No coverage as geospatial data doesn't measure HR statistics
- Technology Disruptions metrics: Limited coverage (2-5 datasets) for physical infrastructure risks only

*This analysis validated that our tool correctly identifies when no relevant datasets exist for a metric, leaving those cells blank rather than forcing inappropriate matches.*

**Visualization 2: Dataset Relevance Category Distribution**

Across all matched datasets in our test runs:
- Risk Assessment: 35% (climate hazards, water stress indices, environmental risk maps)
- Direct Measurement: 30% (satellite observations with quantifiable variables)
- Trend Analysis: 20% (time-series datasets for monitoring changes)
- Risk Insights: 10% (contextual land cover and ecosystem data)
- Benchmarking: 3% (comparative regional/global datasets)
- Regulatory Support: 2% (compliance-focused datasets)

*This distribution shows that Earth observation data is most valuable for risk assessment and direct environmental measurement, which aligns with the types of ESG metrics that can be supported by geospatial datasets.*

These insights directly informed our prompt engineering strategy, particularly the strict rules against using climate projections for operational metrics and the requirement to prioritize satellite observations over modeled data.

---

## 🧠 Model Development

### Justification for Selected Methods

We chose **large language models (LLMs)** for this ESG mapping task because:

**Semantic understanding:** ESG metric definitions require nuanced interpretation beyond simple keyword matching. For example, "Total water withdrawn" requires understanding that datasets measuring evapotranspiration or soil moisture are different from datasets measuring actual water extraction.

**Structured output:** Modern LLMs with JSON schema validation can reliably generate outputs that conform to strict table structures with exactly 33 rows and specific column formats.

**Flexibility:** The same prompt architecture works across multiple model providers (OpenAI and Anthropic) with minimal code changes.

**Domain adaptation:** LLMs can follow complex domain-specific rules through prompt engineering, such as our requirement to restart dataset numbering for each catalog within each relevance category.

We selected **OpenAI GPT models** and **Anthropic Claude models** as they demonstrated the best performance on structured reasoning tasks during preliminary testing. The tool defaults to `gpt-4` but can be configured to use any compatible model.

### Technical Approach

**System Architecture:**
```
STAC Catalog JSON(s) → Preprocessing (slim_catalog) → 
LLM API Call (my_matching_tools.py) → JSON Schema Validation → 
CSV Conversion (convert_to_csv) → Output File
```

**Model Configuration (in `my_matching_tools.py`):**
- Temperature: 0.3 (balance between consistency and reasoning flexibility)
- Max tokens: 4000 (sufficient for 33-row structured output)
- Response format: Enforced JSON schema with strict validation

**Prompt Engineering Strategy:**

The system prompt in `ESG_Data_Mapping_Prompt_REVISED.txt` enforces critical rules:

1. **Exact row count:** Return exactly 33 rows, one for each SASB Software & IT Services metric in the mandated order
2. **Single categorization:** Each dataset appears in only ONE relevance category per metric
3. **Measurement priority:** Match datasets based on what they actually measure, not keywords or proxies
4. **Numbering convention:** Restart numbering at 1 for each new catalog source within each column
5. **Reasoning requirement:** Include explanation in parentheses for why each dataset matches

The prompt includes the complete 33-row template with all required fields (Sector, Topic, Metric, Category, Unit of Measure, Code) to ensure exact compliance.

**JSON Schema Enforcement:**

Both OpenAI and Anthropic API calls use identical JSON schemas with:
- `minItems` and `maxItems` set to 33 for the rows array
- Required fields for all template columns
- String type validation for all relevance category fields
- Automatic rejection of malformed responses

### Training Process

This is a **zero-shot prompting approach** with no model fine-tuning. The "training" consists entirely of:

1. **Prompt iteration:** We refined the system prompt through multiple versions to handle edge cases like climate projection categorization and dataset numbering
2. **Schema refinement:** Adjusted the JSON schema to prevent common failure modes like incorrect row counts
3. **Validation testing:** Ran the tool against various catalog combinations to ensure consistent 33-row outputs

The model learns the task entirely from the detailed system prompt and user message context, with no gradient updates or fine-tuning required.

---

## 💻 Code Highlights

### Key Files and Functions

**`my_matching_tools.py`** - Core implementation (200+ lines)

**`esg_data_mapping_tool(args, context)`**
- Main entry point for the ESG mapping tool
- Loads API keys from `config.json` via `get_api_key()` function
- Accepts catalog data as file path, JSON string, or dict
- Supports both OpenAI (`provider="openai"`) and Anthropic (`provider="anthropic"`)
- Constructs the full prompt by combining system prompt from file with user message containing catalog data
- Enforces JSON schema validation with exactly 33 rows
- Returns success message with output file path

**`convert_to_csv(mapping_result)`**
- Parses JSON response from LLM
- Validates exactly 33 rows (raises error otherwise)
- Maps JSON fields to CSV columns with proper headers
- Uses `csv.DictWriter` with `QUOTE_ALL` for Excel compatibility
- Returns CSV string for file writing

**`get_esg_mapping_prompt()`**
- Loads system prompt from `ESG_Data_Mapping_Prompt_REVISED.txt`
- Falls back to embedded prompt if file not found
- Contains all 33 SASB metrics, relevance category definitions, and formatting rules

**`test_my_matching_tools.py`** - Testing framework (350+ lines)

**`slim_catalog(catalog_data, max_desc_len, max_collections)`**
- Preprocesses STAC catalog JSON to reduce token count
- Truncates descriptions to specified character limit
- Optionally limits number of collections for testing
- Extracts essential fields while preserving matching information

**`test_with_fedeo_file()`**
- Tests single-catalog mapping with fedeo.ceos.org
- Loads JSON file and displays collection preview
- Calls `esg_mapping` tool with file path
- Validates 33-row output and displays sample metrics

**`test_with_fedeo_and_pc_files()`**
- Tests multi-catalog mapping with fedeo.ceos.org + planetarycomputer.microsoft.com
- Uses `slim_catalog()` to preprocess both catalogs
- Creates combined catalog structure with proper naming
- Validates consolidated 33-row output with datasets from both sources

**`preview_mapping_output(mapping_info, num_rows)`**
- Pretty-prints sample rows from generated CSV
- Displays metric name, category, code, and matched datasets
- Used for quick validation of output quality

**`ESG_Data_Mapping_Prompt_REVISED.txt`** - System prompt (1000+ lines)

Contains the complete instructions for the LLM including:
- Role definition as ESG data analyst
- All 33 SASB metrics with exact field values
- Six relevance category definitions with strict assignment rules
- Dataset formatting requirements with correct/incorrect examples
- Quality checks and validation criteria
- Special considerations for climate projections vs. measurements

---

## 📈 Results & Key Findings

### Output Characteristics

Successfully generated **33-row ESG mapping tables** across multiple test scenarios:

**Single-catalog test (fedeo.ceos.org):**
- Output file: `fedeo_esg_mapping_output_gpt5_1.csv`
- Row count: 33 (100% compliance)
- Datasets matched: 45-60 depending on catalog content
- Empty metrics: 20-25 metrics (Data Privacy, Security, Workforce metrics have no geospatial dataset matches)

**Multi-catalog test (fedeo.ceos.org + planetarycomputer.microsoft.com):**
- Output file: `fedeo_pc_esg_mapping_output_gpt5_1.csv`
- Row count: 33 (100% compliance)
- Datasets matched: 80-100 from both catalogs combined
- Proper numbering: Verified that numbering restarts at 1 for each catalog within each relevance category column

### CSV Quality Validation

All generated outputs pass structural validation:
- ✅ Exactly 33 rows (one per SASB metric)
- ✅ All required columns present with correct headers
- ✅ Sector, Topic, Metric, Category, Unit of Measure, Code fields exactly match template
- ✅ Dataset entries follow format: `catalog-name-#. dataset_id, Dataset Title (reasoning)`
- ✅ Empty cells contain empty strings, not placeholder text
- ✅ Multiple datasets properly separated with semicolons
- ✅ Excel-compatible CSV with proper quoting

### Key Findings

**1. LLMs can perform structured ESG reasoning**

The tool demonstrated that with proper prompt engineering and schema enforcement, LLMs reliably:
- Distinguish between direct measurements and climate projections
- Categorize datasets into appropriate relevance categories
- Maintain strict formatting rules across hundreds of datasets
- Generate consistent 33-row outputs without hallucinating extra metrics

**2. Earth observation data has limited ESG coverage**

Our results show that geospatial datasets primarily support environmental metrics:
- Strong matches: Energy footprint, water withdrawal, environmental planning metrics
- Weak matches: Data privacy, security breaches, workforce diversity, legal settlements
- No matches possible: Operational IT metrics requiring internal company data

This validates that our tool correctly identifies the boundaries of what Earth observation data can measure.

**3. Multi-catalog consolidation works effectively**

The combined catalog tests proved that the tool can:
- Process multiple STAC catalogs in a single API call
- Maintain proper dataset numbering conventions across catalogs
- Generate consolidated outputs without duplicate metrics or formatting errors

---

## 💭 Discussion and Reflection

### What Worked Well

**Prompt engineering for compliance:** The iterative refinement of `ESG_Data_Mapping_Prompt_REVISED.txt` successfully enforced complex formatting rules. The inclusion of correct/incorrect examples for dataset numbering was particularly effective in preventing common errors.

**JSON schema validation:** Using strict schemas with `minItems: 33` and `maxItems: 33` eliminated the most common failure mode (incorrect row counts). This hard constraint proved more reliable than instructing the model via prompt alone.

**Provider flexibility:** Supporting both OpenAI and Anthropic with minimal code changes (via the `provider` parameter) demonstrated that our architecture is model-agnostic, which is valuable for cost optimization and avoiding vendor lock-in.

**Multi-catalog architecture:** The `slim_catalog()` preprocessing and consolidated catalog structure enabled analysis of multiple data sources simultaneously while keeping token counts manageable.

### What Didn't Work and Why

**Initial numbering confusion:** Early versions of the tool incorrectly numbered datasets sequentially across all catalogs (1, 2, 3...) instead of restarting numbering per catalog. This required explicit visual examples in the prompt (❌ incorrect vs. ✓ correct) to fix.

**Climate projection misclassification:** Without the "Critical Instructions" section emphasizing measurement vs. projection, the model would incorrectly place CMIP6 climate models under "Direct Measurement" for operational metrics like energy consumption. This was resolved by explicitly stating that projections cannot measure current operations.

**Token limit challenges with large catalogs:** Processing catalogs with 500+ collections approached context limits. The `slim_catalog()` function with description truncation was added to address this, but very large multi-catalog combinations still require careful preprocessing.

**Edge case handling for missing data:** Early outputs sometimes included placeholder text like "No relevant datasets" in empty cells instead of true empty strings. This required explicit instruction in the prompt to leave cells blank and validation in the CSV conversion function.

### Insights Gained

**Structured prompting scales better than few-shot examples:** Given the complexity of formatting rules, providing the complete 33-row template in the prompt proved more effective than showing 2-3 example rows.

**Hard constraints > soft instructions:** Combining JSON schema enforcement with prompt instructions created redundant safeguards that significantly improved reliability.

**Domain knowledge is critical:** Understanding the difference between Earth observation measurements and climate projections was essential for prompt design. This suggests that effective AI tools for specialized domains require subject matter expertise in the prompt engineering process.

---

## 🚀 Next Steps

### Immediate Improvements

**1. Extend sector coverage**

Currently limited to Software & IT Services (33 metrics). Expanding to additional SASB sectors would require:
- Creating sector-specific prompts with new metric templates
- Testing across different environmental, social, and governance focus areas
- Validating that relevance categories remain appropriate for diverse metric types

**2. Add automated unit compatibility validation**

Post-process CSV outputs to verify that datasets in "Direct Measurement" categories actually contain variables measured in the metric's specified unit (e.g., Gigajoules for energy, cubic meters for water). This could flag potential mismatches for manual review.

**3. Implement catalog caching**

For frequently used catalogs like Planetary Computer, implement local caching to:
- Reduce API calls and latency
- Enable offline testing
- Support diff-based updates when catalogs are refreshed

### Long-term Enhancements

**4. Improve scalability for very large catalogs**

Explore strategies for handling 1000+ collection catalogs:
- Implement streaming or batch processing
- Use embedding-based semantic search to pre-filter relevant datasets
- Consider chunking strategies that preserve context

**5. Integration with ESG reporting platforms**

Build connectors to common ESG software:
- Export directly to CDP, GRI, or SASB reporting templates
- Create dashboards showing dataset coverage across all metrics
- Enable automated updates when new satellite datasets become available

**6. Add human-in-the-loop validation workflows**

For production use, implement:
- Confidence scoring for each dataset match
- Flagging of borderline categorizations for expert review
- Feedback loops to improve prompt based on user corrections

**7. Explore fine-tuning for ESG domain**

If sufficient training data becomes available (validated mapping tables), explore fine-tuning smaller models specifically for ESG data mapping to reduce API costs and latency.

---

## 📝 License

This project is intended for **internal, academic, or research use** as part of the Break Through Tech AI Studio program. The code and methodology are proprietary to International Elite Capital and the project team.

For inquiries about commercial use or licensing, please contact the project sponsors at International Elite Capital.

---

## 🙏 Acknowledgements

We would like to thank:

- **Annabelle Zhange** and **Scarlett Lee** - Challenge Advisors from International Elite Capital who provided domain expertise on ESG reporting and SASB standards
- **Yin Su** - AI Coach who guided our technical implementation and prompt engineering strategy
- **Break Through Tech AI Program** - For creating the AI Studio opportunity and providing the infrastructure for this collaboration
- **The STAC community** - For maintaining open geospatial data catalogs that made this project possible

Special thanks to International Elite Capital for sponsoring this project and providing real-world context for ESG data challenges in investment analysis.