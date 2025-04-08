import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_effects_page():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("💫 Spell & Skill Effects")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


    try:
        response = supabase.table("effects").select("*").execute()
        data = response.data

        if not data:
            st.warning("No effects data found.")
            return

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.drop(columns=["id"])

        # Rename column for consistency
        df = df.rename(columns={"Spell or Skill": "Name"})
        df["Type"] = df["Type"].fillna("Unknown")

        # 🔥 Fix escaped newline characters for display
        df["Effects"] = df["Effects"].str.replace(r"\\n|/n", "\n", regex=True)
        df["Notes"] = df["Notes"].str.replace(r"\\n|/n", "\n", regex=True)

        # 🔀 Filter toggle: Spell / Skill / Both
        st.subheader("🔍 Filter by Type")
        type_filter = st.radio("Choose effect type:", ["Spell", "Skill", "Both"], horizontal=True)

        if type_filter != "Both":
            filtered_df = df[df["Type"].str.lower() == type_filter.lower()]
        else:
            filtered_df = df

        st.subheader("📘 Effects Table")
        st.dataframe(
            filtered_df[["Name", "Effects", "Duration", "Notes", "Type"]],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("➕ Add New Entry")
        with st.expander("Add New Entry"):
            with st.form("add_effect_form"):
                new_name = st.text_input("Name")
                new_type = st.selectbox("Type", ["Spell", "Skill"])
                new_effect = st.text_area("Effects")
                new_duration = st.text_input("Duration")
                new_notes = st.text_area("Notes")

                if st.form_submit_button("➕ Add Effect"):
                    supabase.table("effects").insert({
                        "Name": new_name,
                        "Type": new_type,
                        "Effects": new_effect,
                        "Duration": new_duration,
                        "Notes": new_notes
                    }).execute()
                    st.success(f"{new_name} added!")
                    st.rerun()

        st.subheader("✏️ Edit Existing Entry")
        editable_names = filtered_df["Name"].dropna().sort_values().tolist()
        selected_name = st.selectbox("Select entry to edit", editable_names)

        if selected_name:
            row = df[df["Name"] == selected_name].iloc[0]
            with st.expander("Edit This Entry"):
                with st.form("edit_effect_form"):
                    name = st.text_input("Name", row["Name"])
                    effect = st.text_area("Effects", row["Effects"])
                    duration = st.text_input("Duration", row.get("Duration", ""))
                    notes = st.text_area("Notes", row["Notes"])
                    type_val = st.selectbox("Type", ["Spell", "Skill"], index=0 if row["Type"] == "Spell" else 1)

                    if st.form_submit_button("💾 Save Changes"):
                        supabase.table("effects").update({
                            "Name": name,
                            "Effects": effect,
                            "Duration": duration,
                            "Notes": notes,
                            "Type": type_val
                        }).eq("Name", selected_name).execute()
                        st.success(f"{selected_name} updated successfully!")
                        st.rerun()

            with st.expander("🗑️ Delete This Entry"):
                if st.button("Delete Entry"):
                    supabase.table("effects").delete().eq("Name", selected_name).execute()
                    st.success(f"{selected_name} deleted.")
                    st.rerun()

    except Exception as e:
        st.error("Failed to load effects data from Supabase.")
        st.exception(e)
