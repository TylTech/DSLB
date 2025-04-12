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

    search_term = st.text_input(
        label="",
        placeholder="🔎 Search Effects",
        label_visibility="collapsed"
    ).strip().lower()

    try:
        response = supabase.table("effects").select("*").execute()
        data = response.data

        if not data:
            st.warning("No effects data found.")
            return

        df = pd.DataFrame(data)
        df["Type"] = df["Type"].fillna("Unknown")

        df["Effects"] = df["Effects"].str.replace(r"\\n|/n", "\n", regex=True)
        df["Notes"] = df["Notes"].str.replace(r"\\n|/n", "\n", regex=True)

        with st.expander("🔍 Filter Effects", expanded=False):
            type_filter = st.radio("Effect type:", ["Both", "Spell", "Skill"], index=0, horizontal=True, label_visibility="collapsed")

        if type_filter != "Both":
            filtered_df = df[df["Type"].str.lower() == type_filter.lower()]
        else:
            filtered_df = df

        if search_term:
            filtered_df = filtered_df[
                filtered_df["Name"].str.lower().str.contains(search_term) |
                filtered_df["Effects"].str.lower().str.contains(search_term) |
                filtered_df["Notes"].str.lower().str.contains(search_term)
            ]

        st.subheader("📘 Effects Table")
        st.dataframe(
            filtered_df[["Name", "Effects", "Duration", "Notes", "Type"]],
            use_container_width=True,
            hide_index=True
        )

        with st.expander("➕ Add New Effect"):
            with st.form("add_effect_form"):
                col1, col2 = st.columns(2)
                new_name = col1.text_input("Name")
                new_type = col2.selectbox("Type", ["Spell", "Skill"])
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
                    st.toast(f"{new_name} added to effects list!", icon="✨")
                    st.rerun()

        with st.expander("✏️ Edit Existing Effect", expanded=False):
            editable_df = filtered_df.dropna(subset=["id"])
            editable_names = editable_df["Name"].tolist()
            selected_name = st.selectbox("Choose Entry", editable_names)

            if selected_name:
                row = editable_df[editable_df["Name"] == selected_name].iloc[0]
                with st.form("edit_effect_form"):
                    col1, col2 = st.columns(2)
                    name = col1.text_input("Name", row["Name"])
                    type_val = col2.selectbox("Type", ["Spell", "Skill"], index=0 if row["Type"] == "Spell" else 1)

                    effect = st.text_area("Effects", value=row["Effects"], height=100)
                    duration = st.text_input("Duration", value=row.get("Duration", ""))

                    notes = st.text_area("Notes", row["Notes"])

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            supabase.table("effects").update({
                                "Name": name,
                                "Effects": effect,
                                "Duration": duration,
                                "Notes": notes,
                                "Type": type_val
                            }).eq("id", row["id"]).execute()
                            st.success(f"'{name}' updated successfully!")
                            st.rerun()

                    with col2:
                        if st.form_submit_button("🗑️ Delete Effect"):
                            supabase.table("effects").delete().eq("id", row["id"]).execute()
                            st.success(f"'{name}' deleted.")
                            st.rerun()



    except Exception as e:
        st.error("Failed to load effects data from Supabase.")
        st.exception(e)
