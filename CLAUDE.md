# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An exploratory analysis of ENSO (El Niño–Southern Oscillation) variability in the tropical Pacific,
using Empirical Orthogonal Function (EOF) analysis on satellite-derived SST anomalies. See
[README.md](README.md) for the pipeline overview and [docs/ENSO_SST_Analysis.pdf](docs/ENSO_SST_Analysis.pdf)
for the full write-up with methodology and results.

This is a GitHub-backed project at `github.com/shreyasmily/enso-sst-analysis` (remote `origin`, branch
`main`). There is no package structure or test suite — each `.py` file is a standalone script run with
`python <script>.py` from the project root.

## Environment

Scripts run under the `podaac_env` conda environment (Python 3.11):

```
conda activate podaac_env
pip install -r requirements.txt
```

## Repository layout

```
sstAnomalies.py                          \  core pipeline, run in this
eofAnalysis_fixed.py                      |  order to reproduce all results
clusterMaps_correctedSignConvention.py   /
figures/                 result figures (tracked in git)
  eof_analysis.png         EOF spatial patterns + PC time series
  enso_events/              composite SST anomaly maps per El Niño / La Niña event
docs/
  ENSO_SST_Analysis.pdf    full write-up (tracked in git)
exploration/              earlier/exploratory scripts — not required to reproduce results
data/                      (gitignored) raw + intermediate NetCDF/pickle/npy data
```

`data/` is excluded from git (raw OISST + swath NetCDF files run into several GB). All three pipeline
scripts read/write under `data/` and `figures/` using paths relative to the project root — always run
them from the repo root, not from inside a subfolder.

## Data pipeline

1. **`sstAnomalies.py`** — loads daily AVHRR OISST files from `data/sst_gridded/`, computes a monthly
   climatology, subtracts it to produce deseasonalized SST anomalies → `data/sst_anomaly.nc`.
2. **`eofAnalysis_fixed.py`** — loads `data/sst_anomaly.nc`, selects the tropical Pacific box
   (30°S–30°N, 120°E–290°E, longitude converted to 0–360), applies latitude weighting, and runs
   `eofs.xarray.Eof` to get the first 3 EOF modes. Caches `eofs.npy`/`pcs.npy`/`variance.npy`/`time.npy`/
   `lat.npy`/`lon.npy` to `data/`, and saves `figures/eof_analysis.png`.
3. **`clusterMaps_correctedSignConvention.py`** — reloads `data/sst_anomaly.nc`, re-derives PC1, applies
   a sign correction (see below), thresholds at ±1σ to classify El Niño / La Niña months, fills gaps ≤2
   months, discards events <3 months, and saves composite maps to `figures/enso_events/{el_nino,la_nina}/`.

`exploration/` holds earlier/uncorrected versions of some scripts (`eofAnalysis.py`, `clusterMaps.py`)
and genuinely ad hoc ones (data QA, swath stitching, single-granule inspection via a pickled `ds.pkl`).
**These still use their original hardcoded relative paths** (e.g. `folder = 'sst_data'`,
`open('ds.pkl')`) and were not updated when the project was reorganized — check each script's path
assumptions before running it, or fix the path when you touch one.

## Conventions to preserve when editing

- Good-quality MODIS pixels are `quality_level >= 4`; filter on this before using SST values from
  swath data (only relevant in `exploration/`, not the gridded OISST pipeline).
- Raw MODIS temperature is in Kelvin — convert with `- 273.15`. OISST in `data/sst_gridded/` is already
  handled via `ds['analysed_sst'] - 273.15` in `sstAnomalies.py`.
- The EOF solver's sign is arbitrary. `eofAnalysis_fixed.py` and `clusterMaps_correctedSignConvention.py`
  apply an explicit `SIGN_CORRECTION = -1` so that positive PC1 = El Niño (warm) — don't drop this when
  touching PC1-dependent code.
- `clusterMaps_correctedSignConvention.py` currently only classifies El Niño / La Niña (the neutral-phase
  branch is commented out) — the `figures/enso_events/neutral/` images already in the repo are stale,
  from an earlier run of `exploration/clusterMaps.py`.

## Git workflow

Standard flow for changes: `git add .` → `git commit -m "..."` → `git push`. The remote push requires an
interactive browser sign-in (GitHub Credential Manager) the first time per machine/session — this can't
be done from a non-interactive shell.
