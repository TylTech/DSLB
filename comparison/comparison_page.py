import streamlit as st
import pandas as pd
from shared.supabase_client import supabase
import streamlit.components.v1 as components
import re
import uuid

def sanitize_key(name):
    return re.sub(r'\W+', '_', name).lower()

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

# Replace your current format_copy_text_compact function with this one:

def format_copy_text_compact(df, filter_summary=None, sort_by=None):
    lines = []
    
    # Ultra-compact race abbreviations (3 chars)
    RACE_TINY_ABBR = {
        "Human": "Hum", "Goblin": "Gob", "Deep gnome": "DGn", "Shalonesti elf": "ShE",
        "Half elf": "HEl", "Dark elf": "DEl", "Wild elf": "W-E", "Hill dwarf": "HDw",
        "Mountain dwarf": "MDw", "Kender": "Ken", "Ogre": "Ogr", "Giant ogre": "GOg",
        "Half ogre": "HOg", "Minotaur": "Min", "Yinn": "Yin", "Dark dwarf": "DDw",
        "Tinker gnome": "TGn", "Sea elf": "SeE", "Black dragon": "Blk", "Blue dragon": "Blu",
        "Green dragon": "Grn", "Red dragon": "Red", "White dragon": "Wht", "Brass dragon": "Brs",
        "Bronze dragon": "Brz", "Copper dragon": "Cop", "Gold dragon": "Gld", "Silver dragon": "Slv",
        "Demon": "Dem", "Angel": "Ang", "Aurak draconian": "Aur", "Baaz draconian": "Baz",
        "Bozak draconian": "Boz", "Balanx": "Blx", "Felar": "Fel", "Wemic": "Wem",
        "Cloud giant": "ClG", "Frost giant": "FrG", "Fire giant": "FiG", "Bugbear": "Bug",
        "Hobgoblin": "Hob", "Mul": "Mul", "Gully dwarf": "GDw", "Centaur": "Cen", "Ariel": "Ari",
        "Pixie": "Pix", "Bakali": "Bak", "Brown dragon": "Brn", "Steel dragon": "Stl",
        "Troll": "Trl", "Orc": "Orc", "Arboren": "Arb", "Crystal dragon": "Cry",
        "Lagodae": "Lag", "Lepori": "Lep"
    }
    
    # Create a header line with proper spacing - using a monospace string format
    header_line = f"{'Rac':<4}{'Cls':<5}{'S':<3}{'I':<3}{'W':<3}{'D':<3}{'C':<3}{'Bo':<4}{'SD'}"


    lines.append(header_line)
    
    # Process each row with proper column alignment
    for _, row in df.iterrows():
        race = RACE_TINY_ABBR.get(row["Race"], row["Race"][:3])  # Use tiny abbr or first 3 chars
        clas = CLASS_ABBR.get(row["Class"], row["Class"][:3])[:3]  # Use class abbr or first 3 chars, limit to 3
        boost = str(row["Boost"])
        stats = {
            "S": str(row["STR"]), "I": str(row["INT"]), "W": str(row["WIS"]),
            "D": str(row["DEX"]), "C": str(row["CON"]), "SD": str(row["S+D"])
        }

        
        # Format each column with fixed width to ensure alignment
        # Format: each value has fixed width with spaces after
        line = f"{race:<4}{clas:<5}{stats['S']:<3}{stats['I']:<3}{stats['W']:<3}{stats['D']:<3}{stats['C']:<3}{boost:<4}{stats['SD']}"

        lines.append(line)
    
    # Add a blank line after the table
    lines.append("")
    
    # Add filter summary at the end if provided
    if filter_summary and sort_by:
        lines.append("Applied Filters:")
        
        # Format races
        race_filter = next((f for f in filter_summary if f.startswith("Race:")), None)
        if race_filter:
            race_text = race_filter.replace("Race: ", "").strip()
            if race_text.endswith("races"):
                count = race_text.split()[0]
                race_list_raw = [r.strip() for r in race_text.replace(f"{count} races", "").strip().split(",") if r.strip()]
                # Convert full race names to abbreviations in the list
                race_list = []
                for race_name in race_list_raw:
                    abbr = RACE_ABBR.get(race_name, race_name)
                    tiny_abbr = RACE_TINY_ABBR.get(race_name, race_name[:3])
                    if abbr != race_name:  # If there's an abbreviation
                        race_list.append(f"{race_name} ({tiny_abbr})")
                    else:
                        race_list.append(race_name)
                
                if race_list:  # If there's a list after the count
                    lines.append(f"{count} Races: {', '.join(race_list)}")
                else:
                    lines.append(f"{count} Races")
            else:
                # For individual races, also add abbreviations
                race_items = [r.strip() for r in race_text.split(",") if r.strip()]
                race_list = []
                for race_name in race_items:
                    abbr = RACE_ABBR.get(race_name, race_name)
                    tiny_abbr = RACE_TINY_ABBR.get(race_name, race_name[:3])
                    if abbr != race_name:  # If there's an abbreviation
                        race_list.append(f"{race_name} ({tiny_abbr})")
                    else:
                        race_list.append(race_name)
                lines.append(f"Races: {', '.join(race_list)}")
                
        # Format classes
        class_filter = next((f for f in filter_summary if f.startswith("Class:")), None)
        if class_filter:
            class_text = class_filter.replace("Class: ", "").strip()
            if class_text.endswith("classes"):
                count = class_text.split()[0]
                class_list = class_text.replace(f"{count} classes", "").strip()
                if class_list:  # If there's a list after the count
                    lines.append(f"{count} Classes: {class_list}")
                else:
                    lines.append(f"{count} Classes")
            else:
                lines.append(f"Classes: {class_text}")
                
        # Format boosts
        boost_filter = next((f for f in filter_summary if f.startswith("Boost:")), None)
        if boost_filter:
            boost_text = boost_filter.replace("Boost: ", "Boosts: ").strip()
            lines.append(boost_text)
            
        # Format stat minimums
        stat_filter = next((f for f in filter_summary if f.startswith("Min Stats:")), None)
        if stat_filter:
            # Replace the ≥ symbols with "over"
            stat_parts = stat_filter.replace("Min Stats: ", "").strip().split(", ")
            formatted_parts = []
            for part in stat_parts:
                stat_name, value = part.split(": ≥")
                formatted_parts.append(f"{stat_name} over {value}")
            
            lines.append(f"Min: {', '.join(formatted_parts)}")
            
        # Add sort info
        lines.append(f"Sorted by: {sort_by}")
    
    return "```text\n" + "\n".join(lines) + "\n```"

