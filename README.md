# IDS 701 Final Project: Hospital Mergers and Cost Outcomes

This project analyzes whether hospital mergers are associated with changes in hospital cost outcomes using CMS HCRIS hospital cost report data, hospital merger indicators, and a staggered Difference-in-Differences (DiD) event-study design.

The main outcome is `log(cost_per_discharge)`.

## Project Goal

Estimate the relationship between merger exposure and hospital cost per discharge by:

- extracting CMS HCRIS hospital cost report data,
- merging cost report data with hospital merger data,
- building a hospital-year panel,
- checking pre-treatment trends,
- estimating a staggered event-study model with hospital and year fixed effects.

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
│   ├── 01_parallel_trend_check_T.ipynb
│   ├── 02_staggered_did.ipynb
│   └── 02_staggered_did_T.ipynb
├── 04_outputs/
│   └── figures/
└── requirements.txt
```

## Data

### Merger Data

- **File**: `01_data/hospital_merger_dataset.csv`
- **Source note in notebook**: [Strategic Hospital Merger Data repository](https://github.com/hyesunghaceoh/strategichospmergerdata/tree/main)
- Includes merger-related indicators such as `target`, `merger_of_equals`, system events, hospital identifiers, facility names, and system identifiers.

### Cost Report Data

- **Script**: `02_data_preparation/01_hospital_cost_report_extract.py`
- **CMS source**: [CMS Cost Reports Fiscal Year](https://www.cms.gov/data-research/statistics-trends-and-reports/cost-reports/cost-reports-fiscal-year)
- Extracts variables from CMS Form 2552-10 hospital reports, including:
  - `total_operating_costs`,
  - `net_patient_revenue`,
  - `total_charges`,
  - `medicare_charges`,
  - `medicare_payments`,
  - `medicaid_charges`,
  - `medicaid_payments`,
  - `total_discharges`,
  - derived `cost_per_discharge`.

### Final Analysis Panel

- **File**: `01_data/hospital_analysis.csv`
- Built by merging HCRIS cost report data with annualized merger data.
- Key variables include:
  - `PRVDR_NUM`: CMS provider identifier,
  - `fiscal_year`: hospital cost report year,
  - `cost_per_discharge`: main cost outcome before log transformation,
  - `treated`: equals 1 if the hospital ever has a merger event,
  - `merger_year`: first observed merger year for treated hospitals,
  - `years_to_merger`: fiscal year minus merger year,
  - `post_merger`: equals 1 for treated hospitals in or after the merger year.

## Notebook Guide

### `02_data_preparation/02_Exploratory_data_analysis.ipynb`

This notebook builds the analytic hospital-year panel.

It:

- loads `01_data/hospital_merger_dataset.csv` and `01_data/cost_report_dataset/hcris_combined.csv`,
- inspects dataset sizes, columns, missingness, and identifier quality,
- standardizes hospital identifiers so merger data and HCRIS data can be merged,
- aggregates quarterly merger records to the hospital-year level,
- creates annual merger flags, including a combined `any_merger` indicator,
- merges merger data with cost report data,
- creates treatment timing variables: `treated`, `merger_year`, `years_to_merger`, and `post_merger`,
- saves the final panel to `01_data/hospital_analysis.csv`,
- reviews `cost_per_discharge` distribution, missingness, treated/control balance, and first merger years,
- saves EDA figures under `04_outputs/figures/01_exploratory_data_analysis/`.

This notebook should be run before the main analysis notebooks if `hospital_analysis.csv` needs to be rebuilt.

### `03_main_analysis/01_parallel_trend_check.ipynb`

This notebook checks the parallel pre-trends assumption using a regression-based event-study diagnostic with `statsmodels`.

It:

- loads `01_data/hospital_analysis.csv`,
- keeps the model-required columns,
- drops rows with missing required fields and non-positive `cost_per_discharge`,
- creates `log_cost = log(cost_per_discharge)`,
- defines event time as `fiscal_year - merger_year`,
- creates treated-only pre-merger indicators for event times `-4`, `-3`, and `-2`,
- omits event time `-1` as the reference period,
- estimates an OLS model with hospital fixed effects, year fixed effects, and hospital-clustered standard errors,
- plots the pre-treatment coefficients with 95% confidence intervals,
- runs a joint pre-trend test of `ev_m4 = ev_m3 = ev_m2 = 0`.

The full-sample diagnostic does not reject the null that the pre-treatment coefficients are jointly zero. This is consistent with parallel pre-trends, but it does not prove the assumption.

### `03_main_analysis/01_parallel_trend_check_T.ipynb`

This is a PanelOLS version of the parallel-trends notebook.

It follows the same cleaning and pre-treatment event-time setup as `01_parallel_trend_check.ipynb`, but estimates the fixed-effects model using `linearmodels.panel.PanelOLS` with:

- `EntityEffects` for hospital fixed effects,
- `TimeEffects` for year fixed effects,
- clustered standard errors,
- a Wald-style joint test for the pre-treatment coefficients.

It saves the PanelOLS pre-trend coefficient plot under `04_outputs/figures/02_parallel_trend_check/`.

### `03_main_analysis/02_staggered_did.ipynb`

This notebook estimates the main staggered DiD event-study model using `statsmodels`.

It:

- loads `01_data/hospital_analysis.csv`,
- cleans the sample in the same way as the pre-trend notebook,
- creates `log_cost`,
- defines `event_time = fiscal_year - merger_year`,
- creates `post_treatment` for treated hospitals in the merger year or later,
- creates treated-only event-study indicators for event times `-4`, `-3`, `-2`, `0`, `1`, `2`, `3`, and `4`,
- omits event time `-1` as the reference period,
- estimates an OLS event-study model with hospital fixed effects, year fixed effects, and hospital-clustered standard errors,
- converts log-point coefficients into approximate percent changes,
- saves the event-study plot to `04_outputs/figures/03_staggered_DiD/staggered_did_event_study.png`.

The notebook finds small, statistically insignificant pre-treatment estimates. The merger-year estimate is negative and statistically significant in the displayed results, while post-merger estimates for later years are not statistically significant. This means the analysis does not provide strong evidence of a sustained post-merger cost change.

### `03_main_analysis/02_staggered_did_T.ipynb`

This is a PanelOLS version of the main staggered DiD event-study.

It follows the same treatment timing and event-time construction as `02_staggered_did.ipynb`, but estimates the model with `linearmodels.panel.PanelOLS` using:

- hospital/entity fixed effects,
- fiscal year/time fixed effects,
- event-time indicators for pre- and post-merger periods,
- clustered standard errors.

It saves the PanelOLS event-study plot to `04_outputs/figures/03_staggered_DiD/staggered_did_event_study_T.png`.

## Analysis Workflow

Run the project in this order:

1. **Optional: rebuild HCRIS extracts**

   ```bash
   python "02_data_preparation/01_hospital_cost_report_extract.py"
   ```

   The script can use local ZIP files in `hcris_zips/` or attempt CMS downloads. Its default output folder is `cost_report_dataset/`, so move or configure outputs if rebuilding data for `01_data/cost_report_dataset/`.

2. **Build and inspect the merged panel**

   Run:

   ```text
   02_data_preparation/02_Exploratory_data_analysis.ipynb
   ```

3. **Check parallel pre-trends**

   Run one of:

   ```text
   03_main_analysis/01_parallel_trend_check.ipynb
   03_main_analysis/01_parallel_trend_check_T.ipynb
   ```

4. **Estimate the main staggered DiD event study**

   Run one of:

   ```text
   03_main_analysis/02_staggered_did.ipynb
   03_main_analysis/02_staggered_did_T.ipynb
   ```

5. **Review saved outputs**

   Figures are saved under:

   ```text
   04_outputs/figures/
   ```

## Environment Setup

The current `requirements.txt` is empty, so install dependencies directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy matplotlib seaborn statsmodels requests jupyter linearmodels
```

`linearmodels` is only required for the `_T` notebooks.

## Notes and Known Caveats

- The results should be interpreted as suggestive rather than definitive causal evidence because DiD depends on the parallel-trends assumption.
- A non-significant pre-trend test supports, but does not prove, the parallel-trends assumption.
- Hospitals may select into mergers for reasons related to future costs, so time-varying selection remains a concern.
- Standard two-way fixed-effects event studies can be difficult to interpret with staggered treatment timing and heterogeneous treatment effects.
- HCRIS cost report data can contain missing values, outliers, and reporting inconsistencies.
- The current `requirements.txt` is empty; pinning package versions would improve reproducibility.
- Some notebook markdown refers to subgroup checks, but the current `01_parallel_trend_check.ipynb` only implements the full-sample check.


