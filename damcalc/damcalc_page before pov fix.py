import streamlit as st
import re
import pandas as pd
import io
import streamlit.components.v1 as components

def show_damcalc_page():
    """Main page for the damage calculator interface."""
    # 📊 Header + 🏰 Home
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("📊 Damage Calculator")
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Brief description
    st.markdown("""
    Analyze your DSL combat logs to track damage done and taken. 
    Upload a log file or paste text directly from your client.
    """)
    
    # Tab for data input methods
    input_tab, options_tab = st.tabs(["📥 Input Combat Log", "⚙️ Analysis Options"])
    
    with input_tab:
        col1, col2 = st.columns(2)
        
        with col1:
            # Text area for pasting logs
            log_text = st.text_area(
                "Paste combat log here:",
                height=300,
                placeholder="Paste your combat log here..."
            )
        
        with col2:
            # File uploader
            uploaded_file = st.file_uploader("Or upload a log file:", type=["txt", "log"])
            
            # Character name input
            char_name = st.text_input(
                "Your character name:",
                placeholder="Enter your character name (replaces 'You' in logs)"
            )
            
            # Analyze button
            analyze_button = st.button("📊 Analyze Damage", type="primary", use_container_width=True)
            
    with options_tab:
        # Options similar to the original script
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Display Options")
            display_options = {
                "damage_done": st.checkbox("Damage Done by Source", value=True),
                "damage_taken": st.checkbox("Damage Taken by Target", value=True),
                "pvp_damage_done": st.checkbox("PvP Damage Done", value=True),
                "pvp_damage_taken": st.checkbox("PvP Damage Taken", value=True),
                "damage_types": st.checkbox("Damage by Type", value=True),
                "damage_details": st.checkbox("Damage Details", value=True),
                "hide_zero_damage": st.checkbox("Hide Zero Damage", value=True)
            }
        
        with col2:
            st.subheader("Export Options")
            export_format = st.radio(
                "Export Format:",
                ["CSV", "Excel", "Text", "Markdown"],
                index=0
            )

    # Process and analyze log data when button is clicked
    if analyze_button:
        # Process the log and store results in session state
        if log_text:
            log_content = log_text
        elif uploaded_file is not None:
            log_content = uploaded_file.getvalue().decode("utf-8")
        else:
            log_content = ""

        if log_content:
            player_name = char_name if char_name else "Player"
            st.session_state.damage_data = analyze_damage_log(log_content, player_name)
            st.session_state.char_name = player_name
        else:
            st.warning("Please paste a combat log or upload a log file to analyze.")

    damage_data = st.session_state.get("damage_data")
    char_name = st.session_state.get("char_name", "")

    # Display stored damage data if available
    if damage_data:
        display_damage_reports(damage_data, display_options, char_name)

        # 🧾 Export Buttons at Bottom
        st.markdown("---")
        st.subheader("📤 Export Damage Report")

        col1, _ = st.columns([1, 1])  # Export on left only

        # Get formatted data
        exported_text = export_damage_data(damage_data, "text", display_options, char_name)
        exported_csv = export_damage_data(damage_data, "csv", display_options, char_name)

        with col1:
            # Export to Excel (Streamlit native)
            st.download_button(
                label="📥 Export to Excel",
                data=exported_csv,
                file_name="damage_report.csv",
                mime="text/csv"
            )

            # Real clipboard export (matching button style)
            discord_friendly = f"```\n{exported_text.strip()}\n```"
            escaped = discord_friendly.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

            # Custom clipboard button styled like Streamlit's default button
            components.html(f"""
                <style>
                    .streamlit-button {{
                        all: unset;
                        display: inline-block;
                        font-family: inherit;
                        font-weight: 500;
                        line-height: 1.6;
                        user-select: none;
                        padding: 0.375rem 0.75rem;
                        font-size: 0.875rem;
                        border-radius: 0.5rem;
                        background-color: rgb(38, 39, 48);
                        color: white;
                        cursor: pointer;
                        border: 1px solid transparent;
                        text-align: center;
                        margin-top: 0.5rem;
                    }}
                    .streamlit-button:hover {{
                        background-color: rgb(64, 65, 78);
                    }}
                </style>
                <button class="streamlit-button" onclick="navigator.clipboard.writeText(`{escaped}`)">
                    📋 Copy to Clipboard
                </button>
            """, height=50)


