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

        flags_section = lore.split("Weapons flags:")[1].split("Condition:")[0].strip().split()
        one_or_two_handed = "2H" if "two-handed" in flags_section else "1H"
        if "two-handed" in flags_section:
            flags_section.remove("two-handed")

        flag_1 = flags_section[0] if len(flags_section) > 0 else ""
        flag_2 = flags_section[1] if len(flags_section) > 1 else ""

        return {
            "Weapon": weapon_name,
            "Type": weapon_type,
            "Dam": damage,
            "Roll": roll,
            "Noun": "",
            "Flag 1": flag_1,
            "Flag 2": flag_2,
            "Other Notes": "",
            "Wt": weight,
            "1H/2H": one_or_two_handed
        }
    except Exception as e:
        st.error(f"Failed to parse weapon ID: {e}")
        return None

def show_weapons_page():
    st.header("⚔️ Weapons")

    if st.session_state.get("weapon_added"):
        for key in ["filter_types", "filter_handed", "filter_nouns", "filter_flags"]:
            st.session_state.pop(key, None)
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

        df = pd.DataFrame(data)
        df["Dam"] = pd.to_numeric(df["Dam"], errors="coerce")
        df["Wt"] = pd.to_numeric(df["Wt"], errors="coerce")

        # Add lowercased versions for case-insensitive sorting/filtering
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

        sort_column = st.selectbox("Sort by column:", [col for col in df.columns if col not in ["id"]], index=0)
        sort_direction = st.radio("Sort direction:", ["Ascending", "Descending"], horizontal=True)
        filtered_df = filtered_df.sort_values(
            by=sort_column,
            key=lambda col: col.str.lower() if col.dtype == "object" else col,
            ascending=(sort_direction == "Ascending")
        )

        filtered_df_with_id = filtered_df.copy()
        display_df = filtered_df.drop(columns=[col for col in filtered_df.columns if col == "id" or col.endswith("_lower")], errors="ignore")

        edited_df = st.data_editor(
            display_df.reset_index(drop=True),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="weapons_editor"
        )

        if st.button("💾 Save Changes"):
            changes = []
            for i, row in edited_df.iterrows():
                updated_row = row.to_dict()
                full_row = filtered_df_with_id.iloc[i].to_dict()
                if any(updated_row.get(k) != full_row.get(k) for k in updated_row):
                    row_id = full_row["id"]
                    update_payload = {k: v for k, v in updated_row.items() if not k.endswith("_lower")}
                    supabase.table("weapons").update(update_payload).eq("id", row_id).execute()
                    changes.append(update_payload)

            if changes:
                st.success(f"Saved {len(changes)} change(s) to the database.")
            else:
                st.info("No changes to save.")

        with st.expander("🗑️ Delete Weapon(s)"):
            if not filtered_df.empty:
                weapon_names = filtered_df["Weapon"].tolist()
                to_delete = st.multiselect("Select weapon(s) to delete:", weapon_names)

                if st.button("Confirm Delete"):
                    if to_delete:
                        for name in to_delete:
                            try:
                                supabase.table("weapons").delete().eq("Weapon", name).execute()
                            except Exception as e:
                                st.error(f"Failed to delete {name}.")
                                st.exception(e)
                        st.success(f"Deleted {len(to_delete)} weapon(s).")
                        st.rerun()
                    else:
                        st.warning("Please select at least one weapon to delete.")
            else:
                st.info("No weapons available to delete.")

    except Exception as e:
        st.error("Failed to load or update weapons from Supabase.")
        st.exception(e)
