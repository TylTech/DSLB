import streamlit as st
from shared.supabase_client import supabase
import pandas as pd
import re

def parse_weapon_identification(lore):
    try:
        lines = lore.splitlines()
        full_text = " ".join(lines)

        name_match = re.search(r"Object\s+'([^']+)'", full_text)
        if not name_match:
            raise ValueError("Could not find weapon name in quotes.")
        weapon_name = name_match.group(1)
        key_words = weapon_name
        name_lower = weapon_name.lower()

        is_special_material = "arcanium" in name_lower or "fine alloy" in name_lower

        weapon_type_match = re.search(r"weapon type is (\w+)", full_text, re.IGNORECASE)
        weapon_type = weapon_type_match.group(1).capitalize() if weapon_type_match else ""

        weight_match = re.search(r"weight is (\d+)", full_text, re.IGNORECASE)
        level_match = re.search(r"level is (\d+)", full_text, re.IGNORECASE)
        weight = int(weight_match.group(1)) if weight_match else 0
        level = int(level_match.group(1)) if level_match else 0

        damage_match = re.search(r"damage is ([\dd]+) \(average (\d+)\)", full_text, re.IGNORECASE)
        roll = damage_match.group(1) if damage_match else ""
        damage = int(damage_match.group(2)) if damage_match else 0

        one_or_two_handed = "2H" if "two-handed" in full_text.lower() else "1H"

        flag_1 = ""
        flag_2 = ""
        if not is_special_material:
            flag_line = next((l for l in lines if "weapons flags" in l.lower()), "")
            flag_parts = flag_line.split(":", 1)[1].strip().split() if ":" in flag_line else []
            flag_1 = flag_parts[0].capitalize() if len(flag_parts) > 0 else ""
            flag_2 = flag_parts[1].capitalize() if len(flag_parts) > 1 else ""

        noun = "Physical" if is_special_material else ""

        return {
            "Weapon": weapon_name,
            "Key Words": key_words,
            "Type": weapon_type,
            "Dam": damage,
            "Roll": roll,
            "Noun": noun,
            "Flag 1": flag_1,
            "Flag 2": flag_2,
            "Notes": "",
            "Wt": weight,
            "1H/2H": one_or_two_handed,
            "Lvl": level
        }

    except Exception as e:
        st.error(f"Failed to parse weapon ID: {e}")
        return None


