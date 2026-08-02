import xarray as xr
import numpy as np
from eofs.xarray import Eof
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Load anomalies
sst_anomaly = xr.open_dataarray('sst_anomaly.nc')

# Fix longitude from -180:180 to 0:360
sst_anomaly = sst_anomaly.assign_coords(
    lon=(sst_anomaly.lon % 360)
).sortby('lon')

# Now select the full Pacific
sst_pacific = sst_anomaly.sel(
    lat=slice(-30, 30),
    lon=slice(120, 290)
)

print(f"Lon range: {float(sst_pacific.lon.min())} to {float(sst_pacific.lon.max())}")
print(f"Lat range: {float(sst_pacific.lat.min())} to {float(sst_pacific.lat.max())}")
print(f"Time steps: {len(sst_pacific.time)}")
# Fill NaN with 0 for EOF (land/missing data)
sst_pacific = sst_pacific.fillna(0)

# ── Latitude weighting ────────────────────────────────────────────
lat_vals = sst_pacific.lat.values
lon_vals = sst_pacific.lon.values

# Create 2D weights matching (lat, lon)
weights_2d = np.cos(np.deg2rad(lat_vals))
weights_2d = np.tile(weights_2d[:, np.newaxis], (1, len(lon_vals)))

print(f"SST shape:     {sst_pacific.shape}")       # should be (time, lat, lon)
print(f"Weights shape: {weights_2d.shape}") 

# Run EOF
solver = Eof(sst_pacific, weights=weights_2d)

# Get first 3 EOFs
eofs = solver.eofs(neofs=3)
pcs  = solver.pcs(npcs=3)
variance = solver.varianceFraction(neigs=3)

print(f"EOF1 explains {float(variance[0])*100:.1f}% of variance")
print(f"EOF2 explains {float(variance[1])*100:.1f}% of variance")
print(f"EOF3 explains {float(variance[2])*100:.1f}% of variance")

np.save('eofs.npy', eofs.values)
np.save('pcs.npy', pcs.values)
np.save('variance.npy', variance.values)

# Save time coordinate for the PC time series plot
np.save('time.npy', sst_pacific.time.values)

# Save lat/lon for the EOF spatial plot
np.save('lat.npy', sst_pacific.lat.values)
np.save('lon.npy', sst_pacific.lon.values)

print("Saved all EOF variables!")

# ----------transfer to new file

fig, axes = plt.subplots(3, 2, figsize=(16, 12))


eof_names = ['EOF1 (ENSO)', 'EOF2', 'EOF3']


for i in range(3):
    # --- Left column: EOF spatial pattern ---
    ax_map = axes[i, 0]
    print("loop")
    ax_map = plt.subplot(3, 2, i*2+1,
                          projection=ccrs.PlateCarree(central_longitude=180))
    
    ax_map.set_frame_on(False)  # removes the box

    eof_data = eofs[i]
    
    # Auto-scale colormap to actual data range
    vmax = float(np.abs(eof_data).quantile(0.99))
    vmin = -vmax

    eof_data.plot(ax=ax_map,
                 transform=ccrs.PlateCarree(),
                 cmap='RdBu_r',
                 vmin=vmin, vmax=vmax,
                 add_colorbar=True,
                 cbar_kwargs={'label': 'EOF Loading (unitless)'}) 
				# eigenvalue?


    ax_map.add_feature(cfeature.COASTLINE)
    ax_map.add_feature(cfeature.LAND, facecolor='lightgray')
#    ax_map.gridlines(draw_labels=True)


    # Fix double labels — turn off default axes ticks
    ax_map.set_xticks([])
    ax_map.set_yticks([])

    # Gridlines with labels only on left and bottom
    gl = ax_map.gridlines(draw_labels=True, linewidth=0.5, linestyle='--', x_inline = False, y_inline=False)
    gl.top_labels   = False   # no labels on top
    gl.right_labels = False   # no labels on right
    gl.left_labels   = False   # no labels on left
    gl.bottom_labels = False   # no labels on bottom
#    gl.xlabel_style  = {'size': 8}   # smaller font to avoid crowding
#    gl.ylabel_style  = {'size': 8}

    # Set extent to Pacific region
    ax_map.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())

    ax_map.set_title(f'EOF{i+1} — {float(variance[i])*100:.1f}% variance')

    # --- Right column: Principal Component time series ---
    ax_ts = axes[i, 1]
    pc = pcs[:, i]
    ax_ts.plot(sst_pacific.time, pc, color='steelblue', linewidth=0.8)
    ax_ts.axhline(0, color='black', linewidth=0.5)
    ax_ts.fill_between(sst_pacific.time,
                        pc, 0,
                        where=(pc > 0), color='red',   alpha=0.3, label='El Niño')
    ax_ts.fill_between(sst_pacific.time,
                        pc, 0,
                        where=(pc < 0), color='blue',  alpha=0.3, label='La Niña')
    ax_ts.set_title(f'PC{i+1} Time Series')
    ax_ts.set_ylabel('Amplitude')
    ax_ts.legend()
    # Add known ENSO event markers
#    if i == 0:
#        ax_ts.axvspan(np.datetime64('2015-11'), np.datetime64('2016-03'),
#                      alpha=0.15, color='orange', label='Strong El Niño 2015-16')
#        ax_ts.axvspan(np.datetime64('2020-08'), np.datetime64('2021-04'),
#                      alpha=0.15, color='cyan', label='La Niña 2020-21')
#        ax_ts.axvspan(np.datetime64('2023-06'), np.datetime64('2024-01'),
#                      alpha=0.15, color='orange')


plt.suptitle('EOF Analysis of Pacific SST Anomalies', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('eof_analysis.png', dpi=150, bbox_inches='tight')
print("Saved eof_analysis.png")
plt.show()