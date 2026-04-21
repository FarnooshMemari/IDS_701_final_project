# IDS 701 Final Project: Hospital Mergers and Cost Outcomes

This project analyzes whether hospital mergers are associated with changes in hospital cost outcomes using a panel dataset and a staggered Difference-in-Differences (DiD) design.

## Project Goal

Estimate the relationship between merger exposure and hospital cost per discharge by:

- extracting and preparing CMS HCRIS hospital cost report data,
- merging it with hospital merger data,
- running exploratory diagnostics and trend checks,
- estimating a staggered DiD model with fixed effects.

## Repository Structure

```text
IDS_701_final_project/
├── 00_documentation/
├── 01_data/
│   ├── hospital_merger_dataset.csv
│   ├── hospital_analysis.csv
│   └── cost_report_dataset/
│       ├── hcris_2011.csv ... hcris_2019.csv
│       ├── hcris_combined.csv
│       ├── detected_ownership_changes.csv
│       └── detected_disappearances.csv
├── 02_data_preparation/
│   ├── 01_hospital_cost_report_extract.py
│   └── 02_Exploratory_data_analysis.ipynb
├── 03_main_analysis/
│   ├── 01_parallel_trend_check.ipynb
│   └── 02_staggered_did.ipynb
├── 04_outputs/
│   └── figures/
└── requirements.txt
```

## Data

### 1) Merger data

- **File**: `01_data/hospital_merger_dataset.csv`
- **Source note in notebook**: [Strategic Hospital Merger Data repository](https://github.com/hyesunghaceoh/strategichospmergerdata/tree/main)
- Includes merger-related indicators such as `target`, `merger_of_equals`, system events, and hospital identifiers.

### 2) Cost report data (HCRIS)

- **Script**: `02_data_preparation/01_hospital_cost_report_extract.py`
- **CMS source**: [CMS Cost Reports Fiscal Year](https://www.cms.gov/data-research/statistics-trends-and-reports/cost-reports/cost-reports-fiscal-year)
- Extracts variables from CMS-2552-10 hospital reports, including:
  - total operating costs,
  - net patient revenue,
  - total charges,
  - Medicare and Medicaid charges/payments,
  - total discharges,
  - derived `cost_per_discharge`.

### 3) Final panel used in analysis

- **File**: `01_data/hospital_analysis.csv`
- Built by merging HCRIS data with annualized merger data.
- Includes treatment timing variables such as:
  - `any_merger`,
  - `merger_year`,
  - `treated`,
  - `years_to_merger`,
  - `post_merger`.

## Environment Setup

The current `requirements.txt` is empty, so install dependencies directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy matplotlib seaborn statsmodels requests jupyter
```

## How to Run

Run in this order:

1. **(Optional) Rebuild HCRIS extracts**
   - Run:
     ```bash
     python "02_data_preparation/01_hospital_cost_report_extract.py"
     ```
   - The script can use local ZIP files in `hcris_zips/` or attempt CMS download.

2. **Prepare and inspect merged panel**
   - Open and run:
     - `02_data_preparation/02_Exploratory_data_analysis.ipynb`

3. **Check pre-trends**
   - Open and run:
     - `03_main_analysis/01_parallel_trend_check.ipynb`

4. **Estimate main staggered DiD model**
   - Open and run:
     - `03_main_analysis/02_staggered_did.ipynb`

5. **Review figures**
   - Outputs are saved under:
     - `04_outputs/figures/`

## Notes and Known Caveats

- Parallel trends diagnostics are not strongly supported in the current notebooks, so DiD findings should be interpreted cautiously as suggestive rather than strictly causal.
- `03_main_analysis/02_staggered_did.ipynb` contains an absolute local data path in one cell; replace it with a relative path for portability.
- Consider populating `requirements.txt` with pinned versions to improve reproducibility.

## Authors / Course Context

IDS 701 final project repository focused on hospital mergers and cost outcomes.
