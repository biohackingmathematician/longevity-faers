# FAERS Data Structure and Notes

## FAERS Overview

The FDA Adverse Event Reporting System (FAERS) is a database that contains information on adverse event and medication error reports submitted to FDA. It is a **spontaneous reporting system**, meaning reports are voluntarily submitted by healthcare professionals, consumers, and manufacturers.

## Tables Used

### DEMO (Demographics)
- **Purpose:** Patient demographics and report metadata
- **Key Fields:**
  - `caseid` / `primaryid`: Unique case identifier
  - `age`: Patient age (often missing)
  - `sex`: Patient sex (M/F/Unknown)
  - `event_dt`: Date of adverse event
  - `fda_dt`: Date FDA received report
- **Notes:** 
  - Field names changed over time (`caseid` in older files, `primaryid` in newer)
  - Age missing in ~30-50% of records
  - Use `fda_dt` to deduplicate follow-up reports

### DRUG (Medications)
- **Purpose:** All drugs reported in each case
- **Key Fields:**
  - `caseid`: Links to DEMO
  - `drugname`: Drug name (brand or generic, often inconsistent)
  - `prod_ai`: Active ingredient (cleaner than drugname)
  - `role_cod`: Drug role
    - `PS` = Primary Suspect
    - `SS` = Secondary Suspect
    - `C` = Concomitant
    - `I` = Interacting
- **Notes:**
  - Same drug may appear as brand, generic, or misspelling
  - Use `prod_ai` when available for standardization
  - Multiple drugs per case (polypharmacy)

### REAC (Reactions)
- **Purpose:** Adverse events reported for each case
- **Key Fields:**
  - `caseid`: Links to DEMO
  - `pt`: MedDRA Preferred Term (standardized AE term)
- **Notes:**
  - Multiple reactions per case (multi-label)
  - MedDRA PTs are hierarchical (PT → HLT → HLGT → SOC)
  - We map PTs to custom categories (cardiovascular, metabolic, etc.)

### OUTC (Outcomes)
- **Purpose:** Serious outcomes (optional, for severity stratification)
- **Key Fields:**
  - `caseid`: Links to DEMO
  - `outc_cod`: Outcome code (DE=Death, HO=Hospitalization, etc.)
- **Notes:** Not used in primary analysis but available for stratification

### THER (Therapy Dates)
- **Purpose:** Drug start/end dates (rarely available)
- **Key Fields:**
  - `caseid`: Links to DEMO
  - `start_dt`: Drug start date
  - `end_dt`: Drug end date
- **Notes:** Often missing, not used in primary analysis

## Key Challenges

### 1. Case Identifiers
- Older files use `caseid`, newer files use `primaryid`
- Need to normalize field names across quarters

### 2. Duplicate Reports
- Follow-up reports may update initial report
- Strategy: Keep latest `fda_dt` per `caseid`

### 3. Drug Name Variability
- Same drug appears as:
  - Brand name: "OZEMPIC"
  - Generic: "SEMAGLUTIDE"
  - Misspellings: "SEMAGLUTIED"
- Solution: Use `prod_ai` field + fuzzy matching + manual dictionary

### 4. Missing Data
- Age: Missing in 30-50% of records
- Sex: Usually present, but "Unknown" category exists
- Therapy dates: Rarely available
- Strategy: Keep missing as separate category, impute for ML models

### 5. Temporal Inconsistencies
- Field names changed over time
- Delimiter variations (pipe `|` vs `$`)
- File naming conventions vary

## Time Window: 2019 Q1 – 2024 Q2

**Rationale:**
- GLP-1s only became widely used post-2018
- Manageable data size (~10-15M reports total)
- Recent enough for relevance
- ~22 quarters to process

## Data Quality Considerations

### Reporting Bias
- Serious AEs over-represented (mild issues not reported)
- Media attention can spike reports (e.g., GLP-1 weight loss)
- Manufacturer reporting requirements vary

### No Denominator
- Cannot calculate incidence rates
- Cannot compare absolute risk across drugs
- Only relative signals (disproportionality)

### Confounding
- Polypharmacy common (hard to attribute AE to single drug)
- Indication bias (diabetes drugs used in diabetic patients)
- Age/sex distributions differ by drug

## Data Processing Pipeline

1. **Download:** Fetch quarterly zip files from FDA website
2. **Unpack:** Extract and standardize table names
3. **Load:** Read DEMO, DRUG, REAC tables
4. **Deduplicate:** Keep latest report per caseid
5. **Filter:** Keep only cases with target drugs as suspect
6. **Join:** Combine DEMO + DRUG + REAC
7. **Map:** Apply MedDRA PT → AE category mapping
8. **Aggregate:** Create analysis-ready datasets

## References

- FAERS Data Files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- OpenFDA API: https://open.fda.gov/apis/drug/event/
- MedDRA: https://www.meddra.org/

