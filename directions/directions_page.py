import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_directions_page():
    st.header("🧭 Directions")
    st.markdown("✅ Using st.data_editor with copyable formatted column", unsafe_allow_html=True)

    try:
        # Load from Supabase
        response = supabase.table("directions").select("*").execute()
        data = response.data

        if not data:
            st.warning("No direction data found.")
            return

        df = pd.DataFrame(data)

        if "id" in df.columns:
            df = df.drop(columns=["id"])

        # Filter by continent
        continents = sorted(df["Continent"].dropna().unique())
        selected_continent = st.selectbox("🌍 Filter by Continent", continents)

        filtered_df = df[df["Continent"] == selected_continent].copy()

        # Create formatted copy column
        filtered_df["Copy"] = (
            filtered_df["Directions"]
            .str.replace(" ", "", regex=False)
            .str.replace(",", ";", regex=False)
        )

        display_columns = ["Area", "Starting Point", "Directions", "Copy", "Gate Posts", "Levels", "Align"]

        st.subheader(f"📍 Areas in {selected_continent}")
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

    except Exception as e:
        st.error("Failed to load directions data from Supabase.")
        st.exception(e)
