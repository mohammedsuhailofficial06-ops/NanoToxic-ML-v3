from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="NanoToxic-ML 2.0 Engine")

# 1. ALLOW GLOBAL ACCESS (CORS)
# This is vital so your website can talk to your server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. LOAD THE BRAIN (The .pkl files)
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

# 3. DEFINE INPUT SCHEMA
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
        # Calculate S/V Ratio dynamically (Essential Nano-QSAR Descriptor)
        # S/V = 3 / radius
        sv_ratio = 3 / (data.size_nm / 2)
        
        # Build the input row matching the training features exactly
        input_data = {col: [0] for col in feature_cols}
        input_data['size_nm'] = [data.size_nm]
        input_data['zeta_potential_mv'] = [data.zeta_potential_mv]
        input_data['dosage_ug_ml'] = [data.dosage_ug_ml]
        input_data['sv_ratio'] = [sv_ratio]
        
        # Set the material (One-Hot Encoding)
        mat_col = f"core_material_{data.core_material}"
        if mat_col in input_data:
            input_data[mat_col] = [1]
            
        # Scale and Predict
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

# For Render's environment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import UploadFile, File
import io

@app.post("/predict_batch")
async def predict_batch(file: UploadFile = File(...)):
    try:
        # Read the uploaded CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Verify required columns exist
        required = ["core_material", "size_nm", "zeta_potential_mv", "dosage_ug_ml"]
        if not all(col in df.columns for col in required):
            return {"error": f"CSV must contain columns: {required}"}

        # 1. Feature Engineering: Calculate S/V Ratio for the whole batch
        df['sv_ratio'] = 3 / (df['size_nm'] / 2)

        # 2. Pre-process the data (One-Hot Encoding and Scaling)
        # Create a template matching your feature_cols
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
            
            # Predict
            pred = model.predict(scaled_input)[0]
            results.append("Toxic" if pred == 1 else "Safe")

        # 3. Add predictions back to the dataframe
        df['prediction'] = results
        
        # Return as a list of dictionaries for Flutter to read
        return df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}