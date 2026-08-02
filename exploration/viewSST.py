import xarray as xr
import numpy as np

import pickle
with open('ds.pkl', 'rb') as f:
    ds = pickle.load(f)

# ds = xr.open_dataset('your_file.nc')

# Access SST and convert from Kelvin to Celsius
sst = ds['sea_surface_temperature'].isel(time=0)
sst_celsius = sst - 273.15

# Only look at good quality data (quality_level == 5 is best)
quality = ds['quality_level'].isel(time=0)
sst_filtered = sst_celsius.where(quality >= 4)

print("Min SST (°C):", float(np.nanmin(sst_filtered)))
print("Max SST (°C):", float(np.nanmax(sst_filtered)))
print("Mean SST (°C):", float(np.nanmean(sst_filtered)))
print("Shape:", sst.shape)