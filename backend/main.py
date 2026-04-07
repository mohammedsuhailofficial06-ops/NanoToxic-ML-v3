from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI()

# 1. ALLOW PORTAL ACCESS (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. LOAD THE BRAIN
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'models', 'nano_model.pkl')
scaler_path = os.path.join(BASE_DIR, 'models', 'scaler.pkl')
features_path = os.path.join(BASE_DIR, 'models', 'features.pkl')

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feature_cols = joblib.load(features_path)
    print("✅ NanoToxic-ML 2.0 Engine: ONLINE")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load models. {e}")

class NanoInput(BaseModel):
    core_material: str
    size_nm: float
    zeta_potential_mv: float
    dosage_ug_ml: float

@app.get("/health")
def health_check():
    return {"status": "Healthy", "model_loaded": model is not None}

@app.post("/predict")
async def predict(data: NanoInput):
    try:
        # Calculate S/V Ratio dynamically (ProTox style)
        sv_ratio = 3 / (data.size_nm / 2)
        
        # Build the input row matching the training features
        input_data = {col: [0] for col in feature_cols}
        input_data['size_nm'] = [data.size_nm]
        input_data['zeta_potential_mv'] = [data.zeta_potential_mv]
        input_data['dosage_ug_ml'] = [data.dosage_ug_ml]
        input_data['sv_ratio'] = [sv_ratio]
        
        # Set the one-hot material
        mat_col = f"core_material_{data.core_material}"
        if mat_col in input_data:
            input_data[mat_col] = [1]
            
        # Scale and Predict
        df_input = pd.DataFrame(input_data)[feature_cols]
        scaled_input = scaler.transform(df_input)
        
        prediction = model.predict(scaled_input)[0]
        probs = model.predict_proba(scaled_input)[0]
        
        return {
            "prediction": "Toxic" if prediction == 1 else "Safe",
            "confidence": f"{max(probs)*100:.2f}%",
            "descriptors": {"sv_ratio": round(sv_ratio, 4)}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))