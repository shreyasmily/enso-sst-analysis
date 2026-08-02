import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy import ndimage
from eofs.xarray import Eof
import os
 
# ── Load and prep data (same as eofAnalysis.py) ───────────────────────────────
sst_anomaly = xr.open_dataarray('sst_anomaly.nc')
 
sst_anomaly = sst_anomaly.assign_coords(
    lon=(sst_anomaly.lon % 360)
).sortby('lon')
 
sst_pacific = sst_anomaly.sel(
    lat=slice(-30, 30),
    lon=slice(120, 290)
).fillna(0)

# ── Resample to monthly averages ──────────────────────────────────
sst_pacific = sst_pacific.resample(time='MS').mean()
print(f"After resampling: {sst_pacific.shape}")  # should be (~168, lat, lon)
 
# Latitude weighting
lat_vals = sst_pacific.lat.values
lon_vals = sst_pacific.lon.values
weights_2d = np.cos(np.deg2rad(lat_vals))
weights_2d = np.tile(weights_2d[:, np.newaxis], (1, len(lon_vals)))
 
# Run EOF
solver   = Eof(sst_pacific, weights=weights_2d)
pcs      = solver.pcs(npcs=3)
variance = solver.varianceFraction(neigs=3)
 
# ── PC1 and thresholds ────────────────────────────────────────────────────────
# .values converts to numpy, .squeeze() drops any extra dimensions,
# .flatten() guarantees a strictly 1D array of length = number of time steps
pc1_raw = pcs[:, 0]
pc1     = np.array(pc1_raw).squeeze().flatten()   # shape: (n_timesteps,)
times   = sst_pacific.time.values                 # pull time axis once for reuse
 
# Sanity check
print(f"PC1 length:  {len(pc1)} time steps")
print(f"Time length: {len(times)} time steps")
assert len(pc1) == len(times), "PC1 and time axis length mismatch!"
 
sigma = float(pc1.std())
 
print(f"PC1 σ = {sigma:.2f}")
print(f"El Niño  → PC1 > +{sigma:.2f}")
print(f"La Niña  → PC1 < -{sigma:.2f}")
print(f"Neutral  → in between\n")
 
# ── Settings ──────────────────────────────────────────────────────────────────
MIN_DURATION  = 3    # minimum months to count as a real event
GAP_FILL      = 2    # merge events separated by this many months or fewer
 
# Symmetric colorscale — computed once from full dataset
vmax = float(np.nanpercentile(np.abs(sst_pacific.values), 99))
vmin = -vmax
 
# Output folders
os.makedirs('enso_events/el_nino',  exist_ok=True)
os.makedirs('enso_events/la_nina',  exist_ok=True)
os.makedirs('enso_events/neutral',  exist_ok=True)
 
 
# ── Helper functions ──────────────────────────────────────────────────────────
 
def fill_gaps(mask, max_gap):
    """
    Merge contiguous True blocks that are separated by max_gap or fewer False values.
    Prevents a single event from being split by a brief dip below the threshold.
    """
    filled = mask.copy()
    labeled, n = ndimage.label(~mask)   # label the FALSE regions (gaps)
    for gap_id in range(1, n + 1):
        gap_indices = np.where(labeled == gap_id)[0]
        if len(gap_indices) <= max_gap:
            filled[gap_indices] = True  # fill the short gap
    return filled
 
 
def get_events(mask, min_duration):
    """
    Given a boolean mask, return a list of (start_idx, end_idx) tuples,
    one per contiguous True block that meets the minimum duration.
    """
    labeled, n = ndimage.label(mask)
    events = []
    for event_id in range(1, n + 1):
        indices = np.where(labeled == event_id)[0]
        if len(indices) >= min_duration:
            events.append((indices[0], indices[-1]))
    return events
 
 
def plot_event(composite, times, phase, event_num, total_events):
    """
    Plot a single composite SST anomaly map for one event.
    """
    start = str(times[0])[:7]
    end   = str(times[-1])[:7]
    n_months = len(times)
 
    fig, ax = plt.subplots(
        figsize=(12, 5),
        subplot_kw={'projection': ccrs.PlateCarree(central_longitude=180)}
    )
 
    composite.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap='RdBu_r',
        vmin=vmin,
        vmax=vmax,
        add_colorbar=True,
        cbar_kwargs={'label': 'SST Anomaly (°C)', 'shrink': 0.8}
    )
 
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())
 
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--',
                      x_inline=False, y_inline=False)
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}
 
    ax.set_title(
        f'{phase} Event {event_num} of {total_events}:  {start}  →  {end}  '
        f'({n_months} months)',
        fontsize=12, fontweight='bold'
    )
 
    # Filename: e.g. "el_nino/el_nino_event1_2015-11_2016-03.png"
    phase_folder = phase.lower().replace(' ', '_')
    fname = f'enso_events/{phase_folder}/{phase_folder}_event{event_num}_{start}_{end}.png'
    plt.tight_layout()
    plt.savefig(fname, dpi=150, bbox_inches='tight')
    print(f"  Saved: {fname}")
    plt.close()
 
 
# ── Main event detection and plotting loop ────────────────────────────────────
 
# Build masks as plain 1D numpy boolean arrays
phases = {
    'El Nino': (pc1 >  sigma),
    'La Nina': (pc1 < -sigma),
    'Neutral': ((pc1 >= -sigma) & (pc1 <= sigma)),
}
 
summary = {}   # stores event date ranges for printing at the end
 
for phase_name, raw_mask in phases.items():
 
    # Ensure mask is a plain 1D numpy boolean array
    if hasattr(raw_mask, 'values'):
        raw_mask_np = raw_mask.values.squeeze().flatten().astype(bool)
    else:
        raw_mask_np = np.asarray(raw_mask).squeeze().flatten().astype(bool)
    
    print(f"  Mask length: {len(raw_mask_np)} (should equal number of time steps)")
 
    # Fill short gaps so one event isn't split into two
    filled_mask = fill_gaps(raw_mask_np, max_gap=GAP_FILL)
 
    # Get list of (start, end) index pairs for each event
    events = get_events(filled_mask, min_duration=MIN_DURATION)
 
    print(f"\n{'─'*50}")
    print(f"{phase_name}: {len(events)} event(s) found")
    print(f"{'─'*50}")
 
    summary[phase_name] = []
 
    for event_num, (start_idx, end_idx) in enumerate(events, start=1):
 
        # Slice the SST data for this event
        event_sst   = sst_pacific.isel(time=slice(start_idx, end_idx + 1))
        event_times = times[start_idx:end_idx + 1]
 
        # Composite = mean SST anomaly across all months in this event
        composite = event_sst.mean(dim='time')
 
        # Plot and save
        plot_event(composite, event_times, phase_name, event_num, len(events))
 
        # Store for summary
        start_str = str(event_times[0])[:7]
        end_str   = str(event_times[-1])[:7]
        summary[phase_name].append(f"  Event {event_num}: {start_str} → {end_str} ({len(event_times)} months)")
 
 
# ── Print summary ─────────────────────────────────────────────────────────────
print(f"\n{'═'*50}")
print("ENSO EVENT SUMMARY")
print(f"{'═'*50}")
print(f"Threshold: ±{sigma:.2f} (1σ of PC1)")
print(f"Minimum event duration: {MIN_DURATION} months")
print(f"Gap fill tolerance: {GAP_FILL} months\n")
 
for phase_name, event_list in summary.items():
    print(f"{phase_name} ({len(event_list)} events):")
    for e in event_list:
        print(e)
    print()
 
print("All figures saved to enso_events/")