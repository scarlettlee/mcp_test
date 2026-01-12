# team1b/joey/test_my_matching_tools.py

import sys
import os
import json


def slim_catalog(catalog_data, max_desc_len=800, max_collections=None):
    cols = catalog_data.get("collections", [])
    if max_collections is not None:
        cols = cols[:max_collections]

    slim_cols = []
    for col in cols:
        desc = col.get("description", "") or ""
        slim_cols.append({
            "id": col.get("id"),
            "title": col.get("title"),
            "description": desc[:max_desc_len],
            "keywords": col.get("keywords", []),
            "providers": [p.get("name") for p in col.get("providers", [])],
        })
    return {"collections": slim_cols}


# ----------------------------------------------------------------------
# Path setup
# ----------------------------------------------------------------------
current_dir = os.path.dirname(__file__)
team_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(team_dir)

sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)

from mcp_framework import MCPServer
from my_matching_tools import esg_data_mapping_tool


DEFAULT_MODEL = "gpt-5.1"          # OpenAI GPT‑5.1 model id
DEFAULT_PROVIDER = "openai"        # use Anthropic by setting provider="anthropic" in calls


# ----------------------------------------------------------------------
# Helper: pretty-print a sample of the CSV output
# ----------------------------------------------------------------------
def preview_mapping_output(mapping_info, num_rows=3):
    """Print a small sample of the generated CSV for quick inspection."""
    import csv

    print("\n" + "=" * 60)
    print(f"SAMPLE OUTPUT (First {num_rows} Metrics)")
    print("=" * 60)

    with open(mapping_info["output_file"], "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            if i >= num_rows:
                break
            print(f"\n{i + 1}. {row['Metric']}")
            print(f"   Category: {row['Category']}")
            print(f"   Code: {row['Code']}")
            if row.get("Direct Measurement"):
                dm = row["Direct Measurement"][:100]
                print(f"   Direct Measurement: {dm}...")
            if row.get("Risk Assessment"):
                ra = row["Risk Assessment"][:100]
                print(f"   Risk Assessment: {ra}...")


# ----------------------------------------------------------------------
# Test 1: fedeo.ceos.org only
# ----------------------------------------------------------------------
def test_with_fedeo_file():
    """Test ESG mapping tool with the CEOS fedeo STAC catalog JSON file."""

    print("=" * 60)
    print("Testing ESG Mapping Tool with fedeo.ceos.org (single catalog)")
    print("=" * 60)

    server = MCPServer()
    server.register_tool("esg_mapping", esg_data_mapping_tool)
    print("✓ Tool registered successfully\n")

    catalog_file = os.path.join(current_dir, "stac-tags-fedeo.ceos.org.json")

    if not os.path.exists(catalog_file):
        print(f"✗ ERROR: File not found at {catalog_file}")
        print(f"Please place stac-tags-fedeo.ceos.org.json in: {current_dir}")
        return

    # Load and preview catalog
    with open(catalog_file, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    num_collections = len(catalog_data.get("collections", []))
    print(f"Loaded fedeo.ceos.org catalog: {num_collections} collections\n")

    if "collections" in catalog_data and num_collections > 0:
        print("Sample collections:")
        for i, col in enumerate(catalog_data["collections"][:5]):
            col_id = col.get("id", "unknown")
            col_title = col.get("title", "No title")
            print(f"  • {col_id}")
            print(f"    {col_title[:80]}...")
        if num_collections > 5:
            print(f"\n  ... and {num_collections - 5} more collections\n")

    print("Calling ESG mapping tool with fedeo catalog...")
    print("(This will take a moment - the LLM is processing the catalog)\n")

    try:
        result = server.call_tool(
            "esg_mapping",
            {
                "catalog_data": catalog_file,  # pass file path
                "provider": DEFAULT_PROVIDER,
                "model": DEFAULT_MODEL,
                "output_file": "fedeo_esg_mapping_output_gpt5_1.csv",
            },
        )

        print(result["result"])
        print()

        mapping_info = server.get_context("last_esg_mapping")
        if mapping_info:
            print("=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)
            print(f"✓ Output file: {mapping_info['output_file']}")
            print(f"✓ Row count: {mapping_info['row_count']}")

            if mapping_info["row_count"] == 33:
                print("✓ SUCCESS: Exactly 33 rows generated!")
            else:
                print(
                    f"✗ WARNING: Expected 33 rows, got {mapping_info['row_count']}"
                )

            preview_mapping_output(mapping_info, num_rows=3)

            print("\n" + "=" * 60)
            print(f"✓ Full results saved to: {mapping_info['output_file']}")
            print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


# ----------------------------------------------------------------------
# Test 2: fedeo.ceos.org + planetarycomputer.microsoft.com together
# ----------------------------------------------------------------------
def test_with_fedeo_and_pc_files():
    """
    Test ESG mapping tool with both fedeo.ceos.org and
    planetarycomputer.microsoft.com STAC catalog JSON files,
    producing a single 33-row CSV.
    """

    print("=" * 60)
    print("Testing ESG Mapping Tool with fedeo.ceos.org + planetarycomputer.microsoft.com")
    print("=" * 60)

    server = MCPServer()
    server.register_tool("esg_mapping", esg_data_mapping_tool)
    print("✓ Tool registered successfully\n")

    fedeo_file = os.path.join(current_dir, "stac-tags-fedeo.ceos.org.json")
    pc_file = os.path.join(
        current_dir, "stac-tags-planetarycomputer.microsoft.com.json"
    )

    # Verify both files exist
    missing = False
    for path in [fedeo_file, pc_file]:
        if not os.path.exists(path):
            print(f"✗ ERROR: File not found at {path}")
            missing = True
    if missing:
        print("\nPlease ensure both JSON files are present in:", current_dir)
        return

    # Load both catalogs
    with open(fedeo_file, "r", encoding="utf-8") as f:
        fedeo_data = json.load(f)
    with open(pc_file, "r", encoding="utf-8") as f:
        pc_data = json.load(f)

    num_fedeo = len(fedeo_data.get("collections", []))
    num_pc = len(pc_data.get("collections", []))
    print(f"Loaded fedeo.ceos.org catalog: {num_fedeo} collections")
    print(
        f"Loaded planetarycomputer.microsoft.com catalog: {num_pc} collections\n"
    )

    # Simple preview
    if "collections" in pc_data and num_pc > 0:
        print("Sample Planetary Computer collections:")
        for i, col in enumerate(pc_data["collections"][:5]):
            col_id = col.get("id", "unknown")
            col_title = col.get("title", "No title")
            print(f"  • {col_id}")
            print(f"    {col_title[:80]}...")
        if num_pc > 5:
            print(f"\n  ... and {num_pc - 5} more collections\n")

    fedeo_slim = slim_catalog(fedeo_data, max_desc_len=800)
    pc_slim = slim_catalog(pc_data, max_desc_len=800)

    combined_catalogs = {
        "catalogs": [
            {
                "filename": "stac-tags-fedeo.ceos.org.json",
                "catalog_name": "fedeo.ceos.org",
                "data": fedeo_slim,
            },
            {
                "filename": "stac-tags-planetarycomputer.microsoft.com.json",
                "catalog_name": "planetarycomputer.microsoft.com",
                "data": pc_slim,
            },
        ]
    }


    print("Calling ESG mapping tool with both catalogs combined...")
    print("(This will take a moment - the LLM is processing both catalogs)\n")

    try:
        result = server.call_tool(
            "esg_mapping",
            {
                "catalog_data": combined_catalogs,  # pass dict with both catalogs
                "provider": DEFAULT_PROVIDER,
                "model": DEFAULT_MODEL,
                "output_file": "fedeo_pc_esg_mapping_output_gpt5_1.csv",
            },
        )

        print(result["result"])
        print()

        mapping_info = server.get_context("last_esg_mapping")
        if mapping_info:
            print("=" * 60)
            print("VALIDATION RESULTS")
            print("=" * 60)
            print(f"✓ Output file: {mapping_info['output_file']}")
            print(f"✓ Row count: {mapping_info['row_count']}")

            if mapping_info["row_count"] == 33:
                print("✓ SUCCESS: Exactly 33 rows generated!")
            else:
                print(
                    f"✗ WARNING: Expected 33 rows, got {mapping_info['row_count']}"
                )

            preview_mapping_output(mapping_info, num_rows=3)

            print("\n" + "=" * 60)
            print(f"✓ Full results saved to: {mapping_info['output_file']}")
            print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()


# ----------------------------------------------------------------------
# Run tests directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # You can comment/uncomment depending on what you want to run
    # test_with_fedeo_file()
    # print("\n\n")
    test_with_fedeo_and_pc_files()
