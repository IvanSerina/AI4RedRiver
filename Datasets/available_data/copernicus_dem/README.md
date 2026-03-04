# Copernicus DEM (GLO-30 DGED)

This directory contains tiles from the **Copernicus DEM GLO-30** Digital Elevation Model, a global elevation dataset derived from TanDEM-X SAR imagery.

## Dataset Overview

| Property | Value |
|----------|-------|
| **Name** | Copernicus DEM GLO-30 DGED |
| **Source** | European Space Agency (ESA) / Copernicus |
| **Resolution** | 30 meters |
| **Coordinate System** | WGS 84 Geographic (EPSG:4326) |
| **Vertical Datum** | EGM2008 Geoid |
| **Format** | GeoTIFF (Float32) |
| **Coverage** | Northern Vietnam |

## Data Source

- **Portal**: [Copernicus Browser Component Data Access ()](https://browser.dataspace.copernicus.eu/)
- **Product**: COP-DEM_GLO-30-DGED

## Directory Structure

Each top-level folder represents a **data package** from the Copernicus portal:

```
DEM1_SAR_DGE_30_YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_ADS_000000_XXXX_hash/
│
├── Copernicus_DSM_10_N41_00_E016_00/    # Tile folder (1°x1° cell)
│   │
│   ├── DEM/                             # Main elevation data
│   │   └── *_DEM.tif                    # ⭐ PRIMARY DEM (elevation in meters)
│   │
│   ├── AUXFILES/                        # Auxiliary quality layers
│   │   ├── *_ACM.kml                    # Accuracy Mask (KML)
│   │   ├── *_EDM.tif                    # Editing Mask
│   │   ├── *_FLM.tif                    # Filling Mask
│   │   ├── *_HEM.tif                    # Height Error Mask
│   │   └── *_WBM.tif                    # Water Body Mask
│   │
│   ├── INFO/                            # Documentation
│   │   └── eula_F.pdf                   # End User License Agreement
│   │
│   ├── PREVIEW/                         # Quick-look images
│   │   ├── *_DEM_QL.tif                 # DEM preview (hillshade)
│   │   ├── *_DEM_ABS_QL.tif             # DEM absolute preview
│   │   ├── *_EDM_QL.tif                 # Editing mask preview
│   │   ├── *_FLM_QL.tif                 # Filling mask preview
│   │   ├── *_HEM_QL.tif                 # Height error preview
│   │   ├── *_WBM_QL.tif                 # Water body preview
│   │   ├── *_QL.kml                     # Quick-look KML
│   │   └── *_SRC.kml                    # Source coverage KML
│   │
│   └── Copernicus_DSM_10_N41_00_E016_00.xml  # Tile metadata
│
├── GSC_CR_ESA_COP-DEM_*.xml             # Package-level metadata files
└── INSPIRE.xml                          # INSPIRE-compliant metadata
```

## File Types Explained

### Main Data (DEM/)
| File | Description |
|------|-------------|
| `*_DEM.tif` | **Primary elevation raster** - Heights in meters above EGM2008 geoid |

### Auxiliary Files (AUXFILES/)
| File | Description |
|------|-------------|
| `*_EDM.tif` | **Editing Mask** - Indicates pixels that were manually edited |
| `*_FLM.tif` | **Filling Mask** - Indicates void-filled pixels (interpolated) |
| `*_HEM.tif` | **Height Error Mask** - Estimated vertical accuracy per pixel (meters) |
| `*_WBM.tif` | **Water Body Mask** - Water/land classification (0=land, 1=water) |
| `*_ACM.kml` | **Accuracy Coverage Mask** - KML showing accuracy zones |

### Preview Files (PREVIEW/)
Low-resolution quick-look versions of each layer (suffix `_QL`), useful for visual inspection.

## Tile Naming Convention

Example:
```
Copernicus_DSM_10_N41_00_E016_00
            │   │       │
            │   │       └── Longitude: E016°00' (East 16°)
            │   └── Latitude: N41°00' (North 41°)
            └── Resolution code (10 = ~30m at equator)
```

## Usage with Python

```python
import rasterio

dem_path = "DEM1_.../Copernicus_DSM_10_N41_00_E016_00/DEM/Copernicus_DSM_10_N41_00_E016_00_DEM.tif"

with rasterio.open(dem_path) as src:
    elevation = src.read(1)
    print(f"Shape: {elevation.shape}")
    print(f"CRS: {src.crs}")
    print(f"Bounds: {src.bounds}")
```

## License

Copernicus DEM is provided free of charge under the **Copernicus Data Access Policy**.
- Free for research, commercial, and operational use
- See `INFO/eula_F.pdf` for full terms


© DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

## Citation

> European Space Agency, Sinergise (2021). Copernicus Global Digital Elevation Model. Distributed by OpenTopography. https://doi.org/10.5069/G9028PQB

## References

- [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

