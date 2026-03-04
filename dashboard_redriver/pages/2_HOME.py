import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil

from output_scrapper import OutputScrapper
from solve_problem import *
from configuration import *
from utils import create_new_session_folder, extract_pareto_plans_df, logout_button, get_date_range_from_csv, validate_csv, check_date_for_coefficient
from increase_releases import increment_min_release
from problem_generators import ProblemGenerator

logout_button()

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("You must login to see this page.")
    st.stop()

st.set_page_config(
    page_title="Water Management Dashboard",
    page_icon="💧",
    layout="wide",
)

st.title("🏠 Home - Water Management Dashboard")

# ===== Load Existing Session =====
st.subheader("📂 Load saved session")

os.makedirs(SESSIONS_DIR, exist_ok=True)
saved_sessions = [f for f in os.listdir(SESSIONS_DIR)]
selected_session = st.selectbox("Select a session", [""] + saved_sessions)
if selected_session:
    plans_df = pd.read_csv(os.path.join(SESSIONS_DIR, selected_session, "pareto_plans.csv"),
                           index_col=0)
    st.session_state["pareto_plans"] = plans_df
    st.session_state["selected_session"] = selected_session
    col1,col2 = st.columns([4, 1])
    with col1:
        st.success(f"Session '{selected_session}' successfully loaded! you can now browse the dashboard")
    with col2:
        if st.button("📊 Go to plots",
                     key="button_go_to_plots_1"):
            st.switch_page("pages/3_PLANS ANALYSIS.py")


# ===== CREATE PROBLEM AND GENERATE PLAN =====
st.markdown("---")
st.subheader("⚙️    Create Problem and Generate Plan")
# Definizione funzione per gestione errori durante la generazione dei piani:
# Se avvengono errori di qualsiasi tipo viene rimossa la sessione appena creata
@st.dialog("❌ Error during plans generation")
def error_popup(session_path):
    st.write("It is not possible to obtain plans with these parameters or period."
             " Not saving this session")
    shutil.rmtree(session_path, ignore_errors=True)
    st.session_state.pop("csv_file_upload", None) 
    st.session_state.pop("text_input_problem_plan_generation", None)
    if st.button("OK"):
        st.rerun()

col1, _ = st.columns(2)
with col1:
    uploaded_csv_file = st.file_uploader("📄 Upload the csv file containing problem parameters",
                                          type=["csv"],
                                          key="csv_file_upload")
    validation_result_dict = validate_csv(file=uploaded_csv_file)
    if uploaded_csv_file is not None:
        # Proseguo con la generazione dei problemi/piani solo se il CSV caricato è valido
        if validation_result_dict["status"] == "valid":
            st.success(validation_result_dict["message"])
        else:
            st.error(validation_result_dict["message"])
            st.info("Please upload a correct CSV file")
            st.stop()
        planner_session_name = st.text_input("💾 Session name to save (click eneter to continue)", 
                                             key="text_input_problem_plan_generation")
        if planner_session_name:
            if planner_session_name in saved_sessions:
                st.error("❌ A session with this name already exists. Please choose a different name.")
                st.stop()
            constraint1, _ = st.columns(2)
            with constraint1:
                max_time = st.number_input("⏱️ Maximum time (seconds)", min_value=0, value=600, step=60)
            st.session_state["max_time"] = max_time if max_time > 0 else None
            # generazione problena/dominio e successivamente generazione piani
            if st.button("🚀 Generate Problem and Plans",
                         key="button_problem_plan_generation"):
                session_path = create_new_session_folder(session_name=planner_session_name,
                                                        sessions_dir=SESSIONS_DIR)
                uploaded_df = pd.read_csv(uploaded_csv_file)
                uploaded_df.to_csv(os.path.join(session_path, "uploaded_csv.csv"),
                                         index=False)
                # generazione problem e domain
                with st.spinner("⏳ Generating problem.pddl and domain.pddl files"):
                    starting_date, ending_date = get_date_range_from_csv(csv_path=os.path.join(session_path, "uploaded_csv.csv"),
                                                                        date_col="Date")
                    generator = ProblemGenerator(historical_data_path=HISTORICAL_DATA_PATH,
                                                problem_data_path=os.path.join(session_path, "uploaded_csv.csv"))
                    generator.create_simple_problem(
                        starting_date=starting_date,
                        ending_date=ending_date,
                        domain_output_dir=session_path,
                        problem_output_dir=session_path
                    )
                # Controllo se i dati utilizzati per calcolare i coefficienti sono del periodo corretto oppure sono l'ultimo periodo disponibile
                coeff_msg = check_date_for_coefficient(starting_date=starting_date, 
                                                       historical_path=HISTORICAL_DATA_PATH)
                st.success("✅ Problem and Domain files generated successfully!")
                if coeff_msg:
                    st.info(coeff_msg)
                # generazione piani
                #with st.spinner(f"⏳ Generating plan... please wait about {st.session_state['max_time']} seconds. (Started at {datetime.utcnow().strftime('%H:%M:%S')} UTC)"):
                st.info(f"⚙️ Generating plan... please wait (started at {datetime.utcnow().strftime('%H:%M:%S')} UTC). "
                        "The page will update automatically when finished. Do not refresh.")
                try:
                    # la sessione ha diverse "run" con nomi generati in modo automatico
                    run_name = f"run_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
                    increment_min_release(enhsp_path=ENHSP_PATH, 
                                        domain_file=os.path.join(session_path, "domain.pddl"), 
                                        problem_file=os.path.join(session_path, "problem.pddl"), 
                                        output_dir=os.path.join(session_path, "runs", run_name), 
                                        historical_path=os.path.join(session_path, "uploaded_csv.csv"), 
                                        validator_path=VALIDATOR_PATH,
                                        gb=10, 
                                        search="gbfs", 
                                        heuristic="blind", 
                                        max_time=st.session_state["max_time"], 
                                        start_pct = 0.05, 
                                        end_pct = 0.01, 
                                        max_iterations=None)
                    plans_df = extract_pareto_plans_df(domain_path=os.path.join(session_path, "domain.pddl"),
                                                        problem_path=os.path.join(session_path, "problem.pddl"),
                                                        plans_directory=os.path.join(session_path, "runs", run_name, "plans"), 
                                                        scrapper=OutputScrapper(validator_path=VALIDATOR_PATH), 
                                                        initial_date=starting_date,
                                                        run_name=run_name,
                                                        N_sample=PARETO_PLANS)
                    if plans_df.empty:
                        st.error("No valid plans generated!")
                        raise ValueError("No valid plans generated!")
                    #save df to session folder and load into session_state
                    plans_df.to_csv(os.path.join(session_path, "pareto_plans.csv"),
                                    index=False)
                    st.session_state["pareto_plans"] = plans_df
                    st.session_state["selected_session"] = planner_session_name
                    st.success("✅ Plans generated successfully! you can now browse the dashboard")
                except Exception as e:
                    print(e)
                    error_popup(session_path)
