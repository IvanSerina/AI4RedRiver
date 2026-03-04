import os
import numpy as np
import glob
import pandas as pd
import re
from datetime import datetime
from statistics import mean
import streamlit as st

from configuration import global_variables_pattern, daily_variables_pattern


def logout_button():
    with st.sidebar:
        if st.button("Logout", key="logout_button"):
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["role"] = None
            st.switch_page("pages/1_LOGIN.py")

def extract_initial_date_from_problem(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()
        # Extract start date (active in init section)
        start_match = re.search(r'\(active\s+day_(\d{4})_(\d{2})_(\d{2})\)', content)         
        start_year, start_month, start_day = start_match.groups()
        start_date = datetime(int(start_year), int(start_month), int(start_day)).date()
    return start_date

def get_date_range_from_csv(csv_path: str, date_col: str = "Date"):
    """
    Legge un CSV e ritorna la prima e l'ultima data dalla colonna specificata.
    
    Args:
        csv_path (str): percorso al file CSV
        date_col (str): nome della colonna contenente le date (default "Date")
    
    Returns:
        tuple[pd.Timestamp, pd.Timestamp]: (prima_data, ultima_data)
    """
    df = pd.read_csv(csv_path)
    if date_col not in df.columns:
        raise ValueError(f"La colonna '{date_col}' non esiste nel CSV.")
    # conversione a datetime
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if df[date_col].isnull().all():
        raise ValueError("Tutte le date non sono valide o non leggibili.")
    first_date = df[date_col].min()
    last_date = df[date_col].max()
    return first_date, last_date


def create_new_session_folder(session_name, sessions_dir):
    os.makedirs(sessions_dir, exist_ok=True)
    session_path = os.path.join(sessions_dir, session_name) + os.sep
    os.makedirs(session_path, exist_ok=False)
    return session_path

def add_domain_and_problem_file_to_session_folder(session_path, domain_text, problem_text):
    domain_file_path = os.path.join(session_path, "domain.pddl")
    problem_file_path = os.path.join(session_path, "problem.pddl")

    with open(domain_file_path, "w", encoding="utf-8") as f:
        f.write(domain_text)
    with open(problem_file_path, "w", encoding="utf-8") as f:
        f.write(problem_text)


def is_pareto_efficient(points):
    pts = np.array(points)
    is_efficient = np.ones(pts.shape[0], dtype=bool)
    for i, c in enumerate(pts):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(pts[is_efficient] > c, axis=1) | np.all(pts[is_efficient] == c, axis=1)
            is_efficient[i] = True
    return is_efficient

def sample_pareto(plans, points, N):
    """
    Restituisce un sottoinsieme di piani pareto-efficienti.

    - Se N > 0: campiona al massimo N piani ordinati in base alla produzione.
    - Se N == -1: restituisce tutti i piani senza effettuare alcun campionamento.
    """
    if N == -1:
        return plans
    if len(plans) == 0:
        return []
    sorted_idx = np.argsort([pt[0] for pt in points])  # ordina per produzione
    step = max(1, len(sorted_idx) // N)
    sampled_idx = sorted_idx[::step][:N]
    return [plans[i] for i in sampled_idx]


def extract_pareto_plans_df(domain_path,
                            problem_path,
                            plans_directory, 
                            scrapper, 
                            initial_date,
                            run_name,
                            N_sample=-1
                            ):
    """
    Estrae i piani pareto-efficienti e li restituisce in un unico DataFrame.

    - Se N_sample > 0: viene effettuato il campionamento e vengono restituiti al massimo N_sample piani.
    - Se N_sample == -1: vengono considerati tutti i piani pareto-efficienti (nessun campionamento).
    """
    plan_files = sorted(
        glob.glob(os.path.join(plans_directory, "plan_*.plan")),
        key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0])
    )
    # 1. Calcolo obiettivi
    objective_points = []
    valid_plan_files = []
    for plan_file in plan_files:
        data = scrapper.read_output(domain_path, problem_path, plan_file, initial_date, simulation=False)
        cum_prod = data['cumulative_production'].iloc[-1]
        cum_rel = data['cumulative_tot_release'].iloc[-1]
        objective_points.append([cum_prod, -cum_rel])
        valid_plan_files.append(plan_file)
    # 2. Pareto e campionamento
    mask = is_pareto_efficient(objective_points)
    pareto_files = [f for f, m in zip(valid_plan_files, mask) if m]
    pareto_points = [pt for pt, m in zip(objective_points, mask) if m]
    sampled_files = sample_pareto(pareto_files, pareto_points, N=N_sample)
    # 3. Estrai i df dai piani e concatena in un unico df
    all_plans_df = []
    for plan_file in sampled_files:
        plan_name = os.path.basename(plan_file).split(".")[0]
        df = scrapper.read_output(
            domain_path=domain_path,
            problem_path=problem_path,
            plan_path=plan_file,
            initial_date=initial_date,
            simulation=False
        )
        df["plan"] = run_name + "_" + plan_name
        all_plans_df.append(df)

    final_df = pd.concat(all_plans_df, ignore_index=True)
    return final_df


