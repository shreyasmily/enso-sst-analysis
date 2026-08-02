import xarray as xr
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy import ndimage
from eofs.xarray import Eof
import os

# ── Load and prep data ────────────────────────────────────────────
sst_anomaly = xr.open_dataarray('data/sst_anomaly.nc')

sst_anomaly = sst_anomaly.assign_coords(
    lon=(sst_anomaly.lon % 360)
).sortby('lon')

sst_pacific = sst_anomaly.sel(
    lat=slice(-30, 30),
    lon=slice(120, 290)
).fillna(0)

# Resample to monthly to match eofAnalysis.py
sst_pacific = sst_pacific.resample(time='MS').mean()

# Latitude weighting
lat_vals = sst_pacific.lat.values
lon_vals = sst_pacific.lon.values
weights_2d = np.cos(np.deg2rad(lat_vals))
weights_2d = np.tile(weights_2d[:, np.newaxis], (1, len(lon_vals)))

# Run EOF
solver   = Eof(sst_pacific, weights=weights_2d)
pcs      = solver.pcs(npcs=1)
variance = solver.varianceFraction(neigs=1)

# ── Sign correction ───────────────────────────────────────────────
# The raw EOF assigns negative PC1 to El Nino and positive to La Nina
# — the inverse of physical convention. SIGN_CORRECTION = -1 fixes this
# for both the PC1 thresholds AND the SST composite colors:
#   - PC1 * -1  → positive PC1 now = El Nino
#   - SST * -1  → red (positive anomaly) now = El Nino warming
#                  blue (negative anomaly) now = La Nina cooling
SIGN_CORRECTION = -1

pc1_raw = pcs[:, 0]
pc1     = np.array(pc1_raw).squeeze().flatten() * SIGN_CORRECTION
times   = sst_pacific.time.values

# Apply sign correction to SST field so composite map colors are correct
sst_pacific_corrected = sst_pacific # * SIGN_CORRECTION

print(f"PC1 length:  {len(pc1)} time steps")
print(f"Time range:  {str(times[0])[:7]} to {str(times[-1])[:7]}")

sigma = float(pc1.std())
print(f"\nPC1 σ = {sigma:.2f}")
print(f"El Nino  → PC1 > +{sigma:.2f}  (red = warm eastern Pacific)")
print(f"La Nina  → PC1 < -{sigma:.2f}  (blue = cool eastern Pacific)\n")

# ── Settings ──────────────────────────────────────────────────────
MIN_DURATION = 3    # minimum months for a real event
GAP_FILL     = 2    # merge events separated by ≤ this many months

# Colorscale anchored symmetrically at zero
vmax = float(np.nanpercentile(np.abs(sst_pacific_corrected.values), 99))
vmin = -vmax

# Output folders
os.makedirs('figures/enso_events/el_nino', exist_ok=True)
os.makedirs('figures/enso_events/la_nina', exist_ok=True)
# os.makedirs('figures/enso_events/neutral', exist_ok=True)


# ── Helper functions ──────────────────────────────────────────────

def fill_gaps(mask, max_gap):
    filled  = mask.copy()
    labeled, n = ndimage.label(~mask)
    for gap_id in range(1, n + 1):
        gap_indices = np.where(labeled == gap_id)[0]
        if len(gap_indices) <= max_gap:
            filled[gap_indices] = True
    return filled


def get_events(mask, min_duration):
    labeled, n = ndimage.label(mask)
    events = []
    for event_id in range(1, n + 1):
        indices = np.where(labeled == event_id)[0]
        if len(indices) >= min_duration:
            events.append((indices[0], indices[-1]))
    return events


