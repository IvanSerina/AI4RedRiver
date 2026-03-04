# Global Dynamic Land Cover (10 m)

This directory contains tiles from the **Copernicus Global Dynamic Land Cover** product, a 10 m resolution land cover map derived from Sentinel-2 satellite imagery.

## Dataset Overview

| Property | Value |
|----------|-------|
| **Name** | Global Dynamic Land Cover at 10 m (GDLC 10 m) |
| **Source** | Copernicus Land Monitoring Service (CLMS) |
| **Resolution** | 10 meters |
| **Base Year** | 2020 |
| **Format** | Cloud-Optimised GeoTIFF (COG) |
| **Coverage** | Northern Vietnam (tiles N18E105, N21E105) |

## Data Source

- **Official Documentation**: [Copernicus Global Dynamic Land Cover – Overview](https://land.copernicus.eu/en/products/global-dynamic-land-cover?tab=overview)
- **Product ID**: LCFM_LCM-10_V100

## Directory Structure

```
global_dynamic_10m/
├── LCFM_LCM-10_V100_2020_N18E105_cog/
│   └── LCFM_LCM-10_V100_2020_N18E105_MAP.tif   ← Land cover raster
├── LCFM_LCM-10_V100_2020_N21E105_cog/
│   └── LCFM_LCM-10_V100_2020_N21E105_MAP.tif   ← Land cover raster
└── README.md
```

## Files

| GeoTIFF | Tile | Coverage |
|---------|------|----------|
| `LCFM_LCM-10_V100_2020_N18E105_MAP.tif` | N18 E105 | ~18°–21° N, 105°–108° E |
| `LCFM_LCM-10_V100_2020_N21E105_MAP.tif` | N21 E105 | ~21°–24° N, 105°–108° E |

## Naming Convention

```
LCFM_LCM-10_V100_2020_N18E105_MAP.tif
│    │      │    │    │        └── MAP = land cover classification layer
│    │      │    │    └── Tile identifier (SW corner lat/lon)
│    │      │    └── Reference year
│    │      └── Product version (V1.0.0)
│    └── Land Cover Map at 10 m resolution
└── Land Cover / Forest Monitoring
```

## Usage Notes

- The `*_MAP.tif` files are Cloud-Optimised GeoTIFFs ready for direct use in GIS software (QGIS, ArcGIS, etc.) or Python (rasterio, xarray).
- The land cover classes follow the FAO Land Cover Classification System (LCCS).
- Refer to the [official documentation](https://land.copernicus.eu/en/products/global-dynamic-land-cover?tab=overview) for the full class legend, accuracy assessment, and technical specifications.
