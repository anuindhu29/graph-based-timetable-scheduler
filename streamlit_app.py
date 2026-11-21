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
