import xarray as xr

# Open your NC file
# ds = xr.open_dataset('20200627082501-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc')

# ds = xr.open_dataset('20200628163001-JPL-L2P_GHRSST-SSTskin-MODIS_A-N-v02.0-fv01.0.nc')

# ds = xr.open_dataset('20200627081501-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc')

ds = xr.open_dataset('20200627075000-JPL-L2P_GHRSST-SSTskin-MODIS_A-N-v02.0-fv01.0.nc')

# See everything inside
print(ds)

# List all variables
print(ds.data_vars)

# List dimensions
print(ds.dims)

import pickle
with open('ds.pkl', 'wb') as f:
    pickle.dump(ds, f)
print("Saved!")