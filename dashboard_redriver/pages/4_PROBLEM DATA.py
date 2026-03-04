import streamlit as st
import pandas as pd
import numpy as np
import re
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import shutil

from utils import logout_button, modify_global_parameters_in_problem_file, modify_daily_parameters_in_problem_file
from configuration import GLOBAL_VARIABLES, DAILY_VARIABLES, SESSIONS_DIR
from output_scrapper import OutputScrapper
from solve_problem import *
from configuration import *
from utils import extract_initial_date_from_problem, extract_pareto_plans_df, logout_button, check_date_for_coefficient, get_daily_variable_mean, modify_daily_parameters_percentage_in_problem_file
from increase_releases import increment_min_release

logout_button()

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("You must login to see this page.")
    st.stop()

if "pareto_plans" not in st.session_state:
    st.error("❌ No data available. Go to the home page and upload files.")
    st.stop()

# ad ongi refresh/rerun leggo il problem in quanto potrebbero essere stati modificati
with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "r") as f:
    problem_file = f.read()
# creo delle variabili che memorizzano la versione di problem/domain da utilizzare nel caso dovessi ritornare ale versioni precedenti 
# a causa di modifiche errate dei parametri (modifiche che causano errori)
if "original_problem_file" not in st.session_state:
    problem_path = os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl")
    with open(problem_path, "r") as f:
        st.session_state.original_problem_file = f.read()
if "original_domain_file" not in st.session_state:
    domain_path = os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "domain.pddl")
    with open(domain_path, "r") as f:
        st.session_state.original_domain_file = f.read()

# PARAMETRI DASHBOARD
np.random.seed(1234)
st.set_page_config(
    page_title="Water Management Dashboard",
    page_icon="",
    layout="wide",
)

# parametri utilizzati per la gestione della dashboard
if "changed_parameters" not in st.session_state: # se True viene mostrata la sezione per generare nuovi piani con i poarametri modificati
    st.session_state.changed_parameters = False
if "show_daily_success" not in st.session_state: # se True mostra il messaggio di corretta modifica dei parametri daily
    st.session_state.show_daily_success = False
if "show_global_success" not in st.session_state: # se True mostra il messaggio di corretta modifica dei parametri global
    st.session_state.show_global_success = False
if "show_go_to_plots_button" not in st.session_state: # se True mostra un bottone per spostarsi alla pagina con i plot
    st.session_state.show_go_to_plots_button = False

# HEADER
with st.container():
    st.markdown(
        f"<h1 style='text-align: center;'>Info about problem parameters</h1>",
        unsafe_allow_html=True
    )

# ========= 1. GLOBAL PARAMETERS =========
st.subheader("🌍 Global parameters")
if "global_action" not in st.session_state:
    st.session_state.global_action = None
if "global_modified" not in st.session_state:
    st.session_state.global_modified = False

# estraggo un df con le variabili gloabli
global_data = []
for var in GLOBAL_VARIABLES:
    # match del tipo (= (varname) 123.45)
    match = re.search(rf"\(= \({var}\)\s+([\d\.\-eE]+)\)", problem_file)
    if match:
        value = float(match.group(1))
        global_data.append({"variable": var, "value": value})
df_global = pd.DataFrame(global_data)

# mostro le opzioni (visualizzazione parametri o modifica)
_, col1_global, col2_global, _ = st.columns([2,3,3,2])
with col1_global:
    if st.button("📊 Visualize Global Parameters"):
        st.session_state.global_action = "visualize"
with col2_global:
    if st.button("✏️ Edit Global Parameters"):
        st.session_state.global_action = "edit"
# contenuto a tutta pagina in base alla selezione effettuata
if st.session_state.global_action == "visualize":
    st.dataframe(df_global, use_container_width=True)
elif st.session_state.global_action == "edit":
    st.session_state.show_global_success = False # reset flag
    # editor parametri
    edited_df_global = st.data_editor(
        df_global,
        key="editor_globale",
        column_config={
            "variable": st.column_config.Column(disabled=True),
        },
        use_container_width=True,
        num_rows="fixed"
    )
    _, col_center, _ = st.columns([3, 2, 3])
    with col_center:
        if st.button("✅ Apply Changes", use_container_width=True, key="edit_global"):
            with st.spinner("Applying changes"):
                # rileggo il problema in quanto potrebbe essere stato modificato
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "r") as f:
                    problem_file = f.read()
                edited_problem = modify_global_parameters_in_problem_file(file_content=problem_file, 
                                                                        df=edited_df_global)
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "w") as f:
                    f.write(edited_problem)
                st.session_state.global_modified = True
                st.session_state.changed_parameters = True
    if st.session_state.global_modified:
        st.session_state.global_action = None
        st.session_state.show_global_success = True
        st.session_state.global_modified = False
        st.rerun()

if st.session_state.show_global_success:
    st.success("Global variables edited correctly!")

# ========= 2. DAILY PARAMETERS =========
st.divider()
st.subheader("📅 Daily parameters")
if "daily_action" not in st.session_state:
    st.session_state.daily_action = None
