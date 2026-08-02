import xarray as xr
import numpy as np
import os

folder = 'sst_data'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

all_min_lon = 180
all_max_lon = -180

for file in files:
    try:
        ds = xr.open_dataset(os.path.join(folder, file))
        lon = ds['lon'].values
        all_min_lon = min(all_min_lon, float(np.nanmin(lon)))
        all_max_lon = max(all_max_lon, float(np.nanmax(lon)))
        ds.close()
    except:
        pass

print(f"Your data covers: {all_min_lon:.2f}°  to  {all_max_lon:.2f}°")