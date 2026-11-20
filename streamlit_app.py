import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO

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
    "files_confirmed": False
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
        "5. Upload & Retrieve Files"
        "6. Generate Timetable"
    ]
)

# =========================================================
# 1. PROGRAMME CONFIGURATION
# =========================================================
if page == "1. Programme Configuration":

    st.header("Academic Programme Configuration")

    semester_type = st.selectbox(
        "Semester Type",
        ["Odd", "Even"]
    )

    st.subheader("B.Tech")

    include_btech = st.checkbox(
        "Include B.Tech",
        value=True
    )

    btech_sections = st.number_input(
        "Number of B.Tech Sections",
        min_value=1,
        max_value=20,
        value=2
    )

    if semester_type == "Odd":
        btech_semesters = [3, 5, 7]
    else:
        btech_semesters = [4, 6, 8]

    st.info(
        "B.Tech Semester 1 and Semester 2 are excluded."
    )

    st.write("Selected B.Tech semesters:", btech_semesters)

    st.divider()

    st.subheader("M.Tech")

    include_mtech = st.checkbox(
        "Include M.Tech",
        value=True
    )

    mtech_sections = st.number_input(
        "Number of M.Tech Sections",
        min_value=1,
        max_value=20,
        value=2,
        key="mtech_sections"
    )

    if semester_type == "Odd":
        mtech_semesters = [1, 3]
    else:
        mtech_semesters = [2, 4]

    st.write("Selected M.Tech semesters:", mtech_semesters)

    if st.button("Review Programme Configuration"):

        if not include_btech and not include_mtech:
            st.error("Select at least one programme.")

        else:

            config = {
                "semester_type": semester_type,
                "B.Tech": {
                    "included": include_btech,
                    "sections": int(btech_sections),
                    "semesters": btech_semesters
                        if include_btech else []
                },
                "M.Tech": {
                    "included": include_mtech,
                    "sections": int(mtech_sections),
                    "semesters": mtech_semesters
                        if include_mtech else []
                }
            }

            st.session_state.config["academic_programmes"] = config
            st.session_state.config_confirmed = False

            st.success("Configuration reviewed.")

            st.json(config)

    if st.button("Confirm Programme Configuration"):

        if "academic_programmes" not in st.session_state.config:
            st.error("Review configuration first.")

        else:
            st.session_state.config_confirmed = True
            st.success("Programme configuration confirmed!")

# =========================================================
# 2. ACADEMIC CALENDAR
# =========================================================
elif page == "2. Academic Calendar":

    st.header("Academic Calendar & Time Configuration")

    st.info("Working days: Monday to Friday")

    col1, col2 = st.columns(2)

    with col1:

        college_start = st.time_input(
            "College Start",
            datetime.strptime("08:30", "%H:%M").time()
        )

        college_end = st.time_input(
            "College End",
            datetime.strptime("17:00", "%H:%M").time()
        )

        period_duration = st.number_input(
            "Period Duration (minutes)",
            min_value=1,
            max_value=180,
            value=50
        )

    with col2:

        morning_start = st.time_input(
            "Morning Break Start",
            datetime.strptime("10:10", "%H:%M").time()
        )

        morning_end = st.time_input(
            "Morning Break End",
            datetime.strptime("10:30", "%H:%M").time()
        )

        lunch_start = st.time_input(
            "Lunch Start",
            datetime.strptime("12:10", "%H:%M").time()
        )

        lunch_end = st.time_input(
            "Lunch End",
            datetime.strptime("13:30", "%H:%M").time()
        )

        afternoon_start = st.time_input(
            "Afternoon Break Start",
            datetime.strptime("14:20", "%H:%M").time()
        )

        afternoon_end = st.time_input(
            "Afternoon Break End",
            datetime.strptime("14:30", "%H:%M").time()
        )

    if st.button("Review Calendar Configuration"):

        calendar = {
            "college_start": str(college_start),
            "college_end": str(college_end),
            "period_duration": period_duration,
            "morning_break": {
                "start": str(morning_start),
                "end": str(morning_end)
            },
            "lunch": {
                "start": str(lunch_start),
                "end": str(lunch_end)
            },
            "afternoon_break": {
                "start": str(afternoon_start),
                "end": str(afternoon_end)
            },
            "working_days": [
                "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday"
            ]
        }

        st.session_state.config["calendar"] = calendar

        st.json(calendar)

        st.success("Calendar configuration reviewed.")

    if st.button("Confirm Calendar Configuration"):

        if "calendar" not in st.session_state.config:
            st.error("Review the calendar first.")

        else:
            st.session_state.config["calendar_confirmed"] = True
            st.success("Calendar configuration confirmed!")

