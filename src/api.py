# =============================================================================
# MULTIPLE MYELOMA STAGE PREDICTION API
# =============================================================================
# FastAPI REST API for predicting Multiple Myeloma clinical stage.
# Uses Random Forest model trained without clinical selection bias indicators.
#
# Endpoints:
#   GET  /health       — API health check
#   GET  /features     — List of required input features
#   POST /predict      — Predict stage for a single patient
# =============================================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
from typing import Dict
import os

# --- Load model and artifacts ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')

rf_model = joblib.load(os.path.join(MODELS_DIR, 'rf_nobias.joblib'))
feature_cols = joblib.load(os.path.join(MODELS_DIR, 'feature_cols_nobias.joblib'))
le_target = joblib.load(os.path.join(MODELS_DIR, 'le_target.joblib'))

# --- FastAPI app ---
app = FastAPI(
    title="Multiple Myeloma Stage Prediction API",
    description="""
    Predicts the clinical stage of Multiple Myeloma patients 
    using the Durie-Salmon staging system.
    
    Model: Random Forest trained on MM-dataset (Tlemcen, Algeria 2008-2019).
    Explainability: SHAP analysis available in notebooks/03_explainability.ipynb.
    
    ⚠️ This is a proof of concept. Not intended for clinical use.
    """,
    version="1.0.0"
)

# --- Request/Response schemas ---
class PatientFeatures(BaseModel):
    features: Dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "features": {
                    "CBC_Hgb": 7.5,
                    "Ca": 130.0,
                    "creat": 35.0,
                    "prot_rate": 120.0,
                    "a_glob": 8.0,
                    "g_glob": 35.0
                }
            }
        }

class PredictionResponse(BaseModel):
    predicted_stage: str
    probabilities: Dict[str, float]
    disclaimer: str

# --- Endpoints ---
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": "RandomForest",
        "features": len(feature_cols),
        "classes": list(le_target.classes_)
    }

@app.get("/features")
def get_features():
    return {
        "required_features": feature_cols,
        "total": len(feature_cols)
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(patient: PatientFeatures):
    try:
        # Build input dataframe with all features
        # Missing features filled with 0 (will be handled as median by model)
        input_data = {col: patient.features.get(col, 0.0) for col in feature_cols}
        input_df = pd.DataFrame([input_data], columns=feature_cols)

        # Predict
        pred_idx = rf_model.predict(input_df)[0]
        pred_proba = rf_model.predict_proba(input_df)[0]
        pred_class = le_target.classes_[pred_idx]

        # Build probabilities dict
        probabilities = {
            cls: round(float(prob), 3)
            for cls, prob in zip(le_target.classes_, pred_proba)
        }

        return PredictionResponse(
            predicted_stage=pred_class,
            probabilities=probabilities,
            disclaimer="Proof of concept only. Not intended for clinical use."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))