if "daily_modified" not in st.session_state:
    st.session_state.daily_modified = False

# estraggo un df con le variabili daily. Creo una colonna Date estraendo il set di date dal problema
daily_dict = {var: {} for var in DAILY_VARIABLES}
all_dates = set()
for var in DAILY_VARIABLES:
    var_escaped = re.escape(var)
    pattern = (
        r"\(= \("
        + var_escaped
        + r"\s+(day_\d{4}_\d{2}_\d{2})\)\s*([+-]?\d+(?:\.\d+)?)\)"
    )
    matches = re.findall(pattern, problem_file)
    for day, value in matches:
        daily_dict[var][day] = float(value)
        all_dates.add(day)
all_dates = sorted(all_dates)
df_daily = pd.DataFrame({"date": all_dates})
for var, values in daily_dict.items():
    df_daily[var] = [values.get(day, np.nan) for day in all_dates]
# parsing date string
df_daily["date"] = pd.to_datetime(df_daily["date"].str.replace("day_", ""), format="%Y_%m_%d")
df_daily["date"] = df_daily["date"].dt.date
# mostro le opzioni (visualizzazione, edit giorno per giorno o edit con percentuale)
_, col1_daily, col2_daily, col3_daily, _ = st.columns([0.05,0.3,0.3,0.3,0.05])
with col1_daily:
    if st.button("📊 Visualize Daily Parameters"):
        st.session_state.daily_action = "visualize"
with col2_daily:
    if st.button("✏️ Edit Daily Parameters (day by day)"):
        st.session_state.daily_action = "edit_day_by_day"
with col3_daily:
    if st.button("✏️ Adjust Daily Parameters (by %)"):
        st.session_state.daily_action = "edit_percentage"
# contenuto a tutta pagina in base alla selezione effettuata
# caso 1: visualizzazione parametri
if st.session_state.daily_action == "visualize":
    st.dataframe(df_daily, use_container_width=True)
    fig = px.line(df_daily, x="date", y=df_daily.columns[1:], markers=True)
    st.plotly_chart(fig, use_container_width=True)
# caso 2: modifica dei valori giorno per giorno in forma tabellare
elif st.session_state.daily_action == "edit_day_by_day":
    st.session_state.show_daily_success = False
    edited_df_daily = st.data_editor(
        df_daily,
        key="editor_giornaliero",
        column_config={
            "date": st.column_config.Column(disabled=True),
        },
        use_container_width=True,
        num_rows="fixed"
    )
    _, col_center, _ = st.columns([3, 2, 3])
    with col_center:
        if st.button("✅ Apply Changes", use_container_width=True, key="edit_daily"):
            with st.spinner("Applying changes"):
                # rileggo il problema in quanto potrebbe essere stato modificato
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "r") as f:
                    problem_file = f.read()
                edited_problem = modify_daily_parameters_in_problem_file(file_content=problem_file, 
                                                                        df=edited_df_daily)
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "w") as f:
                    f.write(edited_problem)
                st.session_state.daily_modified = True
                st.session_state.changed_parameters = True
    if st.session_state.daily_modified:
        st.session_state.daily_action = None
        st.session_state.show_daily_success = True
        st.session_state.daily_modified = False
        st.rerun()
# caso 2: modifica dei valori in base ad una percentuale.
#         Per ogni feature è possibile aggiungere/rimuovere una percentuale a tutti i giorni
elif st.session_state.daily_action == "edit_percentage":
    st.session_state.show_daily_success = False
    percent_changes = {} # dizionario che memorizza le percentuali di modifica di ogni feature
    # ciclo che visualizza per ogni daily_feature la media di partenza, uno slider e la nuova media
    for var in DAILY_VARIABLES:
        original_mean = get_daily_variable_mean(var, problem_file)
        _, col_title, _ = st.columns([1, 2, 1])
        with col_title:
            st.markdown(f"<h3 style='text-align: center;'>{var}</h3>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_a:
            st.metric("Current mean", f"{original_mean:.6f}")
        with col_b:
            percent_changes[var] = st.slider(
                f"💡 % change for {var}",
                -50.0, 50.0, 0.0, step=0.5,
                key=f"slider_{var}"
            )
            modified_value = original_mean * (1 + percent_changes[var] / 100)
        with col_c:
            st.metric("Modified preview", f"{modified_value:.6f}",
                      delta=f"{percent_changes[var]:.1f}%")
    _, col_center, _ = st.columns([3, 2, 3])
    with col_center:
        if st.button("✅ Apply Changes", use_container_width=True, key="edit_percentage"):
            with st.spinner("Applying changes"):
                # rileggo il problema in quanto potrebbe essere stato modificato
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "r") as f:
                    problem_file = f.read()
                edited_problem = modify_daily_parameters_percentage_in_problem_file(file_content=problem_file, 
                                                                                    percent_changes=percent_changes)
                with open(os.path.join(SESSIONS_DIR, st.session_state["selected_session"], "problem.pddl"), "w") as f:
                    f.write(edited_problem)
                st.session_state.daily_modified = True
                st.session_state.changed_parameters = True
    if st.session_state.daily_modified:
        st.session_state.daily_action = None
        st.session_state.show_daily_success = True
        st.session_state.daily_modified = False
        st.rerun()

