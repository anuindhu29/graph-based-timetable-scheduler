import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
from docx import Document
import io

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
        "5. Upload & Retrieve Files",
        "6. Faculty Constraints & HOD Approval",
        "7. Classroom & Laboratory Configuration",
        "8. Generate Timetable"
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

    if not st.session_state.config.get("complete_confirmed", False):

        st.warning(
            "Please complete and confirm the configuration "
            "before uploading files."
        )

    else:

        academic = st.session_state.config["academic_programmes"]

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

            review_data = {}
            errors = []

            for key, file in uploaded_files.items():

                # Skip curriculum if programme is excluded
                if file is None:

                    if key in ["btech", "mtech"]:
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
# 7. GENERATE TIMETABLE
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
            "✅ Configuration and uploaded datasets are ready."
        )

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

        st.write("DEBUG uploaded_data keys:", list(uploaded_data.keys()))
        st.write("DEBUG B.Tech included:", academic_config["B.Tech"]["included"])
        st.write("DEBUG M.Tech included:", academic_config["M.Tech"]["included"])

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
           st.write("DEBUG course_datasets count:", len(course_datasets))

        if course_datasets:
             st.write("DEBUG first dataset shape:", course_datasets[0].shape)
             st.write("DEBUG all dataset shapes:", [df.shape for df in course_datasets])
            
            curriculum.columns = (
                curriculum.columns
                .astype(str)
                .str.strip()
            )

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
                    # =================================================
        # LAB-COURSE COMPATIBILITY MAPPING
        # =================================================

        st.divider()

        st.subheader("Lab–Course Compatibility Mapping")

        st.write(
            "Select which laboratories each practical course "
            "is permitted to use."
        )

        # ---------------------------------------------
        # GET LABORATORY RESOURCES
        # ---------------------------------------------
        rooms_df = uploaded_data["rooms"]["data"].copy()

        rooms_df.columns = (
            rooms_df.columns.astype(str).str.strip()
        )

        # Remove unwanted exported index columns
        rooms_df = rooms_df.loc[
            :,
            ~rooms_df.columns.astype(str).str.startswith("Unnamed")
        ]

        lab_resources = rooms_df[
            rooms_df["Type"].astype(str).str.lower().str.contains(
                "lab", na=False
            )
        ].copy()

        # ---------------------------------------------
        # CREATE LAB OPTIONS
        # ---------------------------------------------
        lab_options = {}

        for _, lab in lab_resources.iterrows():

            lab_id = str(lab["Room/Lab ID"])

            lab_name = str(lab["Room/Lab Name"])

            lab_options[
                f"{lab_id} - {lab_name}"
            ] = lab_id

        # ---------------------------------------------
        # IDENTIFY COURSES REQUIRING LABS
        # ---------------------------------------------
        lab_courses = requirements_df[
            requirements_df[
                "Lab_Sessions_Per_Week"
            ] > 0
        ].copy()

        # ---------------------------------------------
        # EXISTING MAPPING
        # ---------------------------------------------
        existing_mapping = st.session_state.get(
            "lab_course_mapping",
            {}
        )

        current_mapping = {}

        # ---------------------------------------------
        # DISPLAY COURSE-WISE MAPPING
        # ---------------------------------------------
        if lab_courses.empty:

            st.info(
                "No laboratory courses were identified "
                "in the selected semesters."
            )

        else:

            st.write(
                f"Laboratory courses identified: "
                f"{len(lab_courses)}"
            )

            for _, course in lab_courses.iterrows():

                course_key = (
                    f"{course['Programme']}_"
                    f"Sem{course['Semester']}_"
                    f"{course['Course_ID']}"
                )

                course_label = (
                    f"{course['Programme']} | "
                    f"Semester {course['Semester']} | "
                    f"{course['Course_ID']} — "
                    f"{course['Course_Name']}"
                )

                previously_selected = (
                    existing_mapping.get(course_key, [])
                )

                selected_options = [
                    option
                    for option, lab_id in lab_options.items()
                    if lab_id in previously_selected
                ]

                st.markdown(
                    f"**{course_label}**"
                )

                selected_labs = st.multiselect(
                    "Compatible laboratories",
                    options=list(lab_options.keys()),
                    default=selected_options,
                    key=f"lab_mapping_{course_key}",
                    help=(
                        "Select all laboratories that can "
                        "conduct this course."
                    )
                )

                current_mapping[course_key] = [
                    lab_options[option]
                    for option in selected_labs
                ]

        # ---------------------------------------------
        # SAVE LAB MAPPING
        # ---------------------------------------------
        if st.button(
            "Save Lab–Course Mapping",
            type="primary",
            use_container_width=True
        ):

            mapping_errors = []

            if not lab_courses.empty:

                for course_key, selected_lab_ids in (
                    current_mapping.items()
                ):

                    if not selected_lab_ids:

                        mapping_errors.append(
                            f"{course_key}: Select at least "
                            "one compatible laboratory."
                        )

            if mapping_errors:

                st.error(
                    "Please complete the laboratory mapping:"
                )

                for error in mapping_errors:
                    st.write("❌", error)

            else:

                st.session_state.lab_course_mapping = (
                    current_mapping.copy()
                )

                st.session_state.lab_mapping_confirmed = True

                st.session_state.config[
                    "lab_course_mapping"
                ] = current_mapping.copy()

                st.success(
                    "Lab–Course Compatibility Mapping saved!"
                )

                mapping_display = []

                for _, course in lab_courses.iterrows():

                    course_key = (
                        f"{course['Programme']}_"
                        f"Sem{course['Semester']}_"
                        f"{course['Course_ID']}"
                    )

                    mapped_ids = current_mapping.get(
                        course_key, []
                    )

                    mapped_names = [
                        option
                        for option, lab_id in lab_options.items()
                        if lab_id in mapped_ids
                    ]

                    mapping_display.append({
                        "Programme": course["Programme"],
                        "Semester": course["Semester"],
                        "Course_ID": course["Course_ID"],
                        "Course_Name": course["Course_Name"],
                        "Compatible_Labs": ", ".join(
                            mapped_names
                        )
                    })

                if mapping_display:

                    st.dataframe(
                        pd.DataFrame(mapping_display),
                        use_container_width=True
                    )
            # -----------------------------------------
            # EXCLUDED COURSES
            # -----------------------------------------
            if excluded_courses:

                with st.expander(
                    "View Excluded Courses"
                ):

                    excluded_df = pd.DataFrame(
                        excluded_courses
                    )

                    st.dataframe(
                        excluded_df,
                        use_container_width=True
                    )

        # ---------------------------------------------
        # SAVE REQUIREMENTS
        # ---------------------------------------------
        st.divider()

        if st.button(
            "Confirm Weekly Course Requirements",
            type="primary",
            use_container_width=True
        ):

            # Require lab mapping only if lab courses exist
            if (
                not lab_courses.empty
                and not st.session_state.get(
                    "lab_mapping_confirmed",
                    False
                )
            ):

                st.error(
                    "Please save Lab–Course Compatibility "
                    "Mapping first."
                )

            else:

                st.session_state.course_requirements = (
                    requirements_df.copy()
                )

                st.session_state.course_requirements_confirmed = True

                st.session_state.config[
                    "course_requirements"
                ] = scheduling_requirements

                st.success(
                    "Weekly course requirements confirmed!"
                )

                st.download_button(
                    "Download Weekly Requirements",
                    data=requirements_df.to_csv(
                        index=False
                    ).encode("utf-8"),
                    file_name="WEEKLY_COURSE_REQUIREMENTS.csv",
                    mime="text/csv"
                )

                # ---------------------------------------------
                # NEXT STAGE INDICATOR
                # ---------------------------------------------
                if st.session_state.get(
                    "course_requirements_confirmed",
                    False
                ):
        
                    st.success(
                        "Course requirements are ready for "
                        "scheduling session generation."
                    )
        
                    st.info(
                        """
                        Next stage:
        
                        1. Generate individual theory sessions.
                        2. Generate two-period laboratory blocks.
                        3. Create section-specific scheduling tasks.
                        4. Determine faculty candidate lists.
                        5. Construct the scheduling conflict graph.
                        """
                    )
            # -----------------------------------------
            # NEXT STAGE INDICATOR
            # -----------------------------------------
            if st.session_state.get(
                "course_requirements_confirmed",
                False
            ):

                st.success(
                    "Course requirements are ready for "
                    "scheduling session generation."
                )

                st.info(
                    """
                    Next stage:

                    1. Generate individual theory sessions.
                    2. Generate two-period laboratory blocks.
                    3. Create section-specific scheduling tasks.
                    4. Determine faculty candidate lists.
                    5. Construct the scheduling conflict graph.
                    """
                )

        else:

            st.error(
                "No curriculum dataset is available for processing."
            )

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
