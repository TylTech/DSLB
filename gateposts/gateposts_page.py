import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_gateposts_page():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🌀 Gateposts")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    try:
        response = supabase.table("gateposts").select("*").execute()
        data = response.data
        if not data:
            st.warning("No gatepost data found.")
            return

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.drop(columns=["id"])

        directions_response = supabase.table("directions").select("Continent").execute()
        direction_data = directions_response.data
        continents = sorted(set(entry["Continent"] for entry in direction_data if "Continent" in entry and entry["Continent"]))

        continent_options = ["All"] + continents
        filter_continent = st.selectbox(
            label="",
            options=continent_options,
            index=0,
            key="filter_continent",
            format_func=lambda x: "🌍 Filter by Continent" if x == "All" else x
        )

        filtered_df = df.copy()
        if filter_continent != "All":
            filtered_df = filtered_df[filtered_df["Continent"] == filter_continent]


        st.subheader(f"🚪 Gateposts in {'All Continents' if filter_continent == 'All' else filter_continent}")
        st.data_editor(
            filtered_df[["Gatepost", "Zone", "Levels", "Key Words"]],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="gatepost_editor"
        )

        # ➕ Add New Gatepost
        with st.expander("➕ Add New Gatepost"):
            with st.form("add_gatepost_form"):
                col1, col2 = st.columns(2)
                new_gatepost = col1.text_input("Gatepost")
                new_zone = col2.text_input("Zone")
                col3, col4 = st.columns(2)
                new_levels = col3.text_input("Levels")
                new_keywords = col4.text_input("Key Words")
                new_continent = st.selectbox("Continent", continents)

                if st.form_submit_button("➕ Add Gatepost"):
                    supabase.table("gateposts").insert({
                        "Gatepost": new_gatepost,
                        "Zone": new_zone,
                        "Levels": new_levels,
                        "Key Words": new_keywords,
                        "Continent": new_continent
                    }).execute()
                    st.success(f"{new_gatepost} added!")
                    st.rerun()

        # ✏️ Edit Gatepost (matching other tabs)
        if not filtered_df.empty:
            with st.expander("✏️ Edit Existing Gatepost", expanded=False):
                gatepost_options = filtered_df["Gatepost"].dropna().sort_values().tolist()
                selected_gatepost = st.selectbox("Choose Gatepost", gatepost_options)

                if selected_gatepost:
                    selected_row = df[df["Gatepost"] == selected_gatepost].iloc[0]

                    with st.form("edit_gatepost_form"):
                        col1, col2 = st.columns(2)
                        zone = col1.text_input("Zone", selected_row["Zone"])
                        levels = col2.text_input("Levels", selected_row["Levels"])
                        key_words = st.text_input("Key Words", selected_row["Key Words"])
                        continent = st.selectbox("Continent", continents, index=continents.index(selected_row["Continent"]))

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save Changes"):
                                supabase.table("gateposts").update({
                                    "Zone": zone,
                                    "Levels": levels,
                                    "Key Words": key_words,
                                    "Continent": continent
                                }).eq("Gatepost", selected_gatepost).execute()
                                st.success(f"{selected_gatepost} updated successfully!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("🗑️ Delete Gatepost"):
                                supabase.table("gateposts").delete().eq("Gatepost", selected_gatepost).execute()
                                st.success(f"{selected_gatepost} deleted.")
                                st.rerun()
        else:
            st.info("No gateposts available to edit.")

    except Exception as e:
        st.error("Failed to load gateposts data from Supabase.")
        st.exception(e)