if st.session_state.show_daily_success:
    st.success("Daily variables edited correctly!")

# ======== 3. GENERATE NEW PLANS IF CHANGED PARAMS ==========
# definisco una funzione che in caso di errore durante la generazione dei problemi rimuove la sotto-sessione appena creata
# e riporta i parametri del problema alla versione precedente (pre modifica)
@st.dialog("❌ Error during plans generation")
def error_popup(session_path, run_name):
    st.write("It is not possible to obtain plans with these parameters."
             " Returning to previous problem parameters")
    shutil.rmtree(os.path.join(session_path, f"runs/{run_name}"), ignore_errors=True)
    with open(os.path.join(session_path, "problem.pddl"), "w") as f:
        f.write(st.session_state["original_problem_file"])
    with open(os.path.join(session_path, "domain.pddl"), "w") as f:
        f.write(st.session_state["original_domain_file"])
    st.session_state.pop("csv_file_upload", None) 
    st.session_state.pop("text_input_problem_plan_generation", None)
    if st.button("OK"):
        st.rerun()

if st.session_state.changed_parameters:
    st.divider()
    st.subheader("⚙️ Generate Plan")
    st.markdown("#### Define planning constraints")
    constraint1, constraint2 = st.columns(2)
    with constraint1:
        max_time = st.number_input("⏱️ Maximum time (seconds)", min_value=0, value=600, step=60)
    st.session_state["max_time_edited_param"] = max_time if max_time > 0 else None
    if st.button("🚀 Generate Plan"):
        #with st.spinner(f"⏳ Generating plan... please wait about {st.session_state['max_time_edited_param']} seconds. (Started at {datetime.now().strftime('%H:%M:%S')})"):
        with st.spinner("Preparing data"):
            with open("temp_file.txt", "w") as f:
                f.write("temp file")
            with open("temp_file.txt", "r") as f:
                temp_file = f.read()
            os.remove("temp_file.txt")
        st.info(f"⚙️ Generating plan... please wait (started at {datetime.utcnow().strftime('%H:%M:%S')} UTC). "
                        "The page will update automatically when finished. Do not refresh.")
        session_path = os.path.join(SESSIONS_DIR, st.session_state.selected_session)
        run_name = f"run_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        try:
            increment_min_release(enhsp_path=ENHSP_PATH, 
                                    domain_file=os.path.join(session_path, "domain.pddl"), 
                                    problem_file=os.path.join(session_path, "problem.pddl"), 
                                    output_dir=os.path.join(session_path, f"runs/{run_name}"), 
                                    historical_path=os.path.join(session_path, "uploaded_csv.csv"), 
                                    validator_path=VALIDATOR_PATH,
                                    gb=10, 
                                    search="gbfs", 
                                    heuristic="blind", 
                                    max_time=st.session_state["max_time_edited_param"], 
                                    start_pct = 0.05, 
                                    end_pct = 0.01, 
                                    max_iterations=None)
            initial_date = extract_initial_date_from_problem(os.path.join(session_path, "problem.pddl"))
            plans_df = extract_pareto_plans_df(domain_path=os.path.join(session_path, "domain.pddl"),
                                                problem_path=os.path.join(session_path, "problem.pddl"),
                                                plans_directory=os.path.join(session_path, f"runs/{run_name}/plans/"), 
                                                scrapper=OutputScrapper(validator_path=VALIDATOR_PATH), 
                                                initial_date=initial_date,
                                                run_name=run_name,
                                                N_sample=PARETO_PLANS)
            if plans_df.empty:
                st.error("No valid plans generated!")
                raise ValueError("No valid plans generated!")
            old_df = pd.read_csv(os.path.join(session_path, "pareto_plans.csv"))
            plans_df = pd.concat([old_df, plans_df], ignore_index=True)
            plans_df["date"] = pd.to_datetime(plans_df["date"])
            plans_df.to_csv(os.path.join(session_path, "pareto_plans.csv"))
            st.session_state["pareto_plans"] = plans_df
            coeff_msg = check_date_for_coefficient(starting_date=initial_date, 
                                                historical_path=HISTORICAL_DATA_PATH)
            st.session_state.pop("original_problem_file", None)
            st.session_state.pop("original_domain_file", None)
            st.session_state.changed_parameters = False
            st.session_state.show_daily_success = False
            st.session_state.show_global_success = False
            st.session_state.show_go_to_plots_button = True
            st.success("✅ Problem and Plan files generated successfully!")
            if coeff_msg:
                st.info(coeff_msg)
        except:
            st.session_state.show_daily_success = False
            st.session_state.show_global_success = False
            st.session_state.changed_parameters = False
            st.session_state.global_action = "visualize"
            st.session_state.daily_action = "visualize"
            error_popup(session_path, run_name)

if st.session_state.show_go_to_plots_button:
    if st.button("📊 Go to plots"):
        st.session_state.show_go_to_plots_button = False
        st.switch_page("pages/3_PLANS ANALYSIS.py")
