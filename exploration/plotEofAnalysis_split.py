import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr

# ── Load saved EOF variables ──────────────────────────────────────
eofs_vals = np.load('eofs.npy')
pcs_vals  = np.load('pcs.npy')
variance  = np.load('variance.npy')
time      = np.load('time.npy', allow_pickle=True)
lat       = np.load('lat.npy')
lon       = np.load('lon.npy')

# Wrap back into xarray for plotting
eofs = xr.DataArray(eofs_vals, dims=['eof', 'lat', 'lon'],
                    coords={'lat': lat, 'lon': lon})
pcs  = pcs_vals

print("Loaded all EOF variables!")
print(f"EOF shape:      {eofs.shape}")
print(f"PC shape:       {pcs.shape}")
print(f"Variance:       {variance}")

# ── Build figure ──────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 13))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.3)

for i in range(3):
    # ── Left: EOF spatial map ─────────────────────────────────────
    ax_map = fig.add_subplot(gs[i, 0],
                             projection=ccrs.PlateCarree(central_longitude=180))

    eof_data = eofs[i]
    vmax = float(np.abs(eof_data).quantile(0.99))
    vmin = -vmax

    eof_data.plot(ax=ax_map,
                  transform=ccrs.PlateCarree(),
                  cmap='RdBu_r',
                  vmin=vmin, vmax=vmax,
                  add_colorbar=True,
                  cbar_kwargs={'label': 'EOF Loading (unitless)',
                               'shrink': 0.8})

    ax_map.set_xlabel('')
    ax_map.set_ylabel('')
    ax_map.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax_map.add_feature(cfeature.LAND, facecolor='lightgray')
    ax_map.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())

    gl = ax_map.gridlines(draw_labels=True, linewidth=0.5,
                          linestyle='--', x_inline=False, y_inline=False)
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    ax_map.set_title(f'EOF{i+1} — {float(variance[i])*100:.1f}% variance',
                     fontsize=10)

    # ── Right: PC time series ─────────────────────────────────────
    ax_ts = fig.add_subplot(gs[i, 1])
    pc = pcs[:, i]

    ax_ts.plot(time, pc, color='steelblue', linewidth=0.8)
    ax_ts.axhline(0, color='black', linewidth=0.5)
    ax_ts.fill_between(time, pc, 0,
                       where=(pc > 0), color='red',  alpha=0.3, label='El Niño')
    ax_ts.fill_between(time, pc, 0,
                       where=(pc < 0), color='blue', alpha=0.3, label='La Niña')

    if i == 0:
        ax_ts.axvspan(np.datetime64('2015-11'), np.datetime64('2016-03'),
                      alpha=0.15, color='orange', label='Strong El Niño 2015-16')
        ax_ts.axvspan(np.datetime64('2020-08'), np.datetime64('2021-04'),
                      alpha=0.15, color='cyan', label='La Niña 2020-21')
        ax_ts.axvspan(np.datetime64('2023-06'), np.datetime64('2024-01'),
                      alpha=0.15, color='orange')

    ax_ts.set_title(f'PC{i+1} Time Series', fontsize=10)
    ax_ts.set_ylabel('Amplitude')
    ax_ts.legend(fontsize=7)
    ax_ts.grid(True, alpha=0.3)

fig.suptitle('EOF Analysis of Pacific SST Anomalies',
             fontsize=14, fontweight='bold')

plt.savefig('eof_analysis.png', dpi=150, bbox_inches='tight')
print("Saved eof_analysis.png")