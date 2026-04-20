"""
=============================================================================
HCRIS Hospital Cost Report Extractor — CMS Form 2552-10
=============================================================================
This script extracts key financial variables from the CMS Healthcare Cost
Report Information System (HCRIS) for Hospital form CMS-2552-10.

HOW TO GET THE DATA FILES (do this before running the script):
--------------------------------------------------------------
1. Go to: https://www.cms.gov/data-research/statistics-trends-and-reports/
           cost-reports/cost-reports-fiscal-year
2. On that page, find the table. Look for rows where "Facility Type" says
   "Hospital-2010". Click the year link (e.g. "2015") to download a ZIP.
3. Save each ZIP into a folder called "hcris_zips/" in the same directory
   as this script. Name them clearly, e.g.:
       hcris_zips/hosp10_2011.zip
       hcris_zips/hosp10_2012.zip
       ... etc.
   (The exact filename doesn't matter — the script searches by year.)

Alternatively, the script will also try to download them automatically.
If that fails (e.g. due to a firewall), use the manual steps above.

Variables extracted:
  - Total operating costs
  - Net patient revenue
  - Total charges
  - Medicare charges & payments
  - Medicaid charges & payments
  - Total discharges (used to compute cost per discharge)

Derived variables computed:
  - cost_per_discharge = total_operating_costs / total_discharges

Output: cost_report_dataset/hcris_YYYY.csv per year + cost_report_dataset/hcris_combined.csv

Requirements (install once):
  pip install pandas requests
=============================================================================
"""

import os
import zipfile
import requests
import pandas as pd
from io import BytesIO


# =============================================================================
# SECTION 1: YOUR SETTINGS — edit these
# =============================================================================

START_YEAR = 2011  # First fiscal year to pull
END_YEAR = 2019  # Last fiscal year to pull (use 2019 for pre-2020)

# Folder where output CSVs will be saved
OUTPUT_DIR = "cost_report_dataset"

# Folder where you manually save downloaded ZIPs (if auto-download fails)
ZIP_DIR = "hcris_zips"

# Create folders if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ZIP_DIR, exist_ok=True)


# =============================================================================
# SECTION 2: DOWNLOAD URL PATTERNS
# =============================================================================
#
# CMS hosts the files at this base URL. The exact filename varies by year
# (CMS sometimes renames files). We try multiple patterns per year.


def get_download_urls(year):
    """Returns a list of URLs to try for a given year, in order."""
    return [
        # Pattern 1: most common current naming
        f"https://www.cms.gov/files/zip/hospital-2552-10-cost-report-{year}-form.zip",
        # Pattern 2: alternate short name
        f"https://www.cms.gov/files/zip/hospital-2552-10-{year}.zip",
        # Pattern 3: older style
        f"https://www.cms.gov/Research-Statistics-Data-and-Systems/"
        f"Downloadable-Public-Use-Files/Cost-Reports/Downloads/"
        f"hospital2552-10-{year}.zip",
    ]


# =============================================================================
# SECTION 3: VARIABLE DEFINITIONS
# =============================================================================
#
# HCRIS stores data in a "long" format. Each row in the Numeric (NMRC) file
# is a single data point, identified by three coordinates:
#   WKSHT_CD  = worksheet code   (which form worksheet)
#   LINE_NUM  = line number      (zero-padded 5-digit string)
#   CLMN_NUM  = column number    (zero-padded 5-digit string)
#
# Zero-padding examples:
#   Line 3  -> "00300"     Line 14 -> "01400"
#   Col  1  -> "00100"     Col  6  -> "00600"
#
# Source references:
#   - CMS Provider Reimbursement Manual Part 2, Chapter 40
#   - RAND Hospital Data docs: https://www.hospitaldatasets.org
#   - ResDAC guide: https://resdac.org/articles/medicare-cost-report-data-structure
#
# FORMAT: "variable_name": (worksheet_code, line_num_padded, col_num_padded)
#
VARIABLES = {
    #  Variable name            Worksheet   Line    Column
    "total_operating_costs": ("G300000", "00300", "00100"),  # G-3, Line 3, Col 1
    "net_patient_revenue": ("G300000", "00400", "00100"),  # G-3, Line 4, Col 1
    "total_charges": ("S300001", "01400", "00300"),  # S-3 Pt I, Line 14, Col 3
    "medicare_charges": ("S300001", "01400", "00400"),  # S-3 Pt I, Line 14, Col 4
    "medicare_payments": ("E00A18A", "06200", "00100"),  # E Pt A, Line 62, Col 1
    "medicaid_charges": ("S300001", "01400", "00600"),  # S-3 Pt I, Line 14, Col 6
    "medicaid_payments": ("S300001", "01400", "00700"),  # S-3 Pt I, Line 14, Col 7
    "total_discharges": ("S300001", "01400", "01500"),  # S-3 Pt I, Line 14, Col 15
}

