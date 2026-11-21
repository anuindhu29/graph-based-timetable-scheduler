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
    ]
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
        max_value=20,
        value=int(saved_programmes.get("B.Tech", {}).get("sections", 2)),
        key="btech_sections"
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
        value=saved_programmes.get("M.Tech", {}).get("included", True),
        key="include_mtech"
    )

    mtech_sections = st.number_input(
        "Number of M.Tech Sections",
        min_value=1,
        max_value=20,
        value=int(saved_programmes.get("M.Tech", {}).get("sections", 2)),
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
            st.session_state.config["complete_confirmed"] = False
            st.session_state.config["academic_programmes_confirmed"] = False
            st.session_state.files_confirmed = False
            st.session_state.faculty_constraints_confirmed = False
            st.session_state.room_lab_confirmed = False
            st.session_state.classroom_allocation_confirmed = False
            st.session_state.lab_configuration_confirmed = False
            st.session_state.course_requirements_confirmed = False
            st.session_state.scheduling_dataset_confirmed = False
            st.session_state.scheduling_domains_confirmed = False
            st.session_state.conflict_graph_confirmed = False

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

    saved_calendar = st.session_state.config.get("calendar", {})
    def _time_default(value, fallback):
        try:
            return datetime.strptime(str(value), "%H:%M:%S").time()
        except ValueError:
            try:
                return datetime.strptime(str(value), "%H:%M").time()
            except (ValueError, TypeError):
                return datetime.strptime(fallback, "%H:%M").time()

    col1, col2 = st.columns(2)

    with col1:

        college_start = st.time_input(
            "College Start",
            value=_time_default(saved_calendar.get("college_start"), "08:30"),
            key="calendar_college_start"
        )

        college_end = st.time_input(
            "College End",
            value=_time_default(saved_calendar.get("college_end"), "17:00"),
            key="calendar_college_end"
        )

        period_duration = st.number_input(
            "Period Duration (minutes)",
            min_value=1,
            max_value=180,
            value=int(saved_calendar.get("period_duration", 50)),
            key="calendar_period_duration"
        )

    with col2:

        morning_break_saved = saved_calendar.get("morning_break", {})
        lunch_saved = saved_calendar.get("lunch", {})
        afternoon_break_saved = saved_calendar.get("afternoon_break", {})

        morning_start = st.time_input(
            "Morning Break Start",
            value=_time_default(morning_break_saved.get("start"), "10:10"),
            key="calendar_morning_start"
        )

        morning_end = st.time_input(
            "Morning Break End",
            value=_time_default(morning_break_saved.get("end"), "10:30"),
            key="calendar_morning_end"
        )

        lunch_start = st.time_input(
            "Lunch Start",
            value=_time_default(lunch_saved.get("start"), "12:10"),
            key="calendar_lunch_start"
        )

        lunch_end = st.time_input(
            "Lunch End",
            value=_time_default(lunch_saved.get("end"), "13:30"),
            key="calendar_lunch_end"
        )

        afternoon_start = st.time_input(
            "Afternoon Break Start",
            value=_time_default(afternoon_break_saved.get("start"), "14:20"),
            key="calendar_afternoon_start"
        )

        afternoon_end = st.time_input(
            "Afternoon Break End",
            value=_time_default(afternoon_break_saved.get("end"), "14:30"),
            key="calendar_afternoon_end"
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
        st.session_state.config["calendar_confirmed"] = False
        st.session_state.config["complete_confirmed"] = False
        st.session_state.files_confirmed = False
        st.session_state.faculty_constraints_confirmed = False
        st.session_state.room_lab_confirmed = False
        st.session_state.classroom_allocation_confirmed = False
        st.session_state.lab_configuration_confirmed = False
        st.session_state.course_requirements_confirmed = False
        st.session_state.scheduling_dataset_confirmed = False
        st.session_state.scheduling_domains_confirmed = False
        st.session_state.conflict_graph_confirmed = False

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

    saved_workload = st.session_state.config.get("workload", {})
    ap_hours = st.number_input(
        "Assistant Professor - Weekly Hours",
        value=int(saved_workload.get("Assistant Professor", 16)),
        min_value=1,
        key="workload_ap_hours"
    )

    assoc_hours = st.number_input(
        "Associate Professor - Weekly Hours",
        value=int(saved_workload.get("Associate Professor", 14)),
        min_value=1,
        key="workload_assoc_hours"
    )

    prof_hours = st.number_input(
        "Professor - Weekly Hours",
        value=int(saved_workload.get("Professor", 14)),
        min_value=1,
        key="workload_prof_hours"
    )

    st.subheader("Faculty Rules")

    mtech_allowed = st.checkbox(
        "Only Professors and Associate Professors can handle M.Tech",
        value=saved_workload.get("mtech_eligibility", True),
        key="workload_mtech_allowed"
    )

    lab_consecutive = st.checkbox(
        "Laboratory sessions require consecutive periods",
        value=saved_workload.get("lab_consecutive_periods", True),
        key="workload_lab_consecutive"
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
        st.session_state.config["workload_confirmed"] = False
        st.session_state.config["complete_confirmed"] = False
        st.session_state.faculty_constraints_confirmed = False
        st.session_state.scheduling_dataset_confirmed = False
        st.session_state.scheduling_domains_confirmed = False
        st.session_state.conflict_graph_confirmed = False

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

        unconfirmed = [
            label for label, flag in [
                ("Programme Configuration", st.session_state.get("config_confirmed", False)),
                ("Calendar Configuration", st.session_state.config.get("calendar_confirmed", False)),
                ("Workload Rules", st.session_state.config.get("workload_confirmed", False)),
            ] if not flag
        ]

        if missing:
            st.error(
                "Missing configuration: "
                + ", ".join(missing)
            )

        elif unconfirmed:
            st.error("Confirm these steps first: " + ", ".join(unconfirmed))

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

    if not st.session_state.config.get("complete_confirmed", False):

        st.warning(
            "Please complete and confirm the configuration "
            "before uploading files."
        )

    else:

        academic = st.session_state.config["academic_programmes"]

        uploaded_files = {}

        if st.session_state.uploaded_data:
            st.info("Previously reviewed files are retained in this session.")
            st.write({
                key: info.get("filename", key)
                for key, info in st.session_state.uploaded_data.items()
            })

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

        # -----------------------------
        # SCHEDULING RULES
        # -----------------------------
        st.subheader("Scheduling Rules and Constraints")

        uploaded_files["rules"] = st.file_uploader(
            "Upload Timetable Scheduling Rules",
            type=["pdf", "docx", "txt"],
            key="rules_upload"
        )

        # =================================================
        # REVIEW UPLOADS
        # =================================================
        if st.button("Review Uploaded Files"):

            # Start with already-reviewed data so navigating back and
            # reviewing only a newly uploaded file does not erase others.
            review_data = dict(st.session_state.uploaded_data)
            errors = []

            for key, file in uploaded_files.items():

                # Skip curriculum if programme is excluded
                if file is None:

                    if key in ["btech", "mtech"] or key in review_data:
                        continue

                    errors.append(f"Missing required file: {key}")
                    continue

                try:

                    file_bytes = file.getvalue()
                    filename = file.name.lower()

                    # =====================================
                    # EXCEL / SPREADSHEET
                    # =====================================
                    if filename.endswith((".xlsx", ".xls", ".ods")):

                        df = pd.read_excel(BytesIO(file_bytes))

                        review_data[key] = {
                            "filename": file.name,
                            "type": "excel",
                            "data": df,
                            "raw_bytes": file_bytes
                        }

                    # =====================================
                    # WORD DOCUMENT
                    # =====================================
                    elif filename.endswith(".docx"):

                        doc = Document(BytesIO(file_bytes))

                        # Extract actual paragraph TEXT
                        paragraph_texts = [
                            p.text.strip()
                            for p in doc.paragraphs
                            if p.text.strip()
                        ]

                        # Extract tables
                        tables_data = []

                        for table in doc.tables:

                            table_data = []

                            for row in table.rows:

                                row_data = [
                                    cell.text.strip()
                                    for cell in row.cells
                                ]

                                table_data.append(row_data)

                            tables_data.append(table_data)

                        # Combine paragraphs and tables into text
                        document_text = "\n\n".join(paragraph_texts)

                        for table_index, table in enumerate(
                            tables_data, start=1
                        ):

                            document_text += (
                                f"\n\nTABLE {table_index}\n"
                            )

                            for row in table:

                                document_text += (
                                    " | ".join(row) + "\n"
                                )

                        review_data[key] = {
                            "filename": file.name,
                            "type": "document",
                            "text": document_text,
                            "paragraphs": paragraph_texts,
                            "tables": tables_data,
                            "raw_bytes": file_bytes
                        }

                    # =====================================
                    # PDF DOCUMENT
                    # =====================================
                    elif filename.endswith(".pdf"):

                        from PyPDF2 import PdfReader

                        pdf_reader = PdfReader(BytesIO(file_bytes))

                        pdf_text = "\n\n".join(
                            page.extract_text() or ""
                            for page in pdf_reader.pages
                        )

                        review_data[key] = {
                            "filename": file.name,
                            "type": "document",
                            "text": pdf_text,
                            "paragraphs": pdf_text.splitlines(),
                            "tables": [],
                            "raw_bytes": file_bytes
                        }

                    # =====================================
                    # TEXT FILE
                    # =====================================
                    elif filename.endswith(".txt"):

                        document_text = file_bytes.decode(
                            "utf-8",
                            errors="replace"
                        )

                        review_data[key] = {
                            "filename": file.name,
                            "type": "document",
                            "text": document_text,
                            "paragraphs": document_text.splitlines(),
                            "tables": [],
                            "raw_bytes": file_bytes
                        }

                    else:

                        errors.append(
                            f"{file.name}: Unsupported file format"
                        )

                except Exception as e:

                    errors.append(
                        f"{file.name}: {str(e)}"
                    )

            # =============================================
            # DISPLAY ERRORS
            # =============================================
            if errors:

                st.error("Please correct the following:")

                for error in errors:
                    st.write("❌", error)

            # =============================================
            # DISPLAY REVIEW DATA
            # =============================================
            else:

                st.session_state.uploaded_data = review_data
                st.session_state.files_confirmed = False
                st.session_state.faculty_constraints_confirmed = False
                st.session_state.room_lab_confirmed = False
                st.session_state.classroom_allocation_confirmed = False
                st.session_state.lab_configuration_confirmed = False
                st.session_state.scheduling_dataset_confirmed = False
                st.session_state.scheduling_domains_confirmed = False

                st.success("Files read successfully!")

                for key, info in review_data.items():

                    st.markdown(
                        f"### {key.upper()} — {info['filename']}"
                    )

                    # ---------------------------------
                    # EXCEL REVIEW
                    # ---------------------------------
                    if info["type"] == "excel":

                        df = info["data"]

                        st.write("Rows:", len(df))

                        st.write(
                            "Columns:",
                            list(df.columns)
                        )

                        st.dataframe(
                            df,
                            use_container_width=True
                        )

                    # ---------------------------------
                    # DOCUMENT REVIEW
                    # ---------------------------------
                    elif info["type"] == "document":

                        st.success(
                            "Document extracted successfully"
                        )

                        if info["text"].strip():

                            st.markdown("#### Document Text")

                            st.text_area(
                                "Extracted text",
                                value=info["text"],
                                height=350,
                                key=f"review_text_{key}"
                            )

                        else:

                            st.warning(
                                "No readable text was extracted "
                                "from this document."
                            )

                        # Display extracted tables
                        if info["tables"]:

                            st.markdown("#### Document Tables")

                            for table_index, table_data in enumerate(
                                info["tables"], start=1
                            ):

                                st.write(
                                    f"Table {table_index}"
                                )

                                if table_data:

                                    table_df = pd.DataFrame(
                                        table_data
                                    )

                                    st.dataframe(
                                        table_df,
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
                    "Uploaded files confirmed successfully!"
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
                file_options,
                key="retrieve_dataset"
            )

            selected_info = (
                st.session_state.uploaded_data[selected_file]
            )

            st.write(
                "**Filename:**",
                selected_info["filename"]
            )

            # =============================================
            # RETRIEVE EXCEL
            # =============================================
            if selected_info["type"] == "excel":

                dataset = selected_info["data"]

                st.dataframe(
                    dataset,
                    use_container_width=True
                )

                # CSV DOWNLOAD
                st.download_button(
                    "Download Retrieved Dataset as CSV",
                    data=dataset.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name=f"{selected_file}_retrieved.csv",
                    mime="text/csv",
                    key=f"csv_download_{selected_file}"
                )

                # EXCEL DOWNLOAD
                excel_buffer = BytesIO()

                with pd.ExcelWriter(
                    excel_buffer,
                    engine="openpyxl"
                ) as writer:

                    dataset.to_excel(
                        writer,
                        index=False,
                        sheet_name="Data"
                    )

                st.download_button(
                    "Download Dataset as Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"{selected_file}_retrieved.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    key=f"excel_download_{selected_file}"
                )

            # =============================================
            # RETRIEVE DOCUMENT
            # =============================================
            elif selected_info["type"] == "document":

                st.success(
                    "Document uploaded and extracted successfully."
                )

                document_text = selected_info.get("text", "")

                if document_text.strip():

                    st.subheader("Extracted Document Content")

                    st.text_area(
                        "Document text",
                        value=document_text,
                        height=400,
                        key=f"retrieve_text_{selected_file}"
                    )

                    # DOWNLOAD EXTRACTED TEXT
                    st.download_button(
                        "Download Extracted Text",
                        data=document_text.encode("utf-8"),
                        file_name=f"{selected_file}_extracted.txt",
                        mime="text/plain",
                        key=f"text_download_{selected_file}"
                    )

                else:

                    st.warning(
                        "The document was uploaded, but no readable "
                        "text was extracted."
                    )

                # DOWNLOAD ORIGINAL FILE
                st.download_button(
                    "Download Original Document",
                    data=selected_info["raw_bytes"],
                    file_name=selected_info["filename"],
                    key=f"original_download_{selected_file}"
                )
# =========================================================
# 6. FACULTY CONSTRAINTS & HOD APPROVAL
# =========================================================
elif page == "6. Faculty Constraints & HOD Approval":

    st.header("Faculty Constraints & HOD Approval")

    # -----------------------------------------------------
    # CHECK PREVIOUS STEPS
    # -----------------------------------------------------
    if not st.session_state.get("files_confirmed", False):

        st.warning(
            "Please upload, review and confirm the faculty "
            "dataset before proceeding."
        )

    elif "faculty" not in st.session_state.uploaded_data:

        st.error(
            "Faculty dataset is missing. Upload the faculty "
            "Excel file in Page 5."
        )

    else:

        faculty_df = st.session_state.uploaded_data[
            "faculty"
        ]["data"].copy()

        # -------------------------------------------------
        # IDENTIFY FACULTY COLUMNS
        # -------------------------------------------------
        def find_column(df, possible_names):

            normalized = {
                str(col).strip().lower().replace("_", " "): col
                for col in df.columns
            }

            for name in possible_names:

                name = name.strip().lower().replace("_", " ")

                if name in normalized:
                    return normalized[name]

            return None

        id_col = find_column(
            faculty_df,
            [
                "Faculty ID",
                "Faculty_ID",
                "ID",
                "Employee ID"
            ]
        )

        name_col = find_column(
            faculty_df,
            [
                "Faculty Name",
                "Faculty_Name",
                "Name",
                "Faculty"
            ]
        )

        designation_col = find_column(
            faculty_df,
            [
                "Designation",
                "Position",
                "Academic Designation"
            ]
        )

        # -------------------------------------------------
        # BUILD FACULTY MASTER
        # -------------------------------------------------
        if name_col is None:

            st.error(
                "Could not identify the Faculty Name column "
                "in your uploaded Excel file."
            )

            st.write(
                "Available columns:",
                list(faculty_df.columns)
            )

        else:

            if id_col is None:
                faculty_df["Faculty_ID"] = (
                    faculty_df.index + 1
                ).astype(str)

                id_col = "Faculty_ID"

            if designation_col is None:
                faculty_df["Designation"] = "Unknown"

                designation_col = "Designation"

            faculty_master = (
                faculty_df[
                    [id_col, name_col, designation_col]
                ]
                .drop_duplicates(subset=[id_col])
                .copy()
            )

            faculty_master.columns = [
                "Faculty_ID",
                "Faculty_Name",
                "Designation"
            ]

            faculty_master["Faculty_ID"] = (
                faculty_master["Faculty_ID"]
                .astype(str)
                .str.strip()
            )

            faculty_master["Faculty_Name"] = (
                faculty_master["Faculty_Name"]
                .astype(str)
                .str.strip()
            )

            faculty_master["Designation"] = (
                faculty_master["Designation"]
                .astype(str)
                .str.strip()
            )

            faculty_master = faculty_master[
                faculty_master["Faculty_Name"] != ""
            ].reset_index(drop=True)

            st.success(
                f"Faculty records loaded: {len(faculty_master)}"
            )

            st.dataframe(
                faculty_master,
                use_container_width=True
            )

            # -------------------------------------------------
            # CALENDAR INFORMATION
            # -------------------------------------------------
            calendar = st.session_state.config.get(
                "calendar", {}
            )

            working_days = calendar.get(
                "working_days",
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ]
            )

            college_start = calendar.get(
                "college_start",
                "08:30"
            )

            college_end = calendar.get(
                "college_end",
                "17:00"
            )

            period_duration = int(
                calendar.get(
                    "period_duration",
                    50
                )
            )

            morning_break = calendar.get(
                "morning_break",
                {"start": "10:10", "end": "10:30"}
            )

            lunch = calendar.get(
                "lunch",
                {"start": "12:10", "end": "13:30"}
            )

            afternoon_break = calendar.get(
                "afternoon_break",
                {"start": "14:20", "end": "14:30"}
            )

            # -------------------------------------------------
            # GENERATE VALID PERIODS
            # -------------------------------------------------
            def time_to_minutes(value):

                hour, minute = map(
                    int,
                    str(value).split(":")[:2]
                )

                return hour * 60 + minute

            def minutes_to_time(value):

                return (
                    f"{value // 60:02d}:"
                    f"{value % 60:02d}"
                )

            breaks = [
                (
                    time_to_minutes(morning_break["start"]),
                    time_to_minutes(morning_break["end"])
                ),
                (
                    time_to_minutes(lunch["start"]),
                    time_to_minutes(lunch["end"])
                ),
                (
                    time_to_minutes(afternoon_break["start"]),
                    time_to_minutes(afternoon_break["end"])
                )
            ]

            valid_periods = []

            start_minutes = time_to_minutes(college_start)
            end_minutes = time_to_minutes(college_end)

            for day in working_days:

                current = start_minutes
                period_number = 1

                while current + period_duration <= end_minutes:

                    period_end = current + period_duration

                    overlapping_break = None

                    for break_start, break_end in breaks:

                        if (
                            current < break_end
                            and period_end > break_start
                        ):

                            overlapping_break = break_end
                            break

                    if overlapping_break is not None:

                        current = overlapping_break
                        continue

                    valid_periods.append({
                        "Day": day,
                        "Period": period_number,
                        "Start_Time": minutes_to_time(current),
                        "End_Time": minutes_to_time(period_end)
                    })

                    current += period_duration
                    period_number += 1

            slot_options = [
                (
                    f"{p['Day']} | "
                    f"{p['Start_Time']}-{p['End_Time']}",
                    (
                        f"{p['Day']}|"
                        f"{p['Start_Time']}|"
                        f"{p['End_Time']}"
                    )
                )
                for p in valid_periods
            ]

            # -------------------------------------------------
            # YEAR OPTIONS
            # -------------------------------------------------
            btech_years = [
                "Year 1",
                "Year 2",
                "Year 3",
                "Year 4"
            ]

            mtech_years = [
                "Year 1",
                "Year 2"
            ]

            # -------------------------------------------------
            # FACULTY FORMS
            # -------------------------------------------------
            st.divider()

            st.subheader(
                "Individual Faculty Approval and Availability"
            )

            st.info(
                "Select unavailable days or time slots only. "
                "Leave both empty if the faculty member is "
                "available throughout the week."
            )

            faculty_forms = {}

            for _, faculty in faculty_master.iterrows():

                faculty_id = str(faculty["Faculty_ID"])
                faculty_name = str(faculty["Faculty_Name"])
                designation = str(faculty["Designation"])

                is_senior = (
                    "assistant" not in designation.lower()
                    and "professor" in designation.lower()
                )

                with st.expander(
                    f"{faculty_name} | {faculty_id} | {designation}",
                    expanded=False
                ):

                    st.markdown("#### Programme Approval")

                    btech_approved = st.checkbox(
                        "Approved for B.Tech",
                        value=True,
                        key=f"btech_approved_{faculty_id}"
                    )

                    selected_btech_years = st.multiselect(
                        "B.Tech Years Approved",
                        btech_years,
                        default=btech_years,
                        key=f"btech_years_{faculty_id}"
                    )

                    mtech_approved = st.checkbox(
                        "Approved for M.Tech",
                        value=is_senior,
                        key=f"mtech_approved_{faculty_id}"
                    )

                    selected_mtech_years = st.multiselect(
                        "M.Tech Years Approved",
                        mtech_years,
                        default=mtech_years if is_senior else [],
                        key=f"mtech_years_{faculty_id}"
                    )

                    st.markdown("#### Availability Restrictions")

                    unavailable_days = st.multiselect(
                        "Unavailable Days",
                        working_days,
                        default=[],
                        key=f"unavailable_days_{faculty_id}"
                    )

                    unavailable_slots = st.multiselect(
                        "Unavailable Time Slots",
                        options=[
                            label for label, value in slot_options
                        ],
                        key=f"unavailable_slots_{faculty_id}"
                    )

                    st.markdown("#### HOD Approval")

                    approved_by = st.text_input(
                        "Approved By (HOD)",
                        key=f"approved_by_{faculty_id}"
                    )

                    remarks = st.text_area(
                        "Remarks / Additional Restrictions",
                        key=f"remarks_{faculty_id}"
                    )

                    faculty_forms[faculty_id] = {
                        "name": faculty_name,
                        "designation": designation,
                        "btech_approved": btech_approved,
                        "btech_years": selected_btech_years,
                        "mtech_approved": mtech_approved,
                        "mtech_years": selected_mtech_years,
                        "unavailable_days": unavailable_days,
                        "unavailable_slots": unavailable_slots,
                        "approved_by": approved_by,
                        "remarks": remarks
                    }

            # -------------------------------------------------
            # SAVE FACULTY CONSTRAINTS
            # -------------------------------------------------
            if st.button(
                "Save Faculty Constraints and Approvals",
                type="primary",
                use_container_width=True
            ):

                approval_records = []
                constraint_records = []
                errors = []

                for faculty_id, form in faculty_forms.items():

                    if (
                        form["btech_approved"]
                        and not form["btech_years"]
                    ):

                        errors.append(
                            f"{form['name']}: Select at least "
                            "one B.Tech year."
                        )

                    if (
                        form["mtech_approved"]
                        and not form["mtech_years"]
                    ):

                        errors.append(
                            f"{form['name']}: Select at least "
                            "one M.Tech year."
                        )

                    if (
                        form["mtech_approved"]
                        and "assistant" in form["designation"].lower()
                        and not form["approved_by"].strip()
                    ):

                        errors.append(
                            f"{form['name']}: HOD name is required "
                            "for Assistant Professor M.Tech approval."
                        )

                if errors:

                    st.error("Please correct the following:")

                    for error in errors:
                        st.write("❌", error)

                else:

                    for faculty_id, form in faculty_forms.items():

                        approval_records.append({
                            "Faculty_ID": faculty_id,
                            "Faculty_Name": form["name"],
                            "Designation": form["designation"],
                            "BTech_Approved": form["btech_approved"],
                            "BTech_Years": form["btech_years"],
                            "MTech_Approved": form["mtech_approved"],
                            "MTech_Years": form["mtech_years"],
                            "Approved_By": form["approved_by"],
                            "Remarks": form["remarks"]
                        })

                        constraint_records.append({
                            "Faculty_ID": faculty_id,
                            "Faculty_Name": form["name"],
                            "Unavailable_Days": form["unavailable_days"],
                            "Unavailable_Slots": form["unavailable_slots"]
                        })

                    st.session_state.faculty_approvals = (
                        approval_records
                    )

                    st.session_state.faculty_constraints = (
                        constraint_records
                    )

                    st.session_state.faculty_constraints_confirmed = True

                    st.session_state.config[
                        "faculty_approvals"
                    ] = approval_records

                    st.session_state.config[
                        "faculty_constraints"
                    ] = constraint_records

                    st.success(
                        "Faculty constraints and approvals saved successfully!"
                    )

                    st.subheader("Approval Summary")

                    st.dataframe(
                        pd.DataFrame(approval_records),
                        use_container_width=True
                    )

                    st.subheader("Availability Restrictions")

                    st.dataframe(
                        pd.DataFrame(constraint_records),
                        use_container_width=True
                    )     

# =========================================================
# 7. CLASSROOM & LABORATORY CONFIGURATION
# =========================================================
elif page == "7. Classroom & Laboratory Configuration":

    st.header("Classroom & Laboratory Configuration")

    if not st.session_state.get("files_confirmed", False):

        st.warning(
            "Please upload, review and confirm your files first."
        )

    elif "rooms" not in st.session_state.uploaded_data:

        st.error(
            "Room and Laboratory dataset not found. "
            "Upload it in Page 5."
        )

    else:

        room_df = st.session_state.uploaded_data[
            "rooms"
        ]["data"].copy()

        # Remove exported Excel/CSV index columns
        room_df = room_df.loc[
            :,
            ~room_df.columns.astype(str).str.startswith("Unnamed")
        ]

        st.subheader("Uploaded Infrastructure")

        st.write(
            "Review and modify classroom and laboratory details "
            "if necessary."
        )

        edited_rooms = st.data_editor(
            room_df,
            use_container_width=True,
            num_rows="dynamic",
            key="room_lab_editor"
        )

        st.divider()

        st.subheader("Infrastructure Summary")

        if "Type" in edited_rooms.columns:

            room_count = (
                edited_rooms["Type"]
                .astype(str)
                .str.lower()
                .eq("classroom")
                .sum()
            )

            lab_count = (
                edited_rooms["Type"]
                .astype(str)
                .str.lower()
                .eq("laboratory")
                .sum()
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Resources",
                len(edited_rooms)
            )

            col2.metric(
                "Classrooms",
                int(room_count)
            )

            col3.metric(
                "Laboratories",
                int(lab_count)
            )

        st.divider()

        if st.button(
            "Save Classroom & Laboratory Configuration",
            type="primary",
            use_container_width=True
        ):

            errors = []

            required_columns = [
                "Room/Lab ID",
                "Room/Lab Name",
                "Type",
                "Capacity"
            ]

            missing_columns = [
                col for col in required_columns
                if col not in edited_rooms.columns
            ]

            if missing_columns:

                errors.append(
                    "Missing columns: "
                    + ", ".join(missing_columns)
                )

            else:

                if edited_rooms["Room/Lab ID"].duplicated().any():

                    errors.append(
                        "Room/Lab IDs must be unique."
                    )

                if edited_rooms["Capacity"].isnull().any():

                    errors.append(
                        "Capacity cannot be empty."
                    )

                valid_types = [
                    "Classroom",
                    "Laboratory"
                ]

                invalid_types = edited_rooms[
                    ~edited_rooms["Type"].isin(valid_types)
                ]

                if not invalid_types.empty:

                    errors.append(
                        "Type must be Classroom or Laboratory."
                    )

                try:

                    edited_rooms["Capacity"] = (
                        edited_rooms["Capacity"]
                        .astype(int)
                    )

                    if (
                        edited_rooms["Capacity"] <= 0
                    ).any():

                        errors.append(
                            "Capacity must be greater than zero."
                        )

                except Exception:

                    errors.append(
                        "Capacity must contain numeric values."
                    )

            if errors:

                st.error("Please correct these errors:")

                for error in errors:
                    st.write("❌", error)

            else:

                st.session_state.room_lab_config = (
                    edited_rooms.copy()
                )

                st.session_state.room_lab_confirmed = True

                st.session_state.config[
                    "room_lab_configuration"
                ] = edited_rooms.to_dict(
                    orient="records"
                )

                st.success(
                    "Classroom and Laboratory configuration saved!"
                )

                st.subheader("Final Infrastructure")

                st.dataframe(
                    edited_rooms,
                    use_container_width=True
                )

                st.download_button(
                    "Download Infrastructure Configuration",
                    data=edited_rooms.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="ROOM_LAB_CONFIG.csv",
                    mime="text/csv"
                )
# =========================================================
# 8. GENERATE TIMETABLE
# =========================================================
elif page == "8. Generate Timetable":

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
    
    elif not st.session_state.get(
        "faculty_constraints_confirmed", False
    ):
    
        st.warning(
            "Please complete and save Faculty Constraints "
            "& HOD Approval before generating the timetable."
        )
    
    elif not st.session_state.get(
        "room_lab_confirmed", False
    ):
    
        st.warning(
            "Please complete and save Classroom & Laboratory "
            "Configuration before generating the timetable."
        )
    
    else:

        st.success(
            "Configuration and uploaded datasets are ready."
        )

        # =============================================
        # SCHEDULING WORKFLOW START SCREEN
        # =============================================

        if not st.session_state.get(
            "scheduling_workflow_started", False
        ):

            st.divider()

            st.title("Timetable Scheduling Workflow")

            st.info(
                "Your configurations and datasets are ready. "
                "Click below to begin the timetable generation workflow."
            )

            if st.button(
                "Start New Scheduling Process",
                type="primary",
                use_container_width=True
            ):

                st.session_state.scheduling_workflow_started = True

                st.rerun()

            st.stop()

        
        st.subheader("Dataset Summary")

        uploaded_data = st.session_state.uploaded_data

        cols = st.columns(4)
        
        for i, (key, info) in enumerate(
            uploaded_data.items()
        ):
        
            with cols[i % 4]:
        
                if info.get("type") == "excel":
        
                    count = len(info["data"])
        
                elif info.get("type") == "document":
        
                    count = "Document"
        
                else:
        
                    count = "N/A"
        
                st.metric(
                    key.upper(),
                    count
                )

        st.divider()

        # =================================================
        # COURSE PROCESSING & WEEKLY REQUIREMENTS
        # =================================================

        st.subheader("Course Processing & Weekly Requirements")

        academic_config = st.session_state.config[
            "academic_programmes"
        ]

        semester_type = academic_config["semester_type"]

        if semester_type == "Odd":
            btech_active_semesters = [3, 5, 7]
            mtech_active_semesters = [1, 3]
        else:
            btech_active_semesters = [4, 6, 8]
            mtech_active_semesters = [2, 4]

        course_datasets = []

        # ---------------------------------------------
        # LOAD B.TECH CURRICULUM
        # ---------------------------------------------
        if academic_config["B.Tech"]["included"]:

            if "btech" in uploaded_data:

                btech_df = uploaded_data["btech"]["data"].copy()

                btech_df["Programme_Type"] = "B.Tech"

                course_datasets.append(btech_df)

            else:

                st.warning(
                    "B.Tech curriculum was not uploaded."
                )

        # ---------------------------------------------
        # LOAD M.TECH CURRICULUM
        # ---------------------------------------------
        if academic_config["M.Tech"]["included"]:

            if "mtech" in uploaded_data:

                mtech_df = uploaded_data["mtech"]["data"].copy()

                mtech_df["Programme_Type"] = "M.Tech"

                course_datasets.append(mtech_df)

            else:

                st.warning(
                    "M.Tech curriculum was not uploaded."
                )

        # ---------------------------------------------
        # COMBINE CURRICULUM
        # ---------------------------------------------

        if course_datasets:

            curriculum = pd.concat(
                course_datasets,
                ignore_index=True
            )

            curriculum.columns = (
                curriculum.columns
                .astype(str)
                .str.strip()
            )

        else:

            st.error(
                "No curriculum dataset is available for processing."
            )

            st.stop()
        # -----------------------------------------
        # CLEAN NUMERIC FIELDS
        # -----------------------------------------
        numeric_columns = [
            "Semester",
            "L_Hours",
            "T_Hours",
            "P_Hours",
            "Credits"
        ]

        for column in numeric_columns:

            if column in curriculum.columns:

                curriculum[column] = pd.to_numeric(
                    curriculum[column],
                    errors="coerce"
                ).fillna(0)

        # -----------------------------------------
        # FILTER ACTIVE SEMESTERS
        # -----------------------------------------
        active_rows = []

        for _, course in curriculum.iterrows():

            programme = course["Programme_Type"]

            semester = int(course["Semester"])

            if programme == "B.Tech":

                if semester in btech_active_semesters:
                    active_rows.append(course)

            elif programme == "M.Tech":

                if semester in mtech_active_semesters:
                    active_rows.append(course)

        active_curriculum = pd.DataFrame(
            active_rows
        )

        st.write(
            "Selected semester configuration:",
            semester_type
        )

        st.write(
            "B.Tech semesters:",
            btech_active_semesters
            if academic_config["B.Tech"]["included"]
            else "Not included"
        )

        st.write(
            "M.Tech semesters:",
            mtech_active_semesters
            if academic_config["M.Tech"]["included"]
            else "Not included"
        )

        # -----------------------------------------
        # REQUIREMENT CALCULATION
        # -----------------------------------------
        scheduling_requirements = []

        excluded_courses = []

        for _, course in active_curriculum.iterrows():

            course_id = str(
                course["Course_ID"]
            ).strip()

            course_name = str(
                course["Course_Name"]
            ).strip()

            programme = course["Programme_Type"]

            semester = int(
                course["Semester"]
            )

            category = str(
                course.get("Category", "")
            )

            L = int(course["L_Hours"])
            T = int(course["T_Hours"])
            P = int(course["P_Hours"])
            credits = int(course["Credits"])

            course_type = str(
                course.get(
                    "Course_Type (Theory, Tutorial, Practical/Lab, or Elective)",
                    ""
                )
            ).strip()

            combined_text = (
                course_name + " " + course_type
            ).lower()

            # -------------------------------------
            # EXCLUDE NON-REGULAR SCHEDULING ITEMS
            # -------------------------------------
            excluded_keywords = [
                "internship",
                "industrial training",
                "academic attachment",
                "project work",
                "online courses",
                "nptel",
                "comprehensive viva",
                "viva voce"
            ]

            is_excluded = any(
                keyword in combined_text
                for keyword in excluded_keywords
            )

            if is_excluded:

                excluded_courses.append({
                    "Programme": programme,
                    "Semester": semester,
                    "Course_ID": course_id,
                    "Course_Name": course_name,
                    "Reason": "Non-regular classroom scheduling"
                })

                continue

            # -------------------------------------
            # CALCULATE WEEKLY THEORY AND LAB
            # -------------------------------------
            theory_sessions = 0
            lab_sessions = 0
            lab_periods = 0

            # Theory + practical
            if L > 0 and P > 0:

                theory_sessions = 3

                lab_sessions = 1

                lab_periods = 2

                course_classification = (
                    "Theory + Lab"
                )

            # Practical / lab only
            elif L == 0 and P > 0:

                theory_sessions = 0

                lab_sessions = 1

                lab_periods = 2

                course_classification = (
                    "Lab Only"
                )

            # Theory only
            elif L > 0 and P == 0:

                if credits == 3:

                    theory_sessions = 3

                elif credits == 4:

                    theory_sessions = 4

                else:

                    theory_sessions = L + T

                lab_sessions = 0

                lab_periods = 0

                course_classification = (
                    "Theory Only"
                )

            else:

                excluded_courses.append({
                    "Programme": programme,
                    "Semester": semester,
                    "Course_ID": course_id,
                    "Course_Name": course_name,
                    "Reason": "No weekly teaching hours"
                })

                continue

            # -------------------------------------
            # TOTAL WEEKLY PERIODS
            # -------------------------------------
            total_weekly_periods = (
                theory_sessions
                + lab_periods
            )

            scheduling_requirements.append({

                "Programme": programme,

                "Semester": semester,

                "Course_ID": course_id,

                "Course_Name": course_name,

                "Category": category,

                "Credits": credits,

                "L_Hours": L,

                "T_Hours": T,

                "P_Hours": P,

                "Classification": course_classification,

                "Theory_Sessions_Per_Week": theory_sessions,

                "Lab_Sessions_Per_Week": lab_sessions,

                "Lab_Consecutive_Periods": lab_periods,

                "Total_Weekly_Periods": total_weekly_periods

            })

        # -----------------------------------------
        # DISPLAY REQUIREMENTS
        # -----------------------------------------
        requirements_df = pd.DataFrame(
            scheduling_requirements
        )

        st.divider()

        st.subheader(
            "Calculated Weekly Course Requirements"
        )

        if not requirements_df.empty:

            st.dataframe(
                requirements_df,
                use_container_width=True
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Courses",
                len(requirements_df)
            )

            col2.metric(
                "Theory Sessions",
                int(
                    requirements_df[
                        "Theory_Sessions_Per_Week"
                    ].sum()
                )
            )

            col3.metric(
                "Lab Sessions",
                int(
                    requirements_df[
                        "Lab_Sessions_Per_Week"
                    ].sum()
                )
            )

            col4.metric(
                "Total Weekly Periods",
                int(
                    requirements_df[
                        "Total_Weekly_Periods"
                    ].sum()
                )
            )
        # -------------------------------------------------
        # SAVE AND CONFIRM WEEKLY COURSE REQUIREMENTS
        # -------------------------------------------------
        if not requirements_df.empty:
            previous_requirements = st.session_state.get("course_requirements")
            requirements_changed = (
                previous_requirements is None
                or not isinstance(previous_requirements, pd.DataFrame)
                or not previous_requirements.equals(requirements_df)
            )
            if requirements_changed:
                st.session_state.course_requirements = requirements_df.copy()
                st.session_state.course_requirements_confirmed = False

            if st.button(
                "Confirm Weekly Course Requirements",
                type="primary",
                use_container_width=True
            ):
                st.session_state.course_requirements = requirements_df.copy()
                st.session_state.course_requirements_confirmed = True
                st.session_state.config["course_requirements"] = (
                    requirements_df.to_dict(orient="records")
                )
                st.success("Weekly course requirements confirmed!")
        else:
            st.session_state.course_requirements = pd.DataFrame()
            st.session_state.course_requirements_confirmed = False
            st.error("No course requirements were generated; confirmation is unavailable.")

        # =================================================
        # CELL 18: LABORATORY REQUIREMENTS AND LAB ELIGIBILITY
        # =================================================

        st.divider()
        st.subheader("Laboratory Requirements & Lab Eligibility")

        # -------------------------------------------------
        # 1. VALIDATE PREVIOUS CONFIGURATIONS
        # -------------------------------------------------

        if not st.session_state.get(
            "room_lab_confirmed", False
        ):

            st.error(
                "Please confirm Classroom & Laboratory "
                "Configuration first."
            )

        elif not (
            st.session_state.get("classroom_allocation_confirmed", False)
            or st.session_state.config.get(
                "classroom_allocation_confirmed", False
            )
        ):
        
            st.error(
                "Please confirm Fixed Classroom Allocation first."
            )
        elif not st.session_state.get(
            "course_requirements_confirmed", False
        ):

            st.error(
                "Please confirm Weekly Course Requirements first."
            )

        else:

            requirements_df = (
                st.session_state.course_requirements.copy()
            )

            section_df = (
                st.session_state.section_list.copy()
            )

            rooms_df = (
                st.session_state.room_lab_config.copy()
            )

            # -------------------------------------------------
            # 2. IDENTIFY LABORATORIES
            # -------------------------------------------------

            laboratory_inventory = rooms_df[
                rooms_df["Type"]
                .astype(str)
                .str.strip()
                .str.lower()
                .str.contains("lab", na=False)
            ].copy()

            available_labs = (
                laboratory_inventory["Room/Lab ID"]
                .astype(str)
                .tolist()
            )

            # -------------------------------------------------
            # 3. IDENTIFY LAB COURSES
            # -------------------------------------------------

            lab_courses = requirements_df[
                requirements_df[
                    "Lab_Sessions_Per_Week"
                ] > 0
            ].copy()

            # -------------------------------------------------
            # 4. GENERATE LAB REQUIREMENTS PER SECTION
            # -------------------------------------------------

            lab_requirement_records = []

            for _, section in section_df.iterrows():

                section_courses = lab_courses[
                    (
                        lab_courses["Programme"]
                        == section["Programme"]
                    )
                    &
                    (
                        lab_courses["Semester"].astype(str)
                        == str(section["Semester"])
                    )
                ]

                for _, course in section_courses.iterrows():

                    requirement_id = (
                        f"LAB_{len(lab_requirement_records)+1:03d}"
                    )

                    lab_requirement_records.append({

                        "Requirement_ID": requirement_id,

                        "Section_ID": section["Section_ID"],

                        "Programme": section["Programme"],

                        "Semester": section["Semester"],

                        "Section": section["Section"],

                        "Course_Code": course["Course_ID"],

                        "Course_Title": course["Course_Name"],

                        "Matching_Subject": course["Course_Name"],

                        "Practical_Hours": course["P_Hours"],

                        "Lab_Sessions_Per_Week": 1,

                        "Periods_Required": 2,

                        "Consecutive": True

                    })

            LAB_REQUIREMENTS = pd.DataFrame(
                lab_requirement_records
            )

            st.session_state.lab_requirements = (
                LAB_REQUIREMENTS.copy()
            )

            # -------------------------------------------------
            # 5. HANDLE NO LAB COURSES
            # -------------------------------------------------

            if LAB_REQUIREMENTS.empty:

                st.info(
                    "No laboratory courses were identified "
                    "for the selected curriculum."
                )

                if st.button(
                    "Confirm Laboratory Configuration",
                    type="primary"
                ):

                    empty_mapping = pd.DataFrame()

                    st.session_state.lab_eligibility_mapping = (
                        empty_mapping
                    )

                    st.session_state.lab_configuration_confirmed = True

                    st.session_state.config[
                        "lab_requirements"
                    ] = []

                    st.session_state.config[
                        "lab_eligibility_mapping"
                    ] = []

                    st.success(
                        "Laboratory configuration confirmed. "
                        "No laboratory allocation is required."
                    )

            # -------------------------------------------------
            # 6. VALIDATE LAB INVENTORY
            # -------------------------------------------------

            elif laboratory_inventory.empty:

                st.error(
                    "Laboratory courses exist, but no laboratories "
                    "are available in the uploaded inventory."
                )

            else:

                st.write(
                    f"Laboratory course-section requirements: "
                    f"{len(LAB_REQUIREMENTS)}"
                )

                st.write(
                    "Select suitable laboratories for each "
                    "course and section."
                )

                st.info(
                    "All available laboratories are selected "
                    "by default, matching the notebook logic."
                )

                # -------------------------------------------------
                # 7. LAB ELIGIBILITY SELECTION
                # -------------------------------------------------

                existing_mapping = st.session_state.get(
                    "lab_eligibility_mapping",
                    {}
                )

                current_lab_mapping = {}

                for _, requirement in LAB_REQUIREMENTS.iterrows():

                    requirement_id = (
                        requirement["Requirement_ID"]
                    )

                    section_id = requirement["Section_ID"]

                    course_code = requirement["Course_Code"]

                    course_title = requirement["Course_Title"]

                    requirement_label = (
                        f"{requirement['Programme']} | "
                        f"Semester {requirement['Semester']} | "
                        f"Section {requirement['Section']} | "
                        f"{course_code} — {course_title}"
                    )

                    st.markdown(
                        f"**{requirement_label}**"
                    )

                    st.caption(
                        "One weekly laboratory session — "
                        "2 consecutive periods."
                    )

                    previous_labs = existing_mapping.get(
                        requirement_id,
                        available_labs
                    )

                    previous_labs = [
                        lab
                        for lab in previous_labs
                        if lab in available_labs
                    ]

                    selected_labs = st.multiselect(
                        "Suitable laboratories",
                        options=available_labs,
                        default=previous_labs,
                        key=f"lab_eligibility_{requirement_id}"
                    )

                    current_lab_mapping[
                        requirement_id
                    ] = selected_labs

                # -------------------------------------------------
                # 8. CONFIRM LAB ELIGIBILITY
                # -------------------------------------------------

                if st.button(
                    "Confirm Laboratory Eligibility",
                    type="primary",
                    use_container_width=True
                ):

                    validation_errors = []

                    mapping_records = []

                    for _, requirement in (
                        LAB_REQUIREMENTS.iterrows()
                    ):

                        requirement_id = (
                            requirement["Requirement_ID"]
                        )

                        selected_labs = (
                            current_lab_mapping.get(
                                requirement_id,
                                []
                            )
                        )

                        if not selected_labs:

                            validation_errors.append(
                                f"No suitable laboratory selected for "
                                f"{requirement['Course_Title']} "
                                f"({requirement['Section']})."
                            )

                            continue

                        for lab in selected_labs:

                            mapping_records.append({

                                "Requirement_ID": requirement_id,

                                "Section_ID": requirement["Section_ID"],

                                "Programme": requirement["Programme"],

                                "Semester": requirement["Semester"],

                                "Section": requirement["Section"],

                                "Course_Code": requirement["Course_Code"],

                                "Course_Title": requirement["Course_Title"],

                                "Matching_Subject": requirement[
                                    "Matching_Subject"
                                ],

                                "Laboratory": lab,

                                "Periods_Required": 2,

                                "Consecutive": True

                            })

                    if validation_errors:

                        st.error(
                            "Laboratory eligibility is incomplete."
                        )

                        for error in validation_errors:
                            st.write("❌", error)

                        st.session_state.lab_configuration_confirmed = False

                    else:

                        LAB_ELIGIBILITY_MAPPING = pd.DataFrame(
                            mapping_records
                        )

                        st.session_state.lab_eligibility_mapping = (
                            LAB_ELIGIBILITY_MAPPING.copy()
                        )

                        st.session_state.lab_configuration_confirmed = True

                        st.session_state.config[
                            "lab_requirements"
                        ] = LAB_REQUIREMENTS.to_dict(
                            orient="records"
                        )

                        st.session_state.config[
                            "lab_eligibility_mapping"
                        ] = mapping_records

                        st.success(
                            "Laboratory eligibility confirmed successfully!"
                        )

                        st.metric(
                            "Lab Course–Section Requirements",
                            len(LAB_REQUIREMENTS)
                        )

                        st.metric(
                            "Suitable Lab Combinations",
                            len(LAB_ELIGIBILITY_MAPPING)
                        )

                        st.subheader(
                            "Confirmed Laboratory Eligibility"
                        )

                        st.dataframe(
                            LAB_ELIGIBILITY_MAPPING,
                            use_container_width=True,
                            hide_index=True
                        )

                        st.download_button(
                            "Download Laboratory Eligibility Mapping",
                            data=LAB_ELIGIBILITY_MAPPING.to_csv(
                                index=False
                            ).encode("utf-8"),
                            file_name="LAB_ELIGIBILITY_MAPPING.csv",
                            mime="text/csv"
                        )
        
        # =================================================
        # SECTION GENERATION & FIXED CLASSROOM ALLOCATION
        # =================================================

        st.divider()
        st.subheader("Section Generation & Fixed Classroom Allocation")

        if st.session_state.get(
            "course_requirements_confirmed",
            False
        ):

            requirements = st.session_state.course_requirements.copy()

            academic_config = st.session_state.config[
                "academic_programmes"
            ]

            # ---------------------------------------------
            # 1. GENERATE SECTION LIST
            # ---------------------------------------------

            section_records = []

            programme_semesters = (
                requirements[
                    ["Programme", "Semester"]
                ]
                .drop_duplicates()
                .reset_index(drop=True)
            )

            for _, row in programme_semesters.iterrows():

                programme = row["Programme"]
                semester = int(row["Semester"])

                programme_config = academic_config.get(
                    programme,
                    {}
                )

                section_count = int(
                    programme_config.get("sections", 0)
                )

                for section_number in range(section_count):

                    section_label = chr(65 + section_number)

                    section_id = (
                        f"{programme}_SEM_{semester}_"
                        f"SECTION_{section_label}"
                    )

                    section_records.append({

                        "Section_ID": section_id,

                        "Programme": programme,

                        "Semester": semester,

                        "Section": section_label

                    })

            section_df = pd.DataFrame(section_records)

            st.session_state.section_list = section_df.copy()

            st.subheader("Generated Sections")

            st.dataframe(
                section_df,
                use_container_width=True,
                hide_index=True
            )

            st.metric(
                "Total Sections",
                len(section_df)
            )

            # ---------------------------------------------
            # 2. GET AVAILABLE CLASSROOMS
            # ---------------------------------------------

            if st.session_state.get(
                "room_lab_confirmed",
                False
            ):

                rooms_df = st.session_state.room_lab_config.copy()

                classroom_df = rooms_df[
                    rooms_df["Type"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == "classroom"
                ].copy()

                classroom_options = (
                    classroom_df["Room/Lab ID"]
                    .astype(str)
                    .tolist()
                )

                st.write(
                    "Available classrooms:",
                    classroom_options
                )

                # -----------------------------------------
                # 3. CHECK CLASSROOM COUNT
                # -----------------------------------------

                if len(classroom_options) < len(section_df):

                    st.error(
                        f"Insufficient classrooms. "
                        f"Required: {len(section_df)}, "
                        f"Available: {len(classroom_options)}."
                    )

                else:

                    # -------------------------------------
                    # 4. CLASSROOM ASSIGNMENT
                    # -------------------------------------

                    st.write(
                        "Assign one fixed classroom to each section. "
                        "A classroom cannot be assigned to multiple sections."
                    )

                    existing_mapping = st.session_state.get(
                        "section_classroom_mapping",
                        {}
                    )

                    current_mapping = {}

                    for index, section in section_df.iterrows():

                        section_id = section["Section_ID"]

                        section_label = (
                            f"{section['Programme']} | "
                            f"Semester {section['Semester']} | "
                            f"Section {section['Section']}"
                        )

                        default_room = classroom_options[index]

                        previous_room = existing_mapping.get(
                            section_id,
                            default_room
                        )

                        if previous_room not in classroom_options:

                            previous_room = default_room

                        selected_room = st.selectbox(

                            section_label,

                            options=classroom_options,

                            index=classroom_options.index(
                                previous_room
                            ),

                            key=f"classroom_{section_id}"

                        )

                        current_mapping[section_id] = selected_room

                    # -------------------------------------
                    # 5. CONFIRM CLASSROOM ALLOCATION
                    # -------------------------------------

                    if st.button(
                        "Confirm Fixed Classroom Allocation",
                        type="primary",
                        use_container_width=True
                    ):

                        assigned_rooms = list(
                            current_mapping.values()
                        )

                        duplicate_rooms = (
                            len(assigned_rooms)
                            != len(set(assigned_rooms))
                        )

                        if duplicate_rooms:

                            st.error(
                                "A classroom is assigned to multiple "
                                "sections. Please correct the allocation."
                            )

                        else:

                            mapping_records = []

                            for _, section in section_df.iterrows():

                                section_id = section["Section_ID"]

                                mapping_records.append({

                                    "Section_ID": section_id,

                                    "Programme": section["Programme"],

                                    "Semester": section["Semester"],

                                    "Section": section["Section"],

                                    "Classroom": current_mapping[
                                        section_id
                                    ]

                                })

                            mapping_df = pd.DataFrame(
                                mapping_records
                            )

                            st.session_state.section_classroom_mapping = (
                                current_mapping.copy()
                            )

                            st.session_state.section_classroom_mapping_df = (
                                mapping_df.copy()
                            )

                            st.session_state.classroom_allocation_confirmed = True

                            # Store confirmation in configuration as well
                            st.session_state.config[
                                "classroom_allocation_confirmed"
                            ] = True

                            st.session_state.config[
                                "section_classroom_mapping"
                            ] = mapping_records

                            st.success(
                                "Fixed classroom allocation confirmed!"
                            )

                            st.dataframe(
                                mapping_df,
                                use_container_width=True,
                                hide_index=True
                            )

                            st.download_button(
                                "Download Section–Classroom Mapping",
                                data=mapping_df.to_csv(
                                    index=False
                                ).encode("utf-8"),
                                file_name="SECTION_CLASSROOM_MAPPING.csv",
                                mime="text/csv"
                            )

            else:

                st.warning(
                    "Confirm Classroom & Laboratory Configuration "
                    "on Page 7 first."
                )

        else:

            st.warning(
                "Confirm Weekly Course Requirements first."
            )
        # =================================================
        # CELL 15: FACULTY ELIGIBILITY & AVAILABILITY
        # =================================================

        st.divider()
        st.subheader("Faculty Eligibility & Availability Processing")

        # -------------------------------------------------
        # 1. VALIDATE INPUTS
        # -------------------------------------------------

        if not st.session_state.get(
            "faculty_constraints_confirmed", False
        ):

            st.error(
                "Confirm Faculty Constraints & HOD Approval first."
            )

        else:

            faculty_raw = (
                st.session_state.uploaded_data["faculty"]["data"]
                .copy()
            )

            approvals_df = pd.DataFrame(
                st.session_state.faculty_approvals
            )

            constraints_df = pd.DataFrame(
                st.session_state.faculty_constraints
            )

            # -------------------------------------------------
            # 2. SUBJECT NORMALIZATION — NOTEBOOK LOGIC
            # -------------------------------------------------

            def canonicalize_subject_name(value):

                if pd.isna(value):
                    return ""

                subject = str(value).strip()

                subject = re.sub(
                    r"\([^)]*\)",
                    "",
                    subject
                ).strip()

                if "/" in subject:

                    subject = subject.split("/")[-1].strip()

                subject = re.sub(
                    r"\s+",
                    " ",
                    subject
                ).strip()

                return subject


            def normalize_subject_name(value):

                subject = canonicalize_subject_name(value)

                subject = subject.lower()

                subject = re.sub(
                    r"[^a-z0-9 ]",
                    "",
                    subject
                )

                subject = re.sub(
                    r"\s+",
                    " ",
                    subject
                ).strip()

                return subject


            # -------------------------------------------------
            # 3. FIND FACULTY COLUMNS
            # -------------------------------------------------

            def find_column(df, possible_names):

                normalized_columns = {
                    str(col).strip().lower().replace("_", " "): col
                    for col in df.columns
                }

                for name in possible_names:

                    normalized_name = (
                        name.strip()
                        .lower()
                        .replace("_", " ")
                    )

                    if normalized_name in normalized_columns:

                        return normalized_columns[
                            normalized_name
                        ]

                return None


            faculty_id_col = find_column(
                faculty_raw,
                [
                    "Faculty ID",
                    "Faculty_ID",
                    "ID",
                    "Employee ID"
                ]
            )

            faculty_name_col = find_column(
                faculty_raw,
                [
                    "Faculty Name",
                    "Faculty_Name",
                    "Name",
                    "Faculty"
                ]
            )

            designation_col = find_column(
                faculty_raw,
                [
                    "Designation",
                    "Position",
                    "Academic Designation"
                ]
            )

            subject_col = find_column(
                faculty_raw,
                [
                    "Subject",
                    "Subjects",
                    "Subjects Interested",
                    "Willing Subjects"
                ]
            )


            required_columns = {
                "Faculty ID": faculty_id_col,
                "Faculty Name": faculty_name_col,
                "Designation": designation_col,
                "Subject": subject_col
            }

            missing_columns = [
                name
                for name, column in required_columns.items()
                if column is None
            ]

            if missing_columns:

                st.error(
                    "Faculty Excel is missing required columns: "
                    + ", ".join(missing_columns)
                )

            else:

                # -------------------------------------------------
                # 4. CREATE FACULTY MASTER
                # -------------------------------------------------

                faculty_master = faculty_raw[
                    [
                        faculty_id_col,
                        faculty_name_col,
                        designation_col
                    ]
                ].copy()

                faculty_master.columns = [
                    "Faculty_ID",
                    "Faculty_Name",
                    "Designation"
                ]

                faculty_master["Faculty_ID"] = (
                    faculty_master["Faculty_ID"]
                    .astype(str)
                    .str.strip()
                )

                faculty_master["Faculty_Name"] = (
                    faculty_master["Faculty_Name"]
                    .astype(str)
                    .str.strip()
                )

                faculty_master["Designation"] = (
                    faculty_master["Designation"]
                    .astype(str)
                    .str.strip()
                )

                faculty_master = faculty_master[
                    faculty_master["Faculty_Name"] != ""
                ].drop_duplicates(
                    subset=["Faculty_ID"]
                ).reset_index(drop=True)


                # -------------------------------------------------
                # 5. EXTRACT FIVE WILLING SUBJECTS PER FACULTY
                # -------------------------------------------------

                mapping_records = []

                faculty_subject_errors = []

                for _, faculty_row in faculty_raw.iterrows():

                    faculty_id = str(
                        faculty_row[faculty_id_col]
                    ).strip()

                    faculty_name = str(
                        faculty_row[faculty_name_col]
                    ).strip()

                    designation = str(
                        faculty_row[designation_col]
                    ).strip()

                    subject_text = str(
                        faculty_row[subject_col]
                    ).strip()

                    if faculty_name.lower() in [
                        "",
                        "nan",
                        "none"
                    ]:

                        continue

                    subject_matches = re.findall(
                        r"\d+\.\s*(.*?)(?=\d+\.\s*|$)",
                        subject_text,
                        flags=re.DOTALL
                    )

                    subjects = [
                        re.sub(
                            r"\s+",
                            " ",
                            subject
                        ).strip()
                        for subject in subject_matches
                        if subject.strip()
                    ]

                    if len(subjects) != 5:

                        faculty_subject_errors.append(
                            f"{faculty_name}: "
                            f"{len(subjects)} subjects extracted; "
                            f"exactly 5 are required."
                        )

                        continue

                    normalized_subjects = [
                        normalize_subject_name(subject)
                        for subject in subjects
                    ]

                    if len(set(normalized_subjects)) != 5:

                        faculty_subject_errors.append(
                            f"{faculty_name}: duplicate subjects found."
                        )

                        continue

                    for subject in subjects:

                        canonical_subject = (
                            canonicalize_subject_name(subject)
                        )

                        mapping_records.append({

                            "Faculty_ID": faculty_id,

                            "Faculty_Name": faculty_name,

                            "Designation": designation,

                            "Original_Subject": subject,

                            "Subject": canonical_subject,

                            "Normalized_Subject": (
                                normalize_subject_name(
                                    canonical_subject
                                )
                            )

                        })


                FACULTY_SUBJECT_MAPPING = pd.DataFrame(
                    mapping_records
                )


                # -------------------------------------------------
                # 6. APPROVAL LOOKUP
                # -------------------------------------------------

                approvals_lookup = {}

                for _, approval in approvals_df.iterrows():

                    faculty_id = str(
                        approval["Faculty_ID"]
                    ).strip()

                    approvals_lookup[faculty_id] = {

                        "BTech_Approved": bool(
                            approval["BTech_Approved"]
                        ),

                        "BTech_Years": approval.get(
                            "BTech_Years",
                            []
                        ),

                        "MTech_Approved": bool(
                            approval["MTech_Approved"]
                        ),

                        "MTech_Years": approval.get(
                            "MTech_Years",
                            []
                        ),

                        "Approved_By": approval.get(
                            "Approved_By",
                            ""
                        ),

                        "Remarks": approval.get(
                            "Remarks",
                            ""
                        )

                    }


                # -------------------------------------------------
                # 7. BUILD FINAL FACULTY ELIGIBILITY
                # -------------------------------------------------

                eligibility_records = []

                for _, mapping_row in (
                    FACULTY_SUBJECT_MAPPING.iterrows()
                ):

                    faculty_id = str(
                        mapping_row["Faculty_ID"]
                    ).strip()

                    approval = approvals_lookup.get(
                        faculty_id,
                        {}
                    )

                    faculty_match = faculty_master[
                        faculty_master["Faculty_ID"]
                        == faculty_id
                    ]

                    if faculty_match.empty:
                        continue

                    faculty_info = faculty_match.iloc[0]

                    eligibility_records.append({

                        "Faculty_ID": faculty_id,

                        "Faculty_Name": (
                            faculty_info["Faculty_Name"]
                        ),

                        "Designation": (
                            faculty_info["Designation"]
                        ),

                        "Subject": mapping_row["Subject"],

                        "Normalized_Subject": (
                            mapping_row["Normalized_Subject"]
                        ),

                        "BTech_Eligible": approval.get(
                            "BTech_Approved",
                            False
                        ),

                        "BTech_Years": approval.get(
                            "BTech_Years",
                            []
                        ),

                        "MTech_Eligible": approval.get(
                            "MTech_Approved",
                            False
                        ),

                        "MTech_Years": approval.get(
                            "MTech_Years",
                            []
                        ),

                        "Approved_By": approval.get(
                            "Approved_By",
                            ""
                        ),

                        "Approval_Remarks": approval.get(
                            "Remarks",
                            ""
                        )

                    })


                FACULTY_ELIGIBILITY = pd.DataFrame(
                    eligibility_records
                )


                # -------------------------------------------------
                # 8. SEMESTER TO YEAR CONVERSION
                # -------------------------------------------------

                def semester_to_year(semester):

                    roman_map = {
                        "I": 1,
                        "II": 2,
                        "III": 3,
                        "IV": 4,
                        "V": 5,
                        "VI": 6,
                        "VII": 7,
                        "VIII": 8
                    }

                    value = str(
                        semester
                    ).strip().upper()

                    if value in roman_map:

                        semester_number = roman_map[value]

                    else:

                        try:

                            semester_number = int(
                                float(value)
                            )

                        except (ValueError, TypeError):

                            return None

                    if semester_number < 1:
                        return None

                    year_number = (
                        semester_number + 1
                    ) // 2

                    return f"Year {year_number}"


                # -------------------------------------------------
                # 9. ELIGIBLE FACULTY FUNCTION
                # -------------------------------------------------

                def get_eligible_faculty_for_subject(
                    normalized_subject,
                    programme,
                    semester=None
                ):

                    programme_type = (
                        str(programme)
                        .lower()
                        .replace(" ", "")
                        .replace(".", "")
                    )

                    subject = normalize_subject_name(
                        normalized_subject
                    )

                    year = (
                        semester_to_year(semester)
                        if semester is not None
                        else None
                    )

                    matching = FACULTY_ELIGIBILITY[
                        FACULTY_ELIGIBILITY[
                            "Normalized_Subject"
                        ]
                        .astype(str)
                        .str.strip()
                        .str.casefold()
                        == subject
                    ]

                    eligible_ids = []

                    for _, faculty in matching.iterrows():

                        if "btech" in programme_type:

                            approved = faculty[
                                "BTech_Eligible"
                            ]

                            approved_years = faculty[
                                "BTech_Years"
                            ]

                        elif "mtech" in programme_type:

                            approved = faculty[
                                "MTech_Eligible"
                            ]

                            approved_years = faculty[
                                "MTech_Years"
                            ]

                        else:

                            continue

                        if not approved:
                            continue

                        if (
                            year is not None
                            and year not in approved_years
                        ):

                            continue

                        eligible_ids.append(
                            faculty["Faculty_ID"]
                        )

                    return eligible_ids


                # -------------------------------------------------
                # 10. BUILD VALID PERIODS
                # -------------------------------------------------

                calendar = st.session_state.config.get(
                    "calendar",
                    {}
                )

                working_days = calendar.get(
                    "working_days",
                    [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday"
                    ]
                )

                college_start = calendar.get(
                    "college_start",
                    "08:30"
                )

                college_end = calendar.get(
                    "college_end",
                    "17:00"
                )

                period_duration = int(
                    calendar.get(
                        "period_duration",
                        50
                    )
                )

                morning_break = calendar.get(
                    "morning_break",
                    {"start": "10:10", "end": "10:30"}
                )

                lunch = calendar.get(
                    "lunch",
                    {"start": "12:10", "end": "13:30"}
                )

                afternoon_break = calendar.get(
                    "afternoon_break",
                    {"start": "14:20", "end": "14:30"}
                )


                def time_to_minutes(value):

                    hour, minute = map(
                        int,
                        str(value).split(":")[:2]
                    )

                    return hour * 60 + minute


                def minutes_to_time(value):

                    return (
                        f"{value // 60:02d}:"
                        f"{value % 60:02d}"
                    )


                breaks = [
                    (
                        time_to_minutes(
                            morning_break["start"]
                        ),
                        time_to_minutes(
                            morning_break["end"]
                        )
                    ),

                    (
                        time_to_minutes(
                            lunch["start"]
                        ),
                        time_to_minutes(
                            lunch["end"]
                        )
                    ),

                    (
                        time_to_minutes(
                            afternoon_break["start"]
                        ),
                        time_to_minutes(
                            afternoon_break["end"]
                        )
                    )
                ]


                VALID_PERIODS = []

                start_minutes = time_to_minutes(
                    college_start
                )

                end_minutes = time_to_minutes(
                    college_end
                )

                for day in working_days:

                    current = start_minutes

                    period_number = 1

                    while (
                        current + period_duration
                        <= end_minutes
                    ):

                        period_end = (
                            current + period_duration
                        )

                        overlapping_break = None

                        for break_start, break_end in breaks:

                            if (
                                current < break_end
                                and period_end > break_start
                            ):

                                overlapping_break = break_end

                                break

                        if overlapping_break is not None:

                            current = overlapping_break

                            continue

                        VALID_PERIODS.append({

                            "Day": day,

                            "Period": period_number,

                            "Start_Time": minutes_to_time(
                                current
                            ),

                            "End_Time": minutes_to_time(
                                period_end
                            )

                        })

                        current += period_duration

                        period_number += 1


                # -------------------------------------------------
                # 11. BUILD FACULTY AVAILABILITY
                # -------------------------------------------------

                constraints_lookup = {}

                for _, constraint in (
                    constraints_df.iterrows()
                ):

                    faculty_id = str(
                        constraint["Faculty_ID"]
                    ).strip()

                    constraints_lookup[faculty_id] = {

                        "Unavailable_Days": (
                            constraint.get(
                                "Unavailable_Days",
                                []
                            )
                        ),

                        "Unavailable_Slots": (
                            constraint.get(
                                "Unavailable_Slots",
                                []
                            )
                        )

                    }


                availability_records = []

                for _, faculty in faculty_master.iterrows():

                    faculty_id = str(
                        faculty["Faculty_ID"]
                    ).strip()

                    constraint = constraints_lookup.get(
                        faculty_id,
                        {
                            "Unavailable_Days": [],
                            "Unavailable_Slots": []
                        }
                    )

                    unavailable_days = set(
                        str(day)
                        for day in constraint[
                            "Unavailable_Days"
                        ]
                    )

                    unavailable_slots = set(
                        str(slot)
                        for slot in constraint[
                            "Unavailable_Slots"
                        ]
                    )

                    for period in VALID_PERIODS:

                        day = period["Day"]

                        start_time = period["Start_Time"]

                        end_time = period["End_Time"]

                        slot_key = (
                            f"{day}|{start_time}|{end_time}"
                        )

                        is_available = (
                            day not in unavailable_days
                            and slot_key not in unavailable_slots
                        )

                        availability_records.append({

                            "Faculty_ID": faculty_id,

                            "Faculty_Name": (
                                faculty["Faculty_Name"]
                            ),

                            "Day": day,

                            "Period": period["Period"],

                            "Start_Time": start_time,

                            "End_Time": end_time,

                            "Available": is_available

                        })


                FACULTY_AVAILABILITY = pd.DataFrame(
                    availability_records
                )


                # -------------------------------------------------
                # 12. SAVE TO SESSION STATE
                # -------------------------------------------------

                st.session_state.faculty_master = (
                    faculty_master.copy()
                )

                st.session_state.faculty_subject_mapping = (
                    FACULTY_SUBJECT_MAPPING.copy()
                )

                st.session_state.faculty_eligibility = (
                    FACULTY_ELIGIBILITY.copy()
                )

                st.session_state.faculty_availability = (
                    FACULTY_AVAILABILITY.copy()
                )

                st.session_state.valid_periods = (
                    VALID_PERIODS.copy()
                )

                st.session_state.faculty_configuration_confirmed = True


                # -------------------------------------------------
                # 13. DISPLAY SUMMARY
                # -------------------------------------------------

                st.success(
                    "Faculty eligibility and availability "
                    "processing completed."
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Faculty",
                    len(faculty_master)
                )

                col2.metric(
                    "Faculty–Subject Combinations",
                    len(FACULTY_SUBJECT_MAPPING)
                )

                col3.metric(
                    "Availability Records",
                    len(FACULTY_AVAILABILITY)
                )

                st.subheader(
                    "Faculty Subject Eligibility"
                )

                st.dataframe(
                    FACULTY_ELIGIBILITY,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader(
                    "Faculty Availability"
                )

                st.dataframe(
                    FACULTY_AVAILABILITY.head(20),
                    use_container_width=True,
                    hide_index=True
                )

                if faculty_subject_errors:

                    st.warning(
                        "Faculty subject validation warnings:"
                    )

                    for error in faculty_subject_errors:

                        st.write("⚠️", error)
         # =================================================
        # CELL 19: TEACHING SESSION GENERATION
        # =================================================

        st.divider()
        st.subheader(
            "Teaching Session Generation & Scheduling Dataset"
        )

        required_confirmations = {
            "Faculty Configuration": (
                st.session_state.get(
                    "faculty_configuration_confirmed", False
                )
            ),
            "Classroom Allocation": (
                st.session_state.get(
                    "classroom_allocation_confirmed", False
                )
            ),
            "Laboratory Configuration": (
                st.session_state.get(
                    "lab_configuration_confirmed", False
                )
            )
        }

        missing_confirmations = [
            name
            for name, status in required_confirmations.items()
            if not status
        ]

        if missing_confirmations:

            st.error(
                "Complete these configurations first: "
                + ", ".join(missing_confirmations)
            )

        elif (
            "active_curriculum" not in locals()
            or active_curriculum.empty
        ):

            st.error(
                "Selected semester curriculum is missing."
            )

        elif (
            "section_list" not in st.session_state
            or st.session_state.section_list.empty
        ):

            st.error(
                "SECTION_LIST is missing."
            )

        elif (
            "faculty_eligibility"
            not in st.session_state
        ):

            st.error(
                "Faculty eligibility data is missing."
            )

        else:

            # ---------------------------------------------
            # 1. PREPARE CURRICULUM
            # ---------------------------------------------

            CURRICULUM_FOR_SCHEDULING = (
                active_curriculum.copy()
            )

            SECTION_LIST = (
                st.session_state.section_list.copy()
            )

            FACULTY_ELIGIBILITY = (
                st.session_state.faculty_eligibility.copy()
            )

            SECTION_CLASSROOM_MAPPING = (
                st.session_state.section_classroom_mapping_df.copy()
            )

            LAB_ELIGIBILITY_MAPPING = (
                st.session_state.lab_eligibility_mapping.copy()
            )

            # ---------------------------------------------
            # 2. FIND CURRICULUM COLUMNS
            # ---------------------------------------------

            def find_column(df, possible_names):

                for name in possible_names:

                    if name in df.columns:
                        return name

                return None


            programme_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Programme",
                    "Program",
                    "Programme Name",
                    "Programme_Type"
                ]
            )

            semester_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Semester",
                    "Semester Number"
                ]
            )

            course_code_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Course_Code",
                    "Course Code",
                    "Course_ID",
                    "Course ID"
                ]
            )

            course_title_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Course_Title",
                    "Course Title",
                    "Course_Name",
                    "Course Name",
                    "Original Course Title"
                ]
            )

            subject_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Normalized Subject",
                    "Normalized_Subject"
                ]
            )

            matching_subject_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "Matching Subject",
                    "Matching_Subject"
                ]
            )

            l_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "L",
                    "Lecture",
                    "L_Hours"
                ]
            )

            t_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "T",
                    "Tutorial",
                    "T_Hours"
                ]
            )

            p_col = find_column(
                CURRICULUM_FOR_SCHEDULING,
                [
                    "P",
                    "Practical",
                    "P_Hours"
                ]
            )

            required_columns = {
                "Programme": programme_col,
                "Semester": semester_col,
                "Course Title": course_title_col,
                "L": l_col,
                "T": t_col,
                "P": p_col
            }

            missing_columns = [
                name
                for name, column in required_columns.items()
                if column is None
            ]

            if missing_columns:

                st.error(
                    "Curriculum is missing required fields: "
                    + ", ".join(missing_columns)
                )

                st.write(
                    "Available columns:",
                    list(CURRICULUM_FOR_SCHEDULING.columns)
                )

            else:

                # ---------------------------------------------
                # 3. HELPER FUNCTIONS
                # ---------------------------------------------

                def safe_number(value):

                    try:

                        if pd.isna(value):
                            return 0

                        return max(
                            0,
                            int(float(value))
                        )

                    except (ValueError, TypeError):

                        return 0


                def safe_text(value):

                    if pd.isna(value):
                        return ""

                    return str(value).strip()


                def get_course_subject(row):

                    if subject_col is not None:

                        value = safe_text(
                            row[subject_col]
                        )

                        if value:
                            return value

                    if matching_subject_col is not None:

                        value = safe_text(
                            row[matching_subject_col]
                        )

                        if value:
                            return value

                    return safe_text(
                        row[course_title_col]
                    )


                def get_course_code(row):

                    if course_code_col is None:

                        return "NOT_SPECIFIED"

                    value = safe_text(
                        row[course_code_col]
                    )

                    return (
                        value
                        if value
                        else "NOT_SPECIFIED"
                    )


                def get_course_labs(
                    section_id,
                    course_code,
                    course_title
                ):

                    if LAB_ELIGIBILITY_MAPPING.empty:
                        return []

                    matching = (
                        LAB_ELIGIBILITY_MAPPING[
                            (
                                LAB_ELIGIBILITY_MAPPING[
                                    "Section_ID"
                                ].astype(str)
                                == str(section_id)
                            )
                            &
                            (
                                LAB_ELIGIBILITY_MAPPING[
                                    "Course_Code"
                                ].astype(str)
                                == str(course_code)
                            )
                        ]
                    )

                    # Notebook fallback:
                    # match using course title
                    if matching.empty:

                        matching = (
                            LAB_ELIGIBILITY_MAPPING[
                                (
                                    LAB_ELIGIBILITY_MAPPING[
                                        "Section_ID"
                                    ].astype(str)
                                    == str(section_id)
                                )
                                &
                                (
                                    LAB_ELIGIBILITY_MAPPING[
                                        "Course_Title"
                                    ].astype(str)
                                    == str(course_title)
                                )
                            ]
                        )

                    if matching.empty:
                        return []

                    return sorted(
                        matching[
                            "Laboratory"
                        ]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )


                # ---------------------------------------------
                # 4. GENERATE INDIVIDUAL SESSIONS
                # ---------------------------------------------
                # ---------------------------------------------
                # NORMALIZE PROGRAMME NAMES FOR MATCHING
                # ---------------------------------------------
                
                def normalize_programme_name(value):
                
                    value = str(value).strip().lower()
                
                    if "b.tech" in value or "btech" in value:
                        return "btech"
                
                    if "m.tech" in value or "mtech" in value:
                        return "mtech"
                
                    return value
                
                
                def normalize_semester(value):
                
                    try:
                        return int(float(str(value).strip()))
                    except (ValueError, TypeError):
                        return str(value).strip().upper()
                
                
                session_records = []
                
                session_counter = 1
                
                for _, section in SECTION_LIST.iterrows():

                    section_id = str(
                        section["Section_ID"]
                    )

                    programme = section["Programme"]

                    semester = section["Semester"]

                    section_name = section["Section"]

                    section_programme_normalized = normalize_programme_name(
                        section["Programme"]
                    )
                    
                    section_semester_normalized = normalize_semester(
                        section["Semester"]
                    )
                    
                    curriculum_programme_normalized = (
                        CURRICULUM_FOR_SCHEDULING[programme_col]
                        .apply(normalize_programme_name)
                    )
                    
                    curriculum_semester_normalized = (
                        CURRICULUM_FOR_SCHEDULING[semester_col]
                        .apply(normalize_semester
                        )
                    )
                    
                    section_courses = CURRICULUM_FOR_SCHEDULING[
                        (
                            curriculum_programme_normalized
                            == section_programme_normalized
                        )
                        &
                        (
                            curriculum_semester_normalized
                            == section_semester_normalized
                        )
                    ].copy()
                    
                    # ---------------------------------------------
                    # NOTEBOOK COURSE EXCLUSION RULES
                    # ---------------------------------------------
                    
                    EXCLUSION_KEYWORDS = [
                        "summer internship",
                        "internship",
                        "industrial training",
                        "academic attachment",
                        "project work",
                        "comprehensive viva",
                        "industrial lecture",
                        "online course",
                        "online courses",
                        "nptel"
                    ]
                    
                    def is_excluded_course(course_title):
                    
                        title = str(course_title).strip().lower()
                    
                        return any(
                            keyword in title
                            for keyword in EXCLUSION_KEYWORDS
                        )
                    
                    section_courses = section_courses[
                        ~section_courses[course_title_col]
                        .apply(is_excluded_course)
                    ].copy()

                    # -----------------------------------------
                    # FIXED CLASSROOM FOR SECTION
                    # -----------------------------------------

                    room_match = (
                        SECTION_CLASSROOM_MAPPING[
                            SECTION_CLASSROOM_MAPPING[
                                "Section_ID"
                            ].astype(str)
                            == section_id
                        ]
                    )

                    fixed_classroom = (
                        room_match.iloc[0]["Classroom"]
                        if not room_match.empty
                        else None
                    )

                    # -----------------------------------------
                    # PROCESS EACH COURSE
                    # -----------------------------------------

                    for _, course in section_courses.iterrows():

                        course_code = get_course_code(
                            course
                        )

                        course_title = safe_text(
                            course[course_title_col]
                        )

                        normalized_subject = (
                            get_course_subject(course)
                        )

                        lecture_count = safe_number(
                            course[l_col]
                        )

                        tutorial_count = safe_number(
                            course[t_col]
                        )

                        practical_count = safe_number(
                            course[p_col]
                        )

                        # Notebook faculty eligibility function
                        eligible_faculty = (
                            get_eligible_faculty_for_subject(
                                normalized_subject,
                                programme,
                                semester
                            )
                        )

                        # -------------------------------------
                        # THEORY: L + T
                        # -------------------------------------

                        theory_count = (
                            lecture_count
                            + tutorial_count
                        )

                        for number in range(
                            1,
                            theory_count + 1
                        ):

                            session_records.append({

                                "Session_ID": (
                                    f"SESSION_{session_counter:04d}"
                                ),

                                "Section_ID": section_id,

                                "Programme": programme,

                                "Semester": semester,

                                "Section": section_name,

                                "Course_Code": course_code,

                                "Course_Title": course_title,

                                "Normalized_Subject": (
                                    normalized_subject
                                ),

                                "Session_Type": "Theory",

                                "Session_Number": number,

                                "Periods_Required": 1,

                                "Consecutive": False,

                                "Eligible_Faculty": (
                                    eligible_faculty
                                ),

                                "Candidate_Faculty_Count": (
                                    len(eligible_faculty)
                                ),

                                "Fixed_Classroom": (
                                    fixed_classroom
                                ),

                                "Candidate_Labs": [],

                                "Coverage_Status": (
                                    "Covered"
                                    if eligible_faculty
                                    else "No Eligible Faculty"
                                )

                            })

                            session_counter += 1

                        # -------------------------------------
                        # LAB: ONE 2-PERIOD BLOCK IF P > 0
                        # -------------------------------------

                        if practical_count > 0:

                            candidate_labs = (
                                get_course_labs(
                                    section_id,
                                    course_code,
                                    course_title
                                )
                            )

                            session_records.append({

                                "Session_ID": (
                                    f"SESSION_{session_counter:04d}"
                                ),

                                "Section_ID": section_id,

                                "Programme": programme,

                                "Semester": semester,

                                "Section": section_name,

                                "Course_Code": course_code,

                                "Course_Title": course_title,

                                "Normalized_Subject": (
                                    normalized_subject
                                ),

                                "Session_Type": "Laboratory",

                                "Session_Number": 1,

                                "Periods_Required": 2,

                                "Consecutive": True,

                                "Eligible_Faculty": (
                                    eligible_faculty
                                ),

                                "Candidate_Faculty_Count": (
                                    len(eligible_faculty)
                                ),

                                "Fixed_Classroom": None,

                                "Candidate_Labs": (
                                    candidate_labs
                                ),

                                "Coverage_Status": (
                                    "Covered"
                                    if eligible_faculty
                                    else "No Eligible Faculty"
                                )

                            })

                            session_counter += 1


                # ---------------------------------------------
                # 5. CREATE SCHEDULING DATASET
                # ---------------------------------------------

                SCHEDULING_SESSIONS = pd.DataFrame(
                    session_records
                )

                if SCHEDULING_SESSIONS.empty:
                
                    st.error("No scheduling sessions were generated.")
                
                    st.subheader("Debug Information")
                
                    st.write("Curriculum shape:",
                             CURRICULUM_FOR_SCHEDULING.shape)
                
                    st.write("Curriculum columns:",
                             list(CURRICULUM_FOR_SCHEDULING.columns))
                
                    st.write("Sections shape:",
                             SECTION_LIST.shape)
                
                    st.write("Sections:")
                    st.dataframe(SECTION_LIST)
                
                    st.write("Programme values in curriculum:")
                    st.write(
                        CURRICULUM_FOR_SCHEDULING[programme_col]
                        .unique().tolist()
                    )
                
                    st.write("Semester values in curriculum:")
                    st.write(
                        CURRICULUM_FOR_SCHEDULING[semester_col]
                        .unique().tolist()
                    )
                
                    st.write("Programme values in sections:")
                    st.write(
                        SECTION_LIST["Programme"]
                        .unique().tolist()
                    )
                
                    st.write("Semester values in sections:")
                    st.write(
                        SECTION_LIST["Semester"]
                        .unique().tolist()
                    )
                
                    st.stop()

                else:

                    # -----------------------------------------
                    # 6. IDENTIFY UNRESOLVED REQUIREMENTS
                    # -----------------------------------------

                    NO_FACULTY_SESSIONS = (
                        SCHEDULING_SESSIONS[
                            SCHEDULING_SESSIONS[
                                "Candidate_Faculty_Count"
                            ] == 0
                        ].copy()
                    )

                    NO_LAB_SESSIONS = (
                        SCHEDULING_SESSIONS[
                            (
                                SCHEDULING_SESSIONS[
                                    "Session_Type"
                                ] == "Laboratory"
                            )
                            &
                            (
                                SCHEDULING_SESSIONS[
                                    "Candidate_Labs"
                                ].apply(len) == 0
                            )
                        ].copy()
                    )

                    NO_CLASSROOM_SESSIONS = (
                        SCHEDULING_SESSIONS[
                            (
                                SCHEDULING_SESSIONS[
                                    "Session_Type"
                                ] == "Theory"
                            )
                            &
                            (
                                SCHEDULING_SESSIONS[
                                    "Fixed_Classroom"
                                ].isna()
                            )
                        ].copy()
                    )

                    # -----------------------------------------
                    # 7. SUMMARY
                    # -----------------------------------------

                    theory_total = (
                        SCHEDULING_SESSIONS[
                            "Session_Type"
                        ] == "Theory"
                    ).sum()

                    lab_total = (
                        SCHEDULING_SESSIONS[
                            "Session_Type"
                        ] == "Laboratory"
                    ).sum()

                    st.success(
                        "Scheduling dataset generated."
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Sections",
                        len(SECTION_LIST)
                    )

                    col2.metric(
                        "Courses",
                        len(CURRICULUM_FOR_SCHEDULING)
                    )

                    col3.metric(
                        "Total Sessions",
                        len(SCHEDULING_SESSIONS)
                    )

                    col4.metric(
                        "Theory / Lab",
                        f"{int(theory_total)} / {int(lab_total)}"
                    )

                    st.subheader(
                        "Generated Scheduling Sessions"
                    )

                    st.dataframe(
                        SCHEDULING_SESSIONS,
                        use_container_width=True,
                        hide_index=True
                    )

                    # -----------------------------------------
                    # 8. UNRESOLVED REQUIREMENTS
                    # -----------------------------------------

                    st.subheader(
                        "Unresolved Requirements"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "No Eligible Faculty",
                        len(NO_FACULTY_SESSIONS)
                    )

                    col2.metric(
                        "No Candidate Laboratory",
                        len(NO_LAB_SESSIONS)
                    )

                    col3.metric(
                        "No Fixed Classroom",
                        len(NO_CLASSROOM_SESSIONS)
                    )

                    if not NO_FACULTY_SESSIONS.empty:

                        st.warning(
                            "Sessions without eligible faculty"
                        )

                        st.dataframe(
                            NO_FACULTY_SESSIONS,
                            use_container_width=True
                        )

                    if not NO_LAB_SESSIONS.empty:

                        st.warning(
                            "Lab sessions without candidate labs"
                        )

                        st.dataframe(
                            NO_LAB_SESSIONS,
                            use_container_width=True
                        )

                    if not NO_CLASSROOM_SESSIONS.empty:

                        st.warning(
                            "Theory sessions without fixed classrooms"
                        )

                        st.dataframe(
                            NO_CLASSROOM_SESSIONS,
                            use_container_width=True
                        )

                    # -----------------------------------------
                    # 9. SAVE DATASET
                    # -----------------------------------------

                    st.session_state.scheduling_sessions = (
                        SCHEDULING_SESSIONS.copy()
                    )

                    st.session_state.no_faculty_sessions = (
                        NO_FACULTY_SESSIONS.copy()
                    )

                    st.session_state.no_lab_sessions = (
                        NO_LAB_SESSIONS.copy()
                    )

                    st.session_state.no_classroom_sessions = (
                        NO_CLASSROOM_SESSIONS.copy()
                    )

                    st.session_state.setdefault("scheduling_dataset_confirmed",
                        False
                    )

                    st.session_state.config[
                        "scheduling_sessions"
                    ] = SCHEDULING_SESSIONS.to_dict(
                        orient="records"
                    )

                    st.session_state.config[
                        "scheduling_dataset_summary"
                    ] = {

                        "total_sessions": (
                            len(SCHEDULING_SESSIONS)
                        ),

                        "theory_sessions": int(
                            theory_total
                        ),

                        "lab_sessions": int(
                            lab_total
                        ),

                        "total_sections": (
                            len(SECTION_LIST)
                        )

                    }

                    # -----------------------------------------
                    # 10. REVIEW & CONFIRM
                    # -----------------------------------------

                    st.divider()

                    if st.button(
                        "Confirm Domains & Continue to Conflict Graph",
                        type="primary",
                        use_container_width=True
                    ):

                        errors = []

                        if not NO_FACULTY_SESSIONS.empty:

                            errors.append(
                                f"{len(NO_FACULTY_SESSIONS)} "
                                "sessions have no eligible faculty."
                            )

                        if not NO_LAB_SESSIONS.empty:

                            errors.append(
                                f"{len(NO_LAB_SESSIONS)} "
                                "lab sessions have no candidate laboratory."
                            )

                        if not NO_CLASSROOM_SESSIONS.empty:

                            errors.append(
                                f"{len(NO_CLASSROOM_SESSIONS)} "
                                "theory sessions have no fixed classroom."
                            )

                        if errors:

                            st.session_state.scheduling_dataset_confirmed = False

                            st.error(
                                "Dataset cannot be confirmed yet."
                            )

                            for error in errors:

                                st.write("❌", error)

                        else:

                            st.session_state.scheduling_dataset_confirmed = True

                            st.session_state.config[
                                "scheduling_dataset_confirmed"
                            ] = True

                            st.success(
                                "Scheduling dataset confirmed successfully!"
                            )

                    # -----------------------------------------
                    # 11. DOWNLOAD
                    # -----------------------------------------

                    st.download_button(
                        "Download Scheduling Dataset CSV",
                        data=SCHEDULING_SESSIONS.to_csv(
                            index=False
                        ).encode("utf-8"),
                        file_name="SCHEDULING_SESSIONS.csv",
                        mime="text/csv"
                    )
        
        # =========================================================
        # CELL 20: SCHEDULING VARIABLES & DOMAIN GENERATION
        # =========================================================

        st.divider()
        st.subheader("Scheduling Variables & Domain Generation")

        if not st.session_state.get(
            "scheduling_dataset_confirmed", False
        ):

            st.warning(
                "Confirm the scheduling dataset first."
            )

        else:

            SCHEDULING_SESSIONS = (
                st.session_state.scheduling_sessions.copy()
            )

            VALID_PERIODS = st.session_state.valid_periods.copy()

            FACULTY_AVAILABILITY = (
                st.session_state.faculty_availability.copy()
            )

            SECTION_CLASSROOM_MAPPING = (
                st.session_state.section_classroom_mapping_df.copy()
            )

            LAB_ELIGIBILITY_MAPPING = (
                st.session_state.lab_eligibility_mapping.copy()
            )

            # -------------------------------------------------
            # 1. PREPARE PERIODS BY DAY
            # -------------------------------------------------

            periods_by_day = {}

            for period in VALID_PERIODS:

                day = str(period["Day"])

                periods_by_day.setdefault(day, []).append(
                    period
                )

            for day in periods_by_day:

                periods_by_day[day].sort(
                    key=lambda x: (
                        x["Period"],
                        x["Start_Time"]
                    )
                )

            # -------------------------------------------------
            # 2. FACULTY AVAILABILITY LOOKUP
            # -------------------------------------------------

            availability_lookup = {}

            for _, row in FACULTY_AVAILABILITY.iterrows():

                key = (
                    str(row["Faculty_ID"]).strip(),
                    str(row["Day"]).strip(),
                    str(row["Start_Time"]).strip(),
                    str(row["End_Time"]).strip()
                )

                availability_lookup[key] = bool(
                    row["Available"]
                )

            def faculty_available_for_period(
                faculty_id,
                day,
                start_time,
                end_time
            ):

                key = (
                    str(faculty_id).strip(),
                    str(day).strip(),
                    str(start_time).strip(),
                    str(end_time).strip()
                )

                return availability_lookup.get(key, False)

            # -------------------------------------------------
            # 3. GENERATE TWO-PERIOD LAB BLOCKS
            # -------------------------------------------------

            LAB_PERIOD_BLOCKS = []

            for day, periods in periods_by_day.items():

                for index in range(len(periods) - 1):

                    first = periods[index]
                    second = periods[index + 1]

                    if first["End_Time"] != second["Start_Time"]:
                        continue

                    LAB_PERIOD_BLOCKS.append({

                        "Day": day,

                        "Period_1": first["Period"],
                        "Period_2": second["Period"],

                        "Start_Time": first["Start_Time"],
                        "End_Time": second["End_Time"],

                        "Periods": [
                            first["Period"],
                            second["Period"]
                        ]
                    })

            # -------------------------------------------------
            # 4. RESOURCE OPTIONS
            # -------------------------------------------------

            def get_session_resources(session):

                if session["Session_Type"] == "Theory":

                    classroom = session["Fixed_Classroom"]

                    if pd.isna(classroom):
                        return []

                    return [str(classroom)]

                elif session["Session_Type"] == "Laboratory":

                    return [
                        str(lab)
                        for lab in session["Candidate_Labs"]
                        if pd.notna(lab)
                    ]

                return []

            # -------------------------------------------------
            # 5. GENERATE DOMAINS
            # -------------------------------------------------

            SCHEDULING_DOMAINS = {}
            DOMAIN_RECORDS = []
            DOMAIN_SUMMARY = []

            for _, session in SCHEDULING_SESSIONS.iterrows():

                session_id = str(session["Session_ID"])

                session_type = str(session["Session_Type"])

                eligible_faculty = [
                    str(fid).strip()
                    for fid in session["Eligible_Faculty"]
                ]

                candidate_resources = (
                    get_session_resources(session)
                )

                domain = []

                # THEORY: ONE PERIOD
                if session_type == "Theory":

                    for day, periods in periods_by_day.items():

                        for period in periods:

                            for faculty_id in eligible_faculty:

                                if not faculty_available_for_period(
                                    faculty_id,
                                    day,
                                    period["Start_Time"],
                                    period["End_Time"]
                                ):
                                    continue

                                for resource in candidate_resources:

                                    domain.append({

                                        "Session_ID": session_id,
                                        "Faculty_ID": faculty_id,
                                        "Day": day,

                                        "Start_Period": period["Period"],
                                        "End_Period": period["Period"],

                                        "Start_Time": period["Start_Time"],
                                        "End_Time": period["End_Time"],

                                        "Periods": [period["Period"]],

                                        "Resource": resource,
                                        "Resource_Type": "Classroom"
                                    })

                # LAB: TWO CONSECUTIVE PERIODS
                elif session_type == "Laboratory":

                    for block in LAB_PERIOD_BLOCKS:

                        for faculty_id in eligible_faculty:

                            day_periods = periods_by_day[
                                block["Day"]
                            ]

                            first_period = next(
                                p for p in day_periods
                                if p["Period"] == block["Period_1"]
                            )

                            second_period = next(
                                p for p in day_periods
                                if p["Period"] == block["Period_2"]
                            )

                            first_available = (
                                faculty_available_for_period(
                                    faculty_id,
                                    block["Day"],
                                    first_period["Start_Time"],
                                    first_period["End_Time"]
                                )
                            )

                            second_available = (
                                faculty_available_for_period(
                                    faculty_id,
                                    block["Day"],
                                    second_period["Start_Time"],
                                    second_period["End_Time"]
                                )
                            )

                            if not (
                                first_available
                                and second_available
                            ):
                                continue

                            for resource in candidate_resources:

                                domain.append({

                                    "Session_ID": session_id,
                                    "Faculty_ID": faculty_id,
                                    "Day": block["Day"],

                                    "Start_Period": block["Period_1"],
                                    "End_Period": block["Period_2"],

                                    "Start_Time": block["Start_Time"],
                                    "End_Time": block["End_Time"],

                                    "Periods": block["Periods"],

                                    "Resource": resource,
                                    "Resource_Type": "Laboratory"
                                })

                SCHEDULING_DOMAINS[session_id] = domain

                DOMAIN_RECORDS.extend(domain)

                DOMAIN_SUMMARY.append({

                    "Session_ID": session_id,
                    "Course_Title": session["Course_Title"],
                    "Session_Type": session_type,
                    "Section_ID": session["Section_ID"],

                    "Eligible_Faculty_Count": (
                        len(eligible_faculty)
                    ),

                    "Candidate_Resource_Count": (
                        len(candidate_resources)
                    ),

                    "Domain_Size": len(domain),

                    "Domain_Status": (
                        "Valid Options Available"
                        if domain
                        else "Empty Domain"
                    )
                })

            # -------------------------------------------------
            # 6. DOMAIN DATAFRAMES
            # -------------------------------------------------

            DOMAIN_DATAFRAME = pd.DataFrame(
                DOMAIN_RECORDS
            )

            DOMAIN_SUMMARY_DF = pd.DataFrame(
                DOMAIN_SUMMARY
            )

            EMPTY_DOMAIN_SESSIONS = (
                DOMAIN_SUMMARY_DF[
                    DOMAIN_SUMMARY_DF["Domain_Size"] == 0
                ].copy()
            )

            # -------------------------------------------------
            # 7. SUMMARY
            # -------------------------------------------------

            total_sessions = len(
                SCHEDULING_SESSIONS
            )

            sessions_with_options = (
                DOMAIN_SUMMARY_DF["Domain_Size"] > 0
            ).sum()

            total_domain_options = len(
                DOMAIN_RECORDS
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Scheduling Variables",
                total_sessions
            )

            col2.metric(
                "Sessions with Options",
                int(sessions_with_options)
            )

            col3.metric(
                "Assignment Combinations",
                total_domain_options
            )

            col4.metric(
                "Empty Domains",
                len(EMPTY_DOMAIN_SESSIONS)
            )

            st.subheader("Domain Summary")

            st.dataframe(
                DOMAIN_SUMMARY_DF,
                use_container_width=True,
                hide_index=True
            )

            # -------------------------------------------------
            # 8. EMPTY DOMAIN CHECK
            # -------------------------------------------------

            if not EMPTY_DOMAIN_SESSIONS.empty:

                st.error(
                    "Some scheduling sessions have no valid assignments."
                )

                st.dataframe(
                    EMPTY_DOMAIN_SESSIONS,
                    use_container_width=True
                )

            else:

                st.success(
                    "Every scheduling session has valid assignment options."
                )

            # -------------------------------------------------
            # 9. REVIEW ASSIGNMENT OPTIONS
            # -------------------------------------------------

            with st.expander(
                "View All Candidate Assignment Options"
            ):

                st.dataframe(
                    DOMAIN_DATAFRAME,
                    use_container_width=True,
                    hide_index=True
                )

            # -------------------------------------------------
            # 10. SAVE TO SESSION STATE
            # -------------------------------------------------

            previous_domains = st.session_state.get("scheduling_domains")
            domains_changed = (
                previous_domains is None
                or previous_domains != SCHEDULING_DOMAINS
            )
            if domains_changed:
                st.session_state.scheduling_domains_confirmed = False
                st.session_state.conflict_graph_confirmed = False

            st.session_state.scheduling_domains = (
                SCHEDULING_DOMAINS
            )

            st.session_state.domain_dataframe = (
                DOMAIN_DATAFRAME
            )

            st.session_state.domain_summary_df = (
                DOMAIN_SUMMARY_DF
            )

            st.session_state.empty_domain_sessions = (
                EMPTY_DOMAIN_SESSIONS
            )

            if st.button(
                "Confirm Candidate Domains",
                type="primary",
                use_container_width=True
            ):
                if not EMPTY_DOMAIN_SESSIONS.empty:
                    st.session_state.scheduling_domains_confirmed = False
                    st.error("Cannot confirm candidate domains while empty domains remain.")
                else:
                    st.session_state.scheduling_domains_confirmed = True
                    st.session_state.config["candidate_domains_confirmed"] = True
                    st.success("Candidate domains confirmed. Review the conflict graph next.")

            # ============================================================
            # CELL 21: CONFLICT GRAPH + INTERACTIVE EXPLORER
            # ============================================================
            
            st.divider()
            st.header("Conflict Graph Construction")
            
            # ------------------------------------------------------------
            # 1. GRAPH VERTICES
            # ------------------------------------------------------------
            
            GRAPH_VERTICES = {}
            
            for _, session in SCHEDULING_SESSIONS.iterrows():
            
                session_id = str(session["Session_ID"])
            
                GRAPH_VERTICES[session_id] = {
            
                    "Session_ID": session_id,
                    "Section_ID": str(session["Section_ID"]),
                    "Programme": str(session["Programme"]),
                    "Semester": str(session["Semester"]),
                    "Section": str(session["Section"]),
                    "Course_Code": str(session["Course_Code"]),
                    "Course_Title": str(session["Course_Title"]),
                    "Session_Type": str(session["Session_Type"]),
                    "Periods_Required": session["Periods_Required"],
                    "Consecutive": session["Consecutive"],
                    "Eligible_Faculty": session["Eligible_Faculty"],
                    "Fixed_Classroom": session["Fixed_Classroom"],
                    "Candidate_Labs": session["Candidate_Labs"]
                }
            
            
            # ------------------------------------------------------------
            # 2. HELPER FUNCTIONS
            # ------------------------------------------------------------
            
            def graph_clean_list(values):
            
                if values is None:
                    return set()
            
                if isinstance(values, str):
                    return {values.strip()} if values.strip() else set()
            
                try:
                    return {
                        str(v).strip()
                        for v in values
                        if pd.notna(v)
                    }
            
                except TypeError:
                    return set()
            
            
            def graph_candidate_resources(data):
            
                if data["Session_Type"] == "Theory":
            
                    classroom = data["Fixed_Classroom"]
            
                    if classroom is None or pd.isna(classroom):
                        return set()
            
                    return {str(classroom).strip()}
            
                return graph_clean_list(
                    data["Candidate_Labs"]
                )
            
            
            # ------------------------------------------------------------
            # 3. FIXED CONFLICT EDGES
            #    Sessions belonging to the same section cannot overlap.
            # ------------------------------------------------------------
            
            STATIC_GRAPH_EDGES = []
            
            session_ids = list(GRAPH_VERTICES.keys())
            
            for i in range(len(session_ids)):
            
                session_a_id = session_ids[i]
                session_a = GRAPH_VERTICES[session_a_id]
            
                for j in range(i + 1, len(session_ids)):
            
                    session_b_id = session_ids[j]
                    session_b = GRAPH_VERTICES[session_b_id]
            
                    if (
                        session_a["Section_ID"]
                        == session_b["Section_ID"]
                    ):
            
                        STATIC_GRAPH_EDGES.append({
            
                            "Source": session_a_id,
                            "Target": session_b_id,
            
                            "Conflict_Type": "SECTION_CONFLICT",
            
                            "Description": (
                                "Both sessions belong to the same "
                                "student section and cannot overlap."
                            ),
            
                            "Section_ID": session_a["Section_ID"]
            
                        })
            
            
            # ------------------------------------------------------------
            # 4. CONDITIONAL CONFLICTS
            #    These are NOT drawn as fixed graph edges.
            # ------------------------------------------------------------
            
            CONDITIONAL_CONFLICTS = []
            
            for i in range(len(session_ids)):
            
                session_a_id = session_ids[i]
                session_a = GRAPH_VERTICES[session_a_id]
            
                faculty_a = graph_clean_list(
                    session_a["Eligible_Faculty"]
                )
            
                resources_a = graph_candidate_resources(
                    session_a
                )
            
                for j in range(i + 1, len(session_ids)):
            
                    session_b_id = session_ids[j]
                    session_b = GRAPH_VERTICES[session_b_id]
            
                    faculty_b = graph_clean_list(
                        session_b["Eligible_Faculty"]
                    )
            
                    resources_b = graph_candidate_resources(
                        session_b
                    )
            
                    common_faculty = (
                        faculty_a.intersection(faculty_b)
                    )
            
                    common_resources = (
                        resources_a.intersection(resources_b)
                    )
            
                    if common_faculty:
            
                        CONDITIONAL_CONFLICTS.append({
            
                            "Session_A": session_a_id,
                            "Session_B": session_b_id,
            
                            "Conflict_Type": "FACULTY_CONFLICT",
            
                            "Common_Faculty_Candidates": (
                                sorted(common_faculty)
                            ),
            
                            "Common_Resources": []
            
                        })
            
                    if common_resources:
            
                        CONDITIONAL_CONFLICTS.append({
            
                            "Session_A": session_a_id,
                            "Session_B": session_b_id,
            
                            "Conflict_Type": "RESOURCE_CONFLICT",
            
                            "Common_Faculty_Candidates": [],
            
                            "Common_Resources": (
                                sorted(common_resources)
                            )
            
                        })
            
            
            # ------------------------------------------------------------
            # 5. BUILD NETWORKX GRAPH
            # ------------------------------------------------------------
            
            G_CONFLICT = nx.Graph()
            
            for session_id, data in GRAPH_VERTICES.items():
            
                G_CONFLICT.add_node(
                    session_id,
                    **data
                )
            
            for edge in STATIC_GRAPH_EDGES:
            
                G_CONFLICT.add_edge(
                    edge["Source"],
                    edge["Target"],
                    conflict_type=edge["Conflict_Type"],
                    description=edge["Description"],
                    section_id=edge["Section_ID"]
                )
            
            
            ADJACENCY_LIST = {
                node: set(G_CONFLICT.neighbors(node))
                for node in G_CONFLICT.nodes()
            }
            
            
            # ------------------------------------------------------------
            # 6. GRAPH STATISTICS
            # ------------------------------------------------------------
            
            total_nodes = G_CONFLICT.number_of_nodes()
            total_edges = G_CONFLICT.number_of_edges()
            
            degrees = dict(
                G_CONFLICT.degree()
            )
            
            maximum_degree = (
                max(degrees.values())
                if degrees
                else 0
            )
            
            average_degree = (
                sum(degrees.values()) / total_nodes
                if total_nodes
                else 0
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "Graph Nodes",
                total_nodes
            )
            
            col2.metric(
                "Fixed Conflict Edges",
                total_edges
            )
            
            col3.metric(
                "Maximum Degree",
                maximum_degree
            )
            
            col4.metric(
                "Average Degree",
                round(average_degree, 2)
            )
            
            
            # ------------------------------------------------------------
            # 7. SAVE GRAPH DATA FOR FUTURE CSP ALGORITHMS
            # ------------------------------------------------------------
            
            previous_graph_edges = st.session_state.get("STATIC_GRAPH_EDGES")
            graph_changed = (
                previous_graph_edges is None
                or previous_graph_edges != STATIC_GRAPH_EDGES
            )
            if graph_changed:
                st.session_state.conflict_graph_confirmed = False

            st.session_state.GRAPH_VERTICES = GRAPH_VERTICES
            
            st.session_state.STATIC_GRAPH_EDGES = (
                STATIC_GRAPH_EDGES
            )
            
            st.session_state.ADJACENCY_LIST = (
                ADJACENCY_LIST
            )
            
            st.session_state.CONDITIONAL_CONFLICTS = (
                CONDITIONAL_CONFLICTS
            )
            
            st.session_state.G_CONFLICT = G_CONFLICT
            
            
            # ------------------------------------------------------------
            # 8. GLOBAL CIRCULAR LAYOUT — SINGLE GRAPH
            # ------------------------------------------------------------
            
            positions = nx.circular_layout(
                G_CONFLICT,
                scale=10,
                center=(0, 0)
            )
            
            # ------------------------------------------------------------
            # 9. PREPARE GRAPH EDGES
            # ------------------------------------------------------------
            
            edge_x = []
            edge_y = []
            
            edge_mid_x = []
            edge_mid_y = []
            
            edge_customdata = []
            edge_hover = []
            
            for edge_index, edge in enumerate(
                STATIC_GRAPH_EDGES
            ):
            
                source = edge["Source"]
                target = edge["Target"]
            
                x1, y1 = positions[source]
                x2, y2 = positions[target]
            
                edge_x.extend([
                    x1,
                    x2,
                    None
                ])
            
                edge_y.extend([
                    y1,
                    y2,
                    None
                ])
            
                edge_mid_x.append(
                    (x1 + x2) / 2
                )
            
                edge_mid_y.append(
                    (y1 + y2) / 2
                )
            
                edge_customdata.append(
                    edge_index
                )
            
                source_data = GRAPH_VERTICES[source]
                target_data = GRAPH_VERTICES[target]
                
                source_domain = SCHEDULING_DOMAINS.get(
                    source,
                    []
                )
                
                target_domain = SCHEDULING_DOMAINS.get(
                    target,
                    []
                )
                
                source_slots = {
                    (
                        str(option["Day"]),
                        str(option["Start_Time"]),
                        str(option["End_Time"])
                    )
                    for option in source_domain
                }
                
                target_slots = {
                    (
                        str(option["Day"]),
                        str(option["Start_Time"]),
                        str(option["End_Time"])
                    )
                    for option in target_domain
                }
                
                common_slots = sorted(
                    source_slots.intersection(target_slots)
                )
                
                common_slots_text = (
                    "<br>".join(
                        f"{day}: {start} - {end}"
                        for day, start, end in common_slots[:10]
                    )
                    if common_slots
                    else "No common candidate time slots"
                )
                
                source_faculty = sorted(
                    graph_clean_list(
                        source_data["Eligible_Faculty"]
                    )
                )
                
                target_faculty = sorted(
                    graph_clean_list(
                        target_data["Eligible_Faculty"]
                    )
                )
                
                source_faculty_text = (
                    ", ".join(source_faculty)
                    if source_faculty
                    else "None"
                )
                
                target_faculty_text = (
                    ", ".join(target_faculty)
                    if target_faculty
                    else "None"
                )
                
                edge_hover.append(
                
                    f"<b>⚠ FIXED TIMETABLE CONFLICT</b><br><br>"
                
                    f"<b>Session A:</b> {source}<br>"
                    f"<b>Subject:</b> {source_data['Course_Title']}<br>"
                    f"<b>Course Code:</b> {source_data['Course_Code']}<br>"
                    f"<b>Faculty Candidates:</b> {source_faculty_text}<br><br>"
                
                    f"<b>Session B:</b> {target}<br>"
                    f"<b>Subject:</b> {target_data['Course_Title']}<br>"
                    f"<b>Course Code:</b> {target_data['Course_Code']}<br>"
                    f"<b>Faculty Candidates:</b> {target_faculty_text}<br><br>"
                
                    f"<b>Section:</b> {edge['Section_ID']}<br><br>"
                
                    f"<b>Conflict:</b> Both sessions belong to "
                    f"the same student section.<br>"
                
                    f"<b>Constraint:</b> They cannot be scheduled "
                    f"on the same day and time slot."
                )                    
            
            # ------------------------------------------------------------
            # 10. PREPARE NODE DATA
            # ------------------------------------------------------------
            
            node_x = []
            node_y = []
            
            node_customdata = []
            node_colors = []
            node_hover = []
            
            for node, data in GRAPH_VERTICES.items():
            
                x, y = positions[node]
            
                node_x.append(x)
                node_y.append(y)
            
                node_customdata.append(node)
            
                if data["Session_Type"] == "Theory":
            
                    node_colors.append("#2878C8")
            
                else:
            
                    node_colors.append("#E58A32")
            
                node_hover.append(
            
                    f"<b>{data['Course_Title']}</b><br>"
                    f"Session: {node}<br>"
                    f"Course Code: {data['Course_Code']}<br>"
                    f"Programme: {data['Programme']}<br>"
                    f"Semester: {data['Semester']}<br>"
                    f"Section: {data['Section']}<br>"
                    f"Type: {data['Session_Type']}<br>"
                    f"Periods: {data['Periods_Required']}<br>"
                    f"<b>Fixed Conflict Degree: {degrees[node]}</b><br>"
                    f"<b>Conflicts With:</b><br>"
                    f"{'<br>'.join(sorted(ADJACENCY_LIST[node])[:12])}<br>"
                    f"Faculty Candidates: "
                    f"{len(graph_clean_list(data['Eligible_Faculty']))}<br>"
                    f"<b>Click to inspect session</b>"
                )
            
            
            # ------------------------------------------------------------
            # 11. INTERACTIVE PLOTLY GRAPH
            # ------------------------------------------------------------
            
            fig = go.Figure()
            
            
            # Fixed graph edges
            fig.add_trace(
            
                go.Scatter(
            
                    x=edge_x,
                    y=edge_y,
            
                    mode="lines",
            
                    line=dict(
                        color="rgba(170,170,170,0.50)",
                        width=1.1
                    ),
                    
                    hoverinfo="skip",
            
                    name="Fixed Section Conflicts"
            
                )
            )
            
            
            # Selectable edge markers
            fig.add_trace(
            
                go.Scatter(
            
                    x=edge_mid_x,
                    y=edge_mid_y,
            
                    mode="markers",
            
                    marker=dict(
                        size=12,
                        color="rgba(100,100,100,0.02)"
                    ),
            
                    customdata=edge_customdata,
            
                    text=edge_hover,
            
                    hovertemplate=(
                        "%{text}<extra></extra>"
                    ),
            
                    name="Select Conflict Edge"
            
                )
            )
            
            
            # Interactive nodes
            fig.add_trace(
            
                go.Scatter(
            
                    x=node_x,
                    y=node_y,
            
                    mode="markers+text",
            
                    text=node_customdata,
            
                    textposition="top center",
            
                    textfont=dict(
                        size=7
                    ),
            
                    marker=dict(
            
                        size=19,
            
                        color=node_colors,
            
                        line=dict(
                            color="white",
                            width=1.2
                        )
            
                    ),
            
                    customdata=node_customdata,
            
                    hovertext=node_hover,
            
                    hovertemplate=(
                        "%{hovertext}<extra></extra>"
                    ),
            
                    name="Teaching Sessions"
            
                )
            )
            
            
            fig.update_layout(
            
                title={
                    "text": "Interactive Conflict Graph",
                    "x": 0.5
                },
            
                height=1100,
            
                showlegend=True,
            
                hovermode="closest",
            
                clickmode="event+select",
            
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=20
                ),
            
                xaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False
                ),
            
                yaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False,
                    scaleanchor="x",
                    scaleratio=1
                )
            
            )
            
            
            st.markdown(
                """
                **Graph interaction**
            
                - 🔵 Blue nodes: Theory sessions
                - 🟠 Orange nodes: Laboratory sessions
                - Grey edges: Fixed section conflicts
                - Hover: Preview session/conflict information
                - Click a node or edge: Inspect its details below
                """
            )
            
            
            graph_selection = st.plotly_chart(
            
                fig,
            
                use_container_width=True,
            
                key="interactive_conflict_graph",
            
                on_select="rerun",
            
                selection_mode="points"
            
            )
            
            
            # ------------------------------------------------------------
            # 12. NODE / EDGE DETAILS
            # ------------------------------------------------------------
            
            st.subheader("Selected Node / Edge Information")
            
            selected_points = []
            
            try:
            
                selected_points = (
                    graph_selection.selection.points
                )
            
            except Exception:
            
                selected_points = []
            
            
            if selected_points:
            
                selected_point = selected_points[-1]
            
                curve_number = selected_point.get(
                    "curve_number"
                )
            
                customdata = selected_point.get(
                    "customdata"
                )
            
                # EDGE SELECTED
                if curve_number == 1:
            
                    try:
            
                        edge_index = int(customdata)
            
                        edge = STATIC_GRAPH_EDGES[
                            edge_index
                        ]
            
                        source = edge["Source"]
                        target = edge["Target"]
            
                        source_data = GRAPH_VERTICES[source]
                        target_data = GRAPH_VERTICES[target]
            
                        st.info(
                            f"**Conflict Type:** {edge['Conflict_Type']}  \n"
                            f"**Description:** {edge['Description']}  \n"
                            f"**Section:** {edge['Section_ID']}"
                        )
            
                        col_a, col_b = st.columns(2)
            
                        with col_a:
            
                            st.markdown("### Session A")
            
                            st.write(source)
            
                            st.write(
                                source_data["Course_Title"]
                            )
            
                            st.write(
                                source_data["Session_Type"]
                            )
            
                        with col_b:
            
                            st.markdown("### Session B")
            
                            st.write(target)
            
                            st.write(
                                target_data["Course_Title"]
                            )
            
                            st.write(
                                target_data["Session_Type"]
                            )
            
                    except Exception as e:
            
                        st.warning(
                            f"Could not display edge details: {e}"
                        )
            
            
                # NODE SELECTED
                elif curve_number == 2:
            
                    session_id = str(customdata)
            
                    if session_id in GRAPH_VERTICES:
            
                        data = GRAPH_VERTICES[
                            session_id
                        ]
            
                        st.markdown(
                            f"## {data['Course_Title']}"
                        )
            
                        col_a, col_b, col_c = st.columns(3)
            
                        col_a.metric(
                            "Session ID",
                            session_id
                        )
            
                        col_b.metric(
                            "Session Type",
                            data["Session_Type"]
                        )
            
                        col_c.metric(
                            "Fixed Conflict Degree",
                            degrees[session_id]
                        )
            
                        st.write(
                            "**Course Code:**",
                            data["Course_Code"]
                        )
            
                        st.write(
                            "**Programme:**",
                            data["Programme"]
                        )
            
                        st.write(
                            "**Semester:**",
                            data["Semester"]
                        )
            
                        st.write(
                            "**Section:**",
                            data["Section"]
                        )
            
                        st.write(
                            "**Periods Required:**",
                            data["Periods_Required"]
                        )
            
                        st.write(
                            "**Consecutive:**",
                            data["Consecutive"]
                        )
            
                        st.markdown(
                            "### Eligible Faculty Candidates"
                        )
            
                        faculty = graph_clean_list(
                            data["Eligible_Faculty"]
                        )
            
                        if faculty:
            
                            st.write(
                                sorted(faculty)
                            )
            
                        else:
            
                            st.write(
                                "No eligible faculty candidates."
                            )
            
            
                        st.markdown(
                            "### Candidate Resources"
                        )
            
                        resources = graph_candidate_resources(
                            data
                        )
            
                        if resources:
            
                            st.write(
                                sorted(resources)
                            )
            
                        else:
            
                            st.write(
                                "No candidate resources."
                            )
            
            
                        st.markdown(
                            "### Fixed Conflict Neighbours"
                        )
            
                        neighbours = sorted(
                            ADJACENCY_LIST[session_id]
                        )
            
                        st.write(
                            f"{len(neighbours)} fixed conflicts"
                        )
            
                        if neighbours:
            
                            neighbour_df = pd.DataFrame([
            
                                {
            
                                    "Session_ID": neighbour,
            
                                    "Course_Title": (
                                        GRAPH_VERTICES[neighbour]
                                        ["Course_Title"]
                                    ),
            
                                    "Session_Type": (
                                        GRAPH_VERTICES[neighbour]
                                        ["Session_Type"]
                                    )
            
                                }
            
                                for neighbour in neighbours
            
                            ])
            
                            st.dataframe(
                                neighbour_df,
                                use_container_width=True,
                                hide_index=True
                            )
            
            
                        st.markdown(
                            "### Conditional Relationships"
                        )
            
                        conditional_for_node = [
            
                            item
            
                            for item in CONDITIONAL_CONFLICTS
            
                            if session_id in [
                                item["Session_A"],
                                item["Session_B"]
                            ]
            
                        ]
            
                        if conditional_for_node:
            
                            conditional_df = pd.DataFrame(
                                conditional_for_node
                            )
            
                            st.dataframe(
                                conditional_df,
                                use_container_width=True,
                                hide_index=True
                            )
            
                        else:
            
                            st.write(
                                "No conditional faculty/resource relationships."
                            )
            
            else:
            
                st.info(
                    "Click a graph node or an edge to inspect its details."
                )
            
            
            # ------------------------------------------------------------
            # 13. NODE DEGREE TABLE
            # ------------------------------------------------------------
            
            st.subheader("Degree Analysis")
            
            DEGREE_DF = pd.DataFrame({
            
                "Session_ID": list(degrees.keys()),
            
                "Degree": list(degrees.values())
            
            }).sort_values(
                "Degree",
                ascending=False
            )
            
            st.dataframe(
                DEGREE_DF,
                use_container_width=True,
                hide_index=True
            )
            
            
            # ------------------------------------------------------------
            # 14. CONDITIONAL CONFLICT TABLE
            # ------------------------------------------------------------
            
            st.subheader(
                "Conditional Faculty / Resource Relationships"
            )
            
            if CONDITIONAL_CONFLICTS:
            
                CONDITIONAL_DF = pd.DataFrame(
                    CONDITIONAL_CONFLICTS
                )
            
                st.dataframe(
                    CONDITIONAL_DF,
                    use_container_width=True,
                    hide_index=True
                )
            
            else:
            
                st.info(
                    "No conditional relationships were detected."
                )
            
            
            # ------------------------------------------------------------
            # 15. DOWNLOAD GRAPH DATA
            # ------------------------------------------------------------
            
            STATIC_EDGE_DF = pd.DataFrame(STATIC_GRAPH_EDGES)
            
            NODE_MAPPING_DF = pd.DataFrame(
                list(GRAPH_VERTICES.values())
            )
            
            st.download_button(
                "Download Fixed Conflict Edges",
                data=STATIC_EDGE_DF.to_csv(index=False).encode("utf-8"),
                file_name="STATIC_CONFLICT_EDGES.csv",
                mime="text/csv"
            )
            
            st.download_button(
                "Download Node Mapping",
                data=NODE_MAPPING_DF.to_csv(index=False).encode("utf-8"),
                file_name="GRAPH_NODE_MAPPING.csv",
                mime="text/csv"
            )
            
            st.divider()
            
            
            # ------------------------------------------------------------
            # 16. CONFIRM CONFLICT GRAPH
            # ------------------------------------------------------------
            
            if st.button(
                "Confirm Conflict Graph",
                type="primary",
                use_container_width=True
            ):
            
                if not st.session_state.get(
                    "scheduling_domains_confirmed", False
                ):
            
                    st.error(
                        "Confirm candidate domains before confirming the conflict graph."
                    )
            
                    st.session_state.conflict_graph_confirmed = False
            
                    st.session_state.config[
                        "conflict_graph_confirmed"
                    ] = False
            
                else:
            
                    st.session_state.conflict_graph_confirmed = True
            
                    st.session_state.config[
                        "conflict_graph_confirmed"
                    ] = True
            
                    st.success(
                        "Conflict graph confirmed. CP-SAT is ready."
                    )


            # ------------------------------------------------------------
            # 17. CP-SAT READY STATUS
            # ------------------------------------------------------------

            if st.session_state.get(
                "conflict_graph_confirmed", False
            ):

                st.success(
                    "Conflict graph is confirmed. You can now proceed to CP-SAT."
                )

            else:

                st.info(
                    "Confirm the conflict graph before proceeding to CP-SAT."
                )

                            "Semester": session_data.get(
                                "Semester", ""
                            ),

                            "Section": session_data.get(
                                "Section", ""
                            ),

                            "Course_Code": session_data.get(
                                "Course_Code", ""
                            ),

                            "Course_Title": session_data.get(
                                "Course_Title", ""
                            ),

                            "Session_Type": session_data.get(
                                "Session_Type", ""
                            ),

                            "Faculty_ID": selected_option[
                                "Faculty_ID"
                            ],

                            "Day": selected_option["Day"],

                            "Start_Period": selected_option[
                                "Start_Period"
                            ],

                            "End_Period": selected_option[
                                "End_Period"
                            ],

                            "Start_Time": selected_option[
                                "Start_Time"
                            ],

                            "End_Time": selected_option[
                                "End_Time"
                            ],

                            "Periods": selected_option[
                                "Periods"
                            ],

                            "Resource": selected_option[
                                "Resource"
                            ],

                            "Resource_Type": selected_option[
                                "Resource_Type"
                            ]

                        })

                    TIMETABLE_DF = pd.DataFrame(
                        timetable_records
                    )

                    # ---------------------------------------------
                    # SAVE RESULTS
                    # ---------------------------------------------

                    st.session_state.generated_timetable = (
                        TIMETABLE_DF
                    )

                    st.session_state.cpsat_status = (
                        solver.StatusName(status)
                    )

                    st.session_state.cpsat_runtime = (
                        solver.WallTime()
                    )

                    st.session_state.cpsat_constraints = {

                        "Section Conflict Constraints":
                            section_constraints,

                        "Faculty Conflict Constraints":
                            faculty_constraints,

                        "Resource Conflict Constraints":
                            resource_constraints
                    }
        
            # =====================================================

                else:

                    st.error(
                        f"CP-SAT could not generate a timetable. "
                        f"Solver status: {solver.StatusName(status)}"
                    )

                    st.session_state.cpsat_status = solver.StatusName(status)
                    st.session_state.cpsat_runtime = solver.WallTime()

