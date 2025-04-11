import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_summons_page():
    # ✨ Header + Home
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("✨ Summons")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 🌍 Load data + continent filter
    response = supabase.table("summons").select("*").execute()
    data = response.data
    if not data:
        st.warning("No summons data found.")
        return

    df = pd.DataFrame(data)
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    continents = sorted(df["Continent"].dropna().unique())
    continent_options = ["All"] + continents
    selected_continent = st.selectbox(
        label="🌍 Filter by Continent",
        options=continent_options,
        index=0,
        format_func=lambda x: "🌍 Filter by Continent" if x == "All" else x,
        key="summon_filter_continent",
        label_visibility="collapsed"
    )


    filtered_df = df if selected_continent == "All" else df[df["Continent"] == selected_continent]

    st.subheader(f"📜 Summons in {selected_continent if selected_continent != 'All' else 'All Continents'}")
    st.data_editor(
        filtered_df[["Summon", "Levels", "Hit Points", "Attributes", "Key Words"]],
        use_container_width=True,
        hide_index=True,
        disabled=True,
        key="summons_editor"
    )

    with st.expander("➕ Add New Summon"):
        with st.form("add_summon_form"):
            col1, col2 = st.columns(2)
            summon = col1.text_input("Summon")
            levels = col2.text_input("Levels")

            col3, col4 = st.columns(2)
            hit_points = col3.text_input("Hit Points")
            attributes = col4.text_input("Attributes")

            keywords = st.text_input("Key Words")
            continent = st.selectbox("Continent", continents)

            if st.form_submit_button("➕ Add Summon"):
                try:
                    supabase.table("summons").insert({
                        "Summon": summon,
                        "Levels": levels,
                        "Hit Points": hit_points,
                        "Attributes": attributes,
                        "Key Words": keywords,
                        "Continent": continent
                    }).execute()
                    st.success(f"{summon} added!")
                    st.rerun()
                except Exception as e:
                    st.error("Failed to add summon.")
                    st.exception(e)

    if not df.empty:
        summon_list = df["Summon"].dropna().sort_values().tolist()
        if "selected_summon_name" not in st.session_state:
            st.session_state["selected_summon_name"] = summon_list[0] if summon_list else ""

        with st.expander("✏️ Edit Existing Summon", expanded=False):
            selected_summon_name = st.selectbox(
                "Choose Summon",
                options=summon_list,
                key="selected_summon_name"
            )

            selected_row = df[df["Summon"] == selected_summon_name].iloc[0]

            with st.form("edit_summon_form"):
                col1, col2 = st.columns(2)
                levels = col1.text_input("Levels", selected_row["Levels"])
                hit_points = col2.text_input("Hit Points", selected_row["Hit Points"])

                col3, col4 = st.columns(2)
                attributes = col3.text_input("Attributes", selected_row["Attributes"])
                keywords = col4.text_input("Key Words", selected_row["Key Words"])

                continent = st.selectbox("Continent", continents, index=continents.index(selected_row["Continent"]))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        try:
                            supabase.table("summons").update({
                                "Levels": levels,
                                "Hit Points": hit_points,
                                "Attributes": attributes,
                                "Key Words": keywords,
                                "Continent": continent
                            }).eq("Summon", selected_summon_name).execute()
                            st.success(f"{selected_summon_name} updated!")
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to update summon.")
                            st.exception(e)
                with col2:
                    if st.form_submit_button("🗑️ Delete Summon"):
                        try:
                            supabase.table("summons").delete().eq("Summon", selected_summon_name).execute()
                            st.success(f"{selected_summon_name} deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to delete summon.")
                            st.exception(e)
