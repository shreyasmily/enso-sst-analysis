import xarray as xr
import numpy as np
import pandas as pd
import os

folder = 'sst_data'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

print(f"{'File':<60} {'Min Lat':>8} {'Max Lat':>8} {'Min Lon':>8} {'Max Lon':>8}")
print("-" * 100)

results = []

for file in files:
    try:
        ds = xr.open_dataset(os.path.join(folder, file))
        
        lat = ds['lat'].values
        lon = ds['lon'].values
        
        min_lat = round(float(np.nanmin(lat)), 3)
        max_lat = round(float(np.nanmax(lat)), 3)
        min_lon = round(float(np.nanmin(lon)), 3)
        max_lon = round(float(np.nanmax(lon)), 3)
        
        print(f"{file:<60} {min_lat:>8} {max_lat:>8} {min_lon:>8} {max_lon:>8}")
        
        results.append({
            'file': file,
            'min_lat': min_lat,
            'max_lat': max_lat,
            'min_lon': min_lon,
            'max_lon': max_lon
        })
        
        ds.close()
        
    except Exception as e:
        print(f"{file:<60} ❌ ERROR: {e}")

# Save to CSV
df = pd.DataFrame(results)
df.to_csv('file_lat_lon_summary.csv', index=False)
print(f"\nSaved summary of {len(df)} files to file_lat_lon_summary.csv")