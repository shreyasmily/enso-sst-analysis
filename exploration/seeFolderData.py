import xarray as xr
import pandas as pd
import os

folder = 'sst_data'
files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

print(f"{'File':<60} {'Timestamp':<25} {'nj':>6} {'ni':>6}")
print("-" * 100)

results = []  # moved to before the loop

for file in files:
    try:
        ds = xr.open_dataset(os.path.join(folder, file))
        timestamp = str(ds.time.values[0])[:19]
        nj = ds.sizes['nj']  # fixed: sizes instead of dims
        ni = ds.sizes['ni']  # fixed: sizes instead of dims
        print(f"{file:<60} {timestamp:<25} {nj:>6} {ni:>6}")
        results.append({'file': file, 'timestamp': timestamp, 'nj': nj, 'ni': ni})
        ds.close()
    except Exception as e:
        print(f"{file:<60} ❌ ERROR: {e}")

# Save to CSV
df = pd.DataFrame(results)
df.to_csv('file_summary.csv', index=False)
print(f"\nSaved summary of {len(df)} files to file_summary.csv")





# import xarray as xr
# import os

# folder = 'sst_data'
# files = sorted([f for f in os.listdir(folder) if f.endswith('.nc')])

# print(f"{'File':<60} {'Timestamp':<25} {'nj':>6} {'ni':>6}")
# print("-" * 100)

# for file in files:
  #  try:
   #     ds = xr.open_dataset(os.path.join(folder, file))
    #    timestamp = str(ds.time.values[0])[:19]
     #   nj = ds.dims['nj']
      #  ni = ds.dims['ni']
       # print(f"{file:<60} {timestamp:<25} {nj:>6} {ni:>6}")
       # ds.close()
 #   except Exception as e:
  #      print(f"{file:<60} ❌ ERROR: {e}")

# import pandas as pd
# df = pd.DataFrame(results)
# df.to_csv('file_summary.csv', index=False)