# Methods Documentation

## Disproportionality Analysis

### Rationale

Reporting odds ratio (ROR) and proportional reporting ratio (PRR) quantify whether a drug-event pair is reported more frequently than expected under independence. These are standard pharmacovigilance metrics for signal detection.

### Contingency Table

For each (drug, adverse event category) pair, we construct a 2×2 contingency table:

```
                 Event+    Event-
Drug+              a         b
Drug-              c         d
```

Where:
- **a** = reports with BOTH drug and event
- **b** = reports with drug, WITHOUT event
- **c** = reports with event, WITHOUT drug
- **d** = reports with NEITHER drug nor event

### Metrics

#### Reporting Odds Ratio (ROR)

```
ROR = (a/b) / (c/d) = (a*d) / (b*c)
```

- Interpretation: Odds of reporting the event given the drug vs not
- 95% CI: `exp(log(ROR) ± 1.96 * SE)` where `SE = sqrt(1/a + 1/b + 1/c + 1/d)`
- **Signal threshold:** ROR > 2 AND lower CI > 1

#### Proportional Reporting Ratio (PRR)

```
PRR = (a / (a+b)) / (c / (c+d))
```

- Interpretation: Proportion of drug reports with event vs background
- **Signal threshold:** PRR > 2 AND χ² > 4 AND a ≥ 3

### Signal Criteria

We define a "signal" as:
- ROR > 2.0 AND lower 95% CI > 1.0
- OR PRR > 2.0 AND χ² > 4 AND ≥3 cases

### Adjustments

- Minimum case count: a ≥ 5
- Minimum drug reports: (a + b) ≥ 10
- Stratified by age group and sex when sample size permits
- No formal multiple testing correction (exploratory analysis), but we report effect sizes and CIs

### Limitations

- Susceptible to reporting bias (more attention to certain drug-event pairs)
- Cannot establish causality
- Background rate (c+d) may be biased by database composition
- No exposure denominator → cannot calculate true incidence rates

## Multi-Label AE Prediction Model

### Objective

Predict which AE categories will be reported for a given patient-drug context, using demographics, drug class, and polypharmacy.

### Problem Formulation

**Task:** Multi-label classification
- **Input:** Patient + drug + polypharmacy features (one row per case-drug)
- **Output:** Binary vector of AE category presence [cardio, metabolic, musculo, GI, renal]

### Feature Engineering

**Demographic Features:**
- `age_group`: binned [<18, 18-44, 45-64, 65-74, 75+, Unknown] (one-hot encoded)
- `sex`: [M, F, Unknown] (one-hot)
- `age_raw`: continuous (if available), for tree-based models

**Temporal Features:**
- `report_year`: continuous or one-hot (captures temporal trends)

**Drug Features:**
- `drug_class`: [metformin, glp1, sglt2, statin] (one-hot)

**Polypharmacy Features:**
- `n_concomitant_drugs`: count of other drugs reported
- `has_cardio_comedication`: binary flag if other cardio drugs present
- `has_insulin`: binary (important for hypoglycemia risk with metformin)

### Models

1. **Logistic Regression (L2):** Baseline, interpretable
   - Separate logistic model per AE category
   - L2 regularization (tune `C`)
   - Interpretable coefficients

2. **XGBoost:** Captures nonlinear effects, handles missing data
   - Use `MultiOutputClassifier(XGBClassifier())` from sklearn
   - Advantages: handles missing data, nonlinear interactions, feature importance
   - Tune: `max_depth`, `learning_rate`, `n_estimators`

### Evaluation

**Train/Val/Test Split:**
- **Time-based split (recommended):**
  - Train: 2019-2022 (~70%)
  - Validation: 2023 (~15%)
  - Test: 2024 (~15%)
  - Rationale: Simulates deployment scenario (predict future reports)

**Metrics:**

Per-category metrics:
- **AUC-ROC:** Area under ROC curve (handles class imbalance)
- **Average Precision (AP):** Area under PR curve (better for rare labels)
- **F1 score:** Balance of precision/recall at fixed threshold

Aggregate metrics:
- **Macro-averaged AUC:** Average AUC across categories (treats all equally)
- **Micro-averaged AUC:** Weighted by label frequency
- **Hamming Loss:** Fraction of incorrect labels
- **Subset Accuracy:** Exact match of full label vector (usually very low, not critical)

### Interpretability

**For Logistic Regression:**
- Plot coefficient magnitudes per AE category
- Identify: "Age 65+ increases musculoskeletal AE odds by X%"

**For XGBoost:**
- **Feature Importance:** Gain/split-based importance per category model
- **SHAP Values (Stretch):**
  - `shap.TreeExplainer` for XGBoost
  - Compute SHAP values for test set
  - Plot: Summary plot (beeswarm), dependence plots for key features

### Limitations

- Model trained on reported AEs (not ground truth)
- Predictive accuracy limited by data quality (missing covariates)
- Cannot predict novel AEs not seen in training data
- Temporal trends may affect generalizability