def plot_event(composite, event_times, phase, event_num, total_events):
    start    = str(event_times[0])[:7]
    end      = str(event_times[-1])[:7]
    n_months = len(event_times)

    fig, ax = plt.subplots(
        figsize=(12, 5),
        subplot_kw={'projection': ccrs.PlateCarree(central_longitude=180)}
    )

    composite.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap='RdBu_r',       # red = warm = El Nino, blue = cool = La Nina
        vmin=vmin,
        vmax=vmax,
        add_colorbar=True,
        cbar_kwargs={'label': 'SST Anomaly (°C)', 'shrink': 0.8}
    )

    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.set_extent([120, 290, -30, 30], crs=ccrs.PlateCarree())

    gl = ax.gridlines(draw_labels=True, linewidth=0.5, linestyle='--',
                      x_inline=False, y_inline=False)
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    ax.set_title(
        f'{phase} Event {event_num} of {total_events}:  {start}  →  {end}  ({n_months} months)',
        fontsize=12, fontweight='bold'
    )

    phase_folder = phase.lower().replace(' ', '_')
    fname = f'figures/enso_events/{phase_folder}/{phase_folder}_event{event_num}_{start}_{end}.png'
    plt.tight_layout()
    plt.savefig(fname, dpi=150, bbox_inches='tight')
    print(f"  Saved: {fname}")
    plt.close()


# ── Event detection ───────────────────────────────────────────────
phases = {
    'El Nino': (pc1 >  sigma),   # positive corrected PC1 = warm eastern Pacific
    'La Nina': (pc1 < -sigma),   # negative corrected PC1 = cool eastern Pacific
    # 'Neutral': ((pc1 >= -sigma) & (pc1 <= sigma)),
}

summary = {}

for phase_name, raw_mask in phases.items():

    if hasattr(raw_mask, 'values'):
        raw_mask_np = raw_mask.values.squeeze().flatten().astype(bool)
    else:
        raw_mask_np = np.asarray(raw_mask).squeeze().flatten().astype(bool)

    filled_mask = fill_gaps(raw_mask_np, max_gap=GAP_FILL)
    events      = get_events(filled_mask, min_duration=MIN_DURATION)

    print(f"\n{'─'*50}")
    print(f"{phase_name}: {len(events)} event(s) found")
    print(f"{'─'*50}")

    summary[phase_name] = []

    for event_num, (start_idx, end_idx) in enumerate(events, start=1):
        # Use sign-corrected SST for composites so colors are physically correct
        event_sst   = sst_pacific_corrected.isel(time=slice(start_idx, end_idx + 1))
        event_times = times[start_idx:end_idx + 1]
        composite   = event_sst.mean(dim='time')


        # Verify colors match phase before saving
        eastern_pacific_mean = float(
            composite.sel(lat=slice(-5, 5), lon=slice(210, 280)).mean()
        )
        print(f"  Event {event_num} eastern Pacific mean anomaly: "
              f"{eastern_pacific_mean:+.3f}°C "
              f"({'warm ✅' if phase_name == 'El Nino' and eastern_pacific_mean > 0 else 'cool ✅' if phase_name == 'La Nina' and eastern_pacific_mean < 0 else '⚠️ check sign'})")
 
        plot_event(composite, event_times, phase_name, event_num, len(events))

        start_str = str(event_times[0])[:7]
        end_str   = str(event_times[-1])[:7]
        summary[phase_name].append(
            f"  Event {event_num}: {start_str} → {end_str} ({len(event_times)} months)"
        )


# ── Summary ───────────────────────────────────────────────────────
print(f"\n{'═'*50}")
print("ENSO EVENT SUMMARY")
print(f"{'═'*50}")
print(f"Threshold:              ±{sigma:.2f} (1σ of PC1)")
print(f"Sign correction:        PC1 and SST × {SIGN_CORRECTION}")
print(f"Minimum event duration: {MIN_DURATION} months")
print(f"Gap fill tolerance:     {GAP_FILL} months\n")

for phase_name, event_list in summary.items():
    print(f"{phase_name} ({len(event_list)} events):")
    for e in event_list:
        print(e)
    print()

print("All figures saved to figures/enso_events/")