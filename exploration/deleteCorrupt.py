import xarray as xr
import os

folder = 'sst_data'

for file in os.listdir(folder):
    if file.endswith('.nc'):
        filepath = os.path.join(folder, file)
        try:
            ds = xr.open_dataset(filepath)
            ds.close()
            print(f"✅ OK: {file}")
        except Exception as e:
            os.remove(filepath)
            print(f"🗑️ Deleted corrupted file: {file}")