# =========================================================
# 10. INDEPENDENT GENERATED TIMETABLE VIEWER
# =========================================================
elif page == "10. View Generated Timetable":

    st.header("📅 View Generated Timetable")

    # CHECK IF TIMETABLE EXISTS
    if (
        "generated_timetable" not in st.session_state
        or st.session_state.generated_timetable is None
        or st.session_state.generated_timetable.empty
    ):

        st.info("Generate the timetable using CP-SAT first.")

    else:

        timetable_df = st.session_state.generated_timetable.copy()

        st.success(
            f"Saved timetable loaded: {len(timetable_df)} scheduled sessions | "
            f"Status: {st.session_state.get('cpsat_status', 'Unknown')}"
        )

        # -------------------------------------------------
        # VIEW TYPE
        # -------------------------------------------------

        view_type = st.selectbox(
            "View timetable by",
            [
                "Master Timetable",
                "Section-wise",
                "Faculty-wise",
                "Laboratory-wise"
            ],
            key="independent_timetable_view_type"
        )

        filtered_df = timetable_df.copy()

        # -------------------------------------------------
        # FILTER CONFIGURATION
        # -------------------------------------------------

        if view_type == "Section-wise":

            column = "Section_ID"
            label = "Select Section"

            options = (
                sorted(
                    filtered_df[column]
                    .dropna()
                    .astype(str)
                    .unique()
                )
                if column in filtered_df.columns
                else []
            )

        elif view_type == "Faculty-wise":

            column = "Faculty_ID"
            label = "Select Faculty"

            options = (
                sorted(
                    filtered_df[column]
                    .dropna()
                    .astype(str)
                    .unique()
                )
                if column in filtered_df.columns
                else []
            )

        elif view_type == "Laboratory-wise":

            lab_mask = (
                filtered_df.get(
                    "Session_Type",
                    pd.Series(index=filtered_df.index, dtype=str)
                )
                .astype(str)
                .str.contains("Lab", case=False, na=False)

                |

                filtered_df.get(
                    "Resource_Type",
                    pd.Series(index=filtered_df.index, dtype=str)
                )
                .astype(str)
                .str.contains("Lab", case=False, na=False)
            )

            filtered_df = filtered_df[lab_mask].copy()

            column = "Resource"
            label = "Select Laboratory"

            options = (
                sorted(
                    filtered_df[column]
                    .dropna()
                    .astype(str)
                    .unique()
                )
                if column in filtered_df.columns
                else []
            )

        else:

            column = None
            options = []

        # -------------------------------------------------
        # ENTITY SELECTION
        # -------------------------------------------------

        if column is not None:

            if options:

                selected_value = st.selectbox(
                    label,
                    options,
                    key=f"independent_timetable_entity_{view_type}"
                )

                filtered_df = filtered_df[
                    filtered_df[column].astype(str)
                    == selected_value
                ].copy()

            else:

                st.warning(
                    f"No available options for {view_type.lower()} view."
                )

        # -------------------------------------------------
        # DISPLAY TIMETABLE
        # -------------------------------------------------

        if not filtered_df.empty:

            # SORTING
            sort_columns = [
                c
                for c in [
                    "Day",
                    "Start_Period",
                    "Semester",
                    "Section_ID"
                ]
                if c in filtered_df.columns
            ]

            if sort_columns:

                filtered_df = filtered_df.sort_values(
                    sort_columns
                )

            # SESSION COUNT
            st.metric(
                "Sessions displayed",
                len(filtered_df)
            )

            # TABLE
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )

            # DOWNLOAD
            st.download_button(
                "⬇️ Download displayed timetable as CSV",
                data=filtered_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{view_type.replace(' ', '_')}_timetable.csv",
                mime="text/csv",
                key="independent_timetable_download"
            )

        else:

            st.info(
                "No timetable rows match this view."
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Graph-Based Timetable Conflict Detection and Resolution System"
)

st.caption(
    "Graph-Based Timetable Conflict Detection and Resolution System"
)
