import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

folder = 'sst_data'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])
total = len(files)

print(f"Found {total} files. Starting plot...")

fig, ax = plt.subplots(figsize=(15, 10),
                        subplot_kw={'projection': ccrs.PlateCarree()})

ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=1)
ax.add_feature(cfeature.COASTLINE, zorder=2)
ax.add_feature(cfeature.BORDERS, zorder=2)
ax.gridlines(draw_labels=True)

all_min_lat, all_max_lat =  90, -90
all_min_lon, all_max_lon = 180, -180

# Process in batches of 50 to avoid memory issues
batch_size = 50
for batch_start in range(0, total, batch_size):
    batch = files[batch_start:batch_start + batch_size]
    print(f"Processing files {batch_start + 1}–{min(batch_start + batch_size, total)} of {total}...")

    for file in batch:
        try:
            ds = xr.open_dataset(os.path.join(folder, file))

            sst     = ds['sea_surface_temperature'].isel(time=0).values - 273.15
            quality = ds['quality_level'].isel(time=0).values
            lat     = ds['lat'].values
            lon     = ds['lon'].values

            # Filter good quality only
            sst_filtered = np.where(quality >= 4, sst, np.nan)

            # Skip file if all NaN after filtering
            if np.all(np.isnan(sst_filtered)):
                ds.close()
                continue

            # Downsample by taking every 3rd pixel (speeds up plotting)
            ax.pcolormesh(lon[::5, ::5], lat[::5, ::5], sst_filtered[::5, ::5],
                          cmap='RdYlBu_r',
                          vmin=0, vmax=35,
                          transform=ccrs.PlateCarree(),
                          alpha=0.6)

            # Update extent
            all_min_lat = min(all_min_lat, float(np.nanmin(lat)))
            all_max_lat = max(all_max_lat, float(np.nanmax(lat)))
            all_min_lon = min(all_min_lon, float(np.nanmin(lon)))
            all_max_lon = max(all_max_lon, float(np.nanmax(lon)))

            ds.close()

        except Exception as e:
            print(f"❌ Skipped: {file} — {e}")

    print(f"  ✅ Batch done — {min(batch_start + batch_size, total)}/{total} files plotted")

# Set map extent
ax.set_extent([all_min_lon - 2, all_max_lon + 2,
               all_min_lat - 2, all_max_lat + 2],
               crs=ccrs.PlateCarree())

# Colorbar
sm = plt.cm.ScalarMappable(cmap='RdYlBu_r',
                            norm=plt.Normalize(vmin=0, vmax=35))
plt.colorbar(sm, ax=ax, label='SST (°C)', shrink=0.5)

ax.set_title(f'MODIS Aqua SST — All {total} Files Overlaid')
plt.tight_layout()
plt.savefig('sst_stitched_map.png', dpi=150, bbox_inches='tight')
print("\n✅ Done! Saved as sst_stitched_map.png")
plt.show()