import xarray as xr
import numpy as np
import pandas as pd

# ds = xr.open_dataset('your_file.nc')

import pickle
with open('ds.pkl', 'rb') as f:
    ds = pickle.load(f)

# Flatten lat and lon
lat = ds['lat'].values.flatten()
lon = ds['lon'].values.flatten()

# Build table with ALL variables
df = pd.DataFrame({
    'lat': lat,
    'lon': lon,
    'sea_surface_temperature': (ds['sea_surface_temperature'].isel(time=0).values.flatten()) - 273.15,
    'quality_level':            ds['quality_level'].isel(time=0).values.flatten(),
    'sst_dtime':                ds['sst_dtime'].isel(time=0).values.flatten(),
    'sses_bias':                ds['sses_bias'].isel(time=0).values.flatten(),
    'sses_standard_deviation':  ds['sses_standard_deviation'].isel(time=0).values.flatten(),
    'wind_speed':               ds['wind_speed'].isel(time=0).values.flatten(),
    'chlorophyll_a':            ds['chlorophyll_a'].isel(time=0).values.flatten(),
    'K_490':                    ds['K_490'].isel(time=0).values.flatten(),
    'dt_analysis':              ds['dt_analysis'].isel(time=0).values.flatten(),
    'l2p_flags':                ds['l2p_flags'].isel(time=0).values.flatten(),
})

# Save to Excel
df_filtered = df[df['quality_level'] >= 4]
df_filtered.to_excel('sst_filtered_data.xlsx', index=False)
print(f"Saved {len(df_filtered)} rows")


quality = ds['quality_level'].isel(time=0).values.flatten()

# See all unique quality values and how many of each
unique, counts = np.unique(quality[~np.isnan(quality)], return_counts=True)
for val, count in zip(unique, counts):
    print(f"Quality {val}: {count} pixels")

print(f"Total pixels: {len(quality)}")
print(f"NaN pixels: {np.sum(np.isnan(quality))}")
print(f"Valid pixels: {np.sum(~np.isnan(quality))}")

# df.to_excel('sst_full_data.xlsx', index=False)
# print("Done! Saved as sst_full_data.xlsx")
# print(f"Total rows: {len(df)}")