# ----------------- Core Constants and Mappings -----------------

# Complete damage values mapping based on CMUD implementation (from DamMon_1.3.xml)
DAMAGE_VALUES = {
    # Standard damage verbs (lowercase)
    "scratches": 2.5, "grazes": 6.5, "hits": 10.5, "injures": 14.5,
    "wounds": 18.5, "mauls": 22.5, "decimates": 26.5, "devastates": 30.5,
    "maims": 34.5, "mutilates": 38.5, "disembowels": 42.5, "dismembers": 46.5,
    "massacres": 50.5, "mangles": 54.5, "demolishes": 58.5, 
    
    # Uppercase damage verbs (high damage)
    "DEMOLISHES": 58.5, "DEVASTATES": 68, "OBLITERATES": 88,
    "ANNIHILATES": 113, "ERADICATES": 138, "GHASTLY": 163, "HORRID": 188,
    "DREADFUL": 213, "HIDEOUS": 238, "INDESCRIBABLE": 263, "UNSPEAKABLE": 300,
    
    # Handle both forms with case-insensitive lookup
    "MUTILATES": 38.5, "DISEMBOWELS": 42.5, "DISMEMBERS": 46.5,
    "MASSACRES": 50.5, "MANGLES": 54.5
}

# Special formatting patterns from CMUD triggers
SPECIAL_DAMAGE_PATTERNS = [
    # Each tuple is (prefix, verb, suffix, damage)
    ("***", "DEMOLISHES", "***", 58.5),
    ("***", "DEVASTATES", "***", 68),
    ("===", "OBLITERATES", "===", 88),
    (">>>", "ANNIHILATES", "<<<", 113),
    ("<<<", "ERADICATES", ">>>", 138)
]

# Skip indicators based on CMUD's DMFakeCheck function
SKIP_INDICATORS = [
    "answers ", "ask ", "tells ", "tell ", "says ", 
    "gossips ", "yells ", "clans ", "quests ",
    "the group ", "OOC: ", "OOC Clan: ",
    "Bloodbath: ", "Kingdom: ", "radios ", "grats ",
    "shouts ", "[Newbie]: ", "auctions: ",
    "You have", "level!!", "some ", "flash of holy power erupts",
    "The bolt", "lightning bolt leaps",
    # Additional skip indicators from CMUD's secondary DMFakeCheck mode
    "holy smite", "mighty blow from", "hits the ground", 
    "transfer to", "his head", "her head", "DEAD."
]

# ----------------- Core Parsing Functions -----------------

def should_skip_line(line):
    """Determine if a line should be skipped (not combat related) - based on CMUD's DMFakeCheck."""
    for indicator in SKIP_INDICATORS:
        if indicator in line:
            return True
    
    # Additional check for possessive indicator - from CMUD code
    if "'s " not in line and "you" not in line.lower():
        return True
    
    return False

def clean_entity_name(name, player_name):
    """
    Clean and normalize entity names - based on CMUD's DMCleaner mode 1 and 2.
    This handles substituting 'You' with the player name and cleaning up entity references.
    """
    if not name:
        return ""

    name = name.strip()
    
    # Replace "You" with player name (case insensitive)
    if name.lower() == "you":
        return player_name
    
    # Remove tags and decorative characters
    name = re.sub(r'\[.*?\]', '', name)  # Remove bracketed content
    name = re.sub(r'<.*?>', '', name)    # Remove angle-bracketed content
    name = re.sub(r'\(.*?\)', '', name)  # Remove parenthesized content
    name = re.sub(r'{.*?}', '', name)    # Remove brace-enclosed content
    name = re.sub(r'[*=<>]+', '', name)  # Remove decorative characters
    
    # Handle possessive forms (based on CMUD DMCleaner mode 1)
    if "'s " in name:
        name = name.split("'s ")[0]
    
    # Strip punctuation based on CMUD DMCleaner mode 2
    name = name.replace("!", "").replace(".", "").replace("things to ", "")
    
    # Remove common prefixes 
    name = re.sub(r'^(a|an|the)\s+', '', name, flags=re.IGNORECASE)
    
    name = name.strip()
    if not name or name.lower() in ["a", "an", "him", "her", "the", "the ground"]:
        return None  # Filter out malformed names
    
    return name

