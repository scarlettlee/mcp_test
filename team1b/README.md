# International Elite Capital Team 1B: AI-Powered ESG Data Mapping Tool

---

### 👥 **Team Members**

| Name             | GitHub Handle | Contribution                                                             |
|------------------|---------------|--------------------------------------------------------------------------|
| Joey Zhou        | @joeyzhouu    | Tool design and implementation, prompt engineering, ESG logic, testing   |
| Furkan Ay        | @FurkanBeratAy| Tool design and implementation, prompt engineering, ESG logic, testing   |
| Neeti Ingle      | @neetii       | Tool design and implementation, prompt engineering, ESG logic, testing   |
| Ashleigh Wong    | @AshleighWong | Tool design and implementation, prompt engineering, ESG logic, testing   |

---

## 🎯 **Project Highlights**

- Built an AI-driven mapping tool that aligns geospatial datasets to `33 SASB ESG metrics` with strict formatting and compliance rules.
- Designed a robust `system prompt` that enforces metric relevance, dataset categorization, and audit-ready output.
- Supported both `OpenAI` and `Anthropic` models with structured JSON outputs and CSV conversion.
- Produced a consolidated ESG mapping table suitable for `Excel, auditing, and sustainability reporting` workflows.

---

## 👩🏽‍💻 **Setup and Installation**

### 1. Clone the repository
```bash
git clone https://github.com/scarlettlee/mcp_test.git
cd team1B
```

### 2. Install dependencies
```bash
pip install openai anthropic
```
Python 3.9+ is required.

### 3. Configure API keys
Create a config.json file at the project root:
```bash
{
  "openai": "YOUR_OPENAI_API_KEY",
  "anthropic": "YOUR_ANTHROPIC_API_KEY"
}
```
The tool automatically selects the correct key based on the chosen provider.
---

## 🏗️ **Project Overview**

This project was developed as part of the Break Through Tech AI Program – AI Studio.

**Objective:**
Enable ESG analysts and sustainability teams to systematically map Earth observation and environmental datasets to SASB ESG metrics, prioritizing what is actually being measured rather than proxy or projected data.

**Scope:**
- Software & IT Services sector
- 33 SASB-defined ESG metrics
- Multi-catalog geospatial dataset support
- Strict relevance categorization and formatting rules

**Real-world impact:**
This tool helps bridge the gap between Earth observation data and corporate ESG disclosure, improving transparency, auditability, and consistency in sustainability reporting.

---

## 📊 **Data Exploration**

- Data sources: STAC catalog JSON files (e.g., `fedeo.ceos.org`, `planetarycomputer.microsoft.com`)
- Data type: Geospatial metadata describing satellite, climate, and environmental datasets
- Preprocessing: Description truncation and collection filtering for large catalogs
- Key challenges: Enforcing consistent dataset numbering across catalogs, Maintaining exact compliance with SASB metric definitions

---

## 🧠 **Model Development**

### Models Used
- OpenAI GPT models  
- Anthropic Claude models  

### Approach
- Prompt-driven structured reasoning with enforced JSON schema output  
- Dataset-to-metric matching based on **measurement validity**, not keyword similarity  

### Key Design Choices
- Exactly **33 rows** returned (no more, no less)  
- Each dataset assigned to **only one relevance category**  
- Climate projections restricted to **risk assessment** or **trend analysis**  

---

## 📈 **Results & Key Findings**

- Successfully generated **33-row ESG mapping tables** across:
  - Single-catalog inputs  
  - Multi-catalog combined inputs  

### Output CSV Characteristics
- Pass structural validation  
- Preserve all SASB-required fields  
- Leave cells blank where no valid dataset applies  

- Demonstrated that LLMs can reliably perform **structured ESG reasoning** when guided by strict prompt constraints  

---

## 🚀 **Next Steps**

- Extend support to additional SASB sectors  
- Add automated validation checks for dataset unit compatibility  
- Improve scalability for very large catalogs  
- Explore integration with ESG reporting platforms and dashboards  

---

## 📝 **License**

This project is intended for **internal, academic, or research use** unless otherwise specified.

---

## 🙏 **Acknowledgements** (Optional but encouraged)

Thank your Challenge Advisors, Annabelle Zhange and Scarlett Lee, AI coach Yin Su, and others who supported our project.
