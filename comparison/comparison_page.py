import streamlit as st
import pandas as pd
from shared.supabase_client import supabase
import streamlit.components.v1 as components

# Abbreviation Maps
CLASS_ABBR = {
    "Mage": "Mag", "Cleric": "Cle", "Thief": "Thi", "Warrior": "War", "Dragon": "Dra", "Bladesinger": "Bla",
    "Battlerager": "Bat", "Necromancer": "Nec", "Transmuter": "Tra", "Invoker": "Inv", "Paladin": "Pal",
    "Monk": "Mon", "Assassin": "Asn", "Crusader": "Cru", "Druid": "Dru", "Ranger": "Ran", "Barbarian": "Bar",
    "Shaman": "Sha", "Warlock": "Wlk", "Witch": "Wit", "Bard": "Brd", "Illusionist": "Ill", "Angel": "Ang",
    "Draconian": "Drc", "Citizen": "Ctz", "Swashbuckler": "Swb", "Demon": "Dem", "Balanx": "Bal", 
    "Anti-paladin": "Apl", "Jongleur": "Jng", "Enchantor": "Enc", "Enchanter": "Enc", "Charlatan": "Cha", "Priest": "Pri", 
    "Giant": "Gia", "Shadowknight": "Skn", "Bandit": "Bnd", "Runesmith": "Run", "Eldritch": "Eld", 
    "Battlemage": "Bmg", "Nightshade": "Nsh", "Skald": "Skd", "Armsman": "Arm", "Dragonslayer": "Slr", 
    "Pirate": "Pir", "Defiler": "Def", "Mentalist": "Mtl", "Confessor": "Cfr", "Shadowmage": "Smg",
    "Samurai": "Sam", "Wujen": "WuJ", "Brewmaster": "Brw", "Shukenja": "Shu", "Ninja": "Nin", "Ovate": "Ovt"
}

RACE_ABBR = {
    "Human": "Human", "Goblin": "Goblin", "Deep gnome": "DGnome", "Shalonesti elf": "S-Elf",
    "Half elf": "H-Elf", "Dark elf": "D-Elf", "Wild elf": "W-Elf", "Hill dwarf": "H-Dwf",
    "Mountain dwarf": "M-Dwf", "Kender": "Kender", "Ogre": "Ogre", "Giant ogre": "G-Ogre",
    "Half ogre": "H-Ogre", "Minotaur": "Minotr", "Yinn": "Yinn", "Dark dwarf": "D-Dwf",
    "Tinker gnome": "TGnome", "Sea elf": "Sea-E", "Black dragon": "Black", "Blue dragon": "Blue",
    "Green dragon": "Green", "Red dragon": "Red", "White dragon": "White", "Brass dragon": "Brass",
    "Bronze dragon": "Bronze", "Copper dragon": "Copper", "Gold dragon": "Gold", "Silver dragon": "Silver",
    "Demon": "Demon", "Angel": "Angel", "Aurak draconian": "Aurak", "Baaz draconian": "Baaz",
    "Bozak draconian": "Bozak", "Balanx": "Balanx", "Felar": "Felar", "Wemic": "Wemic",
    "Cloud giant": "Cloud", "Frost giant": "Frost", "Fire giant": "Fire", "Bugbear": "B-Bear",
    "Hobgoblin": "HobGob", "Mul": "Mul", "Gully dwarf": "Gully", "Centaur": "Cent", "Ariel": "Ariel",
    "Pixie": "Pixie", "Bakali": "Bakali", "Brown dragon": "Brown", "Steel dragon": "Steel",
    "Troll": "Troll", "Orc": "Orc", "Arboren": "Arbor", "Crystal dragon": "Crystl",
    "Lagodae": "Lagoda", "Lepori": "Lepori"
}