# NOTE: If some variables return all NaN, the worksheet codes above may
# not exactly match those in your downloaded files. Use the diagnose_worksheets()
# function at the bottom of this script to find the correct codes.


# =============================================================================
# SECTION 4: CORE FUNCTIONS
# =============================================================================


def find_local_zip(year):
    """
    Looks for a manually downloaded ZIP in ZIP_DIR containing the year in
    its filename (e.g. hosp10_2015.zip). Returns the path if found.
    """
    for fname in os.listdir(ZIP_DIR):
        if str(year) in fname and fname.endswith(".zip"):
            path = os.path.join(ZIP_DIR, fname)
            print(f"  Found local ZIP: {path}")
            return path
    return None


def download_zip(year):
    """
    Tries multiple URL patterns to download the ZIP for a given year.
    Returns a ZipFile object on success, or None on failure.
    """
    for url in get_download_urls(year):
        print(f"  Trying: {url}")
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200:
                print(f"  Download successful.")
                return zipfile.ZipFile(BytesIO(resp.content))
            else:
                print(f"  HTTP {resp.status_code} — trying next URL...")
        except requests.exceptions.RequestException as e:
            print(f"  Connection error ({e}) — trying next URL...")
    return None


def open_zip_for_year(year):
    """
    Opens a ZIP for a given year. Tries:
      1. Local manually-downloaded file in ZIP_DIR
      2. Auto-download from CMS
    Returns a ZipFile object, or None if both fail.
    """
    # Check for local file first
    local_path = find_local_zip(year)
    if local_path:
        return zipfile.ZipFile(local_path)

    # Try auto-download
    print(f"  No local file found. Attempting auto-download...")
    zf = download_zip(year)
    if zf:
        return zf

    # Both failed — give the user clear instructions
    print(f"\n  *** ACTION REQUIRED for year {year} ***")
    print(f"  Auto-download failed. Please manually download the file:")
    print(
        f"  1. Visit: https://www.cms.gov/data-research/statistics-trends-and-reports/cost-reports/cost-reports-fiscal-year"
    )
    print(f"  2. Find the 'Hospital-2010' row for year {year} and click to download")
    print(f"  3. Save the ZIP as: {ZIP_DIR}/hosp10_{year}.zip")
    print(f"  4. Re-run this script\n")
    return None


def find_file_in_zip(zf, keyword):
    """Finds a file in the ZIP whose name contains the given keyword."""
    for name in zf.namelist():
        if keyword.lower() in name.lower():
            return name
    return None


def load_report_file(zf):
    """
    Loads the RPT file (one row per hospital).
    Contains the hospital's CCN (PRVDR_NUM) and other identifiers.
    """
    rpt_file = find_file_in_zip(zf, "rpt")
    if not rpt_file:
        print("  ERROR: RPT file not found in ZIP.")
        return None

    # Column names from the HCRIS data model — the raw file has no header row.
    col_names = [
        "RPT_REC_NUM",
        "PRVDR_CTRL_TYPE_CD",
        "PRVDR_NUM",
        "NPI",
        "RPT_STUS_CD",
        "FY_BGN_DT",
        "FY_END_DT",
        "PROC_DT",
        "INITL_RPT_SW",
        "LAST_RPT_SW",
        "TRNSMTL_NUM",
        "FI_NUM",
        "ADC_NUM",
        "FI_CREAT_DT",
        "UTIL_CD",
        "NPR_DT",
        "SPEC_IND",
        "FI_RCPT_DT",
    ]

    with zf.open(rpt_file) as f:
        rpt = pd.read_csv(f, header=None, names=col_names, dtype=str, low_memory=False)

    print(f"  RPT loaded: {len(rpt):,} hospitals.")
    return rpt


