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
    # Add this just after the function starts
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🧭 Directions")
    with col2:
        st.markdown("<div style='padding-top: 18px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)



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

        # 🔍 Search and Filter
        search_query = st.text_input(
            label="",
            placeholder="🔍 Search Areas",
            label_visibility="collapsed"
        ).strip().lower()

        # Build options list: placeholder first, then actual options
        continents = sorted(df["Continent"].dropna().unique())
        options_with_placeholder = ["🌍 Filter by Continent"] + ["All"] + continents

        selected_option = st.selectbox(
            label="",
            options=options_with_placeholder,
            index=0,
        )

        # Filter logic
        if selected_option == "🌍 Filter by Continent":
            selected_continent = "All"
        else:
            selected_continent = selected_option

        # Apply filter
        if selected_continent != "All":
            df = df[df["Continent"] == selected_continent]


        if search_query:
            df = df[df["Area"].str.lower().str.contains(search_query)]

        df["SortName"] = df["Area"].apply(strip_leading_articles)
        df = df.sort_values(by="SortName", key=lambda col: col.str.lower())

        st.subheader(f"🗺️ Areas ({'All Continents' if selected_continent == 'All' else selected_continent})")

        scroll_html = """
        <div style='max-height: 700px; overflow-y: auto; padding-right: 10px; font-family: sans-serif; font-size: 14px;'>
        """

        for _, row in df.iterrows():
            clean = row["Directions"]
            zmud = format_directions_semicolon(clean)
            mudrammer = zmud  # Same format

            scroll_html += f"""
            <div style='padding: 6px 0 6px 6px; border-bottom: 1px solid #ccc;'>
                <div style='padding-left: 4px; font-weight: bold;'>{row['Area']}</div>
                <div style='padding-left: 6px;'>
                    From {row['Starting Point']}: <code>{row['Directions']}</code><br>
                    Gateposts: {row['Gateposts']}<br>
                    Levels: {row['Levels']} &nbsp;&nbsp;&nbsp; Align: {row['Align']} &nbsp;&nbsp;&nbsp; Continent: {row['Continent']}<br>
                    <div style="margin: 1px 0;">
                        <button onclick="navigator.clipboard.writeText(`{clean}`)">🧽 Clean</button>
                        <button onclick="navigator.clipboard.writeText(`{zmud}`)">⚡ zMUD</button>
                        <button onclick="navigator.clipboard.writeText(`{mudrammer}`)">📱 Mudrammer</button>
                    </div>
                </div>
            </div>
            """

        scroll_html += "</div>"
        components.html(scroll_html, height=700, scrolling=False)

        # --- Add New Area ---

        with st.expander("➕ Add New Area"):
            with st.form("add_area_form"):
                col1, col2 = st.columns(2)
                new_area = col1.text_input("Area")
                new_starting_point = col2.text_input("Starting Point")
                new_directions = st.text_area("Directions")
                new_gateposts = st.text_input("Gateposts")
                new_levels = st.text_input("Levels")
                new_align = st.text_input("Align")
                new_continent = st.selectbox("Continent", continents[1:])

                if st.form_submit_button("➕ Add Area"):
                    new_entry = {
                        "Area": new_area,
                        "Starting Point": new_starting_point,
                        "Directions": new_directions,
                        "Gateposts": new_gateposts,
                        "Levels": new_levels,
                        "Align": new_align,
                        "Continent": new_continent
                    }
                    try:
                        supabase.table("directions").insert(new_entry).execute()
                        st.success(f"'{new_area}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error("Failed to add new area.")
                        st.exception(e)

        # --- Edit Existing Area ---


        with st.expander("✏️ Edit Existing Area", expanded=False):
            area_list = df["Area"].dropna().sort_values(key=lambda col: col.str.lower()).tolist()
            selected_area = st.selectbox("Choose Area", area_list)

            if selected_area:
                selected_row = df[df["Area"] == selected_area].iloc[0]

                with st.form("edit_area_form"):
                    col1, col2 = st.columns(2)
                    starting_point = col1.text_input("Starting Point", selected_row["Starting Point"])
                    directions = col2.text_area("Directions", selected_row["Directions"])
                    gateposts = st.text_input("Gateposts", selected_row["Gateposts"])
                    levels = st.text_input("Levels", selected_row["Levels"])
                    align = st.text_input("Align", selected_row["Align"])
                    continent_options = continents[1:]  # Remove placeholder
                    selected_continent_value = selected_row["Continent"]

                    # Default to first option if current value is missing
                    default_index = continent_options.index(selected_continent_value) if selected_continent_value in continent_options else 0

                    continent = st.selectbox("Continent", continent_options, index=default_index)


                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            update_payload = {
                                "Starting Point": starting_point,
                                "Directions": directions,
                                "Gateposts": gateposts,
                                "Levels": levels,
                                "Align": align,
                                "Continent": continent
                            }
                            try:
                                supabase.table("directions").update(update_payload).eq("Area", selected_area).execute()
                                st.success(f"'{selected_area}' updated successfully!")
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