def show_comparison_page():
    @st.cache_data(ttl=60)
    def load_combos():
        response = supabase.table("raceclass").select("*").execute()
        return pd.DataFrame(response.data)

    df = load_combos()
    if df.empty:
        st.warning("No race/class data found.")
        return

    race_opts = sorted(df["Race"].dropna().unique().tolist())
    class_opts = sorted(df["Class"].dropna().unique().tolist())
    boost_opts = sorted(df["Boost"].dropna().unique().tolist())

    # Initialize session state for selections if not already present
    if "selected_races" not in st.session_state:
        st.session_state.selected_races = []
    if "selected_classes" not in st.session_state:
        st.session_state.selected_classes = []
    if "selected_boosts" not in st.session_state:
        st.session_state.selected_boosts = []

    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🧬 Race/Class Comparison")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Create a single clean row of filter controls
    colf1, colf2, colf3, colf4, colf5 = st.columns([3, 3, 3, 1.5, 1.5])
    
    # Race selection expander
    with colf1:
        with st.expander("Race Filter", expanded=False):
            # Determine if "Select All" should be checked
            all_races_selected = len(st.session_state.selected_races) == len(race_opts)
            
            # Select All checkbox at the top
            select_all_races = st.checkbox("Select All Races", value=all_races_selected, key="select_all_races")
            
            # If Select All state changed, update accordingly
            if select_all_races and not all_races_selected:
                # User just checked "Select All" - select all races
                st.session_state.selected_races = race_opts.copy()
                st.rerun()
            elif not select_all_races and all_races_selected:
                # User just unchecked "Select All" - deselect all races
                st.session_state.selected_races = []
                st.rerun()
            
            # Individual race checkboxes
            race_selections = {}
            for race in race_opts:
                race_checked = race in st.session_state.selected_races
                race_selections[race] = st.checkbox(race, value=race_checked, key=f"race_{race}")
            
            # Update selected races based on checkboxes
            st.session_state.selected_races = [race for race, selected in race_selections.items() if selected]
            
            # Rerun if Select All state needs to be updated
            if len(st.session_state.selected_races) == len(race_opts) and not select_all_races:
                st.rerun()
            elif len(st.session_state.selected_races) < len(race_opts) and select_all_races:
                st.rerun()
    
    # Class selection expander
    with colf2:
        with st.expander("Class Filter", expanded=False):
            # Determine if "Select All" should be checked
            all_classes_selected = len(st.session_state.selected_classes) == len(class_opts)
            
            # Select All checkbox at the top
            select_all_classes = st.checkbox("Select All Classes", value=all_classes_selected, key="select_all_classes")
            
            # If Select All state changed, update accordingly
            if select_all_classes and not all_classes_selected:
                st.session_state.selected_classes = class_opts.copy()
                st.rerun()
            elif not select_all_classes and all_classes_selected:
                st.session_state.selected_classes = []
                st.rerun()
            
            # Individual class checkboxes
            class_selections = {}
            for cls in class_opts:
                class_checked = cls in st.session_state.selected_classes
                class_selections[cls] = st.checkbox(cls, value=class_checked, key=f"class_{cls}")
            
            # Update selected classes based on checkboxes
            st.session_state.selected_classes = [cls for cls, selected in class_selections.items() if selected]
            
            # Rerun if Select All state needs to be updated
            if len(st.session_state.selected_classes) == len(class_opts) and not select_all_classes:
                st.rerun()
            elif len(st.session_state.selected_classes) < len(class_opts) and select_all_classes:
                st.rerun()
    
    # Boost selection expander
    with colf3:
        with st.expander("Boost Filter", expanded=False):
            # Determine if "Select All" should be checked
            all_boosts_selected = len(st.session_state.selected_boosts) == len(boost_opts)
            
            # Select All checkbox at the top
            select_all_boosts = st.checkbox("Select All Boosts", value=all_boosts_selected, key="select_all_boosts")
            
            # If Select All state changed, update accordingly
            if select_all_boosts and not all_boosts_selected:
                st.session_state.selected_boosts = boost_opts.copy()
                st.rerun()
            elif not select_all_boosts and all_boosts_selected:
                st.session_state.selected_boosts = []
                st.rerun()
            
            # Individual boost checkboxes
            boost_selections = {}
            for boost in boost_opts:
                boost_checked = boost in st.session_state.selected_boosts
                boost_selections[boost] = st.checkbox(str(boost), value=boost_checked, key=f"boost_{boost}")
            
            # Update selected boosts based on checkboxes
            st.session_state.selected_boosts = [boost for boost, selected in boost_selections.items() if selected]
            
            # Rerun if Select All state needs to be updated
            if len(st.session_state.selected_boosts) == len(boost_opts) and not select_all_boosts:
                st.rerun()
            elif len(st.session_state.selected_boosts) < len(boost_opts) and select_all_boosts:
                st.rerun()
    
    # Clear filters button - properly aligned with expanders
    with colf4:
        with st.expander("Clear Filters", expanded=False):
            if st.button("🧹 Clear All", type="secondary", use_container_width=True):
                st.session_state.selected_races = []
                st.session_state.selected_classes = []
                st.session_state.selected_boosts = []
                st.rerun()
    
    # Gender selection as expander to match the row alignment
    with colf5:
        with st.expander("Gender", expanded=False):
            gender = st.radio("", options=["Male", "Female"], horizontal=True, index=0)

    with st.expander("📊 Minimum Stat Requirements", expanded=False):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        st.session_state["min_str"] = col1.text_input("Strength", value=st.session_state.get("min_str", "0"))
        st.session_state["min_int"] = col2.text_input("Intelligence", value=st.session_state.get("min_int", "0"))
        st.session_state["min_wis"] = col3.text_input("Wisdom", value=st.session_state.get("min_wis", "0"))
        st.session_state["min_dex"] = col4.text_input("Dexterity", value=st.session_state.get("min_dex", "0"))
        st.session_state["min_con"] = col5.text_input("Constitution", value=st.session_state.get("min_con", "0"))
        st.session_state["min_sd"] = col6.text_input("S+D", value=st.session_state.get("min_sd", "0"))
        st.session_state["min_sdi"] = col7.text_input("S+D+I", value=st.session_state.get("min_sdi", "0"))

    col_order = ["Race", "Class", "Boost", "STR", "INT", "WIS", "DEX", "CON", "S+D", "S+D+I", "TOT"]

    def format_copy_text(df):
        headers = col_order
        lines = []
        header_line = "{:<8} {:<6} {:<5} {:<4} {:<4} {:<4} {:<4} {:<4} {:<5} {:<6} {:<4}".format(*headers)
        lines.append(header_line)
        for _, row in df.iterrows():
            race = RACE_ABBR.get(row["Race"], row["Race"])
            clas = CLASS_ABBR.get(row["Class"], row["Class"])
            boost = str(row["Boost"])
            stats = [str(row[col]) for col in headers[3:]]
            line = "{:<8} {:<6} {:<5} {:<4} {:<4} {:<4} {:<4} {:<4} {:<5} {:<6} {:<4}".format(race, clas, boost, *stats)
            lines.append(line)
        return "```text\n" + "\n".join(lines) + "\n```"

    if st.button("🚀 Generate Comparison", use_container_width=True, help="Apply all filters and show matching combinations"):
        filtered_df = df.copy()
        for col in ["STR", "INT", "WIS", "DEX", "CON"]:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce").fillna(0).astype(int)

        # Only apply filters if selections exist
        if st.session_state.selected_races:
            filtered_df = filtered_df[filtered_df["Race"].isin(st.session_state.selected_races)]
        if st.session_state.selected_classes:
            filtered_df = filtered_df[filtered_df["Class"].isin(st.session_state.selected_classes)]
        if st.session_state.selected_boosts:
            filtered_df = filtered_df[filtered_df["Boost"].isin(st.session_state.selected_boosts)]

        if gender == "Male":
            filtered_df["STR"] += 2
        else:
            filtered_df["WIS"] += 2

        def get_stat(key):
            val = st.session_state.get(key, "0")
            return int(val) if str(val).isdigit() else 0

        filtered_df["TOT"] = filtered_df["STR"] + filtered_df["INT"] + filtered_df["WIS"] + filtered_df["DEX"] + filtered_df["CON"]
        filtered_df["S+D"] = filtered_df["STR"] + filtered_df["DEX"]
        filtered_df["S+D+I"] = filtered_df["STR"] + filtered_df["DEX"] + filtered_df["INT"]

        filtered_df = filtered_df[
            (filtered_df["STR"] >= get_stat("min_str")) &
            (filtered_df["INT"] >= get_stat("min_int")) &
            (filtered_df["WIS"] >= get_stat("min_wis")) &
            (filtered_df["DEX"] >= get_stat("min_dex")) &
            (filtered_df["CON"] >= get_stat("min_con")) &
            (filtered_df["S+D"] >= get_stat("min_sd")) &
            (filtered_df["S+D+I"] >= get_stat("min_sdi"))
        ]

        st.session_state["comparison_df"] = filtered_df.reset_index(drop=True)
        st.rerun()

    # 🚨 Must live OUTSIDE the generate block so it stays after rerun
    if "comparison_df" in st.session_state and not st.session_state["comparison_df"].empty:
        df_view = st.session_state["comparison_df"].drop(columns=["id"], errors="ignore")

        with st.expander("**Sort results**)", expanded=False):
            sort_col = st.radio(
                "", ["STR", "INT", "WIS", "DEX", "CON", "S+D", "S+D+I", "TOT"],
                index=7, horizontal=True
            )
            df_view = df_view.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

        st.subheader("🗒 Matching Combinations")
        
        # Convert dataframe to HTML
        def generate_html_table(df, height_px):
            # Start the table with styling
            html = f"""
            <style>
                .race-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    font-size: 14px;
                }}
                .race-table thead {{
                    position: sticky;
                    top: 0;
                    z-index: 1;
                }}
                .race-table th {{
                    background-color: #f2f2f6;
                    color: #262730;
                    font-weight: bold;
                    text-align: center;
                    padding: 10px 8px;
                    border: 1px solid #e1e4e8;
                }}
                .race-table td {{
                    text-align: center;
                    padding: 8px;
                    border: 1px solid #e1e4e8;
                    background-color: white;
                }}
                .race-table tr:hover {{
                    background-color: #f0f2f6;
                }}
                .race-table tr:hover td {{
                    background-color: #f0f2f6;
                }}
                /* Column width adjustments */
                .race-table th:nth-child(1), .race-table td:nth-child(1),  /* Race */
                .race-table th:nth-child(2), .race-table td:nth-child(2) {{ /* Class */
                    min-width: 110px;
                }}
                .race-table th:nth-child(3), .race-table td:nth-child(3) {{ /* Boost */
                    min-width: 70px;
                }}
                .race-table th:nth-child(n+4), .race-table td:nth-child(n+4) {{ /* Stats */
                    min-width: 65px;
                }}
            </style>
            <div style="height: {height_px}px; overflow-y: auto; margin-bottom: 20px;">
            <table class="race-table">
                <thead>
                    <tr>
            """
            
            # Add headers
            for col in df.columns:
                html += f"<th>{col}</th>"
            
            html += """
                    </tr>
                </thead>
                <tbody>
            """
            
            # Add data rows
            for _, row in df.iterrows():
                html += "<tr>"
                for col in df.columns:
                    html += f"<td>{row[col]}</td>"
                html += "</tr>"
            
            html += """
                </tbody>
            </table>
            </div>
            """
            return html
        
        # Calculate dynamic height based on number of rows (with a maximum)
        row_height = 40  # Estimate of pixels per row
        header_height = 60  # Estimated header height
        min_height = 200  # Minimum height of table
        max_height = 750  # Maximum height of table
        
        # Calculate height based on content, within the min/max bounds
        table_height = max(min_height, min(len(df_view) * row_height + header_height, max_height))
        
        # Generate and display HTML table
        html_table = generate_html_table(df_view[col_order], table_height)
        st.markdown(html_table, unsafe_allow_html=True)

        copy_text = format_copy_text(df_view[col_order])

        if st.button("📋 Copy Results to Clipboard", type="secondary", key="copy_button"):
            random_id = f"copyTarget_{int(pd.Timestamp.now().timestamp() * 1000)}"
            components.html(f"""
                <textarea id="{random_id}" style="position:absolute; left:-1000px; top:-1000px;">{copy_text}</textarea>
                <script>
                async function copyToClipboard() {{
                    var textArea = document.getElementById("{random_id}");
                    textArea.select();
                    try {{
                        await navigator.clipboard.writeText(textArea.value);
                        return true;
                    }} catch (err) {{
                        try {{
                            return document.execCommand('copy');
                        }} catch (err) {{
                            return false;
                        }}
                    }}
                }}
                copyToClipboard();
                </script>
            """, height=0)
            st.markdown('<div style="color: green; font-weight: bold;">✅ Copied!</div>', unsafe_allow_html=True)