import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_summons_page():
    st.header("✨ Summons")

    try:
        response = supabase.table("summons").select("*").execute()
        data = response.data

        if not data:
            st.warning("No summons data found.")
            return

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.drop(columns=["id"])

        continents = sorted(df["Continent"].dropna().unique())
        selected_continent = st.selectbox("🌍 Filter by Continent", continents)
        filtered_df = df[df["Continent"] == selected_continent].copy()

        st.subheader(f"📜 Summons in {selected_continent}")
        st.data_editor(
            filtered_df[["Summon", "Levels", "Hit Points", "Attributes", "Key Words"]],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="summons_editor"
        )

        st.subheader("➕ Add New Summon")
        with st.expander("Add New Entry"):
            with st.form("add_summon_form"):
                col1, col2 = st.columns(2)
                new_summon = col1.text_input("Summon")
                new_levels = col2.text_input("Levels")
                new_hit_points = st.text_input("Hit Points")
                new_attributes = st.text_input("Attributes")
                new_keywords = st.text_input("Key Words")
                new_continent = st.text_input("Continent")

                if st.form_submit_button("➕ Add Summon"):
                    supabase.table("summons").insert({
                        "Summon": new_summon,
                        "Levels": new_levels,
                        "Hit Points": new_hit_points,
                        "Attributes": new_attributes,
                        "Key Words": new_keywords,
                        "Continent": new_continent
                    }).execute()
                    st.success(f"{new_summon} added!")
                    st.rerun()
        
        st.subheader("✏️ Edit Existing Summon")
        editable_names = filtered_df["Summon"].dropna().sort_values().tolist()
        selected_summon = st.selectbox("Select summon to edit", editable_names)

        if selected_summon:
            row = df[df["Summon"] == selected_summon].iloc[0]
            with st.expander("Edit This Summon"):
                with st.form("edit_summon_form"):
                    col1, col2 = st.columns(2)
                    levels = col1.text_input("Levels", row["Levels"])
                    hit_points = col2.text_input("Hit Points", row["Hit Points"])
                    attributes = st.text_input("Attributes", row["Attributes"])
                    keywords = st.text_input("Key Words", row["Key Words"])

                    if st.form_submit_button("💾 Save Changes"):
                        supabase.table("summons").update({
                            "Levels": levels,
                            "Hit Points": hit_points,
                            "Attributes": attributes,
                            "Key Words": keywords
                        }).eq("Summon", selected_summon).execute()
                        st.success(f"{selected_summon} updated!")
                        st.rerun()

            with st.expander("🗑️ Delete This Summon"):
                if st.button("Delete Summon"):
                    supabase.table("summons").delete().eq("Summon", selected_summon).execute()
                    st.success(f"{selected_summon} deleted.")
                    st.rerun()

        

    except Exception as e:
        st.error("Failed to load summons data from Supabase.")
        st.exception(e)
