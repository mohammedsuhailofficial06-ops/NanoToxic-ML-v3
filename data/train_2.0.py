import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os

# 1. Load the refined data you just created
# We use the relative path since we run from the root
df = pd.read_csv('data/refined_nanodata.csv')

# 2. Separate Features and Target
# Features: size, zeta, dosage, sv_ratio, and the one-hot material columns
X = df.drop('toxicity', axis=1) 
y = df['toxicity']

# 3. Scale the features (Professional Grade)
# This prevents one feature (like dosage) from over-powering others (like size)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Train the Random Forest
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Export to your BACKEND/MODELS folder
# This is the 'bridge' to your web portal
output_dir = 'backend/models'
os.makedirs(output_dir, exist_ok=True)

joblib.dump(model, f'{output_dir}/nano_model.pkl')
joblib.dump(scaler, f'{output_dir}/scaler.pkl')
joblib.dump(list(X.columns), f'{output_dir}/features.pkl')

print(f"✅ Phase 3 Complete!")
print(f"--- Model accuracy: {model.score(X_test, y_test)*100:.2f}%")
print(f"--- Files saved to: {output_dir}")