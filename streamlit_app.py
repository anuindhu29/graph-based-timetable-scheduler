                                    tickvals=list(range(len(periods))),
                                    ticktext=period_labels,
                                    autorange="reversed"
                                ),
                                showlegend=False
                            )
    
                            st.plotly_chart(
                                fig,
                                use_container_width=True
                            )
    
                        # DETAILS
                        with st.expander("View Timetable Data"):
    
                            st.dataframe(
                                view_df,
                                use_container_width=True,
                                hide_index=True
                            )
    
                        # DOWNLOAD
                        st.download_button(
                            "Download Timetable CSV",
                            data=view_df.to_csv(index=False).encode("utf-8"),
                            file_name=f"{view_type}_{selected}.csv",
                            mime="text/csv",
                            key=f"download_{view_type}"
                        )
    
                    else:
    
                        st.warning("No timetable data available for this selection.")
    
            else:
    
                st.info(
                    "Generate the timetable using CP-SAT first. "
                    "The timetable viewer will remain available after generation."
                )

# =========================================================
# 10. INDEPENDENT GENERATED TIMETABLE VIEWER
# =========================================================
elif page == "10. View Generated Timetable":

    st.header("📅 View Generated Timetable")

    if "generated_timetable" not in st.session_state:
        st.info("Generate the timetable using CP-SAT first.")
    else:
        timetable_df = st.session_state.generated_timetable.copy()

        st.success(
            f"Saved timetable loaded: {len(timetable_df)} scheduled sessions | "
            f"Status: {st.session_state.get('cpsat_status', 'Unknown')}"
        )

        view_type = st.selectbox(
            "View timetable by",
            ["Master Timetable", "Section-wise", "Faculty-wise", "Laboratory-wise"],
            key="independent_timetable_view_type"
        )

        filtered_df = timetable_df.copy()

        if view_type == "Section-wise":
            column = "Section_ID"
            label = "Select Section"
            options = sorted(filtered_df[column].dropna().astype(str).unique()) if column in filtered_df.columns else []
        elif view_type == "Faculty-wise":
            column = "Faculty_ID"
            label = "Select Faculty"
            options = sorted(filtered_df[column].dropna().astype(str).unique()) if column in filtered_df.columns else []
        elif view_type == "Laboratory-wise":
            lab_mask = (
                filtered_df.get("Session_Type", pd.Series(index=filtered_df.index, dtype=str)).astype(str).str.contains("Lab", case=False, na=False)
                | filtered_df.get("Resource_Type", pd.Series(index=filtered_df.index, dtype=str)).astype(str).str.contains("Lab", case=False, na=False)
            )
            filtered_df = filtered_df[lab_mask].copy()
            column = "Resource"
            label = "Select Laboratory"
            options = sorted(filtered_df[column].dropna().astype(str).unique()) if column in filtered_df.columns else []
        else:
            column = None
            options = []

        if column is not None:
            if options:
                selected_value = st.selectbox(
                    label, options, key=f"independent_timetable_entity_{view_type}"
                )
                filtered_df = filtered_df[filtered_df[column].astype(str) == selected_value].copy()
            else:
                st.warning(f"No available options for {view_type.lower()} view.")

        if not filtered_df.empty:
            sort_columns = [c for c in ["Day", "Start_Period", "Semester", "Section_ID"] if c in filtered_df.columns]
            if sort_columns:
                filtered_df = filtered_df.sort_values(sort_columns)

            st.metric("Sessions displayed", len(filtered_df))
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            st.download_button(
                "⬇️ Download displayed timetable as CSV",
                filtered_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{view_type.replace(' ', '_')}_timetable.csv",
                mime="text/csv",
                key="independent_timetable_download"
            )
        else:
            st.info("No timetable rows match this view.")

# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "Graph-Based Timetable Conflict Detection and Resolution System"
)
