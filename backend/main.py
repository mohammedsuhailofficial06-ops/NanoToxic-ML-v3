from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os
import io

# 1. INITIALIZE APP
app = FastAPI(title="NanoToxic-ML 4.0 Engine")

# 2. ALLOW GLOBAL ACCESS (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. LOAD THE BRAIN (The .pkl files)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'models', 'nano_model.pkl')
scaler_path = os.path.join(BASE_DIR, 'models', 'scaler.pkl')
features_path = os.path.join(BASE_DIR, 'models', 'features.pkl')

# Initialize variables as None so the endpoints can check them
model = None
scaler = None
feature_cols = None

try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    feature_cols = joblib.load(features_path)
    print("✅ NanoToxic-ML 4.0 Engine: ONLINE")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load models. {e}")

# 4. INPUT SCHEMA
class NanoInput(BaseModel):
    core_material: str
    size_nm: float
    zeta_potential_mv: float
    dosage_ug_ml: float

# 5. ENDPOINTS
@app.get("/health")
def health_check():
    return {"status": "Healthy", "model_loaded": model is not None}

@app.post("/predict")
async def predict(data: NanoInput):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded on server.")
    
    try:
        sv_ratio = 3 / (data.size_nm / 2)
        input_data = {col: [0] for col in feature_cols}
        input_data['size_nm'] = [data.size_nm]
        input_data['zeta_potential_mv'] = [data.zeta_potential_mv]
        input_data['dosage_ug_ml'] = [data.dosage_ug_ml]
        input_data['sv_ratio'] = [sv_ratio]
        
        mat_col = f"core_material_{data.core_material}"
        if mat_col in input_data:
            input_data[mat_col] = [1]
            
        df_input = pd.DataFrame(input_data)[feature_cols]
        scaled_input = scaler.transform(df_input)
        
        prediction = int(model.predict(scaled_input)[0])
        probs = model.predict_proba(scaled_input)[0]
        
        return {
            "prediction": "Toxic" if prediction == 1 else "Safe",
            "confidence": f"{max(probs)*100:.2f}%",
            "descriptors": {"sv_ratio": round(sv_ratio, 4)}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_batch")
async def predict_batch(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded on server."}
        
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required = ["core_material", "size_nm", "zeta_potential_mv", "dosage_ug_ml"]
        if not all(col in df.columns for col in required):
            return {"error": f"CSV must contain: {required}"}

        df['sv_ratio'] = 3 / (df['size_nm'] / 2)
        results = []

        for _, row in df.iterrows():
            input_row = {col: [0] for col in feature_cols}
            input_row['size_nm'] = [row['size_nm']]
            input_row['zeta_potential_mv'] = [row['zeta_potential_mv']]
            input_row['dosage_ug_ml'] = [row['dosage_ug_ml']]
            input_row['sv_ratio'] = [row['sv_ratio']]

            mat_col = f"core_material_{row['core_material']}"
            if mat_col in input_row:
                input_row[mat_col] = [1]

            df_input = pd.DataFrame(input_row)[feature_cols]
            scaled_input = scaler.transform(df_input)
            
            pred = model.predict(scaled_input)[0]
            results.append("Toxic" if pred == 1 else "Safe")

        df['prediction'] = results
        return df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}

# 6. RENDER STARTUP (Keep this at the very bottom!)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)