def modify_global_parameters_in_problem_file(file_content, df):
    """
    Modifica il contenuto di problem.pddl in base ai valori del dataframe df.
    df ha colonne ["variable", "value"].
    """
    for _, row in df.iterrows():
        key = row["variable"]  # es: "maximum_turbine_release hoa_binh_dam"
        new_value = row["value"]

        pattern = global_variables_pattern[key]

        def replace(match):
            return match.group(0).replace(match.group(1), f"{new_value:.4f}")

        file_content = re.sub(pattern, replace, file_content)

    return file_content


def modify_daily_parameters_in_problem_file(file_content, df):
    """
    Applica le modifiche giornaliere al testo problem.pddl
    in base ai valori aggiornati in df.
    
    df deve avere colonne: ["date", ...variabili...]
    """
    for _, row in df.iterrows():
        # data originale nel formato "day_YYYY_MM_DD"
        day_str = "day_" + row["date"].strftime("%Y_%m_%d")
        for col in df.columns:
            if col == "date" or pd.isna(row[col]):
                continue
            # pattern che include sia variabile che data
            pattern = (
                r"\(= \(" + re.escape(col) +
                r"\s+" + re.escape(day_str) +
                r"\)\s+[+-]?\d+(?:\.\d+)?\)"
            )
            replacement = f"(= ({col} {day_str}) {row[col]:.6f})"
            file_content = re.sub(pattern, replacement, file_content)
    return file_content


def modify_daily_parameters_percentage_in_problem_file(file_content: str, percent_changes: dict) -> str:
    """
    Modifica i valori giornalieri delle variabili nel file PDDL applicando la percentuale indicata in percent_changes.
    
    :param file_content: contenuto del file problem.pddl come stringa
    :param percent_changes: dict con chiave = nome variabile, valore = percentuale di modifica
                           es: {"agricultural_demand": 10, "max_level_dam": -5}
    :return: stringa modificata del file
    """
    updated_content = file_content
    for var, pattern in daily_variables_pattern.items():
        percent = percent_changes.get(var, 0)
        if percent == 0:
            continue  # non modificare se non c'è variazione
        def replace(match):
            day = match.group(1)
            value = float(match.group(2))
            new_value = value * (1 + percent / 100)
            return f"(= ({var} {day}) {new_value:.6f})"
        updated_content = re.sub(pattern, replace, updated_content)
    return updated_content


