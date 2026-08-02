# ENSO SST Analysis

An exploratory analysis of El Niño–Southern Oscillation (ENSO) variability in the tropical Pacific,
using Empirical Orthogonal Function (EOF) analysis on satellite-derived sea surface temperature (SST)
anomalies. Done as preparation for graduate-level research.

The full write-up, with methodology and figures, is in [`docs/ENSO_SST_Analysis.pdf`](docs/ENSO_SST_Analysis.pdf).

**Headline result:** EOF1 cleanly recovers the ENSO spatial pattern and explains 31.3% of total SST
anomaly variance (EOF2: 10.0%, EOF3: 5.8%) over the tropical Pacific, 2016–2024. Thresholding the PC1
time series at ±1σ identifies individual El Niño / La Niña events, including the 2015–16 and 2023–24
El Niño events and the 2020–22 "triple-dip" La Niña.

## Data

Analysis uses the **NOAA AVHRR Optimally Interpolated SST (OISST) v2.1** product — daily, gap-free,
0.25° gridded SST, 1 Jan 2016 – 31 Dec 2024 (DOI: [10.5067/GHAAO-4BC21](https://doi.org/10.5067/GHAAO-4BC21),
via PO.DAAC).

The `exploration/` scripts additionally use a small sample of **MODIS Aqua L2P swath SST**
(DOI: [10.5067/GHGMR-4FJ04](https://doi.org/10.5067/GHGMR-4FJ04)) from an earlier trial to understand
the raw satellite data format, before switching to the gridded OISST product for the full analysis.

Raw and intermediate data files (NetCDF, pickled datasets, `.npy` arrays — several GB total) are **not**
committed to this repository; they're excluded via `.gitignore`. To reproduce the pipeline, download the
OISST data for your date range of interest from PO.DAAC and place the daily `.nc` files in
`data/sst_gridded/`.

## Setup

```
conda create -n podaac_env python=3.11
conda activate podaac_env
pip install -r requirements.txt
```

## Pipeline

Run from the project root, in order:

1. **`sstAnomalies.py`** — loads daily OISST files from `data/sst_gridded/`, computes the monthly
   climatology, and subtracts it to produce deseasonalized SST anomalies → `data/sst_anomaly.nc`.
2. **`eofAnalysis_fixed.py`** — selects the tropical Pacific box (30°S–30°N, 120°E–290°E), applies
   latitude weighting, and runs EOF/PCA decomposition (via the [`eofs`](https://ajdawson.github.io/eofs/)
   library) to get the first 3 modes. Saves the EOF/PC arrays to `data/` and the summary figure to
   `figures/eof_analysis.png`.
3. **`clusterMaps_correctedSignConvention.py`** — thresholds the (sign-corrected) PC1 time series at
   ±1σ to classify months as El Niño / La Niña, merges brief gaps, discards events shorter than 3 months,
   and saves composite SST anomaly maps for each event to `figures/enso_events/`.

```
python sstAnomalies.py
python eofAnalysis_fixed.py
python clusterMaps_correctedSignConvention.py
```

## Repository structure

```
sstAnomalies.py                        \  core pipeline — run in this
eofAnalysis_fixed.py                    |  order to reproduce all results
clusterMaps_correctedSignConvention.py  /
figures/                 result figures produced by the pipeline above
  eof_analysis.png         EOF spatial patterns + PC time series
  enso_events/              composite SST anomaly maps per El Niño / La Niña event
docs/
  ENSO_SST_Analysis.pdf    full write-up
exploration/              earlier/exploratory scripts (data QA, swath plotting,
                           un-corrected first-pass versions, ad hoc inspection).
                           Not required to reproduce the results above, and some
                           still reference their original relative data paths.
data/                     (gitignored) raw + intermediate NetCDF/pickle/npy data
```

## Notes

- The sign of an EOF eigenvector is mathematically arbitrary. `eofAnalysis_fixed.py` and
  `clusterMaps_correctedSignConvention.py` apply an explicit correction so that positive PC1
  corresponds to El Niño (warm) conditions, matching physical convention.
- `exploration/` contains the earlier, uncorrected versions of some scripts (e.g. `eofAnalysis.py`,
  `clusterMaps.py`) kept for reference alongside genuinely exploratory ones (data QA, swath stitching,
  single-granule inspection).
