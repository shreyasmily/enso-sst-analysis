import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

import pickle
with open('ds.pkl', 'rb') as f:
    ds = pickle.load(f)

# ds = xr.open_dataset('your_file.nc')

# Get variables
sst = ds['sea_surface_temperature'].isel(time=0) - 273.15
lat = ds['lat'].values
lon = ds['lon'].values
quality = ds['quality_level'].isel(time=0)

# Filter to good quality only
sst_filtered = sst.where(quality >= 4)

# Plot
fig, ax = plt.subplots(figsize=(12, 8),
                        subplot_kw={'projection': ccrs.PlateCarree()})

plt.pcolormesh(lon, lat, sst_filtered,
               cmap='RdYlBu_r', vmin=0, vmax=35,
               transform=ccrs.PlateCarree())

plt.colorbar(label='SST (°C)')
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS)
ax.gridlines(draw_labels=True)
ax.set_title('MODIS Aqua Sea Surface Temperature - 2020-06-27')
plt.show()