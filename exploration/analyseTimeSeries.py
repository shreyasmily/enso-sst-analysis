import pickle
with open('ds.pkl', 'rb') as f:
    ds = pickle.load(f)

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

# ds = xr.open_dataset('your_file.nc')

# see what the data covers

lat = ds['lat'].values
lon = ds['lon'].values

print("Lat range:", np.nanmin(lat), "to", np.nanmax(lat))
print("Lon range:", np.nanmin(lon), "to", np.nanmax(lon))


# Get SST, lat, lon
sst = ds['sea_surface_temperature'].isel(time=0) - 273.15
lat = ds['lat'].values
lon = ds['lon'].values
quality = ds['quality_level'].isel(time=0)

# Filter good quality
sst_filtered = sst.where(quality >= 4)

# Define a region (adjust to your area of interest)
lat_min, lat_max = np.nanmin(lat), np.nanmax(lat)   # from what data is covered
lon_min, lon_max = np.nanmin(lon), np.nanmax(lon)

# Create mask for region
region_mask = (
    (lat >= lat_min) & (lat <= lat_max) &
    (lon >= lon_min) & (lon <= lon_max)
)

# Apply mask
sst_region = sst_filtered.values[region_mask]

# Plot histogram of SST values in region
plt.figure(figsize=(10, 5))
plt.hist(sst_region[~np.isnan(sst_region)], bins=50, color='steelblue')
plt.xlabel('SST (°C)')
plt.ylabel('Pixel Count')
plt.title('SST Distribution - Gulf of Mexico - 2020-06-27')
plt.show()

print("Regional Mean SST:", np.nanmean(sst_region), "°C")