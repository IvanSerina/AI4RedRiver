# ISRIC SoilGrids 2.0 (Capitanata Region)

This directory contains soil property maps from the **ISRIC SoilGrids 2.0** dataset.

## Overview
- **Source**: [ISRIC - World Soil Information](https://www.isric.org/explore/soilgrids)
- **Version**: 2.0
- **Resolution**: 250m
- **Format**: GeoTIFF (.tif)
- **Projection**: Interrupted Goode Homolosine (ESRI:54052 / EPSG:152160)
- **License**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Processing
Data was downloaded using the Web Coverage Service (WCS) API via Python.
- **Method**: WCS GetCoverage (Native Homolosine subsetting)
- **Statistic**: Mean (Prediction Mean)

## Variables

| Variable Code | Name | Units (Mapped) | Conversion to Conventional | Conventional Units | Description |
|---|---|---|---|---|---|
| **bdod** | Bulk density | cg/cm³ | / 100 | kg/dm³ | Fine earth fraction (<2 mm) |
| **cec** | Cation Exchange Capacity | mmol(c)/kg | / 10 | cmol(c)/kg | Reliability at pH 7 |
| **cfvo** | Coarse fragments | cm³/dm³ (vol‰) | / 10 | % (vol) | Volumetric fraction > 2mm |
| **clay** | Clay content | g/kg | / 10 | % (weight) | < 0.002 mm fraction |
| **nitrogen** | Nitrogen | cg/kg | / 100 | g/kg | Total nitrogen |
| **phh2o** | pH (water) | pH * 10 | / 10 | pH | Soil pH in H₂O |
| **sand** | Sand content | g/kg | / 10 | % (weight) | 0.05 - 2 mm fraction |
| **silt** | Silt content | g/kg | / 10 | % (weight) | 0.002 - 0.05 mm fraction |
| **soc** | Soil Organic Carbon | dg/kg | / 10 | g/kg | Carbon concentration |
| **ocd** | Organic Carbon Density | hg/m³ | / 10 | kg/m³ | Density of organic carbon |
| **ocs** | Organic Carbon Stocks | t/ha | / 10 | kg/m² | Stock (0-30 cm only) |
| **wv0010** | Water Content (10 kPa) | 0.1 vol% | / 10 | % | Volumetric water content at pF 2.0 |
| **wv0033** | Water Content (33 kPa) | 0.1 vol% | / 10 | % | Volumetric water content at pF 2.5 (Field Capacity) |
| **wv1500** | Water Content (1500 kPa) | 0.1 vol% | / 10 | % | Volumetric water content at pF 4.2 (Wilting Point) |

*Note: SoilGrids stores values as integers to save space. Apply conversion factors for analysis.*

## Standard Depths
Maps are provided for the following depth intervals (as per GlobalSoilMap specs):
1. **0-5 cm**
2. **5-15 cm**
3. **15-30 cm**
4. **30-60 cm**
5. **60-100 cm**
6. **100-200 cm**

*(Note: `ocs` is provided for 0-30 cm only)*

## Usage Note on Projection
The files are in the **Homolosine** projection. To use them with other datasets (like ERA5 in WGS84/UTM), they must be reprojected to ensure correct resampling.

Example Re-projection with `gdalwarp`:
```bash
gdalwarp -t_srs EPSG:4326 input_homolosine.tif output_wgs84.tif
```
