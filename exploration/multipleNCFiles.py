# import xarray as xr

# Load multiple files at once
# ds = xr.open_mfdataset('sst_data/*.nc', combine='by_coords')
# print(ds.dims)  # time will be > 1

import xarray as xr

ds = xr.open_mfdataset('sst_data/*.nc', combine='nested', concat_dim='time')
print(ds)
print(f"Total time steps: {len(ds.time)}")