def show_comparison_page():
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def load_combos():
        """
        Load all race/class combinations from Supabase using pagination to ensure ALL records are fetched.
        """
        # Initialize an empty list to store all data
        all_data = []
        
        # Set pagination parameters
        page_size = 1000  # Fetch 1000 records at a time
        current_page = 0
        more_data = True
        
        # Show a progress indicator during initial load
        with st.spinner("Loading data from database..."):
            # Use pagination to fetch all records
            while more_data:
                # Calculate offset for pagination
                offset = current_page * page_size
                
                # Fetch data with pagination
                response = supabase.table("raceclass").select("*").range(offset, offset + page_size - 1).execute()
                
                # Get the data from the response
                page_data = response.data
                
                # If no data was returned, we've reached the end
                if not page_data:
                    more_data = False
                    break
                    
                # Add the data to our list
                all_data.extend(page_data)
                
                # Increment the page counter
                current_page += 1
                
                # Break if we got fewer records than the page size (we've reached the end)
                if len(page_data) < page_size:
                    more_data = False
        
        # Create a DataFrame from all the data
        df = pd.DataFrame(all_data)
        
        # Return the DataFrame
        return df

    # Load the data
    df = load_combos()
    
    # Display loading stats
    st.write(f"✅ Loaded {len(df)} rows")
    
    df["Boost"] = df["Boost"].replace("NO", "N/A")
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

    # Create a single clean row of filter controls (now 4 columns)
    colf1, colf2, colf3, colf4 = st.columns(4)

    # Race selection
    with colf1:
        with st.expander("Race Filter", expanded=False):
            all_races_selected = len(st.session_state.selected_races) == len(race_opts)
            select_all_races = st.checkbox("Select All Races", value=all_races_selected, key="select_all_races")
            if select_all_races and not all_races_selected:
                st.session_state.selected_races = race_opts.copy()
                st.rerun()
            elif not select_all_races and all_races_selected:
                st.session_state.selected_races = []
                st.rerun()
            
            # Replace the race_selections block with this:
            race_selections = {
                race: st.checkbox(race, value=(race in st.session_state.selected_races), key=f"race_{sanitize_key(race)}")
                for race in race_opts
            }

            st.session_state.selected_races = [race for race, selected in race_selections.items() if selected]
            if len(st.session_state.selected_races) == len(race_opts) and not select_all_races:
                st.rerun()
            elif len(st.session_state.selected_races) < len(race_opts) and select_all_races:
                st.rerun()

    # Class selection
    with colf2:
        with st.expander("Class Filter", expanded=False):
            all_classes_selected = len(st.session_state.selected_classes) == len(class_opts)
            select_all_classes = st.checkbox("Select All Classes", value=all_classes_selected, key="select_all_classes")
            if select_all_classes and not all_classes_selected:
                st.session_state.selected_classes = class_opts.copy()
                st.rerun()
            elif not select_all_classes and all_classes_selected:
                st.session_state.selected_classes = []
                st.rerun()
            class_selections = {
                cls: st.checkbox(cls, value=(cls in st.session_state.selected_classes), key=f"class_{cls}")
                for cls in class_opts
            }
            st.session_state.selected_classes = [cls for cls, selected in class_selections.items() if selected]
            if len(st.session_state.selected_classes) == len(class_opts) and not select_all_classes:
                st.rerun()
            elif len(st.session_state.selected_classes) < len(class_opts) and select_all_classes:
                st.rerun()

    # Boost selection
    with colf3:
        with st.expander("Boost Filter", expanded=False):
            all_boosts_selected = len(st.session_state.selected_boosts) == len(boost_opts)
            select_all_boosts = st.checkbox("Select All Boosts", value=all_boosts_selected, key="select_all_boosts")
            if select_all_boosts and not all_boosts_selected:
                st.session_state.selected_boosts = boost_opts.copy()
                st.rerun()
            elif not select_all_boosts and all_boosts_selected:
                st.session_state.selected_boosts = []
                st.rerun()
            boost_selections = {
                boost: st.checkbox(str(boost), value=(boost in st.session_state.selected_boosts), key=f"boost_{boost}")
                for boost in boost_opts
            }
            st.session_state.selected_boosts = [boost for boost, selected in boost_selections.items() if selected]
            if len(st.session_state.selected_boosts) == len(boost_opts) and not select_all_boosts:
                st.rerun()
            elif len(st.session_state.selected_boosts) < len(boost_opts) and select_all_boosts:
                st.rerun()

    # Gender selection
    with colf4:
        with st.expander("Gender", expanded=False):
            gender = st.radio("Gender", options=["Male", "Female"], horizontal=True, index=0, label_visibility="collapsed")

    # Clean left-aligned Clear Filters without ghost box
    clear_col = st.columns([3, 1, 1, 1])[0]
    with clear_col:
        if st.button("🧹 Clear All Filters", type="secondary", key="clear_filters_button"):
            st.session_state.selected_races = []
            st.session_state.selected_classes = []
            st.session_state.selected_boosts = []
            st.rerun()

    with st.expander("📊 Minimum Stat Requirements", expanded=False):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        st.session_state["min_str"] = col1.text_input("Strength", value=st.session_state.get("min_str", "0"))
        st.session_state["min_int"] = col2.text_input("Intelligence", value=st.session_state.get("min_int", "0"))
        st.session_state["min_wis"] = col3.text_input("Wisdom", value=st.session_state.get("min_wis", "0"))
        st.session_state["min_dex"] = col4.text_input("Dexterity", value=st.session_state.get("min_dex", "0"))
        st.session_state["min_con"] = col5.text_input("Constitution", value=st.session_state.get("min_con", "0"))
        st.session_state["min_sd"] = col6.text_input("S+D", value=st.session_state.get("min_sd", "0"))
        st.session_state["min_sdi"] = col7.text_input("S+D+I", value=st.session_state.get("min_sdi", "0"))

    col_order = ["Race", "Class", "STR", "INT", "WIS", "DEX", "CON", "Boost", "S+D", "S+D+I", "TOT"]

    if st.button("🚀 Generate Comparison", use_container_width=True, help="Apply all filters and show matching combinations"):
        filtered_df = df.copy()
        for col in ["STR", "INT", "WIS", "DEX", "CON"]:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce").fillna(0).astype(int)

        # Track applied filters for the summary
        filter_summary = []
        
        # Only apply filters if selections exist
        if st.session_state.selected_races:
            filtered_df = filtered_df[filtered_df["Race"].isin(st.session_state.selected_races)]
            if len(st.session_state.selected_races) < 5:  # Show individual races if not too many
                race_str = ", ".join(st.session_state.selected_races)
            else:
                race_str = f"{len(st.session_state.selected_races)} races"
            filter_summary.append(f"Race: {race_str}")
            
        if st.session_state.selected_classes:
            filtered_df = filtered_df[filtered_df["Class"].isin(st.session_state.selected_classes)]
            if len(st.session_state.selected_classes) < 5:  # Show individual classes if not too many
                class_str = ", ".join(st.session_state.selected_classes)
            else:
                class_str = f"{len(st.session_state.selected_classes)} classes"
            filter_summary.append(f"Class: {class_str}")
            
        if st.session_state.selected_boosts:
            filtered_df = filtered_df[filtered_df["Boost"].isin(st.session_state.selected_boosts)]
            boost_str = ", ".join(map(str, st.session_state.selected_boosts))
            filter_summary.append(f"Boost: {boost_str}")

        # Don't add gender to filter summary per requirements

        for i, row in filtered_df.iterrows():
            race = row["Race"]

            if race in ["Felar", "Lagodae", "Wemic", "Lepori"]:
                # These already include their bonus in the spreadsheet — do nothing
                continue
            else:
                # Apply gender-based stat bonus for all other races
                if gender == "Male":
                    filtered_df.at[i, "STR"] += 2
                else:
                    filtered_df.at[i, "WIS"] += 2


        def get_stat(key):
            val = st.session_state.get(key, "0")
            return int(val) if str(val).isdigit() else 0

        # Add stat minimums to filter summary if they're > 0
        min_stats = {
            "STR": get_stat("min_str"),
            "INT": get_stat("min_int"),
            "WIS": get_stat("min_wis"),
            "DEX": get_stat("min_dex"),
            "CON": get_stat("min_con"),
            "S+D": get_stat("min_sd"),
            "S+D+I": get_stat("min_sdi")
        }
        
        stat_filters = [f"{stat}: ≥{val}" for stat, val in min_stats.items() if val > 0]
        if stat_filters:
            filter_summary.append("Min Stats: " + ", ".join(stat_filters))

        filtered_df["TOT"] = filtered_df["STR"] + filtered_df["INT"] + filtered_df["WIS"] + filtered_df["DEX"] + filtered_df["CON"]
        filtered_df["S+D"] = filtered_df["STR"] + filtered_df["DEX"]
        filtered_df["S+D+I"] = filtered_df["STR"] + filtered_df["DEX"] + filtered_df["INT"]

        filtered_df = filtered_df[
            (filtered_df["STR"] >= min_stats["STR"]) &
            (filtered_df["INT"] >= min_stats["INT"]) &
            (filtered_df["WIS"] >= min_stats["WIS"]) &
            (filtered_df["DEX"] >= min_stats["DEX"]) &
            (filtered_df["CON"] >= min_stats["CON"]) &
            (filtered_df["S+D"] >= min_stats["S+D"]) &
            (filtered_df["S+D+I"] >= min_stats["S+D+I"])
        ]

        # Store filter summary in session state
        st.session_state["filter_summary"] = filter_summary
        st.session_state["comparison_df"] = filtered_df.reset_index(drop=True)
        st.rerun()

    # 🚨 Must live OUTSIDE the generate block so it stays after rerun
    if "comparison_df" in st.session_state and not st.session_state["comparison_df"].empty:
        df_view = st.session_state["comparison_df"].drop(columns=["id"], errors="ignore")

        # Sort options
        with st.expander("**Sort results:**", expanded=False):
            sort_col = st.radio(
                "", ["STR", "INT", "WIS", "DEX", "CON", "S+D", "S+D+I", "TOT"],
                index=5, horizontal=True  # Default is S+D (index 5)
            )
            df_view = df_view.sort_values(by=sort_col, ascending=False).reset_index(drop=True)
            # Store sorting info for summary
            st.session_state["sort_by"] = sort_col

        st.subheader("🗒 Matching Combinations")
        
        # Only display the number of combinations found
        st.write(f"Found {len(df_view)} matching combinations")
        
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

        # Use the compact format for copying with filter summary
        copy_text = format_copy_text_compact(
            df_view, 
            filter_summary=st.session_state.get("filter_summary", []),
            sort_by=st.session_state.get("sort_by", "TOT")
        )
        copy_id = f"copyText_{int(pd.Timestamp.now().timestamp() * 1000)}"

        components.html(f"""
            <div style="text-align: left; max-width: 400px; margin-left: 0;">
                <textarea id="{copy_id}" style="position:absolute; left:-1000px; top:-1000px;">{copy_text}</textarea>

                <button id="copyBtn_{copy_id}" onclick="
                    var textArea = document.getElementById('{copy_id}');
                    textArea.select();
                    if (document.execCommand('copy')) {{
                        window.parent.postMessage({{type: 'copied'}}, '*');
                        var btn = document.getElementById('copyBtn_{copy_id}');
                        btn.innerHTML = '✅ Copied!';
                        btn.style.backgroundColor = '#4CAF50';
                        btn.style.color = 'white';
                        btn.style.borderColor = '#4CAF50';
                        setTimeout(function() {{
                            btn.innerHTML = '📋 Copy to Clipboard';
                            btn.style.backgroundColor = '#f0f2f6';
                            btn.style.color = 'black';
                            btn.style.borderColor = '#ccc';
                        }}, 3000);
                    }}
                " style="
                    padding: 10px 18px;
                    margin: 8px 0;
                    background-color: #f0f2f6;
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                    width: 100%;
                    box-sizing: border-box;
                ">📋 Copy to Clipboard</button>

                <div id="copied-message-container" style="text-align: left;"></div>
            </div>

            <script>
                window.addEventListener('message', function(event) {{
                    if (event.data && event.data.type === 'copied') {{
                        const copiedEvent = new Event('streamlit:copied');
                        window.dispatchEvent(copiedEvent);
                    }}
                }});
            </script>
        """, height=140)

