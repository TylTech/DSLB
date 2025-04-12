import streamlit as st
import pandas as pd
from shared.supabase_client import supabase
import streamlit.components.v1 as components
import re

def format_directions_semicolon(directions):
    parts = []
    tokens = directions.split(",")
    for token in tokens:
        token = token.strip()
        if re.match(r"^\(?[a-zA-Z\s]+\)?$", token):
            if re.match(r"^\d+[neswud]+$", token):  # e.g., 2s
                count = int(token[:-1])
                dir_ = token[-1]
                parts.extend([dir_] * count)
            else:
                parts.append(token)
        elif re.match(r"^(\d+)([neswud]+)$", token):  # e.g., 3w
            count, dir_ = re.match(r"^(\d+)([neswud]+)$", token).groups()
            parts.extend([dir_] * int(count))
        else:
            parts.append(token)
    return ";".join(parts)

def strip_leading_articles(name):
    return re.sub(r"^(a |the )", "", name.strip(), flags=re.IGNORECASE)

def show_directions_page():
    # 🔝 Separate header and home button
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🧭 Directions")
    with col2:
        st.markdown("<div style='padding-top: 18px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 🔍 Now show the search box — in its own block to avoid stacking issues
    search_term = st.text_input(
        label="",
        placeholder="🔎 Search Areas",
        label_visibility="collapsed"
    ).strip().lower()

    try:
        response = supabase.table("directions").select("*").execute()
        data = response.data
        if not data:
            st.warning("No direction data found.")
            return

        df = pd.DataFrame(data)
        if "id" in df.columns:
            df = df.drop(columns=["id"])
        if "Gate Posts" in df.columns:
            df.rename(columns={"Gate Posts": "Gateposts"}, inplace=True)

        df["SortName"] = df["Area"].apply(strip_leading_articles)
        df = df.sort_values(by="SortName", key=lambda col: col.str.lower())

        with st.expander("🔍 Filter Areas"):
            col1, col2, col3 = st.columns(3)

            continents = sorted(df["Continent"].dropna().unique())
            continent_options = ["All"] + continents
            filter_continent = col1.selectbox(
                label="",
                options=continent_options,
                index=0,
                key="filter_continent",
                format_func=lambda x: "All Continents" if x == "All" else x
            )
            filter_level = col2.text_input(label="", placeholder="Level", key="filter_level")
            filter_align = col3.multiselect(
                label="",
                options=["Good", "Neutral", "Evil"],
                placeholder="Align",
                key="filter_align"
            )

           

        # 🌍 Apply continent filter
        if filter_continent != "All":
            df = df[df["Continent"] == filter_continent]

        if search_term:
            df = df[df["Area"].str.lower().str.contains(search_term)]

        # 🎯 Apply level filter
        if filter_level.isdigit():
            level_target = int(filter_level)

            def matches_level_range(level_text):
                match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", str(level_text))
                if match:
                    low, high = int(match.group(1)), int(match.group(2))
                    return low <= level_target <= high
                return False

            df = df[df["Levels"].apply(matches_level_range)]

        # 😇😈 Align filter
        if filter_align:
            df = df[df["Align"].apply(lambda align: any(f in align for f in filter_align))]





        st.subheader(f"🌍 Areas ({'All Continents' if filter_continent == 'All' else filter_continent})")

        scroll_html = """
        <div style='max-height: 700px; overflow-y: auto; padding-right: 10px; font-family: sans-serif; font-size: 14px;'>
        """

        for _, row in df.iterrows():
            starting_point = row["Starting Point"]
            clean_directions = row["Directions"]
            clean = f"From {starting_point}: {clean_directions}"
            zmud = format_directions_semicolon(clean_directions)
            mudrammer = zmud



            scroll_html += f"""
            <div style='padding: 6px 0 6px 6px; border-bottom: 1px solid #ccc; display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style="margin-bottom: 4px;">
                        <span style="font-weight: bold;">{row['Area']}</span>
                        <span style="padding-left: 10px;">({row['Levels']}; {row['Align']})</span>
                        <span style="padding-left: 10px;">
                            <button style="padding: 1px 5px; font-size: 0.9em;" onclick="navigator.clipboard.writeText(`{clean}`)">📋</button>
                            <button style="padding: 1px 5px; font-size: 0.9em;" onclick="navigator.clipboard.writeText(`{zmud}`)">⚡</button>
                            <button style="padding: 1px 5px; font-size: 0.9em;" onclick="navigator.clipboard.writeText(`{mudrammer}`)">📱</button>
                        </span>
                    </div>





                    <div style='padding-left: 2px;'>
                        From {row['Starting Point']}: <code>{row['Directions']}</code><br>
                        Gateposts: {row['Gateposts']}<br>

                    </div>


                </div>

            </div>
            """


        scroll_html += "</div>"
        components.html(scroll_html, height=700, scrolling=False)

        # ➕ Add New Area
        with st.expander("➕ Add New Area"):
            with st.form("add_area_form"):
                col1, col2 = st.columns(2)
                new_area = col1.text_input("Area")
                new_starting_point = col2.text_input("Starting Point")
                new_directions = st.text_area("Directions")
                new_gateposts = st.text_input("Gateposts")
                new_levels = st.text_input("Levels")
                new_align = st.multiselect("Align", ["Good", "Neutral", "Evil"])
                new_continent = st.selectbox("Continent", continents)

                if st.form_submit_button("➕ Add Area"):
                    new_entry = {
                        "Area": new_area,
                        "Starting Point": new_starting_point,
                        "Directions": new_directions,
                        "Gateposts": new_gateposts,
                        "Levels": new_levels,
                        "Align": ", ".join(new_align),  # Stored as comma-separated string
                        "Continent": new_continent
                    }
                    try:
                        supabase.table("directions").insert(new_entry).execute()
                        st.success(f"'{new_area}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to add new area.")
                        st.exception(e)

        # ✏️ Edit Existing Area
        with st.expander("✏️ Edit Existing Area", expanded=False):
            area_list = df["Area"].dropna().sort_values(key=lambda col: col.str.lower()).tolist()
            selected_area = st.selectbox("Choose Area", area_list)

            if selected_area:
                selected_row = df[df["Area"] == selected_area].iloc[0]
                current_align = selected_row["Align"].split(", ") if selected_row["Align"] else []

                with st.form("edit_area_form"):
                    col1, col2 = st.columns(2)
                    area = col1.text_input("Area", selected_row["Area"])
                    starting_point = col2.text_input("Starting Point", selected_row["Starting Point"])

                    directions = st.text_area("Directions", selected_row["Directions"])
                    gateposts = st.text_input("Gateposts", selected_row["Gateposts"])
                    levels = st.text_input("Levels", selected_row["Levels"])

                    current_align = selected_row["Align"].split(", ") if selected_row["Align"] else []
                    align = st.multiselect("Align", ["Good", "Neutral", "Evil"], default=current_align)

                    continent = st.selectbox("Continent", continents, index=continents.index(selected_row["Continent"]))

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            update_payload = {
                                "Area": area,
                                "Starting Point": starting_point,
                                "Directions": directions,
                                "Gateposts": gateposts,
                                "Levels": levels,
                                "Align": ", ".join(align),
                                "Continent": continent
                            }
                            try:
                                supabase.table("directions").update(update_payload).eq("Area", selected_area).execute()
                                st.success(f"'{area}' updated successfully!")
                                st.session_state["selected_weapon_override"] = area  # optional override if you're using it
                                st.rerun()
                            except Exception as e:
                                st.error("Failed to update area.")
                                st.exception(e)

                    with col2:
                        if st.form_submit_button("🗑️ Delete Area"):
                            try:
                                supabase.table("directions").delete().eq("Area", selected_area).execute()
                                st.success(f"'{selected_area}' deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error("Failed to delete area.")
                                st.exception(e)




    except Exception as e:
        st.error("Failed to load directions data from Supabase.")
        st.exception(e)
