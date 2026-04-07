import pandas as pd
import os

# 1. This finds the folder where this script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, 'nanoparticles.csv')

print(f"🔍 Searching for file at: {file_path}")

# 2. Safety check: Verify the file exists and is not empty
if not os.path.exists(file_path):
    print("❌ ERROR: File not found at the path above!")
elif os.path.getsize(file_path) == 0:
    print("❌ ERROR: The file is empty (0 bytes). Add data to it first!")
else:
    # 3. Load and process
    try:
        df = pd.read_csv(file_path)
        print("✅ File loaded successfully!")

        # Calculate Surface-to-Volume Ratio (S/V = 3/radius)
        df['sv_ratio'] = 3 / (df['size_nm'] / 2)

        # One-Hot Encoding for materials
        df = pd.get_dummies(df, columns=['core_material'])

        # Save the refined dataset
        output_path = os.path.join(BASE_DIR, 'refined_nanodata.csv')
        df.to_csv(output_path, index=False)
        print(f"✅ Refined dataset created at: {output_path}")

    except Exception as e:
        print(f"❌ Processing Error: {e}")