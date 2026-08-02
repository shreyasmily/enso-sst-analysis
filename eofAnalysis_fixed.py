import xarray as xr
import numpy as np
from eofs.xarray import Eof
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# ── Load anomalies ────────────────────────────────────────────────
sst_anomaly = xr.open_dataarray('data/sst_anomaly.nc')

# Fix longitude from -180:180 to 0:360
sst_anomaly = sst_anomaly.assign_coords(
    lon=(sst_anomaly.lon % 360)
).sortby('lon')

# Select the full Pacific
sst_pacific = sst_anomaly.sel(
    lat=slice(-30, 30),
    lon=slice(120, 290)
)

print(f"Lon range:  {float(sst_pacific.lon.min())} to {float(sst_pacific.lon.max())}")
print(f"Lat range:  {float(sst_pacific.lat.min())} to {float(sst_pacific.lat.max())}")
print(f"Time steps: {len(sst_pacific.time)}")

# Fill NaN with 0 for EOF
sst_pacific = sst_pacific.fillna(0)

# ── Latitude weighting ────────────────────────────────────────────
lat_vals = sst_pacific.lat.values
lon_vals = sst_pacific.lon.values

weights_2d = np.cos(np.deg2rad(lat_vals))
weights_2d = np.tile(weights_2d[:, np.newaxis], (1, len(lon_vals)))

print(f"SST shape:     {sst_pacific.shape}")
print(f"Weights shape: {weights_2d.shape}")

# ── Run EOF ───────────────────────────────────────────────────────
solver   = Eof(sst_pacific, weights=weights_2d)
eofs     = solver.eofs(neofs=3)
pcs      = solver.pcs(npcs=3)
variance = solver.varianceFraction(neigs=3)

print(f"EOF1 explains {float(variance[0])*100:.1f}% of variance")
print(f"EOF2 explains {float(variance[1])*100:.1f}% of variance")
print(f"EOF3 explains {float(variance[2])*100:.1f}% of variance")

# ── Save EOF variables ────────────────────────────────────────────
np.save('data/eofs.npy', eofs.values)
np.save('data/pcs.npy', pcs.values)
np.save('data/variance.npy', variance.values)
np.save('data/time.npy', sst_pacific.time.values)
np.save('data/lat.npy', sst_pacific.lat.values)
np.save('data/lon.npy', sst_pacific.lon.values)
print("Saved all EOF variables!")

# ── Build figure using ONLY fig.add_subplot — no plt.subplots() ──
# This is the key fix: only one axis is ever created per panel,
# so there are no hidden 0-1 axes underneath the cartopy maps.
fig = plt.figure(figsize=(18, 13))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

sign_correction = [-1, 1, 1]  # flip EOF1 only

eofs_plot = eofs.copy()
pcs_plot  = pcs.copy()

for i in range(3):

    eofs_plot[i] = eofs[i] * sign_correction[i]
    pcs_plot[:, i] = pcs[:, i] * sign_correction[i]

    # ── Left: EOF spatial map ─────────────────────────────────────
    # fig.add_subplot creates ONE cartopy axis directly — no regular
    # axis is created first, so no 0-1 box can appear underneath.
    ax_map = fig.add_subplot(gs[i, 0],
                             projection=ccrs.PlateCarree(central_longitude=180))

    eof_data = eofs_plot[i]
    vmax = float(np.abs(eof_data).quantile(0.99))
    vmin = -vmax

    eof_data.plot(ax=ax_map,
                  transform=ccrs.PlateCarree(),
                  cmap='RdBu_r',
                  vmin=vmin, vmax=vmax,
                  add_colorbar=True,
                  cbar_kwargs={'label': 'EOF Loading (unitless)', 'shrink': 0.8})

    # Remove xarray's auto-generated axis labels
    ax_map.set_xlabel('')
    ax_map.set_ylabel('')

    ax_map.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax_map.add_feature(cfeature.LAND, facecolor='lightgray')
    ax_map.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())

    # ONE gridlines call with lat/lon labels on left and bottom only.
    # x_inline=False and y_inline=False keep labels outside the map
    # so they don't overlap the data.
    gl = ax_map.gridlines(draw_labels=True, linewidth=0.5,
                          linestyle='--', x_inline=False, y_inline=False)
    gl.top_labels   = False   # no labels on top edge
    gl.right_labels = False   # no labels on right edge
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    ax_map.set_title(f'EOF{i+1} — {float(variance[i])*100:.1f}% variance',
                     fontsize=10)

    # ── Right: PC time series ─────────────────────────────────────
    # fig.add_subplot for regular (non-map) axes — same approach,
    # one axis per panel, no mixing with plt.subplots().
    ax_ts = fig.add_subplot(gs[i, 1])
    pc = pcs_plot[:, i]

    ax_ts.plot(sst_pacific.time, pc, color='steelblue', linewidth=0.8)
    ax_ts.axhline(0, color='black', linewidth=0.5)
    ax_ts.fill_between(sst_pacific.time, pc, 0,
                       where=(pc > 0), color='red',  alpha=0.3, label='El Niño')
    ax_ts.fill_between(sst_pacific.time, pc, 0,
                       where=(pc < 0), color='blue', alpha=0.3, label='La Niña')

    # ENSO event reference bands on PC1 only
 #   if i == 0:
  #      ax_ts.axvspan(np.datetime64('2015-11'), np.datetime64('2016-03'),
   #                   alpha=0.15, color='orange', label='Strong El Niño 2015-16')
    #    ax_ts.axvspan(np.datetime64('2020-08'), np.datetime64('2021-04'),
     #                 alpha=0.15, color='cyan', label='La Niña 2020-21')
      #  ax_ts.axvspan(np.datetime64('2023-06'), np.datetime64('2024-01'),
       #               alpha=0.15, color='orange')

    ax_ts.set_title(f'PC{i+1} Time Series', fontsize=10)
    ax_ts.set_ylabel('Amplitude')
    ax_ts.legend(fontsize=7)
    ax_ts.grid(True, alpha=0.3)

fig.suptitle('EOF Analysis of Pacific SST Anomalies',
             fontsize=14, fontweight='bold')

plt.savefig('figures/eof_analysis.png', dpi=150, bbox_inches='tight')
print("Saved figures/eof_analysis.png")