# =========================================================
# 3. FACULTY WORKLOAD
# =========================================================
elif page == "3. Faculty Workload":

    st.header("Faculty Workload Configuration")

    st.write("Modify weekly workload rules if required.")

    ap_hours = st.number_input(
        "Assistant Professor - Weekly Hours",
        value=16,
        min_value=1
    )

    assoc_hours = st.number_input(
        "Associate Professor - Weekly Hours",
        value=14,
        min_value=1
    )

    prof_hours = st.number_input(
        "Professor - Weekly Hours",
        value=14,
        min_value=1
    )

    st.subheader("Faculty Rules")

    mtech_allowed = st.checkbox(
        "Only Professors and Associate Professors can handle M.Tech",
        value=True
    )

    lab_consecutive = st.checkbox(
        "Laboratory sessions require consecutive periods",
        value=True
    )

    if st.button("Review Workload Rules"):

        rules = {
            "Assistant Professor": ap_hours,
            "Associate Professor": assoc_hours,
            "Professor": prof_hours,
            "mtech_eligibility": mtech_allowed,
            "lab_consecutive_periods": lab_consecutive
        }

        st.session_state.config["workload"] = rules

        st.json(rules)

    if st.button("Confirm Workload Rules"):

        if "workload" not in st.session_state.config:
            st.error("Review workload rules first.")

        else:
            st.session_state.config["workload_confirmed"] = True
            st.success("Workload rules confirmed!")

# =========================================================
# 4. COMPLETE CONFIGURATION REVIEW
# =========================================================
elif page == "4. Configuration Review":

    st.header("Complete Configuration Review")

    st.write("Review all configuration information.")

    st.json(st.session_state.config)

    if st.button("Confirm Complete Configuration"):

        required = [
            "academic_programmes",
            "calendar",
            "workload"
        ]

        missing = [
            item for item in required
            if item not in st.session_state.config
        ]

        if missing:
            st.error(
                "Missing configuration: "
                + ", ".join(missing)
            )

        else:
            st.session_state.config["complete_confirmed"] = True

            st.success(
                "Complete configuration confirmed!"
            )

            st.download_button(
                "Download PROJECT_CONFIG.json",
                json.dumps(
                    st.session_state.config,
                    indent=4
                ),
                file_name="PROJECT_CONFIG.json",
                mime="application/json"
            )