def extract_known_players(log, player_name):
    """
    Extract known player names from the log by identifying capitalized possessives.
    Always includes the main player's name.
    """
    names = set()
    for line in log.splitlines():
        match = re.findall(r"\b([A-Z][a-z]+)'s\b", line)
        for name in match:
            if name.lower() != player_name.lower():
                names.add(name)
    names.add(player_name)
    return names


def extract_attack_type(source_text):
    """
    Extract attack type from source text - based on CMUD's DMCleaner mode 3.
    This handles cases like "Dhavi's pierce" -> "pierce"
    """
    # Special attack patterns
    if "draws life from" in source_text:
        return "life drain"
    if "is struck by lightning" in source_text:
        return "lightning strike"
    if "cut throat" in source_text:
        return "cut throat"
    
    # Remove location information and decorative characters
    source_text = re.sub(r'\[\s*[^\]]+\s*\]\s*', '', source_text)
    source_text = re.sub(r'[*=<>]+', '', source_text)
    
    # Extract everything after the possessive marker - CMUD's approach
    if "'s " in source_text:
        parts = source_text.split("'s ")
        if len(parts) > 1:
            attack_raw = parts[-1].strip()
            
            # Avoid using damage verbs as attack types
            damage_verbs = [verb.lower() for verb in DAMAGE_VALUES.keys()]
            attack_words = attack_raw.split()
            
            if attack_words and attack_words[0].lower() not in damage_verbs:
                return attack_words[0].lower()  # Return just the first word after possessive
    
    # Default to generic attack type
    return "attack"

def is_player_character(name, player_name, known_players=None):
    """
    Determine if a name is likely a player character.
    Uses a list of known players extracted from the log.
    """
    name = name.strip()
    if not name:
        return False

    if known_players:
        return name in known_players

    # fallback logic
    name_lower = name.lower()
    player_name_lower = player_name.strip().lower()

    if name_lower == player_name_lower:
        return True
    if " " in name_lower or re.match(r'^(a|an|the)\s', name_lower):
        return False
    if name[0].isupper() and not name.isupper():
        return True

    return False


def analyze_damage_log(log_content, player_name="Player"):
    known_players = extract_known_players(log_content, player_name)
    damage_data = {
        "damage_done": {}, "damage_taken": {}, "damage_details": {},
        "damage_types": {}, "pvp_damage_done": {}, "pvp_damage_taken": {}
    }


    for line in log_content.splitlines():
        line = line.strip()
        if not line or re.match(r'^\[\d+/\d+hp', line) or should_skip_line(line):
            continue

        # Strip location tags - like CMUD DMStrip function
        line = re.sub(r'\[\s*[^\]]+\s*\]\s*', '', line)

        # --- 1. Cut throat pattern (specific to CMUD) ---
        throat_match = re.search(r"(.*?)'s cut throat\s+<<<\s+([A-Z]+)\s+>>>\s+(.*?)(!|\.|$)", line)
        if throat_match:
            source_raw, verb, target_raw = map(str.strip, throat_match.groups()[:3])
            source = clean_entity_name(source_raw, player_name)
            target = clean_entity_name(target_raw, player_name)
            damage = DAMAGE_VALUES.get(verb.lower(), 0)
            record_damage(damage_data, source, target, damage, "cutthroat", player_name, line, known_players=known_players)
            continue

        # --- 2. Special formatting patterns (from CMUD triggers) ---
        special_pattern_matched = False
        for prefix, verb, suffix, damage_val in SPECIAL_DAMAGE_PATTERNS:
            pattern = fr"(.*?){re.escape(prefix)}\s*{verb}\s*{re.escape(suffix)}\s+(.*?)($|!|\.)"
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                source_raw = match.group(1).strip()
                target_raw = match.group(2).strip()
                
                # Clean source and target names
                source = clean_entity_name(source_raw, player_name)
                target = clean_entity_name(target_raw, player_name)
                
                # Extract attack type from source if possible
                attack_type = extract_attack_type(source_raw)
                if not attack_type or attack_type == "attack":
                    attack_type = verb.lower()  # Use the verb as fallback
                
                record_damage(damage_data, source, target, damage_val, attack_type, player_name, line, known_players=known_players)
                special_pattern_matched = True
                break
        if special_pattern_matched:
            continue

        # --- 3. Standard damage verb patterns ---
        # Try both uppercase and lowercase forms of damage verbs
        verb_matched = False
        for verb, damage_val in DAMAGE_VALUES.items():
            # Try possessive pattern first: "X's Y VERB Z"
            possessive_pattern = fr"(.*?)'s\s+([a-zA-Z\s]+?)\s+{verb}\s+(.*?)($|!|\.)"
            match = re.search(possessive_pattern, line, re.IGNORECASE)
            
            if match:
                source_raw = match.group(1).strip()
                attack_raw = match.group(2).strip()
                target_raw = match.group(3).strip()

                # Clean names
                source = clean_entity_name(source_raw, player_name)
                target = clean_entity_name(target_raw, player_name)

                # Get attack type from the possessive form
                attack_type = attack_raw.strip().lower()
                
                record_damage(damage_data, source, target, damage_val, attack_type, player_name, line, known_players=known_players)
                verb_matched = True
                break
            
            # If no possessive match, try regular pattern: "X VERB Y"
            regular_pattern = fr"^(.*?)\s+{verb}\s+(.*?)($|!|\.)"
            match = re.search(regular_pattern, line, re.IGNORECASE)
            
            if match:
                source_raw = match.group(1).strip()
                target_raw = match.group(2).strip()
                
                # Clean names
                words = source_raw.split()
                
                if len(words) > 1:
                    # This is likely "Entity attack_type" format
                    source_name = words[0]
                    attack_type = " ".join(words[1:]).lower()
                else:
                    source_name = source_raw
                    attack_type = "attack"  # Generic fallback
                
                source = clean_entity_name(source_name, player_name)
                target = clean_entity_name(target_raw, player_name)
                
                record_damage(damage_data, source, target, damage_val, attack_type, player_name, line, known_players=known_players)
                verb_matched = True
                break
        
        if verb_matched:
            continue

    # Calculate percentages and totals (like CMUD's DMSorter)
    calculate_percentages(damage_data)
    return damage_data

