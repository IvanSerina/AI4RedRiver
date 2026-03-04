from pathlib import Path


BASE_DIR = Path(__file__).parent.resolve()

USERS_FILE = (BASE_DIR / "users.yaml").resolve()
SESSIONS_DIR = (BASE_DIR / "saved_sessions").resolve()
VALIDATOR_PATH = (BASE_DIR / "Validator" / "Validate").resolve()
ENHSP_PATH = (BASE_DIR / "ENHSP" / "enhsp.jar").resolve()
HISTORICAL_DATA_PATH = (BASE_DIR / "historical_data" / "Historical_data.csv").resolve()

PARETO_PLANS = -1 # con -1 vengono considerati tutti i piani generati e non viene fatto il sampling

GLOBAL_VARIABLES = ["maximum_turbine_release hoa_binh_dam",
                    "storage hoa_binh_dam",
                    "efficiency hoa_binh_dam",
                    "lagged_flow yen_bai_station",
                    "lagged_flow vu_quang_station",
                    "lagged_flow hoa_binh_dam",
                    "max_bottom_release hoa_binh_dam",
                    "max_spillways_release hoa_binh_dam"]
DAILY_VARIABLES = ["agricultural_demand",
                   "flow_beta input_hoa_binh",
                   "flow_beta yen_bai_station",
                   "flow_beta vu_quang_station"]

global_variables_pattern = {
    "maximum_turbine_release hoa_binh_dam": r"\(= \(maximum_turbine_release hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "storage hoa_binh_dam": r"\(= \(storage hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "efficiency hoa_binh_dam": r"\(= \(efficiency hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "lagged_flow yen_bai_station": r"\(= \(lagged_flow yen_bai_station\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "lagged_flow vu_quang_station": r"\(= \(lagged_flow vu_quang_station\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "lagged_flow hoa_binh_dam": r"\(= \(lagged_flow hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "max_bottom_release hoa_binh_dam": r"\(= \(max_bottom_release hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "max_spillways_release hoa_binh_dam": r"\(= \(max_spillways_release hoa_binh_dam\)\s+([+-]?\d+(?:\.\d+)?)\)",
}

daily_variables_pattern = {
    "agricultural_demand": r"\(= \(agricultural_demand (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "flow_beta input_hoa_binh": r"\(= \(flow_beta input_hoa_binh (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "flow_beta yen_bai_station": r"\(= \(flow_beta yen_bai_station (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "flow_beta vu_quang_station": r"\(= \(flow_beta vu_quang_station (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "max_level_dam": r"\(= \(max_level_dam (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
    "min_level_dam": r"\(= \(min_level_dam (day_\d{4}_\d{2}_\d{2})\)\s+([+-]?\d+(?:\.\d+)?)\)",
}