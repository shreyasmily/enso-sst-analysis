import xarray as xr
import os

folder = 'sst_data'

for file in os.listdir(folder):
    if file.endswith('.nc'):
        try:
            ds = xr.open_dataset(os.path.join(folder, file))
            ds.close()
            print(f"✅ OK: {file}")
        except Exception as e:
            print(f"❌ CORRUPTED: {file}")