def record_damage(damage_data, source, target, damage_value, damage_type=None, player_name="", line="", known_players=None):
    """
    Record damage in the appropriate categories.
    Based on CMUD's DMAdd function implementation.
    """
    # Ensure all parameters have values
    if damage_type is None:
        damage_type = "attack"
    
    # Clean and standardize 
    damage_type = str(damage_type).strip().lower()
    
    # Clean entity names one final time
    source_clean = source if source else ""
    target_clean = target if target else ""
    
    # Skip invalid records
    if not source_clean or not target_clean:
        return

    # Handle special cases where target might be shorthand
    if target_clean.lower() in ["him", "her"]:
        target_clean = source_clean  # CMUD uses source as target in these cases

    # --- Record damage in various categories ---

    # 1. Total damage done (by source)
    damage_data["damage_done"].setdefault(source_clean, [0, 0])
    damage_data["damage_done"][source_clean][0] += damage_value
    damage_data["damage_done"][source_clean][1] += 1

    # 2. Total damage taken (by target)
    damage_data["damage_taken"].setdefault(target_clean, [0, 0])
    damage_data["damage_taken"][target_clean][0] += damage_value
    damage_data["damage_taken"][target_clean][1] += 1

    # 3. Damage details (source -> target)
    detail_key = f"{source_clean} -> {target_clean}"
    damage_data["damage_details"].setdefault(detail_key, [0, 0, damage_type])
    damage_data["damage_details"][detail_key][0] += damage_value
    damage_data["damage_details"][detail_key][1] += 1

    # 4. Damage by type (source -> attack type)
    type_key = f"{source_clean} -> {damage_type}"
    damage_data["damage_types"].setdefault(type_key, [0, 0])
    damage_data["damage_types"][type_key][0] += damage_value
    damage_data["damage_types"][type_key][1] += 1

    # 5. PvP tracking (if both source and target are players)
    source_is_player = is_player_character(source_clean, player_name, known_players)
    target_is_player = is_player_character(target_clean, player_name, known_players)

    if source_is_player and target_is_player:
        # PvP damage done
        damage_data["pvp_damage_done"].setdefault(source_clean, [0, 0])
        damage_data["pvp_damage_done"][source_clean][0] += damage_value
        damage_data["pvp_damage_done"][source_clean][1] += 1

        # PvP damage taken
        damage_data["pvp_damage_taken"].setdefault(target_clean, [0, 0])
        damage_data["pvp_damage_taken"][target_clean][0] += damage_value
        damage_data["pvp_damage_taken"][target_clean][1] += 1


