fig, axes = plt.subplots(3, 2, figsize=(16, 12))

eof_names = ['EOF1 (ENSO)', 'EOF2', 'EOF3']

for i in range(3):
    # --- Left column: EOF spatial pattern ---
    ax_map = axes[i, 0]
    ax_map = plt.subplot(3, 2, i*2+1,
                          projection=ccrs.PlateCarree(central_longitude=180))

    eofs[i].plot(ax=ax_map,
                 transform=ccrs.PlateCarree(),
                 cmap='RdBu_r',
                 vmin=-0.1, vmax=0.1,
                 add_colorbar=True)

    ax_map.add_feature(cfeature.COASTLINE)
    ax_map.add_feature(cfeature.LAND, facecolor='lightgray')
    ax_map.set_title(f'{eof_names[i]} — {float(variance[i])*100:.1f}% variance')

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

plt.suptitle('EOF Analysis of Pacific SST Anomalies', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('eof_analysis.png', dpi=150, bbox_inches='tight')
print("Saved eof_analysis.png")
plt.show()