# Multiple Myeloma Stage Prediction & Explainability

## Overview
End-to-end explainable AI pipeline for predicting the clinical stage of Multiple Myeloma (MM)
patients using the Durie-Salmon staging system. The project emphasizes model explainability
using SHAP, making predictions interpretable for clinical use.

This project is a **proof of concept** demonstrating the methodology of explainable AI
in a clinical setting. Results should not be interpreted as clinically validated findings
due to dataset size limitations.

## Dataset
**Multiple Myeloma Dataset (MM-dataset)**
Guilal R., Bendahmane A.F., Settouti N., Chikh M.E.A., Mesli N.
University Hospital of Tlemcen, Algeria (2008-2019)
https://data.mendeley.com/datasets/7wpcv7kp6f/1

- 203 patient records, 59 clinical features
- 9 target classes based on Durie-Salmon staging system
- Features cover: demographics, hematology, protein tests, imaging, biochemistry

## Clinical Context
Multiple Myeloma staging follows the **Durie-Salmon classification system**:

| Stage | Criteria | Sub-class |
|-------|----------|-----------|
| I | Hgb > 10 g/dl, normal calcium, low protein | A: creatinine < 20 mg/l |
| II | Neither stage I nor III | B: creatinine > 20 mg/l |
| III | Hgb < 8.5 g/dl, calcium > 12 mg/dl, multiple bone lesions | |

For modeling, classes were grouped into 3 stages (Stage I, II, III),
excluding MGUS, ASYM and PLASMO due to insufficient sample size (n<6).

## Project Structure
```
myeloma-explainability/
├── data/               # Raw dataset (not versioned)
├── notebooks/
│   ├── 01_eda.ipynb              # Exploratory Data Analysis
│   ├── 02_modeling.ipynb         # Model training and evaluation
│   └── 03_explainability.ipynb   # SHAP analysis and bias experiment
├── src/                # Source code
├── models/             # Trained models
└── README.md
```

## Methodology

### 1. Exploratory Data Analysis
- Class distribution analysis — highly imbalanced dataset (Stage III = 53%)
- Durie-Salmon criteria validation against dataset biomarkers
- Missing values analysis: 36/60 features affected, up to 83% missing (Ferritin)
- Data quality findings: calcium unit discrepancy, clinical selection bias identified

### 2. Preprocessing
- Critical features (>50% missing): dropped but replaced with binary availability indicators
- Remaining missing values: imputed with median
- Categorical features: label encoded
- Processed dataset saved to `data/mm_processed.csv` (not versioned)

### 3. Modeling
- Problem: 3-class classification (Stage I, II, III)
- Class imbalance handled with **SMOTE** (Synthetic Minority Over-sampling Technique)
- Models evaluated: Random Forest, XGBoost (baseline and SMOTE versions)
- Experiment tracking: **MLflow** (local, `mlruns/`)

| Model | F1 weighted | F1 macro |
|-------|-------------|----------|
| RF + SMOTE ✅ | 0.698 | 0.374 |
| XGBoost + SMOTE | 0.649 | 0.331 |
| RF + SMOTE + GridSearch | 0.665 | 0.290 |
| RF baseline | 0.661 | 0.289 |
| XGBoost baseline | 0.634 | 0.277 |

### 4. Explainability (SHAP)

#### Global Explanations
SHAP summary plots and mean absolute SHAP values reveal the most influential features:

| Feature | Clinical meaning | SHAP importance |
|---------|-----------------|-----------------|
| B2M_available | Beta-2 Microglobulin availability indicator | 0.040 |
| a_glob | Alpha globulins | 0.026 |
| roll_RBC | Red blood cell rouleaux formation | 0.025 |
| body_surf | Body surface area | 0.021 |
| g_glob | Gamma globulins | 0.019 |
| HBP | Hypertension | 0.014 |
| Fib_available | Fibrinogen availability indicator | 0.013 |

#### Local Explanations
Waterfall plots generated for one representative patient per stage, showing
individual feature contributions to each prediction.

All SHAP plots logged as artifacts in MLflow under `plots/shap/`.

### 5. Bias Removal Experiment