def calculate_percentages(damage_data):
    """
    Calculate percentage contributions for damage statistics.
    Based on the CMUD DMSorter function.
    """
    # Process each category
    for category in damage_data:
        if not damage_data[category]:
            continue
            
        # Calculate total damage in this category
        total_damage = sum(data[0] for data in damage_data[category].values())
        if total_damage == 0:
            continue
            
        # Calculate percentage for each entry
        for key in damage_data[category]:
            if category == "damage_details":
                # damage_details has a different structure with damage type
                damage_type = damage_data[category][key][2]
                percentage = (damage_data[category][key][0] / total_damage) * 100
                
                # Calculate average damage per hit
                hits = damage_data[category][key][1]
                average = damage_data[category][key][0] / hits if hits > 0 else 0
                
                # Update with percentage and average
                damage_data[category][key] = [
                    damage_data[category][key][0],  # damage
                    hits,                          # hit count
                    damage_type,                   # damage type
                    percentage,                    # percentage
                    average                        # average damage
                ]
            else:
                # Other categories have a simpler structure
                percentage = (damage_data[category][key][0] / total_damage) * 100
                hits = damage_data[category][key][1]
                average = damage_data[category][key][0] / hits if hits > 0 else 0
                
                # Add percentage and average to existing list
                damage_data[category][key].extend([percentage, average])


# ----------------- Display and Export Functions -----------------