def load_numeric_file(zf):
    """
    Loads the NMRC file (large long-format file with all numeric data).
    Each row = one value, for one worksheet cell, for one hospital.
    """
    nmrc_file = find_file_in_zip(zf, "nmrc")
    if not nmrc_file:
        print("  ERROR: NMRC file not found in ZIP.")
        return None

    col_names = ["RPT_REC_NUM", "WKSHT_CD", "LINE_NUM", "CLMN_NUM", "ITM_VAL_NUM"]

    print("  Loading NMRC file (this is large and may take 1-3 minutes)...")
    with zf.open(nmrc_file) as f:
        nmrc = pd.read_csv(f, header=None, names=col_names, dtype=str, low_memory=False)

    # Convert value to float; strip whitespace from lookup columns
    nmrc["ITM_VAL_NUM"] = pd.to_numeric(nmrc["ITM_VAL_NUM"], errors="coerce")
    for col in ["WKSHT_CD", "LINE_NUM", "CLMN_NUM"]:
        nmrc[col] = nmrc[col].str.strip()

    print(f"  NMRC loaded: {len(nmrc):,} data points.")
    return nmrc


def extract_variables(nmrc, rpt, year):
    """
    For each variable defined in VARIABLES, finds its value in the NMRC
    file and merges it onto the hospital roster from the RPT file.
    Returns a wide DataFrame — one row per hospital.
    """
    print("  Extracting variables...")

    hospitals = rpt[
        [
            "RPT_REC_NUM",
            "PRVDR_NUM",
            "NPI",
            "FY_BGN_DT",
            "FY_END_DT",
            "PRVDR_CTRL_TYPE_CD",
        ]
    ].copy()

    found_any = False
    for var_name, (wksht, line, col) in VARIABLES.items():
        mask = (
            (nmrc["WKSHT_CD"] == wksht)
            & (nmrc["LINE_NUM"] == line)
            & (nmrc["CLMN_NUM"] == col)
        )
        subset = nmrc.loc[mask, ["RPT_REC_NUM", "ITM_VAL_NUM"]].copy()
        subset = subset.rename(columns={"ITM_VAL_NUM": var_name})
        subset = subset.drop_duplicates(subset="RPT_REC_NUM")

        n_found = subset[var_name].notna().sum()
        print(f"    {var_name}: {n_found:,} non-null values found")
        if n_found > 0:
            found_any = True

        hospitals = hospitals.merge(subset, on="RPT_REC_NUM", how="left")

    if not found_any:
        print("\n  WARNING: All variables returned 0 matches!")
        print("  The worksheet codes in VARIABLES may not match this year's data.")
        print("  Run diagnose_worksheets() to find the correct codes.")

    # -------------------------------------------------------------------------
    # Compute derived variable: cost per discharge
    # This normalizes total operating costs by hospital size/volume, making
    # costs comparable across large and small hospitals.
    # Rows where total_discharges is 0 or missing are set to NaN to avoid
    # division errors (e.g. long-term care units with no discharges reported).
    # -------------------------------------------------------------------------
    valid_discharges = hospitals["total_discharges"].replace(0, pd.NA)
    hospitals["cost_per_discharge"] = (
        hospitals["total_operating_costs"] / valid_discharges
    )

    n_valid = hospitals["cost_per_discharge"].notna().sum()
    print(f"    cost_per_discharge: {n_valid:,} non-null values computed")

    hospitals.insert(0, "fiscal_year", year)
    return hospitals


