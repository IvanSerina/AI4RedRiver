# In-Situ Station Data

Daily time-series observations from stations across the Red River basin, provided by Prof. Ngo Le An (Thuyloi University, Vietnam) as part of the AI4RedRiver collaboration. The original source is Vietnam's National Meteorological and Hydrological Administration (VNMHA) and the dam operator (EVN).

## Files

| File | Variables | Stations | Period | Records |
|------|-----------|----------|--------|---------|
| `Historical_data.csv` | Dam operations, flows, water levels, energy/water demand | 5 | 1989–2022 | ~12,418 |
| `Rainfall_mm.csv` | Daily precipitation (mm) | 20 | 2000–2020 | ~9,498 |
| `Evaporation_mm.csv` | Daily evaporation (mm) | 6 | 2000–2020 | ~9,500 |
| `Temperature_oC.csv` | Daily temperature (°C) | 4 | 2000–2020 | ~7,306 |
| `Water_level_(cm).csv` | Water level (cm) | 6 | 2000–2022 (partial) |~8,794 |

## Historical_data.csv — Column Reference

| Column | Description | Unit |
|--------|-------------|------|
| `Date` | Observation date | — |
| `Input_Hoa_Binh` | Inflow to Hoa Binh reservoir (historically measured at Ta Bu station upstream) | m³/s |
| `Yen_Bai` | Flow rate of Thao River at Yen Bai station | m³/s |
| `Vu_Quang` | Flow rate of Lo River at Vu Quang station | m³/s |
| `Evaporation` | Evaporation rate | mm/day |
| `Demand` | Agricultural water demand at Son Tay (irrigation + saline-intrusion control) | m³/s |
| `H_Up (m)` | Hoa Binh reservoir water level | m |
| `Energy_demand` | Energy demand from the national grid (**weekly average** — see Confidentiality below) | MWh |
| `Qtu_(m3/s)` | Turbine discharge | m³/s |
| `Qbot_(m3/s)` | Bottom outlet discharge | m³/s |
| `Qspill_(m3/s)` | Spillway discharge | m³/s |
| `Q_Sơn Tây` | Flow at Son Tay | m³/s |
| `Q_Hà Nội` | Flow at Ha Noi | m³/s |
| `H Hà Nội` | Water level at Ha Noi | m |
| `Day_month` | Auxiliary column (MM-DD) | — |

## Stations

### Historical_data.csv / Water_level_(cm).csv

| Station | Longitude | Latitude |
|---------|-----------|----------|
| Hoa Binh | 105.34727 | 20.85316 |
| Son Tay | 105.51165 | 21.15347 |
| Ha Noi | 105.86163 | 21.03047 |
| Yen Bai | 104.86881 | 21.70010 |
| Vu Quang | 105.29569 | 21.51298 |
| Tuyen Quang | 105.21667 | 21.81667 |

### Rainfall_mm.csv (20 stations)

| Station | Longitude | Latitude |
|---------|-----------|----------|
| Vinh Yen | 105.6051 | 21.3137 |
| Hoa Binh | 105.3388 | 20.8261 |
| Kim Boi | 105.5333 | 20.6744 |
| Son Tay | 105.5115 | 21.1539 |
| Lao Cai | 103.9696 | 22.5000 |
| Son La | 103.9056 | 21.3322 |
| Ba Vi | 105.4299 | 21.1026 |
| Lang | 105.8070 | 21.0204 |
| Tuan Giao | 103.4170 | 21.5888 |
| Muong Lay | 103.1561 | 22.0669 |
| Ha Giang | 104.9823 | 22.8131 |
| Tuyen Quang | 105.2099 | 21.8238 |
| Yen Bai | 104.8692 | 21.7052 |
| Vu Quang | 105.2417 | 21.5917 |
| Bac Me | 105.3667 | 22.7333 |
| Chiem Hoa | 105.2712 | 22.1512 |
| Hung Yen | 106.0509 | 20.6666 |
| Luc Nam | 106.4000 | 21.2833 |
| Chu | 106.5902 | 21.3727 |
| Mai Chau | 105.0825 | 20.6656 |

### Evaporation_mm.csv (6 stations)

| Station | Longitude | Latitude |
|---------|-----------|----------|
| Ba Vi | 105.4298 | 21.1026 |
| Ha Noi | 105.8076 | 21.0214 |
| Ha Giang | 104.9823 | 22.8131 |
| Bac Quang | 104.8667 | 22.5000 |
| Lai Chau | 103.1561 | 22.0669 |
| Hung Yen | 106.0509 | 20.6666 |

### Temperature_oC.csv (4 stations)

| Station | Longitude | Latitude |
|---------|-----------|----------|
| Ba Vi | 105.4299 | 21.1026 |
| Lang | 105.8070 | 21.0204 |
| Son Tay | 105.5115 | 21.1539 |
| Hoa Binh | 105.3388 | 20.8261 |

## Data Completeness

- **Historical_data.csv**: Full coverage 1989–2022.
- **Rainfall / Temperature / Evaporation**: Data ends approximately at the end of 2020.
- **Water_level_(cm).csv**: Partial coverage — Tuyen Quang stops 27/4/2020; Vu Quang, Son Tay, Hoa Binh stop 1/1/2021; Ha Noi stops 1/1/2022; Yen Bai stops 31/12/2022.

## Measurement Methods

- Precipitation: tipping-bucket rain gauges.
- Water level: pile gauges and radar level sensors.

## Confidentiality

The `Energy_demand` column in `Historical_data.csv` contains **weekly averages** instead of true daily values. This masking was applied to protect information deemed sensitive by the Vietnamese authorities.

## Preprocessing Notes

- Anomalous flow values (1989–1999) were identified but retained, as their impact on regression models was negligible (<2% difference in NSE/R²).
- `Input_Hoa_Binh` acts as a proxy for the upstream Ta Bu station.
- Timestamps are aligned and variables standardised for daily-step optimisation problems.

## License

CC BY 4.0
