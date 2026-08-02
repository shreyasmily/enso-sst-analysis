import xarray as xr
import numpy as np
from eofs.xarray import Eof
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os

# ── 1. Load all files and extract Pacific region ──────────────────
folder = 'sst_data'
files  = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

print(f"Loading {len(files)} files...")

sst_list = []
times    = []

for i, file in enumerate(files):
    try:
        ds      = xr.open_dataset(os.path.join(folder, file))
        sst     = ds['sea_surface_temperature'].isel(time=0) - 273.15
        quality = ds['quality_level'].isel(time=0)
        lat     = ds['lat'].values
        lon     = ds['lon'].values
        time    = ds.time.values[0]

        # Filter good quality
        sst_filtered = sst.where(quality >= 4)

        sst_list.append(sst_filtered.values)
        times.append(time)
        ds.close()

        if i % 100 == 0:
            print(f"  Loaded {i}/{len(files)}")

    except Exception as e:
        print(f"❌ Skipped: {file} — {e}")

print(f"Loaded {len(sst_list)} files successfully")

# ── 2. Note About EOF on Swath Data ───────────────────────────────
# Because each file has different nj/ni sizes and lat/lon grids,
# we need to bin everything onto a regular grid first

print("Binning onto regular grid...")

# Define regular grid
lat_bins = np.arange(-30, 31, 0.5)   # 0.5 degree resolution
lon_bins = np.arange(120, 291, 0.5)

nlat = len(lat_bins)
nlon = len(lon_bins)
ntime = len(sst_list)

# Create empty regular grid
sst_grid = np.full((ntime, nlat, nlon), np.nan)

for t, (sst_swath, lat, lon) in enumerate(zip(sst_list,
        [xr.open_dataset(os.path.join(folder, f))['lat'].values for f in files[:ntime]],
        [xr.open_dataset(os.path.join(folder, f))['lon'].values for f in files[:ntime]])):

    # Bin each pixel into the regular grid
    lat_idx = np.searchsorted(lat_bins, lat.flatten()) - 1
    lon_idx = np.searchsorted(lon_bins, lon.flatten()) - 1
    sst_flat = sst_swath.flatten()

    valid = (
        (lat_idx >= 0) & (lat_idx < nlat) &
        (lon_idx >= 0) & (lon_idx < nlon) &
        ~np.isnan(sst_flat)
    )

    for li, loi, val in zip(lat_idx[valid], lon_idx[valid], sst_flat[valid]):
        sst_grid[t, li, loi] = val

    if t % 100 == 0:
        print(f"  Gridded {t}/{ntime}")

print("Gridding done!")


# ── 3. Build xarray DataArray on regular grid ─────────────────────
sst_da = xr.DataArray(
    sst_grid,
    dims=['time', 'lat', 'lon'],
    coords={
        'time': times,
        'lat':  lat_bins,
        'lon':  lon_bins
    }
)

# Fill remaining NaN with 0 for EOF
sst_filled = sst_da.fillna(0)


sst_filled.to_netcdf('sst_gridded_2day.nc')
print("Saved sst_gridded_2day.nc")

# ── 4. Latitude weighting ─────────────────────────────────────────
# NEW - correct shape (1, 122, 342) to match (time, lat, lon)
weights = np.cos(np.deg2rad(sst_da.lat)).values
weights = np.broadcast_to(weights[:, np.newaxis], (len(lat_bins), len(lon_bins)))
weights = weights[np.newaxis, :, :]  # add time dimension

# ── 5. Run EOF ────────────────────────────────────────────────────
print("Running EOF...")
solver   = Eof(sst_filled, weights=weights)
eofs     = solver.eofs(neofs=3)
pcs      = solver.pcs(npcs=3)
variance = solver.varianceFraction(neigs=3)

print(f"EOF1: {float(variance[0])*100:.1f}% variance")
print(f"EOF2: {float(variance[1])*100:.1f}% variance")
print(f"EOF3: {float(variance[2])*100:.1f}% variance")

# ── 6. Plot EOF spatial patterns ──────────────────────────────────
fig = plt.figure(figsize=(16, 12))

for i in range(3):
    ax = plt.subplot(3, 2, i*2+1,
                     projection=ccrs.PlateCarree(central_longitude=180))
    eofs[i].plot(ax=ax,
                 transform=ccrs.PlateCarree(),
                 cmap='RdBu_r',
                 add_colorbar=True)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.set_title(f'EOF{i+1} — {float(variance[i])*100:.1f}% variance')

    # PC time series
    ax_ts = plt.subplot(3, 2, i*2+2)
    ax_ts.plot(range(len(pcs[:, i])), pcs[:, i],
               color='steelblue', linewidth=0.8)
    ax_ts.axhline(0, color='black', linewidth=0.5)
    ax_ts.fill_between(range(len(pcs[:, i])), pcs[:, i], 0,
                        where=(pcs[:, i] > 0), color='red',  alpha=0.3)
    ax_ts.fill_between(range(len(pcs[:, i])), pcs[:, i], 0,
                        where=(pcs[:, i] < 0), color='blue', alpha=0.3)
    ax_ts.set_title(f'PC{i+1} Time Series')
    ax_ts.set_xlabel('File number (time)')
    ax_ts.set_ylabel('Amplitude')

plt.suptitle('EOF Analysis — 2 Day SST Sample (Learning Run)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('eof_2day.png', dpi=150, bbox_inches='tight')
print("Saved eof_2day.png")
plt.show()