# =============================================================================
# SECTION 5: DIAGNOSTIC — use this if variables are all NaN
# =============================================================================


def diagnose_worksheets(year):
    """
    Prints the most common worksheet codes found in a year's NMRC file.
    Use this to check if the WKSHT_CD values in VARIABLES match the data.

    HOW TO USE:
      1. At the bottom of this script, uncomment: diagnose_worksheets(2015)
      2. Run the script: python hcris_extract.py
      3. Compare printed codes to the WKSHT_CD values in VARIABLES above
      4. Update VARIABLES if they differ
    """
    print(f"\n--- DIAGNOSTIC for {year} ---")
    zf = open_zip_for_year(year)
    if not zf:
        return
    nmrc = load_numeric_file(zf)
    if nmrc is None:
        return

    print("\nTop 30 worksheet codes (WKSHT_CD) in the NMRC file:")
    print(nmrc["WKSHT_CD"].value_counts().head(30).to_string())

    print("\nCodes containing 'G3', 'S3', or 'E0':")
    for pattern in ["G3", "S3", "E0"]:
        hits = nmrc["WKSHT_CD"][
            nmrc["WKSHT_CD"].str.contains(pattern, na=False)
        ].unique()
        print(f"  '{pattern}': {list(hits[:8])}")

    print("\nUpdate the WKSHT_CD values in VARIABLES to match what you see above.")


# =============================================================================
# SECTION 6: MAIN
# =============================================================================


def main():
    print("=" * 60)
    print("HCRIS CMS-2552-10 Hospital Cost Report Extractor")
    print(f"Fiscal years: {START_YEAR} to {END_YEAR}")
    print("=" * 60)

    all_years = []

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n[Year: {year}]")

        zf = open_zip_for_year(year)
        if zf is None:
            print(f"  Skipping {year}.")
            continue

        rpt = load_report_file(zf)
        nmrc = load_numeric_file(zf)
        if rpt is None or nmrc is None:
            continue

        year_df = extract_variables(nmrc, rpt, year)

        out_path = os.path.join(OUTPUT_DIR, f"hcris_{year}.csv")
        year_df.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")

        all_years.append(year_df)
        zf.close()

    if all_years:
        combined = pd.concat(all_years, ignore_index=True)
        combined_path = os.path.join(OUTPUT_DIR, "hcris_combined.csv")
        combined.to_csv(combined_path, index=False)

        print(f"\n{'=' * 60}")
        print(f"Complete! Combined file saved: {combined_path}")
        print(f"Total rows: {len(combined):,}")
        print(f"Columns: {list(combined.columns)}")
        print("\nSample (first 3 rows):")
        print(combined.head(3).to_string())
    else:
        print("\nNo data extracted.")
        print("Please download the ZIP files manually into hcris_zips/ and re-run.")


if __name__ == "__main__":
    main()

    # --- Uncomment this line to run diagnostics if variables are all NaN ---
    # diagnose_worksheets(2015)


# =============================================================================
# WORKING WITH THE OUTPUT
# =============================================================================
#
#   import pandas as pd
#
#   df = pd.read_csv("cost_report_dataset/hcris_combined.csv")
#
#   # Count hospitals per year
#   print(df.groupby("fiscal_year")["PRVDR_NUM"].count())
#
#   # Look up a specific hospital by CCN
#   print(df[df["PRVDR_NUM"] == "050625"])
#
#   # Average cost per discharge by year (your main normalized outcome variable)
#   print(df.groupby("fiscal_year")["cost_per_discharge"].mean())
#
#   # Total discharges — useful to verify the normalization looks right
#   print(df.groupby("fiscal_year")["total_discharges"].describe())
#
#   # Average operating costs by year
#   print(df.groupby("fiscal_year")["total_operating_costs"].mean())
#
#   # Filter by ownership type (PRVDR_CTRL_TYPE_CD):
#   #   1 = Voluntary Non-Profit
#   #   2 = For-Profit
#   #   3 = Government
#   nonprofits = df[df["PRVDR_CTRL_TYPE_CD"] == "1"]
#
