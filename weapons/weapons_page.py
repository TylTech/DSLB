import streamlit as st
from shared.supabase_client import supabase
import pandas as pd

def parse_weapon_identification(lore):
    try:
        weapon_name = lore.split("'")[1]
        weapon_type = lore.split("Weapon type is ")[1].split(".")[0]
        weight = int(lore.split("Weight is ")[1].split(",")[0])
        damage = int(lore.split("Damage is ")[1].split(" (average ")[1].split(")")[0])
        roll = lore.split("Damage is ")[1].split(" (")[0]

        # Default values
        one_or_two_handed = "1H"
        flag_1 = ""
        flag_2 = ""

        # Try to get weapon flags from the first line if present
        first_line = lore.splitlines()[0].lower()
        if "extra flags" in first_line:
            flags_section = first_line.split("extra flags")[1].replace(".", "").strip().split()
            if "two-handed" in flags_section:
                one_or_two_handed = "2H"
                flags_section.remove("two-handed")
            if len(flags_section) > 0:
                flag_1 = flags_section[0]
            if len(flags_section) > 1:
                flag_2 = flags_section[1]

        return {
            "Weapon": weapon_name,
            "Type": weapon_type,
            "Dam": damage,
            "Roll": roll,
            "Noun": "",
            "Flag 1": flag_1,
            "Flag 2": flag_2,
            "Notes": "",
            "Wt": weight,
            "1H/2H": one_or_two_handed
        }
    except Exception as e:
        st.error(f"Failed to parse weapon ID: {e}")
        return None

def show_weapons_page():
    st.header("⚔️ Weapons")

    if st.session_state.get("weapon_added"):
        st.session_state["weapon_added"] = False

    with st.expander("📋 Paste Weapon Identification"):
        pasted_text = st.text_area("Paste the weapon identification text here")
        if st.button("Add Weapon from Text"):
            weapon_data = parse_weapon_identification(pasted_text)
            if weapon_data:
                try:
                    supabase.table("weapons").insert(weapon_data).execute()
                    st.success(f"'{weapon_data['Weapon']}' added successfully!")
                    st.session_state["weapon_added"] = True
                    st.rerun()
                except Exception as e:
                    st.error("Failed to add weapon to database.")
                    st.exception(e)

    try:
        response = supabase.table("weapons").select("*").execute()
        data = response.data
        if not data:
            st.warning("No weapons found in the database.")
            return

        df = pd.DataFrame(data).sort_values(by="Weapon", key=lambda col: col.str.lower())
        df["Dam"] = pd.to_numeric(df["Dam"], errors="coerce")
        df["Wt"] = pd.to_numeric(df["Wt"], errors="coerce")

        df["Type_lower"] = df["Type"].str.lower()
        df["1H/2H_lower"] = df["1H/2H"].str.lower()
        df["Noun_lower"] = df["Noun"].str.lower()
        df["Flag 1_lower"] = df["Flag 1"].str.lower()
        df["Flag 2_lower"] = df["Flag 2"].str.lower()

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

        filtered_df = df.copy()
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

        display_columns = ["Weapon", "Type", "Dam", "Noun", "Flag 1", "Flag 2", "Wt", "1H/2H", "Roll", "Notes"]

        st.subheader("🗡️ Weapon Arsenal")
        st.data_editor(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True,
            disabled=True,
            column_config={
                "Weapon": st.column_config.TextColumn("Weapon", width="medium"),
                "Wt": st.column_config.NumberColumn("Wt", width="small"),
                "Dam": st.column_config.NumberColumn("Dam", width="small"),
                "1H/2H": st.column_config.TextColumn("1H/2H", width="small"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Roll": st.column_config.TextColumn("Roll", width="small"),
                "Noun": st.column_config.TextColumn("Noun", width="small"),
                "Flag 1": st.column_config.TextColumn("Flag 1", width="small"),
                "Flag 2": st.column_config.TextColumn("Flag 2", width="small"),
                "Notes": st.column_config.TextColumn("Notes", width="small"),
            }


        )

        st.subheader("🛠️ Edit Weapon Entry")
        weapon_names = filtered_df["Weapon"].dropna().sort_values(key=lambda col: col.str.lower()).tolist()
        selected_weapon_name = st.selectbox("Select weapon to edit", weapon_names)

        if selected_weapon_name:
            selected_row = df[df["Weapon"] == selected_weapon_name].iloc[0]

            with st.expander("✏️ Edit This Weapon"):
                with st.form("edit_weapon_form"):
                    col1, col2 = st.columns(2)
                    weapon_type = col1.text_input("Type", selected_row["Type"])
                    one_h_two_h = col2.selectbox("1H/2H", ["1H", "2H"], index=["1H", "2H"].index(selected_row["1H/2H"]))

                    col3, col4 = st.columns(2)
                    dam = col3.number_input("Damage", value=selected_row["Dam"], step=1)
                    wt = col4.number_input("Weight", value=selected_row["Wt"], step=1)

                    roll = st.text_input("Roll", selected_row["Roll"])
                    noun = st.text_input("Noun", selected_row["Noun"])
                    flag_1 = st.text_input("Flag 1", selected_row["Flag 1"])
                    flag_2 = st.text_input("Flag 2", selected_row["Flag 2"])
                    notes = st.text_area("Notes", selected_row["Notes"])

                    submitted = st.form_submit_button("💾 Save Changes")
                    if submitted:
                        update_payload = {
                            "Type": weapon_type,
                            "1H/2H": one_h_two_h,
                            "Dam": dam,
                            "Wt": wt,
                            "Roll": roll,
                            "Noun": noun,
                            "Flag 1": flag_1,
                            "Flag 2": flag_2,
                            "Notes": notes
                        }
                        try:
                            supabase.table("weapons").update(update_payload).eq("id", selected_row["id"]).execute()
                            st.success(f"'{selected_weapon_name}' updated successfully!")
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