def show_weapons_page():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("⚔️ Weapons")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


    if "just_added_weapon" in st.session_state:
        st.toast(f"{st.session_state['just_added_weapon']} added to repository!", icon="🗡️")
        del st.session_state["just_added_weapon"]

    if st.session_state.get("weapon_added"):
        st.session_state["weapon_added"] = False

    try:
        response = supabase.table("weapons").select("*").execute()
        data = response.data
        if not data:
            st.warning("No weapons found in the database.")
            return

        df = pd.DataFrame(data).sort_values(by="Weapon", key=lambda col: col.str.lower())
        df.fillna("", inplace=True)
        df["Dam"] = pd.to_numeric(df["Dam"], errors="coerce")
        df["Wt"] = pd.to_numeric(df["Wt"], errors="coerce")

        filtered_df = df.copy()

        search_text = st.text_input("🔎 Search Weapon Name")
        df["Type_lower"] = df["Type"].str.lower()
        df["1H/2H_lower"] = df["1H/2H"].str.lower()
        df["Noun_lower"] = df["Noun"].str.lower()
        df["Flag 1_lower"] = df["Flag 1"].str.lower()
        df["Flag 2_lower"] = df["Flag 2"].str.lower()

        if search_text:
            filtered_df = filtered_df[filtered_df["Weapon"].str.contains(search_text, case=False, na=False)]

        with st.expander("🔍 Filter Weapons"):
            col1, col2, col3, col4 = st.columns(4)
            types = col1.multiselect("Type", sorted(df["Type"].dropna().str.capitalize().unique()), key="filter_types")
            one_h_two_h = col2.multiselect("1H/2H", sorted(df["1H/2H"].dropna().unique()), key="filter_handed")
            nouns = col3.multiselect("Noun", sorted(df["Noun"].dropna().str.capitalize().unique()), key="filter_nouns")
            flags = col4.multiselect(
                "Flags",
                sorted(pd.concat([df["Flag 1"], df["Flag 2"]]).dropna().str.capitalize().unique()),
                key="filter_flags"
            )

        if types:
            filtered_df = filtered_df[filtered_df["Type_lower"].isin([t.lower() for t in types])]
        if one_h_two_h:
            filtered_df = filtered_df[filtered_df["1H/2H_lower"].isin([t.lower() for t in one_h_two_h])]
        if nouns:
            filtered_df = filtered_df[filtered_df["Noun_lower"].isin([t.lower() for t in nouns])]
        if flags:
            lower_flags = [f.lower() for f in flags]
            filtered_df = filtered_df[
                filtered_df["Flag 1_lower"].isin(lower_flags) |
                filtered_df["Flag 2_lower"].isin(lower_flags)
            ]

        display_columns = ["Weapon", "Type", "Dam", "Wt", "Noun", "Flag 1", "Flag 2", "1H/2H", "Roll", "Lvl", "Key Words", "Notes"]
        st.subheader("🗡️ Weapon Arsenal")
        st.dataframe(filtered_df[display_columns], use_container_width=True, hide_index=True)

        st.subheader("➕ Add New Weapon")
        with st.expander("Paste Weapon Identification"):
            pasted_text = st.text_area("Paste the weapon identification text here")
            if st.button("Add Weapon"):
                weapon_data = parse_weapon_identification(pasted_text)
                if weapon_data:
                    try:
                        supabase.table("weapons").insert(weapon_data).execute()
                        st.session_state["just_added_weapon"] = weapon_data["Weapon"]
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to add weapon to database.")
                        st.exception(e)

        with st.expander("Manually Enter Weapon Information"):
            with st.form("manual_weapon_form"):
                col1, col2 = st.columns(2)
                weapon_name = col1.text_input("Weapon", key="manual_weapon_name")
                weapon_type = col2.text_input("Type", key="manual_weapon_type")

                col3, col4 = st.columns(2)
                dam = col3.number_input("Damage", min_value=0, step=1)
                wt = col4.number_input("Weight", min_value=0, step=1)

                col5, col6 = st.columns(2)
                roll = col5.text_input("Roll")
                lvl = col6.number_input("Level", min_value=0, step=1)

                key_words = st.text_input("Key Words", value=weapon_name, key="manual_key_words")
                noun = st.text_input("Noun")
                flag_1 = st.text_input("Flag 1")
                flag_2 = st.text_input("Flag 2")
                one_or_two_handed = st.selectbox("1H/2H", ["1H", "2H"])
                notes = st.text_area("Notes")

                submitted = st.form_submit_button("➕ Add Weapon")
                if submitted:
                    manual_data = {
                        "Weapon": weapon_name,
                        "Key Words": key_words,
                        "Type": weapon_type,
                        "Dam": dam,
                        "Roll": roll,
                        "Noun": noun,
                        "Flag 1": flag_1,
                        "Flag 2": flag_2,
                        "Notes": notes,
                        "Wt": wt,
                        "1H/2H": one_or_two_handed,
                        "Lvl": lvl
                    }
                    try:
                        supabase.table("weapons").insert(manual_data).execute()
                        st.session_state["just_added_weapon"] = weapon_name
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to add weapon manually.")
                        st.exception(e)

        st.subheader("✏️ Edit Weapon Entry")
        weapon_names = df["Weapon"].dropna().sort_values(key=lambda col: col.str.lower()).tolist()
        selected_weapon_name = st.selectbox("Select weapon to edit", weapon_names)

        if selected_weapon_name:
            match = df[df["Weapon"] == selected_weapon_name]
            if not match.empty:
                selected_row = match.iloc[0]

                with st.expander("Edit This Weapon"):
                    with st.form("edit_weapon_form"):
                        col1, col2 = st.columns(2)
                        weapon_name = col1.text_input("Weapon", selected_row["Weapon"])
                        weapon_type = col2.text_input("Type", selected_row["Type"])

                        col3, col4 = st.columns(2)
                        key_words = col3.text_input("Key Words", selected_row["Key Words"])
                        one_h_two_h = col4.selectbox("1H/2H", ["1H", "2H"], index=["1H", "2H"].index(selected_row["1H/2H"]))

                        col5, col6 = st.columns(2)
                        dam = col5.number_input("Damage", value=int(selected_row["Dam"]) if str(selected_row["Dam"]).strip().isdigit() else 0, step=1)
                        wt = col6.number_input("Weight", value=int(selected_row["Wt"]) if str(selected_row["Wt"]).strip().isdigit() else 0, step=1)

                        col7, col8 = st.columns(2)
                        roll = col7.text_input("Roll", selected_row["Roll"])
                        lvl = col8.number_input("Level", value=int(selected_row["Lvl"]) if str(selected_row["Lvl"]).strip().isdigit() else 0, step=1)

                        col9, col10 = st.columns(2)
                        noun = col9.text_input("Noun", selected_row["Noun"])
                        flag_1 = col10.text_input("Flag 1", selected_row["Flag 1"])

                        col11, col12 = st.columns(2)
                        flag_2 = col11.text_input("Flag 2", selected_row["Flag 2"])
                        notes = col12.text_input("Notes", selected_row["Notes"])

                        submitted = st.form_submit_button("💾 Save Changes")
                        if submitted:
                            update_payload = {
                                "Weapon": weapon_name,
                                "Key Words": key_words,
                                "Type": weapon_type,
                                "1H/2H": one_h_two_h,
                                "Dam": dam,
                                "Wt": wt,
                                "Roll": roll,
                                "Lvl": lvl,
                                "Noun": noun,
                                "Flag 1": flag_1,
                                "Flag 2": flag_2,
                                "Notes": notes
                            }
                            try:
                                supabase.table("weapons").update(update_payload).eq("id", selected_row["id"]).execute()
                                st.success(f"'{weapon_name}' updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error("Failed to update weapon.")
                                st.exception(e)

                with st.expander("🗑️ Delete This Weapon"):
                    if st.button("Delete Weapon"):
                        try:
                            supabase.table("weapons").delete().eq("id", selected_row["id"]).execute()
                            st.success(f"'{selected_weapon_name}' deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error("Failed to delete weapon.")
                            st.exception(e)

    except Exception as e:
        st.error("Failed to load or update weapons from Supabase.")
        st.exception(e)
