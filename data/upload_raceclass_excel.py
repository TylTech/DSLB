import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from shared.supabase_client import supabase  # ✅ now works because sys.path is set beforehand

# === 🧾 STEP 1: Load Excel from your local path ===
xlsx_path = r"E:\Users\Comp1\Dropbox\Programs\DSLB\data\raceclass_upload.xlsx"
df_new = pd.read_excel(xlsx_path)

# 🧼 Clean up: Strip extra whitespace from column names and values
df_new.columns = [col.strip() for col in df_new.columns]
df_new = df_new.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# === 🗂 STEP 2: Fetch existing entries from Supabase ===
response = supabase.table("raceclass").select("*").execute()
df_existing = pd.DataFrame(response.data)

# 🧠 Build a unique key for comparing rows
def get_key(row):
    return f"{row['Race'].lower()}|{row['Class'].lower()}|{str(row['Boost']).strip()}"

existing_keys = set(df_existing.apply(get_key, axis=1)) if not df_existing.empty else set()

# === 🧹 STEP 3: Filter out duplicates ===
rows_to_insert = []
for _, row in df_new.iterrows():
    key = get_key(row)
    if key not in existing_keys:
        rows_to_insert.append(row.to_dict())

# === 💾 STEP 4: Insert non-duplicate rows ===
if rows_to_insert:
    print(f"📥 Inserting {len(rows_to_insert)} new row(s)...")
    for chunk in [rows_to_insert[i:i+50] for i in range(0, len(rows_to_insert), 50)]:
        supabase.table("raceclass").insert(chunk).execute()
    print("✅ Upload complete!")
else:
    print("🎉 No new data to insert — all rows already existed.")
