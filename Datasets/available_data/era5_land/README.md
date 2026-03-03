# ERA5-Land Hourly Data (Vietnam)

## Overview
- **Source**: [Copernicus Climate Change Service (C3S)](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview)
- **Docs**: https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation (scroll for list of variables)
- **Resolution**: 0.1° x 0.1° (~10 km)
- **Time Step**: Hourly
- **Format**: GRIB / NetCDF (after conversion)
- **Spatial Coverage**: 22, 105, 20, 107.5 (Northern Vietnam)
- **Temporal coverage**: 2000-2022

## Variables

| Variable Code | Long Name | Units | Description |
|---|---|---|---|
| **t2m** | 2 metre temperature | Kelvin (K) | Temperature of air at 2m above the surface. |
| **skt** | Skin temperature | Kelvin (K) | Temperature of the surface of the Earth. |
| **stl1** | Soil temperature level 1 | Kelvin (K) | Temperature of soil in layer 1 (0 - 7 cm). |
| **stl2** | Soil temperature level 2 | Kelvin (K) | Temperature of soil in layer 2 (7 - 28 cm). |
| **stl3** | Soil temperature level 3 | Kelvin (K) | Temperature of soil in layer 3 (28 - 100 cm). |
| **stl4** | Soil temperature level 4 | Kelvin (K) | Temperature of soil in layer 4 (100 - 289 cm). |
| **swvl1** | Volumetric soil water layer 1 | m³/m⁻³ | Volume of water in soil layer 1 (0 - 7 cm). |
| **swvl2** | Volumetric soil water layer 2 | m³/m⁻³ | Volume of water in soil layer 2 (7 - 28 cm). |
| **swvl3** | Volumetric soil water layer 3 | m³/m⁻³ | Volume of water in soil layer 3 (28 - 100 cm). |
| **swvl4** | Volumetric soil water layer 4 | m³/m⁻³ | Volume of water in soil layer 4 (100 - 289 cm). |
| **pev** | Potential evaporation | meters (of water equivalent) | Accumulated water evaporation if vegetation water supply were unlimited. |
| **e** | Total evaporation | meters ((of water equivalent)) | Accumulated water evaporation from Earth's surface. |
| **tp** | Total precipitation | original: meters (m) converted(netcdf):  millimeters (mm) | Accumulated precipitation. |
| **lai_hv** | Leaf area index, high vegetation | m²/m⁻² | Area of leaves per unit area of ground for high vegetation type. |
| **lai_lv** | Leaf area index, low vegetation | m²/m⁻² | Area of leaves per unit area of ground for low vegetation type. |

**Note on accumulated variables**: Precipitation and evaporation are accumulated from the beginning of the forecast time and are reset every day.