def display_damage_reports(damage_data, display_options, player_name):
    """Display the six core CMUD-style damage tables."""

    # 1. TOTAL DAMAGE DONE
    st.subheader("🗡️ Total Damage Done")
    if damage_data["damage_done"]:
        rows = []
        for source, values in damage_data["damage_done"].items():
            rows.append({
                "Source": source,
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "total-damage-done")

    # 2. TOTAL DAMAGE TAKEN
    st.subheader("🛡️ Total Damage Taken")
    if damage_data["damage_taken"]:
        rows = []
        for target, values in damage_data["damage_taken"].items():
            rows.append({
                "Target": target,
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "total-damage-taken")

    # 3. PVP DAMAGE DONE
    st.subheader("⚔️ PvP Damage Done")
    if damage_data["pvp_damage_done"]:
        rows = []
        for source, values in damage_data["pvp_damage_done"].items():
            rows.append({
                "Source": source,
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "pvp-damage-done")
    else:
        st.info("No PvP damage done detected.")

    # 4. PVP DAMAGE TAKEN
    st.subheader("🛡️ PvP Damage Taken")
    if damage_data["pvp_damage_taken"]:
        rows = []
        for target, values in damage_data["pvp_damage_taken"].items():
            rows.append({
                "Target": target,
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "pvp-damage-taken")
    else:
        st.info("No PvP damage taken detected.")

    # 5. DAMAGE TYPES
    st.subheader("🔥 Damage Types")
    if damage_data["damage_types"]:
        rows = []
        for key, values in damage_data["damage_types"].items():
            source, dmg_type = key.split(" -> ")
            rows.append({
                "Source": source,
                "Type": dmg_type.title(),
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "damage-types")

    # 6. DAMAGE DETAILS
    st.subheader("📝 Damage Details")
    if damage_data["damage_details"]:
        rows = []
        for key, values in damage_data["damage_details"].items():
            source, target = key.split(" -> ")
            rows.append({
                "Source": source,
                "Target": target,
                "Hits": values[1],
                "Damage": round(values[0], 1),
                "Avg Dam": round(values[4], 1) if len(values) > 4 else 0,
                "%": f"{values[3]:.1f}%" if len(values) > 3 else "0.0%"
            })
        df = pd.DataFrame(rows).sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df, "damage-details")



def display_sortable_table(df, table_id):
    """
    Display a DataFrame as a nicely styled and sortable HTML table.
    
    Args:
        df: The DataFrame to display
        table_id: A unique ID for the table
    """
    # Calculate dynamic height based on number of rows (with a maximum)
    row_height = 40  # Estimate of pixels per row
    header_height = 60  # Estimated header height
    min_height = 200  # Minimum height of table
    max_height = 550  # Maximum height of table
    
    # Calculate height based on content, within the min/max bounds
    table_height = max(min_height, min(len(df) * row_height + header_height, max_height))
    
    # Generate and display HTML table
    html_table = generate_sortable_table(df, table_height, table_id)
    st.markdown(html_table, unsafe_allow_html=True)


def generate_sortable_table(df, height_px, table_id):
    """
    Generate a sortable HTML table with styling.
    
    Args:
        df: DataFrame containing the data to display
        height_px: Height of the table in pixels
        table_id: A unique ID for the table
    
    Returns:
        HTML string with the styled and sortable table
    """
    # Start with table styling
    html = f"""
    <style>
        .{table_id} {{
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 14px;
        }}
        .{table_id} thead {{
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        .{table_id} th {{
            background-color: #f2f2f6;
            color: #262730;
            font-weight: bold;
            text-align: center;
            padding: 10px 8px;
            border: 1px solid #e1e4e8;
            cursor: pointer;
        }}
        .{table_id} th:hover {{
            background-color: #e0e0e6;
        }}
        .{table_id} th.asc:after {{
            content: " ▲";
        }}
        .{table_id} th.desc:after {{
            content: " ▼";
        }}
        .{table_id} td {{
            text-align: center;
            padding: 8px;
            border: 1px solid #e1e4e8;
            background-color: white;
        }}
        .{table_id} tr:hover {{
            background-color: #f0f2f6;
        }}
        .{table_id} tr:hover td {{
            background-color: #f0f2f6;
        }}
        /* Column width adjustments */
        .{table_id} th:nth-child(1), .{table_id} td:nth-child(1) {{ /* First column (Source/Target) */
            min-width: 120px;
            text-align: left;
        }}
        .{table_id} td:nth-child(1) {{
            text-align: left;
        }}
        .{table_id} th:nth-child(2), .{table_id} td:nth-child(2) {{ /* Second column (Type/Damage) */
            min-width: 100px;
        }}
        .{table_id} th:nth-child(n+3), .{table_id} td:nth-child(n+3) {{ /* Numerical values */
            min-width: 65px;
        }}
    </style>
    <div style="height: {height_px}px; overflow-y: auto; margin-bottom: 20px;">
    <table class="{table_id}" id="{table_id}">
        <thead>
            <tr>
    """
    
    # Add headers with sorting functionality
    col_types = []  # To track column data types (text vs. number)
    for i, col in enumerate(df.columns):
        # Determine if column is numeric or text for proper sorting
        if col in ["Damage", "Hits", "Average"]:
            col_type = "number"
        elif col == "%":
            # Special case for percentage column - we'll parse it as numeric
            col_type = "percent"
        else:
            col_type = "text"
        col_types.append(col_type)
        
        html += f'<th data-col="{i}" data-type="{col_type}">{col}</th>'
    
    html += """
            </tr>
        </thead>
        <tbody>
    """
    
    # Add data rows
    for _, row in df.iterrows():
        html += "<tr>"
        for i, col in enumerate(df.columns):
            # Left-align the first column, center-align the rest
            alignment = "text-align: left;" if i == 0 else ""
            html += f"<td style='{alignment}'>{row[col]}</td>"
        html += "</tr>"
    
    html += """
        </tbody>
    </table>
    </div>
    <script>
        // Add sorting functionality to the table
        document.addEventListener('DOMContentLoaded', function() {
            const table = document.getElementById('""" + table_id + """');
            const headers = table.querySelectorAll('th');
            
            headers.forEach(header => {
                header.addEventListener('click', () => {
                    const colIndex = parseInt(header.dataset.col);
                    const colType = header.dataset.type;
                    const tbody = table.querySelector('tbody');
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    
                    // Determine sort direction
                    const isAscending = header.classList.contains('desc') || !header.classList.contains('asc');
                    
                    // Reset all headers
                    headers.forEach(h => {
                        h.classList.remove('asc', 'desc');
                    });
                    
                    // Set new sort direction
                    header.classList.add(isAscending ? 'asc' : 'desc');
                    
                    // Sort the rows
                    rows.sort((rowA, rowB) => {
                        const cellA = rowA.querySelectorAll('td')[colIndex].textContent.trim();
                        const cellB = rowB.querySelectorAll('td')[colIndex].textContent.trim();
                        
                        let valueA, valueB;
                        
                        if (colType === 'number') {
                            // Parse as numbers
                            valueA = parseFloat(cellA) || 0;
                            valueB = parseFloat(cellB) || 0;
                        } else if (colType === 'percent') {
                            // Parse percentages by removing % and converting to number
                            valueA = parseFloat(cellA.replace('%', '')) || 0;
                            valueB = parseFloat(cellB.replace('%', '')) || 0;
                        } else {
                            // Case-insensitive string comparison
                            valueA = cellA.toLowerCase();
                            valueB = cellB.toLowerCase();
                        }
                        
                        if (valueA < valueB) {
                            return isAscending ? -1 : 1;
                        }
                        if (valueA > valueB) {
                            return isAscending ? 1 : -1;
                        }
                        return 0;
                    });
                    
                    // Reorder the rows
                    rows.forEach(row => tbody.appendChild(row));
                });
            });
        });
    </script>
    """
    return html

def export_damage_data(damage_data, export_format, display_options, player_name=""):
    if not damage_data:
        return ""

    def format_row(cols, widths, row_num=None):
        if row_num is not None:
            row = f"{row_num:03d}  "
        else:
            row = "---  "
        row += "  ".join(str(col).ljust(width) for col, width in zip(cols, widths))
        return row

    def build_text_section(title, columns, entries, total_stats=None):
        lines = []
        header = title.upper()
        lines.append("=" * (len(header) + 40) + header + "=" * 40)
        lines.append(format_row(columns, col_widths))
        lines.append(format_row(["--" + "-" * (w - 2) for w in col_widths], col_widths))
        for i, entry in enumerate(entries, 1):
            lines.append(format_row(entry, col_widths, i))
        lines.append(format_row(["--" + "-" * (w - 2) for w in col_widths], col_widths))
        if total_stats:
            hits, dmg, avg = total_stats
            lines.append("     " + "TOTALS".rjust(45) + f"  {hits}  {dmg:,}      {avg}")
        lines.append("")
        return lines

    output = []
    col_widths = [55, 5, 12, 8, 5]

    # CSV & Excel format
    if export_format.lower() in ["csv", "excel"]:
        def write_csv_section(title, header, data):
            lines = [title.upper(), ",".join(header)]
            lines += [",".join(str(col) for col in row) for row in data]
            lines.append("")
            return lines

        # Helper for sorting
        def sort_dict(data):
            return sorted(data.items(), key=lambda x: x[1][0], reverse=True)

        # Damage Done
        if display_options.get("damage_done", True):
            data = []
            for k, v in sort_dict(damage_data["damage_done"]):
                data.append([k, v[1], round(v[0], 1), round(v[3], 1), f"{v[2]:.1f}%"])
            output += write_csv_section("Total Damage Done", ["Source", "Hits", "Damage", "Avg Dam", "%"], data)

        # Damage Taken
        if display_options.get("damage_taken", True):
            data = []
            for k, v in sort_dict(damage_data["damage_taken"]):
                data.append([k, v[1], round(v[0], 1), round(v[3], 1), f"{v[2]:.1f}%"])
            output += write_csv_section("Total Damage Taken", ["Target", "Hits", "Damage", "Avg Dam", "%"], data)

        # PvP Damage Done
        if display_options.get("pvp_damage_done", True):
            data = []
            for k, v in sort_dict(damage_data["pvp_damage_done"]):
                data.append([k, v[1], round(v[0], 1), round(v[3], 1), f"{v[2]:.1f}%"])
            output += write_csv_section("PvP Damage Done", ["Source", "Hits", "Damage", "Avg Dam", "%"], data)

        # PvP Damage Taken
        if display_options.get("pvp_damage_taken", True):
            data = []
            for k, v in sort_dict(damage_data["pvp_damage_taken"]):
                data.append([k, v[1], round(v[0], 1), round(v[3], 1), f"{v[2]:.1f}%"])
            output += write_csv_section("PvP Damage Taken", ["Target", "Hits", "Damage", "Avg Dam", "%"], data)

        # Damage Types
        if display_options.get("damage_types", True):
            data = []
            for k, v in damage_data["damage_types"].items():
                src, dtype = k.split(" -> ")
                data.append([src, dtype, v[1], round(v[0], 1), round(v[3], 1), f"{v[2]:.1f}%"])
            data.sort(key=lambda x: x[3], reverse=True)
            output += write_csv_section("Damage Types", ["Source", "Type", "Hits", "Damage", "Avg Dam", "%"], data)

        # Damage Details
        if display_options.get("damage_details", True):
            data = []
            for k, v in damage_data["damage_details"].items():
                src, tgt = k.split(" -> ")
                data.append([src, tgt, v[1], round(v[0], 1), round(v[4], 1), f"{v[3]:.1f}%"])
            data.sort(key=lambda x: x[3], reverse=True)
            output += write_csv_section("Damage Details", ["Source", "Target", "Hits", "Damage", "Avg Dam", "%"], data)

        return "\n".join(output)

    # Plain Text / Clipboard
    else:
        # Totals by category
        def get_totals(d):
            hits = sum(v[1] for v in d.values())
            dmg = round(sum(v[0] for v in d.values()))
            avg = round(dmg / hits) if hits > 0 else 0
            return hits, dmg, avg

        if display_options.get("damage_done", True):
            entries = []
            for k, v in sorted(damage_data["damage_done"].items(), key=lambda x: x[1][0], reverse=True):
                entries.append([k, v[1], f"{round(v[0]):,}", round(v[3]), f"{round(v[2]):02d}"])
            output += build_text_section("Total Damage Done", ["SOURCE", "HITS", "DAMAGE", "AVG", "PERC"], entries, get_totals(damage_data["damage_done"]))

        if display_options.get("damage_taken", True):
            entries = []
            for k, v in sorted(damage_data["damage_taken"].items(), key=lambda x: x[1][0], reverse=True):
                entries.append([k, v[1], f"{round(v[0]):,}", round(v[3]), f"{round(v[2]):02d}"])
            output += build_text_section("Total Damage Taken", ["TARGET", "HITS", "DAMAGE", "AVG", "PERC"], entries, get_totals(damage_data["damage_taken"]))

        if display_options.get("pvp_damage_done", True):
            entries = []
            for k, v in sorted(damage_data["pvp_damage_done"].items(), key=lambda x: x[1][0], reverse=True):
                entries.append([k, v[1], f"{round(v[0]):,}", round(v[3]), f"{round(v[2]):02d}"])
            output += build_text_section("PvP Damage Done", ["SOURCE", "HITS", "DAMAGE", "AVG", "PERC"], entries, get_totals(damage_data["pvp_damage_done"]))

        if display_options.get("pvp_damage_taken", True):
            entries = []
            for k, v in sorted(damage_data["pvp_damage_taken"].items(), key=lambda x: x[1][0], reverse=True):
                entries.append([k, v[1], f"{round(v[0]):,}", round(v[3]), f"{round(v[2]):02d}"])
            output += build_text_section("PvP Damage Taken", ["TARGET", "HITS", "DAMAGE", "AVG", "PERC"], entries, get_totals(damage_data["pvp_damage_taken"]))

        if display_options.get("damage_types", True):
            entries = []
            for k, v in damage_data["damage_types"].items():
                src, dtype = k.split(" -> ")
                entries.append([f"{src} -> {dtype}", v[1], f"{round(v[0]):,}", round(v[3]), f"{round(v[2]):02d}"])
            entries.sort(key=lambda x: int(str(x[2]).replace(",", "")), reverse=True)
            output += build_text_section("Damage Types", ["SOURCE -> TYPE", "HITS", "DAMAGE", "AVG", "PERC"], entries)

        if display_options.get("damage_details", True):
            entries = []
            for k, v in damage_data["damage_details"].items():
                src, tgt = k.split(" -> ")
                entries.append([f"{src} -> {tgt}", v[1], f"{round(v[0]):,}", round(v[4]), f"{round(v[3]):02d}"])
            entries.sort(key=lambda x: int(str(x[2]).replace(",", "")), reverse=True)
            output += build_text_section("Damage Details", ["SOURCE -> TARGET", "HITS", "DAMAGE", "AVG", "PERC"], entries)

        return "\n".join(output)