SHAP analysis revealed that availability indicators (`B2M_available`, `Fib_available`,
`P_available`, `Ferr_available`) dominated predictions — reflecting **clinical selection
bias** rather than true biological signal. These tests are ordered when advanced disease
is already suspected, so their availability is itself a proxy for disease severity.

Retraining the model after removing these indicators produced significantly better results:

| Model | F1 weighted | F1 macro |
|-------|-------------|----------|
| RF + SMOTE (with bias indicators) | 0.698 | 0.374 |
| **RF + SMOTE (without bias indicators)** ✅ | **0.719** | **0.484** |

**Top features without bias — true biological signal:**

| Feature | Clinical meaning |
|---------|-----------------|
| a_glob | Alpha globulins — elevated in MM ✅ |
| roll_RBC | Red blood cell rouleaux — sign of elevated proteins ✅ |
| TCA | Coagulation time — affected in advanced MM ✅ |
| CRP | C-reactive protein — inflammation marker ✅ |
| g_glob | Gamma globulins — monoclonal protein profile ✅ |

**Individual prediction test (real patients from test set):**
- Stage III: 23/29 correct (79%) ✅
- Stage I: 1/5 correct (20%) ⚠️
- Stage II: 1/4 correct (25%) ⚠️

Many predictions show uncertain probabilities (~0.40/0.40/0.20), reflecting
insufficient training data for Stage I and Stage II.

## Deployment

### FastAPI REST API
The bias-free model is served via a FastAPI REST API.

**Start the API:**
```bash
source venv/bin/activate
uvicorn src.api:app --reload --port 8000 --host 0.0.0.0
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |
| GET | `/features` | List of required input features |
| POST | `/predict` | Predict stage for a single patient |

**Example prediction request:**
```json
{
  "features": {
    "CBC_Hgb": 7.5,
    "Ca": 130.0,
    "creat": 35.0,
    "prot_rate": 120.0,
    "a_glob": 8.0,
    "g_glob": 35.0,
    "roll_RBC": 1,
    "CRP": 85.0
  }
}
```

**Example response:**
```json
{
  "predicted_stage": "Stage_III",
  "probabilities": {
    "Stage_I": 0.24,
    "Stage_II": 0.22,
    "Stage_III": 0.54
  },
  "disclaimer": "Proof of concept only. Not intended for clinical use."
}
```

**Interactive documentation:** `http://localhost:8000/docs`

**OpenAPI v3 specification:** `docs/openapi.yaml` and `docs/openapi.json`

## Critical Limitations

### Clinical Selection Bias
Availability indicators dominated the original model, reflecting the diagnostic
process rather than disease biology. Removing them improved F1 macro by 30%
and revealed clinically coherent biomarkers.

### Dataset Size
- Only 190 patients available for modeling
- Stage I: 25 patients, Stage II: 20 patients — insufficient for robust learning
- A minimum of 200-300 patients per class would be needed for reliable predictions
- SHAP findings for Stage II should be interpreted with caution

### Proof of Concept
This project demonstrates the methodology of explainable AI in clinical settings.
It is not intended as a clinical decision support tool. The pipeline is directly
applicable to larger datasets such as MMRF CoMMpass.

## Future Work
- Validate findings on larger datasets (MMRF CoMMpass)
- Apply ISS (International Staging System) as alternative target variable
- Deploy as REST API with FastAPI + Docker
- Investigate deep learning approaches with larger datasets

## Tech Stack
- Python 3.13
- scikit-learn, XGBoost, imbalanced-learn
- SHAP, MLflow
- FastAPI, Docker (planned)

## Status
| Phase | Status |
|-------|--------|
| EDA | ✅ Complete |
| Preprocessing | ✅ Complete |
| Modeling | ✅ Complete |
| Explainability (SHAP) | ✅ Complete |
| Bias Removal Experiment | ✅ Complete |
| Deployment (FastAPI + Docker) | 🔜 Planned |
| Documentation | ✅ Complete |

## References
Guilal R. et al. "Multiple Myeloma Dataset (MM-dataset)".
University Hospital of Tlemcen, Algeria (2008-2019).
https://data.mendeley.com/datasets/7wpcv7kp6f/1