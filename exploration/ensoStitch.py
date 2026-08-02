import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

folder = 'sst_data'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])
total = len(files)

print(f"Found {total} files. Starting Pacific ENSO plot...")

fig, ax = plt.subplots(figsize=(18, 10),
                        subplot_kw={'projection': ccrs.PlateCarree(central_longitude=180)})

ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=1)
ax.add_feature(cfeature.COASTLINE, zorder=2)
ax.add_feature(cfeature.BORDERS, zorder=2)
ax.gridlines(draw_labels=True)

# Focus on Pacific Ocean and ENSO region
ax.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())

# Custom colormap better suited for ENSO SST gradients
cmap = plt.cm.RdBu_r  # Blue = cold, Red = warm

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

            # Only process files that overlap the Pacific region
            if np.nanmax(lon) < 120 or np.nanmin(lon) > 290:
                ds.close()
                continue
            if np.nanmax(lat) < -30 or np.nanmin(lat) > 30:
                ds.close()
                continue

            # Filter good quality
            sst_filtered = np.where(quality >= 4, sst, np.nan)

            if np.all(np.isnan(sst_filtered)):
                ds.close()
                continue

            ax.pcolormesh(lon[::5, ::5], lat[::5, ::5], sst_filtered[::5, ::5],
                          cmap=cmap,
                          vmin=20, vmax=32,  # tighter range to show gradients
                          transform=ccrs.PlateCarree(),
                          alpha=0.8)

            ds.close()

        except Exception as e:
            print(f"❌ Skipped: {file} — {e}")

    print(f"  ✅ Batch done — {min(batch_start + batch_size, total)}/{total}")

# Add ENSO monitoring regions as boxes
enso_regions = {
    'Nino 4\n(160E-150W)':  (160, -200, -5, 5),   # Nino 4
    'Nino 3.4\n(170W-120W)': (-170, -120, -5, 5),  # Nino 3.4 (most important)
    'Nino 3\n(150W-90W)':   (-150, -90, -5, 5),    # Nino 3
    'Nino 1+2\n(90W-80W)':  (-90, -80, -10, 0),    # Nino 1+2
}

for name, (lon1, lon2, lat1, lat2) in enso_regions.items():
    ax.plot([lon1, lon2, lon2, lon1, lon1],
            [lat1, lat1, lat2, lat2, lat1],
            color='black', linewidth=1.5,
            transform=ccrs.PlateCarree())
    ax.text((lon1 + lon2) / 2, lat2 + 1, name,
            transform=ccrs.PlateCarree(),
            fontsize=7, ha='center', fontweight='bold')

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=20, vmax=32))
plt.colorbar(sm, ax=ax, label='SST (°C)', shrink=0.6, pad=0.05)

ax.set_title('MODIS Aqua SST — Pacific Ocean ENSO Regions\n(Blue = Cool La Niña | Red = Warm El Niño)', 
             fontsize=13)

plt.tight_layout()
plt.savefig('sst_pacific_enso.png', dpi=150, bbox_inches='tight')
print("\n✅ Done! Saved as sst_pacific_enso.png")
plt.show()