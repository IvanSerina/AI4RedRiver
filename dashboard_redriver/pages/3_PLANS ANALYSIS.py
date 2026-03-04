import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from utils import logout_button, validate_plans, extract_subsession
from output_scrapper import OutputScrapper
from configuration import VALIDATOR_PATH, SESSIONS_DIR


logout_button()

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("You must login to see this page.")
    st.stop()

if "pareto_plans" not in st.session_state:
    st.error("❌ No data available. Go to the home page and upload files.")
    st.stop()

session_path = os.path.join(SESSIONS_DIR,st.session_state.selected_session)
df = pd.read_csv(os.path.join(session_path, "pareto_plans.csv"))


# ==== SELECT PLAN TO PLOT ====
# Mostra un plot tra cui scegliere il piano da analizzare.
# Vengono considerati solo i piani validi al momento della generazione.
# Tutti i piani raccolti vengono validati in base all'ultima versione di problem.pddl
# L'utente può scegliere quali run visualizzare (di default viene visualizzato tutto)
last_rows = df.sort_values("date").groupby("plan").tail(1)
plans_validation = validate_plans(session_dir=os.path.join(SESSIONS_DIR,st.session_state.selected_session),
                                  output_scrapper=OutputScrapper(validator_path=VALIDATOR_PATH))
last_rows = last_rows.merge(
    plans_validation[["plan", "valid"]],
    on="plan",
    how="left"
)
saved_subsessions = [
    f for f in os.listdir(os.path.join(SESSIONS_DIR, st.session_state.selected_session, "runs"))
    if os.path.isdir(os.path.join(SESSIONS_DIR, st.session_state.selected_session, "runs", f))
]
last_rows["subsession"] = last_rows["plan"].apply(extract_subsession) # aggiungi colonna con subsession_name estratto da "plan"
# selezione multipla
selected_subsessions = st.multiselect(
    "📂 Select subsessions to display",
    options=saved_subsessions,
    default=saved_subsessions  # di default mostra tutte
)
filtered_last_rows = last_rows[last_rows["subsession"].isin(selected_subsessions)]
# scatter plot su cui poter selezionare il piano daanalizzare
fig1 = px.scatter(
    filtered_last_rows, 
    x="cumulative_tot_release", 
    y="cumulative_production", 
    color="valid",  # colora in base alla colonna "valid"
    color_discrete_map={True: "green", False: "red"},
    title="SELECT A PLAN (click on a plot's point to select the plan)",
    labels={"valid": "Plan is valid?"},  # label legenda
    hover_data=["plan","cumulative_production","cumulative_tot_release"]
)
# personalizzazione marker e posizione testo (necessaria per la selezione)
fig1.update_traces(marker=dict(size=12),
                   customdata=filtered_last_rows[["plan"]].values,
                   textposition="top center")
# Streamlit widget interattivo
selected = st.plotly_chart(fig1, use_container_width=True, on_select="rerun")

# ======= Selezione piano =======
if selected and selected["selection"]["points"]:
    point = selected["selection"]["points"][0]
    plan_selected = point["customdata"][0]  # recupero plan dai customdata
    st.session_state["selected_plan"] = plan_selected
else:
    plan_selected = st.session_state.get("selected_plan")

# ==== PLOTs ====
st.divider()
if plan_selected:
    st.markdown(f"<h3 style='text-align: center;'>{plan_selected} features</h3>", unsafe_allow_html=True)
    filtered_df = df[df["plan"] == plan_selected]
    # plot con feature predefinita
    plot_1 = px.line(
        filtered_df,
        x=filtered_df.date,
        y="tot_release",
        title="Total Release",
        markers=True,
    )
    st.plotly_chart(plot_1, use_container_width=True)
    # plot con feature predefinita
    plot_2 = px.line(
        filtered_df,
        x=filtered_df.date,
        y="production",
        title="Production",
        markers=True,
    )
    st.plotly_chart(plot_2, use_container_width=True)
    # plot con feature predefinita
    plot_3 = px.line(
        filtered_df,
        x=filtered_df.date,
        y="storage",
        title="Storage",
        markers=True,
    )
    st.plotly_chart(plot_3, use_container_width=True)

    # plot che permette di comparare due feature scelte dall'utente
    st.divider()
    st.markdown("#### Compare custom features")
    numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()
    numeric_cols = [
        col for col in numeric_cols
        if not col.startswith("Unnamed") and col not in ["plan"]
    ]
    col1, col2 = st.columns(2)
    with col1:
        feature_y1 = st.selectbox("Select first feature",
                                  numeric_cols,
                                  index=0, 
                                  key="feature_y1")
    with col2:
        feature_y2 = st.selectbox("Select second feature", 
                                  numeric_cols, 
                                  index=1,
                                  key="feature_y2")
    if feature_y1 and feature_y2:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=filtered_df["date"], y=filtered_df[feature_y1], 
                    mode="lines+markers", name=feature_y1),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=filtered_df["date"], y=filtered_df[feature_y2], 
                    mode="lines+markers", name=feature_y2),
            secondary_y=True,
        )
        fig.update_layout(
            title=f"Comparison: {feature_y1} vs {feature_y2}",
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        )
        fig.update_yaxes(title_text=feature_y1, secondary_y=False)
        fig.update_yaxes(title_text=feature_y2, secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select two features to compare.")
    
else:
    st.info("👉 Select a point on the plot to visualize features.")