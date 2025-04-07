import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_directions_page():
    st.header("🧭 Directions")

    try:
        response = supabase.table("directions").select("*").execute()
        data = response.data

        if not data:
            st.warning("No direction data found.")
            return

        df = pd.DataFrame(data)

        if "id" in df.columns:
            df = df.drop(columns=["id"])

        if "Gate Posts" in df.columns:
            df.rename(columns={"Gate Posts": "Gateposts"}, inplace=True)

        # Filter by continent
        continents = sorted(df["Continent"].dropna().unique())
        selected_continent = st.selectbox("🌍 Filter by Continent", continents)

        filtered_df = df[df["Continent"] == selected_continent].copy()

        # Search by area
        search_query = st.text_input("🔍 Search Areas", "").strip().lower()
        if search_query:
            filtered_df = filtered_df[filtered_df["Area"].str.lower().str.contains(search_query)]

        # 👉 Sort alphabetically by Area
        filtered_df = filtered_df.sort_values(by="Area", key=lambda col: col.str.lower())

        # Create formatted copy column
        filtered_df["Copy"] = (
            filtered_df["Directions"]
            .str.replace(" ", "", regex=False)
            .str.replace(",", ";", regex=False)
        )

        display_columns = ["Area", "Starting Point", "Directions", "Copy", "Gateposts", "Levels", "Align"]

        st.subheader(f"🗺️ Areas in {selected_continent}")
        st.data_editor(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="directions_editor",
            column_config={
                "Copy": st.column_config.TextColumn(
                    "Copy Dirs",
                    help="Formatted directions ready to copy",
                    width="small"
                )
            }
        )

        # --- Edit Existing Area ---
        st.subheader("✏️ Edit Existing Area")
        area_list = filtered_df["Area"].dropna().sort_values().unique().tolist()
        selected_area = st.selectbox("Select area to edit", area_list)

        if selected_area:
            selected_row = df[df["Area"] == selected_area].iloc[0]

            with st.expander("✏️ Edit This Area"):
                with st.form("edit_area_form"):
                    col1, col2 = st.columns(2)
                    starting_point = col1.text_input("Starting Point", selected_row["Starting Point"])
                    directions = col2.text_area("Directions", selected_row["Directions"])
                    gateposts = st.text_input("Gateposts", selected_row["Gateposts"])
                    levels = st.text_input("Levels", selected_row["Levels"])
                    align = st.text_input("Align", selected_row["Align"])
                    continent = st.selectbox("Continent", continents, index=continents.index(selected_row["Continent"]))

                    if st.form_submit_button("💾 Save Changes"):
                        update_payload = {
                            "Starting Point": starting_point,
                            "Directions": directions,
                            "Gateposts": gateposts,
                            "Levels": levels,
                            "Align": align,
                            "Continent": continent
                        }
                        try:
                            supabase.table("directions").update(update_payload).eq("Area", selected_area).execute()
                            st.success(f"'{selected_area}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to update area.")
                            st.exception(e)

            with st.expander("🗑️ Delete This Area"):
                if st.button("Delete Area"):
                    try:
                        supabase.table("directions").delete().eq("Area", selected_area).execute()
                        st.success(f"'{selected_area}' deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to delete area.")
                        st.exception(e)

        # --- Add New Area ---
        st.subheader("➕ Add New Area")
        with st.expander("Paste area info to add a new entry"):
            with st.form("add_area_form"):
                col1, col2 = st.columns(2)
                new_area = col1.text_input("Area")
                new_starting_point = col2.text_input("Starting Point")
                new_directions = st.text_area("Directions")
                new_gateposts = st.text_input("Gateposts")
                new_levels = st.text_input("Levels")
                new_align = st.text_input("Align")
                new_continent = st.selectbox("Continent", continents)

                if st.form_submit_button("➕ Add Area"):
                    new_entry = {
                        "Area": new_area,
                        "Starting Point": new_starting_point,
                        "Directions": new_directions,
                        "Gateposts": new_gateposts,
                        "Levels": new_levels,
                        "Align": new_align,
                        "Continent": new_continent
                    }
                    try:
                        supabase.table("directions").insert(new_entry).execute()
                        st.success(f"'{new_area}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to add new area.")
                        st.exception(e)

    except Exception as e:
        st.error("Failed to load directions data from Supabase.")
        st.exception(e)
