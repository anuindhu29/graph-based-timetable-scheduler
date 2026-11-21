import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
from docx import Document
import io
import re
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import math


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Graph-Based Timetable Scheduler",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Graph-Based Timetable Conflict Detection")
st.caption("Academic Timetable Scheduling System")

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "config": {},
    "config_confirmed": False,
    "uploaded_data": {},
    "files_confirmed": False,

    # Confirmation states
    "room_lab_confirmed": False,
    "classroom_allocation_confirmed": False,
    "lab_configuration_confirmed": False,
    "course_requirements_confirmed": False,
    "scheduling_dataset_confirmed": False,
    "scheduling_domains_confirmed": False,
    "conflict_graph_confirmed": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# SIDEBAR
# =========================================================
page = st.sidebar.radio(
    "Navigation",
    [
        "1. Programme Configuration",
        "2. Academic Calendar",
        "3. Faculty Workload",
        "4. Configuration Review",
        "5. Upload & Retrieve Files",
        "6. Faculty Constraints & HOD Approval",
        "7. Classroom & Laboratory Configuration",
        "8. Generate Timetable",
        "9. CP-SAT Timetable Solver",
        "10. View Generated Timetable"
    ],
    key="persistent_navigation_page"
)

# =========================================================
# 1. PROGRAMME CONFIGURATION
# =========================================================
if page == "1. Programme Configuration":

    st.header("Academic Programme Configuration")

    saved_programmes = st.session_state.config.get("academic_programmes", {})
    semester_type = st.selectbox(
        "Semester Type",
        ["Odd", "Even"],
        index=["Odd", "Even"].index(saved_programmes.get("semester_type", "Odd"))
            if saved_programmes.get("semester_type", "Odd") in ["Odd", "Even"] else 0,
        key="programme_semester_type"
    )

    st.subheader("B.Tech")

    include_btech = st.checkbox(
        "Include B.Tech",
        value=saved_programmes.get("B.Tech", {}).get("included", True),
        key="include_btech"
    )

    btech_sections = st.number_input(
        "Number of B.Tech Sections",
        min_value=1,