# =========================================================
# 5. UPLOAD AND RETRIEVE FILES
# =========================================================
elif page == "5. Upload & Retrieve Files":

    st.header("Upload Curriculum, Faculty and Infrastructure")

    if not st.session_state.config.get(
        "complete_confirmed", False
    ):

        st.warning(
            "Please complete and confirm the configuration "
            "before uploading files."
        )

    else:

        academic = st.session_state.config[
            "academic_programmes"
        ]

        uploaded_files = {}

        # -----------------------------
        # B.TECH CURRICULUM
        # -----------------------------
        if academic["B.Tech"]["included"]:

            st.subheader("B.Tech Curriculum")

            uploaded_files["btech"] = st.file_uploader(
                "Upload B.Tech Curriculum",
                type=["xlsx", "xls", "ods"],
                key="btech_upload"
            )

        # -----------------------------
        # M.TECH CURRICULUM
        # -----------------------------
        if academic["M.Tech"]["included"]:

            st.subheader("M.Tech Curriculum")

            uploaded_files["mtech"] = st.file_uploader(
                "Upload M.Tech Curriculum",
                type=["xlsx", "xls", "ods"],
                key="mtech_upload"
            )

        # -----------------------------
        # FACULTY
        # -----------------------------
        st.subheader("Faculty Details")

        uploaded_files["faculty"] = st.file_uploader(
            "Upload Faculty Willingness / Details",
            type=["xlsx", "xls", "ods"],
            key="faculty_upload"
        )

        # -----------------------------
        # ROOMS / LABS
        # -----------------------------
        st.subheader("Classrooms and Laboratories")

        uploaded_files["rooms"] = st.file_uploader(
            "Upload Room and Laboratory Details",
            type=["xlsx", "xls", "ods"],
            key="rooms_upload"
        )

        # =================================================
        # REVIEW UPLOADS
        # =================================================
        if st.button("Review Uploaded Files"):

            review_data = {}
            errors = []

            for key, file in uploaded_files.items():

                if file is None:

                    if key in ["btech", "mtech"]:
                        continue

                    errors.append(
                        f"Missing required file: {key}"
                    )

                    continue

                try:

                    file_bytes = file.getvalue()

                    excel = pd.ExcelFile(
                        BytesIO(file_bytes)
                    )

                    sheet_name = excel.sheet_names[0]

                    df = pd.read_excel(
                        BytesIO(file_bytes),
                        sheet_name=sheet_name
                    )

                    review_data[key] = {
                        "filename": file.name,
                        "sheet": sheet_name,
                        "data": df
                    }

                except Exception as e:

                    errors.append(
                        f"{file.name}: {str(e)}"
                    )

            if errors:

                st.error("Please correct the following:")

                for error in errors:
                    st.write("❌", error)

            else:

                st.session_state.uploaded_data = review_data
                st.session_state.files_confirmed = False

                st.success("Files read successfully!")

                for key, info in review_data.items():

                    st.markdown(
                        f"### {key.upper()} — {info['filename']}"
                    )

                    st.write(
                        "Worksheet:",
                        info["sheet"]
                    )

                    st.write(
                        "Rows:",
                        len(info["data"])
                    )

                    st.write(
                        "Columns:",
                        list(info["data"].columns)
                    )

                    st.dataframe(
                        info["data"],
                        use_container_width=True
                    )

        # =================================================
        # CONFIRM FILES
        # =================================================
        if st.button("Confirm Uploaded Files"):

            if not st.session_state.uploaded_data:

                st.error(
                    "Upload and review files first."
                )

            else:

                st.session_state.files_confirmed = True

                st.success(
                    "Uploaded files confirmed and retrieved!"
                )

        # =================================================
        # RETRIEVE STORED DATA
        # =================================================
        if st.session_state.uploaded_data:

            st.divider()

            st.subheader("Retrieve Uploaded Data")

            file_options = list(
                st.session_state.uploaded_data.keys()
            )

            selected_file = st.selectbox(
                "Select dataset",
                file_options
            )

            dataset = st.session_state.uploaded_data[
                selected_file
            ]["data"]

            st.dataframe(
                dataset,
                use_container_width=True
            )

            st.download_button(
                "Download Retrieved Dataset as CSV",
                dataset.to_csv(index=False),
                file_name=f"{selected_file}_retrieved.csv",
                mime="text/csv"
            )

            st.download_button(
                "Download Dataset as Excel",
                dataset.to_csv(index=False),
                file_name=f"{selected_file}_retrieved.csv",
                mime="text/csv"
            )
# =========================================================
# 6. GENERATE TIMETABLE
# =========================================================
elif page == "6. Generate Timetable":

    st.header("🗓️ Generate Academic Timetable")

    st.markdown(
        "Generate a conflict-free timetable using the configured "
        "academic programmes, faculty, classrooms and laboratories."
    )

    # -----------------------------------------
    # CHECK CONFIGURATION
    # -----------------------------------------
    if not st.session_state.config.get(
        "complete_confirmed", False
    ):

        st.warning(
            "⚠️ Please complete and confirm Programme Configuration "
            "before proceeding."
        )

    elif not st.session_state.get(
        "files_confirmed", False
    ):

        st.warning(
            "⚠️ Please upload, review and confirm all required datasets "
            "before generating the timetable."
        )

    else:

        st.success(
            "✅ Configuration and uploaded datasets are ready."
        )

        st.subheader("Dataset Summary")

        uploaded_data = st.session_state.uploaded_data

        cols = st.columns(4)

        for i, (key, info) in enumerate(
            uploaded_data.items()
        ):

            with cols[i % 4]:

                st.metric(
                    key.upper(),
                    len(info["data"])
                )

        st.divider()

        st.subheader("Scheduling Engine")

        st.info(
            """
            The scheduling engine will use:

            • Graph-based conflict representation  
            • Faculty constraints  
            • Student section constraints  
            • Classroom and laboratory constraints  
            • Faculty workload constraints  
            • Laboratory continuity constraints  
            • Google OR-Tools CP-SAT solver
            """
        )

        st.warning(
            "The timetable generation engine will be connected "
            "in the next development step."
        )

        # -----------------------------------------
        # GENERATION BUTTON
        # -----------------------------------------
        if st.button(
            "🚀 Generate Timetable",
            type="primary",
            use_container_width=True
        ):

            st.info(
                "Scheduling engine integration is the next step."
            )

# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "Graph-Based Timetable Conflict Detection and Resolution System"
)
