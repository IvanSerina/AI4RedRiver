import pandas as pd
import numpy as np
import statsmodels.api as sm
import datetime
from scipy.optimize import minimize

def coefficients_evaluation(starting_date: datetime = None, data: pd.DataFrame = None) -> dict:
    
        # check if the day before the stating date is in the historical data
        if (starting_date - pd.Timedelta(days=1)) > data['Date'].iloc[-1]:
            print("Day before starting date is in historical data")
            starting_date = datetime.datetime(
                year=data['Date'].iloc[-1].year,
                month=starting_date.month,
                day=starting_date.day
            )
            if starting_date - pd.Timedelta(days=1) > data['Date'].iloc[-1]:
                starting_date = starting_date.replace(year=starting_date.year - 1)
            
            print(f"The last available date for the coefficients is the: {data['Date'].iloc[-1]}")
            
            print(f"New starting date for the coefficients is: {starting_date}")

        starting_year = starting_date.year
        df_coeff = data[
            (data.Date.dt.year >= (starting_year - 3)) & (data.Date < starting_date) & (data.Date.dt.year != 2008)
        ].copy()
        df_coeff["Qout_(m3/s)"] = df_coeff[
            ["Qtu_(m3/s)", "Qbot_(m3/s)", "Qspill_(m3/s)"]
        ].sum(axis=1)
        slopes = find_dry_or_flood_coefficients(df_coeff, starting_date)

        return slopes

def find_dry_or_flood_coefficients(
        df: pd.DataFrame, starting_date: datetime
    ):
        df_coeff = df.copy()

        slopes = dict()

        df_coeff_season: pd.DataFrame = select_season(df=df_coeff, starting_date=starting_date)

        slopes_ST = find_flow_coefficients(
            df_coeff_season,
            ["Qout_(m3/s)", "Yen_Bai", "Vu_Quang"],
            "lagged_flow_ST",
        )
        q_slopes_HN = find_flow_coefficients(
            df_coeff_season, ["Q_Sơn Tây"], "lagged_flow_HN"
        )
        h_slope_HN = find_height_coefficients(
            df_coeff_season, starting_date, ["Q_Hà Nội"], "H Hà Nội"
        )

        slopes.update(
            {
                "q_slope_HN": q_slopes_HN,
                "h_slope_HN": h_slope_HN,
                "slope_ST": slopes_ST,
            }
        )

        return slopes
    
    
def find_flow_coefficients(
        df: pd.DataFrame, x_columns: list, y_column: str
    ) -> np.ndarray:
        X_train = df[x_columns]
        y_train = df[y_column]
        X_train = np.column_stack((X_train, np.ones(len(X_train))))

        initial_guess = np.ones(X_train.shape[1])

        bounds = [(0, 1) for _ in range(X_train.shape[1] - 1)]
        bounds.append((0, None))

        result = minimize(
            lambda coef, X, y: np.sum((np.dot(X, coef) - y) ** 2),
            initial_guess,
            args=(X_train, y_train),
            bounds=bounds,
        )

        return result.x
    
def select_season(df: pd.DataFrame, starting_date: datetime) -> pd.DataFrame:
    if starting_date.month < 6 or starting_date.month > 9:
        return df[(df.Date.dt.month < 6) | (df.Date.dt.month > 9)]
    return df[(df.Date.dt.month >= 6) & (df.Date.dt.month <= 9)]


def find_height_coefficients(
        df_historical: pd.DataFrame,
        starting_date: datetime,
        x_column: list,
        y_column: str,
    ):
        start_year = starting_date.year - 3  # if end_year != 2009 else end_year-2
        clean_data = df_historical[df_historical.Date.dt.year >= start_year]
        q_HN = clean_data[x_column]
        h_HN = clean_data[y_column] / 100
        # Create a column for weights based on time
        w = 1 / (1 + (((starting_date.year - clean_data.Date.dt.year))))
        # Create design matrix X with columns for the intercept and height
        X = np.column_stack((q_HN, q_HN**2, q_HN**3))
        X = sm.add_constant(X)
        # Perform weighted least squares regression
        model_Q_ST = sm.WLS(h_HN, X, weights=w)
        result_Q_ST = model_Q_ST.fit()

        return result_Q_ST.params
