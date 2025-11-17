# FAERS Longevity Drug Safety Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Abstract

This repository presents a computational pharmacovigilance analysis of longevity-relevant medications using the FDA Adverse Event Reporting System (FAERS). We employ disproportionality analysis (reporting odds ratio, proportional reporting ratio) and multi-label machine learning to characterize adverse event profiles for four drug classes with emerging evidence in healthspan extension: metformin, GLP-1 receptor agonists, SGLT2 inhibitors, and statins.

**Key Findings:**
- Analyzed 9.6 million cases across 22 quarters (2019-2024)
- Identified 104 significant drug-adverse event category pairs
- Detected 15 signals (ROR > 2.0, 95% CI > 1.0)
- Statins showed highest musculoskeletal signal (11,534 cases for atorvastatin)
- GLP-1 agonists demonstrated dominant gastrointestinal burden
- Multi-label classification achieved macro-AUC of 0.74

## Research Questions

1. Which adverse event categories (cardiovascular, metabolic, musculoskeletal, gastrointestinal, renal) are disproportionately reported for each longevity-relevant drug?
2. How do safety profiles differ across drug classes?
3. Can patient demographics and polypharmacy predict adverse event patterns?

## Methodology

### Data Source
- **FAERS**: FDA Adverse Event Reporting System (2019 Q1 - 2024 Q2, analyzed in 2025)
- **Drugs Analyzed**: 13 active ingredients across 4 classes
- **Adverse Events**: 8 high-level categories mapped from MedDRA Preferred Terms

### Statistical Methods
- **Disproportionality Analysis**: Reporting Odds Ratio (ROR) and Proportional Reporting Ratio (PRR) with 95% confidence intervals
- **Signal Criteria**: ROR > 2.0 AND lower 95% CI > 1.0
- **Machine Learning**: Multi-label classification (logistic regression, XGBoost) for adverse event prediction

### Data Processing
- Case deduplication (follow-up reports handled)
- Drug name standardization (exact + fuzzy matching)
- MedDRA Preferred Term → category mapping
- Missing data handled via separate "Unknown" categories

See [Methods Documentation](docs/methods.md) for detailed methodology.

## Installation

### Requirements
- Python 3.10 or higher
- 20+ GB disk space (for FAERS data)

### Setup

```bash
# Clone repository
git clone https://github.com/biohackingmathematician/longevity-faers.git
cd longevity-faers

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Complete Analysis Pipeline

```bash
# 1. Download FAERS quarterly data (2019-2024)
# Note: Analysis conducted in 2025
python scripts/download_faers.py

# 2. Unpack and standardize data files
python scripts/unpack_faers.py

# 3. Process data and build analysis datasets
python scripts/build_dataset.py

# 4. Run disproportionality analysis
python run_disproportionality_analysis.py

# 5. Train and evaluate ML models
python run_ml_analysis.py
```

### Interactive Analysis

Jupyter notebooks are available for exploratory analysis:

- `notebooks/01_explore_faers.ipynb` - Data exploration and quality assessment
- `notebooks/02_disproportionality.ipynb` - Disproportionality analysis workflow
- `notebooks/03_multilabel_model.ipynb` - Machine learning model development

## Project Structure

```
longevity-faers/
├── config/                      # Configuration files
│   ├── drug_list.yaml          # Drug names and classifications
│   ├── ae_mapping.yaml         # MedDRA PT → category mappings
│   └── data_config.yaml        # Data processing parameters
├── docs/                        # Documentation
│   ├── methods.md              # Statistical methodology
│   ├── discussion.md           # Results interpretation
│   └── faers_notes.md          # FAERS data structure notes
├── notebooks/                   # Jupyter notebooks
│   ├── 01_explore_faers.ipynb
│   ├── 02_disproportionality.ipynb
│   └── 03_multilabel_model.ipynb
├── scripts/                     # Data processing scripts
│   ├── download_faers.py
│   ├── unpack_faers.py
│   └── build_dataset.py
├── src/                         # Source code
│   ├── data_ingest/            # Data loading and cleaning
│   │   ├── dedupe_cases.py
│   │   ├── demographics_cleaner.py
│   │   ├── drug_normalizer.py
│   │   └── load_faers.py
│   ├── features/               # Feature engineering
│   │   ├── ae_category_mapper.py
│   │   └── feature_engineering.py
│   ├── models/                 # Statistical and ML models
│   │   ├── disproportionality.py
│   │   └── multilabel_classifier.py
│   └── viz/                    # Visualization functions
│       ├── roc_curves.py
│       └── volcano_plots.py
├── results/                     # Analysis outputs
│   ├── figures/                # Visualizations
│   └── tables/                 # Results tables
├── tests/                       # Unit tests
│   └── test_disproportionality.py
├── CITATION.cff                 # Citation metadata
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT License
├── README.md                    # This file
├── pyproject.toml               # Project metadata
├── requirements.txt             # Python dependencies
├── run_disproportionality_analysis.py  # Disproportionality analysis script
├── run_ml_analysis.py           # ML analysis script
└── test_functionality.py        # Functional test suite
```

## Results

### Disproportionality Analysis

**Top Signals (ROR > 3.0):**
- Canagliflozin → Metabolic AEs (ROR = 5.00, 95% CI: 4.67-5.35)
- Semaglutide → Gastrointestinal AEs (ROR = 4.86, 95% CI: 4.75-4.98)
- Dulaglutide → Gastrointestinal AEs (ROR = 4.61, 95% CI: 4.50-4.72)
- Atorvastatin → Musculoskeletal AEs (ROR = 2.33, 95% CI: 2.27-2.38)

**Visualizations:**
- Volcano plots for each drug class
- Heatmap of drugs × adverse event categories
- Top 50 signals per drug (available in `results/tables/`)

### Machine Learning Results

**Model Performance:**
- Macro-averaged AUC: 0.74
- Micro-averaged AUC: 0.78
- Hamming Loss: 0.29

**Key Predictors:**
- Drug class (strongest predictor)
- Age group
- Number of concomitant medications

See [Results Documentation](docs/discussion.md) for detailed interpretation.

## Key Limitations

**Important:** FAERS is a spontaneous reporting system with inherent limitations:

1. **No Exposure Denominator**: Cannot calculate true incidence rates
2. **Reporting Bias**: Serious adverse events are over-represented
3. **Signal Detection Only**: Results indicate associations, not causation
4. **Missing Data**: 30-50% missing values for age/sex in some quarters
5. **Not Medical Advice**: This is a research tool, not a clinical decision support system

See [Methods Documentation](docs/methods.md) for detailed discussion of limitations.

## Data Availability

FAERS data is publicly available from the FDA:
- **Source**: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- **Time Period Analyzed**: 2019 Q1 - 2024 Q2 (22 quarters)
- **Analysis Date**: 2025
- **Size**: ~1.4 GB compressed, ~17 GB uncompressed

Processed datasets are available in `data/processed/` after running the pipeline.

## Citation

If you use this work in your research, please cite:

```bibtex
@software{faers_longevity_2025,
  title = {FAERS Longevity Drug Safety Analysis},
  author = {Chan, Agna},
  year = {2025},
  url = {https://github.com/biohackingmathematician/longevity-faers},
  version = {1.0.0}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FDA for providing FAERS data
- MedDRA terminology for adverse event classification
- Open-source Python community for data science tools

## Contact

For questions or collaboration inquiries, please open an issue on GitHub.

## Disclaimer

This software is provided for educational and research purposes only. It does not constitute medical advice, and results should not be used to make clinical decisions. Consult qualified healthcare professionals for medication-related decisions.
