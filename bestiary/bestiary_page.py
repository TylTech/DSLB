import streamlit as st
import pandas as pd
from shared.supabase_client import supabase
import re

def strip_leading_articles(name):
    return re.sub(r'^(a|an|the)\s+', '', name.strip(), flags=re.IGNORECASE).lower()

def parse_creature_lore(lore):
    lines = lore.strip().split('\n')
    name = lines[0].split('Race:')[0].replace('Creature:', '').strip()
    health = None
    level = None
    for line in lines:
        if line.startswith('The base health of this creature is'):
            health = line.split('is')[-1].strip().replace('.', '')
        if 'This creature is upon the cycle of training' in line:
            match = re.search(r"'([^']+)'", line)
            if match:
                level = match.group(1)
    return {
        'Name': name,
        'Health': health or "",
        'Level': level or "",
        'Lore': lore
    }

def show_bestiary_page():
    # 🐲 Header + 🏰 Home
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🐲 Bestiary")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    search_query = st.text_input(
        label="",
        placeholder="🔎 Search Creatures",
        label_visibility="collapsed"
    ).strip().lower()

    def load_bestiary():
        response = supabase.table("bestiary").select("*").execute()
        return pd.DataFrame(response.data)

    df_raw = load_bestiary()
    df = df_raw.copy()
    df["Name_Sort"] = df["Name"].apply(strip_leading_articles)
    df = df.sort_values(by="Name_Sort")

    if search_query:
        df = df[df["Name"].str.lower().str.contains(search_query)]

    # 📖 Table
    if not df.empty:
        st.subheader("📖 Compendium of Creatures")
        st.data_editor(
            df[["Name", "Level", "Health", "Zone", "Notes", "Lore"]],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            column_config={
                "Lore": st.column_config.TextColumn("Lore", help="Full creature lore", width="small"),
                "Name": st.column_config.TextColumn("Name", disabled=True),
            },
            key="bestiary_editor"
        )
    else:
        st.info("No creatures found in the bestiary.")

    # ➕ Add Creature
    with st.expander("➕ Add New Creature", expanded=False):
        st.markdown("#### 📋 Paste Creaturelore")
        paste_input = st.text_area(label="", placeholder="📋 Paste creaturelore text here...", height=150, label_visibility="collapsed")

        if paste_input.strip():
            try:
                parsed_lore = parse_creature_lore(paste_input.strip())
                st.info(f"Parsed: {parsed_lore['Name']} (Level {parsed_lore['Level']}, {parsed_lore['Health']} HP)")
            except Exception:
                st.warning("Unable to parse creaturelore.")

        if st.button("➕ Add Creature", key="paste_add_btn"):
            if paste_input.strip():
                try:
                    result = parse_creature_lore(paste_input.strip())
                    result.update({
                        "Zone": "",
                        "Notes": ""
                    })
                    supabase.table("bestiary").insert(result).execute()
                    st.success(f"Creature '{result['Name']}' added from lore!")
                    st.rerun()
                except Exception as e:
                    st.error("Failed to parse and add creature.")
                    st.exception(e)
            else:
                st.warning("Please paste some lore first.")

        st.markdown("#### 🛠️ Manually Enter Creature Information")
        with st.form("add_creature_form"):
            col1, col2 = st.columns(2)
            new_name = col1.text_input("Name")
            new_level = col2.text_input("Level")

            col3, col4 = st.columns(2)
            new_health = col3.text_input("Health")
            new_zone = col4.text_input("Zone")

            new_notes = st.text_input("Notes")

            submitted = st.form_submit_button("➕ Add Creature")
            if submitted:
                if new_name and new_level and new_zone and new_health:
                    supabase.table("bestiary").insert({
                        "Name": new_name,
                        "Level": new_level,
                        "Zone": new_zone,
                        "Health": new_health,
                        "Notes": new_notes,
                        "Lore": "Lore coming soon..."
                    }).execute()
                    st.success(f"Creature '{new_name}' added!")
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields.")

    # ✏️ Edit Existing Creature
    if not df_raw.empty:
        with st.expander("✏️ Edit Existing Creature", expanded=False):
            creature_to_edit = st.selectbox("Choose Creature", options=df_raw["Name"].tolist())
            selected_row = df_raw[df_raw["Name"] == creature_to_edit].iloc[0]

            with st.form("edit_creature_form"):
                # Row 1: Name + Level
                col1, col2 = st.columns(2)
                edit_name = col1.text_input("Name", value=selected_row["Name"])
                edit_level = col2.text_input("Level", value=selected_row["Level"])

                # Row 2: Health + Zone
                col3, col4 = st.columns(2)
                edit_health = col3.text_input("Health", value=selected_row["Health"])
                edit_zone = col4.text_input("Zone", value=selected_row["Zone"])

                # Row 3: Notes
                edit_notes = st.text_input("Notes", value=selected_row.get("Notes", ""))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Save Changes"):
                        supabase.table("bestiary").update({
                            "Name": edit_name,
                            "Level": edit_level,
                            "Zone": edit_zone,
                            "Health": edit_health,
                            "Notes": edit_notes
                        }).eq("id", selected_row["id"]).execute()
                        st.success(f"Creature '{edit_name}' updated!")
                        st.rerun()

                with col2:
                    if st.form_submit_button("🗑️ Delete Creature"):
                        supabase.table("bestiary").delete().eq("id", selected_row["id"]).execute()
                        st.success(f"Creature '{selected_row['Name']}' deleted!")
                        st.rerun()
    else:
        st.info("No creatures available to edit.")
