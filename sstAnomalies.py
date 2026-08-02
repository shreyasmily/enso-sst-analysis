import xarray as xr
import numpy as np
import os

folder = 'data/sst_gridded'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

# Load all files
datasets = []
for file in files:
    try:
        ds = xr.open_dataset(os.path.join(folder, file))
        datasets.append(ds['analysed_sst'] - 273.15)
        ds.close()
    except Exception as e:
        print(f"❌ Skipped: {file}")

# Combine into one time series
sst_all = xr.concat(datasets, dim='time')
print(f"Loaded {len(sst_all.time)} time steps")
print(sst_all)

# Calculate climatology (monthly average for each calendar month)
climatology = sst_all.groupby('time.month').mean(dim='time')

# Calculate anomalies (remove seasonal cycle)
# monthly average anomaly
sst_anomaly = sst_all.groupby('time.month') - climatology

print("Anomaly range:", float(sst_anomaly.min()), "to", float(sst_anomaly.max()), "°C")

# Save anomalies for next step
sst_anomaly.to_netcdf('data/sst_anomaly.nc')
print("Saved data/sst_anomaly.nc")