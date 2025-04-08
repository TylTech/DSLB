import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_bestiary_page():
    st.markdown("## 🐲 Bestiary")

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
            df_display[["Name", "Level", "Zone", "Health", "Lore"]],
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

    with st.expander("Paste Creaturelore", expanded=False):
        paste_input = st.text_area("Paste Creaturelore", height=150)

    with st.expander("Manually Enter Creature Information", expanded=False):
        new_name = st.text_input("Name")
        new_level = st.text_input("Level")
        new_zone = st.text_input("Zone")
        new_health = st.text_input("Health")

        if st.button("Add Creature"):
            if new_name and new_level and new_zone and new_health:
                supabase.table("bestiary").insert({
                    "Name": new_name,
                    "Level": new_level,
                    "Zone": new_zone,
                    "Health": new_health,
                    "Lore": paste_input or "Lore coming soon..."
                }).execute()
                st.success(f"Creature '{new_name}' added!")
                st.experimental_rerun()
            else:
                st.warning("Please fill in all fields.")

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

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    supabase.table("bestiary").update({
                        "Name": edit_name,
                        "Level": edit_level,
                        "Zone": edit_zone,
                        "Health": edit_health
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
