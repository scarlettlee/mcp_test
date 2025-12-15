# ESG Risk Assessment Platform for Fintech SMBs (International Elite Capital)

**An AI-powered tool for International Elite Capital to help small and medium-sized businesses assess Environmental, Social, and Governance (ESG) risks using geospatial data and SASB standards.**

---
### **Team Members**

| Name | GitHub Handle | Contribution |
|------------------|---------------|--------------------------------------------------------------------------|
| Lamiah Khan | [@khanlamiah019](https://github.com/khanlamiah019) | STAC data analysis, MCP tool development, flood hazard visualization |
| Karina Lam | [@klam118](https://github.com/klam118) | MCP tool development, collection accessibility verification |
| Jessica Chen | [@jessicachen28](https://github.com/jessicachen28) | Data preprocessing, metadata export tools |
| Josh Perez-Molina | [@jpkidd02](https://github.com/jpkidd02) | Data processing |
| Victor Osunji | [@victorro7](https://github.com/victorro7) | ESG metrics mapping, model evaluation framework |

---
## **Project Highlights**

- **Developed 3 MCP tools** for geospatial data visualization covering flood hazards, water stress, energy infrastructure, climate data, and deforestation
- **Created interactive mapping platform** with STAC API integration enabling click-to-explore ESG risk data
- **Established systematic framework** for matching environmental datasets to SASB sustainability metrics across multiple industry sectors
- **Built STAC API Browser UI** to simplify navigation of complex geospatial data catalogs from AWS, Google Earth, NASA, and Microsoft
- **Demonstrated feasibility** of AI-powered ESG risk prediction for SMBs through working prototypes

---
## ‍**Setup and Installation**

### Installation Steps

1. **Clone the repository**
```bash
   git clone https://github.com/team1a/esg-risk-assessment.git
   cd esg-risk-assessment
```

2. **Install dependencies**
```bash
   pip install -r requirements.txt --break-system-packages
```

3. **Set up STAC API access**
   - Configure API endpoints in `config/stac_endpoints.json`
   - No API keys required for public catalogs

4. **Run the STAC API Browser**
```bash
   python src/stac_browser.py
```

5. **Launch interactive visualizations**
```bash
   python src/visualization_server.py
```
---

### Repository Structure
```text
├── src/                    # Source code for MCP tools and data processing
├── data/                   # STAC catalog metadata and processed datasets
├── notebooks/              # Jupyter notebooks for EDA and prototyping
├── visualizations/         # Interactive maps and data visualizations
├── docs/                   # Project documentation and SASB mapping tables
└── README.md
```

---
## ️ **Project Overview**

### Break Through Tech AI Studio Connection
This project was completed as part of the **Break Through Tech AI Studio program** in partnership with **International Elite Capital** (Fall 2024). The README serves as both project documentation and a professional portfolio artifact for our team.

### Host Company + Objective + Scope
**Host Company:** International Elite Capital  
**Objective:** Democratize ESG risk assessment for fintech SMBs by providing an accessible tool that uses **geospatial data** and **SASB-aligned standards** to identify, interpret, and communicate ESG risk signals.

**Scope:**
- Discover and normalize geospatial ESG-relevant datasets across STAC providers
- Validate dataset accessibility (public vs. restricted/auth required)
- Build a mapping framework from datasets → ESG categories → SASB-style metrics
- Prototype MCP tools and interactive maps for ESG risk exploration and reporting foundations

### Real-World Significance + Impact
SMBs often lack the time, expertise, and budget to perform ESG and climate risk assessments, creating barriers to:
- competing in ESG-aware markets
- accessing ESG-focused capital
- scaling into regions with higher ESG expectations
- communicating credible ESG risk narratives to investors/partners

This project reduces friction by centralizing dataset discovery and making risk signals interpretable through interactive, map-based UX.

---
## **Data Exploration**

### Dataset(s) Used (origin, format, size, type of data)

**Primary Data Sources (STAC Providers):**
1. **AWS STAC Catalog**
   - Size: 100+ collections (varies over time)
   - Format: JSON-based STAC
   - Focus: collection names, regional coverage, descriptions

2. **Google Earth Engine STAC**
   - Size: 50+ collections (varies over time)
   - Format: geospatial imagery with temporal metadata
   - Focus: dataset IDs, catalog links, coordinates/coverage indicators

3. **NASA STAC Catalog**
   - Size: 75+ collections (varies over time)
   - Format: climate and earth observation metadata
   - Focus: collection names, access info, temporal coverage

4. **Microsoft Planetary Computer**
   - Size: 40+ collections (varies over time)
   - Format: cloud-optimized geospatial catalogs + metadata
   - Focus: descriptions, titles, metadata completeness

**STAC Structure:** Catalog → Collections → Items

### Data exploration and preprocessing approaches

**Challenges and assumptions**
- Inconsistent metadata formats across STAC providers
- Nested JSON structures required flattening for analysis and export
- Some datasets require authentication or have restricted access
- Assumption: public STAC catalogs provide sufficient starting coverage for SMB ESG risk discovery
- Assumption: Software & IT Services SASB standard can serve as an initial mapping anchor for fintech-adjacent SMBs

**Preprocessing steps**
1. Extracted metadata from STAC API endpoints
2. Normalized collection descriptions and temporal ranges (when available)
3. Flattened JSON structures into exportable tables
4. Generated accessibility reports for each catalog/provider
5. Mapped collections to ESG risk categories and SASB-style metrics

### Insights from EDA
- **Geographic coverage gaps:** global datasets exist, but resolution and coverage density vary by region.
- **Temporal/spatial trade-offs:** higher temporal frequency often means lower spatial resolution.
- **Accessibility matters:** “relevant” datasets may not be usable if auth/restrictions block access.

### Visualizations

<img width="670" height="306" alt="STAC API Browser UI" src="https://github.com/user-attachments/assets/24bad1ea-7602-4b54-a14d-64dc20ffc200" />
*Figure 1: STAC API Browser showing collections from multiple providers. Users can explore collections, view metadata, and check accessibility status.*

<img width="1347" height="688" alt="Flood hazard visualization prototype" src="https://github.com/user-attachments/assets/31bfab7b-dc1a-47ca-936f-1ec24d7075f1" />
*Figure 2: Interactive flood hazard visualization prototype (Switzerland). Red zones indicate higher overland flow risk. Users can click to retrieve metadata and ESG application notes.*

---
## **Model Development**

### Technical Approach

**Architecture Overview:**

The project implements a modular pipeline consisting of:

1. **STAC Data Ingestion Layer**
   - Connects to multiple STAC API endpoints
   - Retrieves collection metadata and item catalogs
   - Handles pagination and rate limiting

2. **ESG Mapping Engine**
   - Uses Claude AI to analyze STAC collection descriptions
   - Matches geospatial datasets to SASB risk metrics
   - Generates structured mapping tables

3. **MCP Tool Framework**
   - Implements Model Context Protocol for standardized data access
   - Provides 3 specialized tools for different ESG risk categories
   - Enables interactive querying of geospatial data

4. **Visualization Layer**
   - Leaflet-based interactive maps
   - Real-time metadata retrieval on user interaction
   - Support for multiple overlay types (polygons, heatmaps, markers)

**Selected Methods Justification:**

- **STAC Standard**: Chosen for its widespread adoption in geospatial community and interoperability across data providers
- **MCP Tools**: Enables seamless integration with LLMs for natural language querying of complex geospatial data
- **Claude AI for Mapping**: Leverages advanced language understanding to interpret nuanced SASB risk descriptions
- **Interactive Maps**: Provides intuitive interface for non-technical SMB stakeholders

### Training Process

This project focuses on data infrastructure and tooling rather than traditional ML model training. The "training" process consisted of:

1. **Iterative Prompt Engineering** with Claude AI to refine SASB mapping accuracy
2. **Manual Validation** of 50+ collection-to-metric mappings by domain experts
3. **User Testing** of visualization interfaces with stakeholder feedback
4. **Performance Optimization** of STAC API queries for sub-second response times

---

## Code Highlights

### Key Files and Functions

**`src/stac_browser.py`**
- `load_catalogs()`: Fetches and caches STAC catalog metadata from configured endpoints
- `render_collection_cards()`: Generates interactive UI cards for each collection with accessibility badges
- Main entry point for exploring available geospatial datasets

**`src/mcp_tools/flood_risk.py`**
- `get_flood_coverage(lat, lon)`: Retrieves flood hazard data for specified coordinates
- `visualize_flood_zones(bbox)`: Renders interactive map with flood risk overlays
- Implements Switzerland overland flow dataset integration

**`src/mcp_tools/deforestation.py`**
- `track_forest_loss(region, start_date, end_date)`: Analyzes deforestation trends over time
- `generate_esg_report()`: Creates formatted ESG disclosure from forest data
- Uses Chelsa Climatologies and GEO BON datasets

**`src/mapping/sasb_matcher.py`**
- `match_to_sasb(collection_metadata)`: Uses Claude AI to map collections to SASB metrics
- `generate_mapping_table()`: Exports Excel tables with sector-specific ESG mappings
- Core engine for connecting geospatial data to business risk frameworks

**`src/visualization/interactive_map.py`**
- `create_base_map(center, zoom)`: Initializes Leaflet map with OpenStreetMap tiles
- `add_coverage_overlay(collection_id)`: Renders dataset geographic coverage as polygon
- `on_click_metadata(event)`: Displays collection details in popup on user interaction

**`notebooks/eda_stac_catalogs.ipynb`**
- Exploratory analysis of 250+ STAC collections
- Visualizations of temporal coverage and spatial resolution distributions
- Statistical analysis of metadata completeness across providers


### Feature selection / mapping strategy
- Inputs: STAC collection metadata (title, description, keywords, temporal coverage, spatial coverage)
- Mapping outputs: ESG risk category + SASB-style disclosure metric alignment
- Approach: prompt-based semantic mapping with iterative refinement + manual review on a subset

### Training / evaluation setup
- Iterative prompt engineering to improve mapping precision and reduce hallucinated fields
- Manual validation of 50+ mappings (spot checks + consistency checks)
- Performance iteration to improve STAC API responsiveness (caching, limiting heavy operations)

---
### **Results & Key Findings**

### 1) STAC Data Accessibility Report

| Provider | Collections Analyzed | Publicly Accessible | Requires Auth | Restricted |
|----------|---------------------|---------------------|---------------|------------|
| AWS | 112 | 78 (70%) | 24 (21%) | 10 (9%) |
| Google Earth | 53 | 51 (96%) | 2 (4%) | 0 (0%) |
| NASA | 68 | 45 (66%) | 18 (26%) | 5 (8%) |
| Microsoft | 41 | 38 (93%) | 3 (7%) | 0 (0%) |

**Key Finding:** A large portion of ESG-relevant datasets are publicly accessible, which supports low-cost adoption for SMB stakeholders.

### 2) SASB Mapping Coverage (examples)

- **Environmental Footprint of Hardware Infrastructure:** 15 datasets mapped to energy consumption / renewable energy metrics
- **Water Scarcity and Stress:** 8 datasets supporting drought risk and availability indicators
- **Climate Risk Exposure:** 12 datasets supporting anomaly and extreme-event indicators
- **Supply Chain Sustainability:** 6 datasets supporting deforestation / land-use change monitoring
- **Cybersecurity (qualitative):** framework identified for integrating non-geospatial sources


**Baseline Comparison:** Traditional manual ESG dataset discovery and documentation can take 10–20 hours per assessment. Our workflow reduces early-stage discovery and retrieval to minutes for supported indicators.

### Visual outputs

<img width="677" height="274" alt="Screenshot 2025-11-30 at 3 57 37 PM" src="https://github.com/user-attachments/assets/2a5c83fe-0f32-4d6b-b48c-25e4d5c4a0dc" />
*Table 1: Sample SASB mapping for Software & IT Services sector showing how geospatial datasets connect to specific disclosure metrics. Includes sector, topic, metric description, category (quantitative/qualitative), unit of measure, and SASB code.*

<img width="687" height="363" alt="Screenshot 2025-11-30 at 3 57 52 PM" src="https://github.com/user-attachments/assets/7f473a63-94ff-4b5b-8023-a89fba970322" />

*Figure 3: Interactive map of global energy infrastructure colored by fuel type and sized by capacity. Enables SMBs to assess proximity to fossil fuel vs. renewable energy sources for supply chain and location decisions.*

---

## Discussion and Reflection

### What Worked Well

**1. STAC API Integration**
The decision to build on STAC standards proved highly effective. The hierarchical catalog structure aligned naturally with ESG risk categorization, and widespread industry adoption ensured data availability. The API-first approach enabled rapid prototyping without managing large local datasets.

**2. Claude AI for SASB Mapping**
Using Claude AI to interpret SASB risk descriptions and match them to geospatial datasets dramatically accelerated what would otherwise be a months-long manual process. The LLM's ability to understand nuanced language in both SASB frameworks and dataset documentation was crucial.

**3. Interactive Visualizations**
The click-to-explore interface received positive feedback from stakeholders who found traditional ESG reports overwhelming. Seeing geographic risk data on an intuitive map made the information immediately actionable for non-technical decision-makers.

**4. Team Diversity**
Our multidisciplinary team (electrical engineering, CS, energy sector experience) brought complementary perspectives that enriched the solution. Regular collaboration with advisors from International Elite Capital and the BTT AI Studio program kept the work grounded in real business needs.

### Challenges and Limitations

**1. Dataset Fragmentation**
While we successfully analyzed 250+ STAC collections, geospatial data remains fragmented across providers with inconsistent metadata quality. Some critical ESG metrics (e.g., water consumption by facility) lack direct satellite-based datasets and require proxy indicators or third-party sources.

**2. Temporal Coverage Gaps**
Many high-value datasets have limited historical depth (e.g., ESA WorldCover only covers 2020-2021). This constrains trend analysis and long-term risk modeling, which are essential for investor-grade ESG assessments.

**3. Computational Constraints**
Processing large raster datasets in the browser proved challenging. We implemented bounding-box limitations and pre-computed coverage areas, but this restricts real-time analysis capabilities. A production system would need backend processing infrastructure.

**4. SASB Framework Complexity**
SASB defines 77 industry-specific standards with varying applicability. Our initial focus on Software & IT Services provided depth but limited breadth. Expanding to other fintech-relevant sectors (e.g., Commercial Banks, Insurance) requires significant additional mapping work.

**5. Validation Difficulty**
Without ground-truth ESG assessment data from real SMBs, we couldn't rigorously validate our risk scores. We relied on expert judgment and comparison to known high-risk regions (e.g., drought-prone areas, flood zones) for sanity checks.

### Why These Approaches

**STAC Over Proprietary APIs**: We chose STAC because it's vendor-neutral and increasingly adopted by government agencies and research institutions. This ensures long-term data availability and avoids lock-in to commercial providers.

**MCP Tools Over Traditional APIs**: Model Context Protocol enables natural language interaction with geospatial data, which is essential for making ESG assessment accessible to SMB owners without GIS expertise. This aligns with the project's democratization goals.

**Browser-Based Visualization Over Desktop GIS**: Web-based tools lower adoption barriers. SMBs don't need to install specialized software or have GIS training, making the solution more scalable.

**Claude AI Over Rules-Based Matching**: The complexity and ambiguity in SASB descriptions made deterministic matching infeasible. Claude's semantic understanding outperformed keyword-based approaches in pilot tests.

## **Next Steps**

- Expand MCP tool coverage to include **social** and **governance** indicators via non-geospatial sources (labor practices, governance records, policy databases).
- Add backend processing for large raster workflows (server-side tiling, async jobs, caching).
- Improve user experience with SMB profiles (industry + location defaults, saved reports, trend tracking).
- Validate risk scoring with real SMB partner data and benchmark against professional ESG rating approaches.
- Extend mapping to additional SASB industries relevant to fintech (e.g., commercial banks, insurance, payments).

---
## **License**
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.


### Third-Party Data Sources
This project uses publicly available geospatial data from:
- AWS Open Data Registry (various licenses per dataset)
- Google Earth Engine (Google Earth Engine Terms of Service)
- NASA Earth Science Data (NASA Open Data Policy)
- Microsoft Planetary Computer (specific licenses per collection)

Users are responsible for complying with the terms of use for any datasets accessed through this tool. Please review individual dataset licenses before commercial use.

---
## **References** 

- STAC Specification: https://stacspec.org/
- Microsoft Planetary Computer: https://planetarycomputer.microsoft.com/
- NASA Earthdata: https://earthdata.nasa.gov/
- AWS Open Data Registry: https://registry.opendata.aws/
- Google Earth Engine: https://earthengine.google.com/
- SASB Standards (IFRS Foundation): https://www.ifrs.org/issued-standards/sasb-standards/

---
## **Acknowledgements** 

- **Annabelle Zhang** (COO, International Elite Capital) - For defining the business challenge and providing domain expertise on SMB financing
- **Yin Su** (AI Studio Coach, MSCS at Georgia Tech) - For technical guidance on geospatial data processing and model architecture
- **Scarlett Li** (Technical Manager, ESG Section) - For subject matter expertise on SASB standards and ESG reporting requirements
- **Break Through Tech AI Studio Team** - Angelina Collazo-Young, Tyla Daniels, Bradford Smith, Emily Ghazi, Erika Bramwell, Caroline Virani - For program coordination and support

Special thanks to the open-source geospatial community for maintaining the STAC ecosystem and public data catalogs.
