import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_bestiary_page():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.markdown("## 🐲 Bestiary")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    @st.cache_data(ttl=60)
    def load_bestiary():
        response = supabase.table("bestiary").select("*").execute()
        return pd.DataFrame(response.data)

    df = load_bestiary()

    if not df.empty:
        df_display = df.copy()
        df_display["Lore"] = df_display["Lore"]

        st.subheader("📖 Bestiary Table")
        st.data_editor(
            df_display[["Name", "Level", "Zone", "Health", "Key Words", "Notes", "Lore"]],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            key="bestiary_editor",
            column_config={
                "Lore": st.column_config.TextColumn(
                    "Lore",
                    help="Full creature lore",
                    width="small"
                )
            }
        )
    else:
        st.info("No creatures found in the bestiary.")

    st.divider()
    st.subheader("➕ Add New Creature")

    with st.expander("Add New Creature", expanded=False):
        st.markdown("#### 📋 Paste Creaturelore")
        paste_input = st.text_area("Paste Creaturelore", height=150)

        st.markdown("#### 🛠️ Manually Enter Creature Information")
        new_name = st.text_input("Name")
        new_level = st.text_input("Level")
        new_zone = st.text_input("Zone")
        new_health = st.text_input("Health")
        new_keywords = st.text_input("Key Words")
        new_notes = st.text_input("Notes")

        if st.button("Add Creature"):
            if new_name and new_level and new_zone and new_health:
                supabase.table("bestiary").insert({
                    "Name": new_name,
                    "Level": new_level,
                    "Zone": new_zone,
                    "Health": new_health,
                    "Key Words": new_keywords,
                    "Notes": new_notes,
                    "Lore": paste_input or "Lore coming soon..."
                }).execute()
                st.success(f"Creature '{new_name}' added!")
                st.experimental_rerun()
            else:
                st.warning("Please fill in all required fields.")


    st.divider()
    st.subheader("✏️ Edit Creature")

    with st.expander("Edit Existing Creature", expanded=False):
        if not df.empty:
            creature_to_edit = st.selectbox("Choose Creature", options=df["Name"].tolist())
            selected_row = df[df["Name"] == creature_to_edit].iloc[0]

            edit_name = st.text_input("Name", value=selected_row["Name"])
            edit_level = st.text_input("Level", value=selected_row["Level"])
            edit_zone = st.text_input("Zone", value=selected_row["Zone"])
            edit_health = st.text_input("Health", value=selected_row["Health"])
            edit_keywords = st.text_input("Key Words", value=selected_row.get("Key Words", ""))
            edit_notes = st.text_input("Notes", value=selected_row.get("Notes", ""))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    supabase.table("bestiary").update({
                        "Name": edit_name,
                        "Level": edit_level,
                        "Zone": edit_zone,
                        "Health": edit_health,
                        "Key Words": edit_keywords,
                        "Notes": edit_notes
                    }).eq("id", selected_row["id"]).execute()
                    st.success(f"Creature '{edit_name}' updated!")
                    st.experimental_rerun()
            with col2:
                if st.button("Delete Creature"):
                    supabase.table("bestiary").delete().eq("id", selected_row["id"]).execute()
                    st.success(f"Creature '{selected_row['Name']}' deleted!")
                    st.experimental_rerun()
        else:
            st.info("No creatures available to edit.")