def validate_plans(session_dir, output_scrapper):
    target_domain_path = os.path.join(session_dir, "domain.pddl")
    target_problem_path = os.path.join(session_dir, "problem.pddl")
    dict_results = []
    session_runs_dir = os.path.join(session_dir, "runs")
    for subfolder_name in os.listdir(session_runs_dir):
        subfolder_path = os.path.join(session_runs_dir, subfolder_name)
        if os.path.isdir(subfolder_path):
            subfolder_plans_path = os.path.join(subfolder_path, "plans")
            for plan_name in os.listdir(subfolder_plans_path):
                plan_path = os.path.join(subfolder_plans_path, plan_name)
                if not os.path.isfile(plan_path):
                    continue
                valid = output_scrapper.validate_plan(domain_path=target_domain_path,
                                                      problem_path=target_problem_path,
                                                      plan_path=plan_path)
                dict_results.append({"plan": f"{subfolder_name}_{plan_name.split('.')[0]}",
                                     "valid": valid})
    return pd.DataFrame(dict_results)


def validate_csv(file) -> dict:
    """
    Validate a CSV file according to specific rules:
    - Must contain required columns
    - Dates must be contiguous without gaps
    - No negative numbers in numeric columns
    - Required columns must not contain nulls
    - Column 'H_Up (m)' must not be null on the first day
    
    Parameters
    ----------
    file : file-like object
        CSV file uploaded (e.g. from Streamlit file_uploader)
    
    Returns
    -------
    dict
        {
            "status": "valid" | "invalid",
            "message": explanation
        }
    """
    
    required_columns = [
        "Date", "Input_Hoa_Binh", "Yen_Bai", "Vu_Quang", 
        "Demand", "H_Up (m)", "Energy_demand"
    ]
    
    errors = []
    
    # Load CSV
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return {"status": "invalid", "message": f"❌ Error reading CSV: {e}"}
    # --- 1. Check required columns ---
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"❌ Missing required columns: {', '.join(missing_cols)}")
    # --- 2. Check contiguous dates ---
    if "Date" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date").reset_index(drop=True)
            expected_dates = pd.date_range(start=df["Date"].min(), end=df["Date"].max(), freq="D")
            if not df["Date"].equals(expected_dates.to_series().reset_index(drop=True)):
                errors.append("❌ Dates are not contiguous (missing or duplicated days).")
        except Exception:
            errors.append("❌ Column 'Date' has invalid date format.")
    # --- 3. Check negative values ---
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if not df.empty and (df[numeric_cols] < 0).any().any():
        errors.append("❌ Negative values detected in numeric columns.") 
    # --- 4. Check non-null required columns ---
    must_not_null = ["Date", "Input_Hoa_Binh", "Yen_Bai", "Vu_Quang", "Demand", "Energy_demand"]
    for col in must_not_null:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"❌ Column '{col}' contains null values.")
    # --- 5. Check H_Up (m) on first day ---
    if "H_Up (m)" in df.columns:
        if not df.empty and pd.isnull(df.loc[0, "H_Up (m)"]):
            errors.append("❌ Column 'H_Up (m)' must not be null on the first day.")
    # riportiamo il puntatore del file all'inizio
    # in questo modo il file può essere riletto successivamente da altre funzioni
    file.seek(0)
    if errors:
        return {"status": "invalid", "message": "\n".join(errors)}
    else:
        return {"status": "valid", "message": "CSV is valid ✅"}
    


def check_date_for_coefficient(starting_date, historical_path):
    historical_df = pd.read_csv(historical_path)
    historical_df["Date"] = pd.to_datetime(historical_df["Date"])
    historical_df = historical_df.sort_values("Date").reset_index(drop=True)
    last_historical_date  = historical_df["Date"].max()
    starting_date = pd.to_datetime(starting_date)
    if last_historical_date < (starting_date - pd.Timedelta(days=1)):
        return f"Attention! Historical data aren't updated. Last date used to calculate coefficients is {last_historical_date}"
    return None


def get_daily_variable_mean(var, problem):
    pattern = daily_variables_pattern[var]
    matches = re.findall(pattern, problem)
    values = [float(m[1]) for m in matches]
    return mean(values)


def extract_subsession(plan_name: str) -> str:
    # prende la parte prima di "_plan_<numero>"
    match = re.match(r"^(.*)_plan_\d+$", plan_name)
    return match.group(1) if match else plan_name
