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

        continents = sorted(df["Continent"].dropna().unique())
        selected_continent = st.selectbox("🌍 Filter by Continent", continents)
        filtered_df = df[df["Continent"] == selected_continent].copy()

        st.subheader(f"🚪 Gateposts in {selected_continent}")
        st.data_editor(
            filtered_df[["Gatepost", "Zone", "Levels", "Key Words"]],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="gatepost_editor"
        )

        with st.expander("➕ Add New Gatepost"):
            with st.form("add_gatepost_form"):
                col1, col2 = st.columns(2)
                new_gatepost = col1.text_input("Gatepost")
                new_zone = col2.text_input("Zone")
                new_levels = st.text_input("Levels")
                new_keywords = st.text_input("Key Words")
                new_continent = st.text_input("Continent")

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
        
        st.subheader("✏️ Edit Existing Gatepost")
        editable_names = filtered_df["Gatepost"].dropna().sort_values().tolist()
        selected_gatepost = st.selectbox("Select gatepost to edit", editable_names)

        if selected_gatepost:
            row = df[df["Gatepost"] == selected_gatepost].iloc[0]
            with st.expander("Edit This Gatepost"):
                with st.form("edit_gatepost_form"):
                    col1, col2 = st.columns(2)
                    zone = col1.text_input("Zone", row["Zone"])
                    levels = col2.text_input("Levels", row["Levels"])
                    keywords = st.text_input("Key Words", row["Key Words"])

                    if st.form_submit_button("💾 Save Changes"):
                        supabase.table("gateposts").update({
                            "Zone": zone,
                            "Levels": levels,
                            "Key Words": keywords
                        }).eq("Gatepost", selected_gatepost).execute()
                        st.success(f"{selected_gatepost} updated successfully!")
                        st.rerun()

            with st.expander("🗑️ Delete This Gatepost"):
                if st.button("Delete Gatepost"):
                    supabase.table("gateposts").delete().eq("Gatepost", selected_gatepost).execute()
                    st.success(f"{selected_gatepost} deleted.")
                    st.rerun()

        

    except Exception as e:
        st.error("Failed to load gateposts data from Supabase.")
        st.exception(e)
