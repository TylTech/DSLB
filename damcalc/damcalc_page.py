import streamlit as st
import re
import pandas as pd
import io
import pprint
import streamlit.components.v1 as components

def show_damcalc_page():
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



def clean_entity_name(name, player_name):
    """Clean entity names from combat text."""
    # Replace "You" and "you" with player name
    if name.lower() == "you":
        return player_name
    
    # Handle common entity patterns
    # Group similar mobs/weapons
    entity_groups = {
        "burrow guard": ["a burrow guard", "the burrow guard"],
        "pointed staff": ["a burrow guard's pointed staff"],
        "wood and stone weapon": ["a wood and stone dagger", "a wood and stone knife"]
    }
    
    for group_name, patterns in entity_groups.items():
        for pattern in patterns:
            if pattern.lower() in name.lower():
                return group_name
    
    # Remove decorations and markers - improved to handle ***, ===, etc.
    name = re.sub(r'[*=<>]+', '', name)  # Remove all decorative characters completely
    name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    name = re.sub(r"'s\s+", "", name)
    name = re.sub(r'[!.,]$', '', name)
    
    return name.strip()

def is_player_character(name, player_name):
    """
    Determine if a name is likely a player character.
    - Have proper capitalization (first letter uppercase)
    - Don't contain 'a' or 'an' as first word
    - Don't have common mob descriptors
    - Player's own name is always considered a player character
    - Don't count as player if name contains a space (for PvP table)
    """
    name = name.strip()
    player_name = player_name.strip()

    if not name:
        return False

    if name.lower() == player_name.lower():
        return True

    # Per requirements, don't count names with spaces (like "Huwen Kamak") as players for PvP table
    if " " in name:
        return False

    if re.match(r'^(a|an|the)\s', name.lower()):
        return False

    mob_patterns = [
        "guard", "scout", "sword", "dagger", "knife", "staff", 
        "pointed", "fluted", "burrow", "wood", "stone", "weapon"
    ]

    if any(pattern in name.lower() for pattern in mob_patterns):
        return False

    # Proper check for capitalization
    if name[0].isupper() and not name.isupper():
        return True

    return False


def extract_entity_name(text, player_name):
    """Extract clean entity name from combat text."""
    # First, remove any location/room information in square brackets
    # This pattern matches things like "[ Western Coliseum Wall ]"
    text = re.sub(r'\[\s*[^\]]+\s*\]\s*', '', text)
    
    # Replace "You" with player name
    if text.lower() == "you":
        return player_name
        
    # First, detect weapon names which are often acting as damage sources
    weapon_patterns = [
        "a burrow guard's pointed staff",
        "a wood and stone dagger",
        "a wood and stone knife",
        "burrow scout's fluted knife",
        "burrow scout's fluted dagger"
    ]
    
    for pattern in weapon_patterns:
        if pattern.lower() in text.lower():
            return pattern
    
    # Handle player attacks which often have the format "Name's attack"
    if "'s " in text:
        parts = text.split("'s ", 1)
        return parts[0].strip()
    
    # For normal entity names (without possessives)
    # Remove any decorations or formatting - improved to handle all special characters
    name = re.sub(r'[*=<>]+', '', text)  # Remove decorative characters completely
    
    # Remove type markers like (fire), [undead], etc.
    name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    
    # If multiple words, check if the first word is "a" or "an" for mobs
    parts = name.strip().split()
    if parts and parts[0].lower() in ["a", "an"]:
        return " ".join(parts)  # Return the full mob name with "a" or "an"
    
    # For single names like character names
    if parts and len(parts) == 1:
        return parts[0]
        
    # If we can't determine, return the cleaned text
    return name.strip()

def extract_attack_type(source_text):
    """
    Extract attack type from source text based on CMUD's DMCleaner mode 3 logic.
    This handles cases like "Dhavi's pierce" -> "pierce" and "a burrow guard's pointed staff" -> "pointed staff"
    """
    # First handle special attack patterns directly
    if "draws life from" in source_text:
        return "life drain"
    if "is struck by lightning" in source_text:
        return "lightning strike"
    if "cut throat" in source_text:
        return "cut throat"
        
    # Remove location information
    source_text = re.sub(r'\[\s*[^\]]+\s*\]\s*', '', source_text)
    
    # Clean decorative characters from attack types
    source_text = re.sub(r'[*=<>]+', '', source_text)
    
    # CMUD logic: Extract everything after the possessive marker
    if "'s " in source_text:
        # Get the part after the last possessive marker
        parts = source_text.split("'s ")
        if len(parts) > 1:
            attack_type = parts[-1].strip()
            # If there's still a space, take the first word (the verb)
            if " " in attack_type:
                attack_type = attack_type.split()[0]
            return attack_type
    
    # If no possessive marker, check for known attack patterns
    known_attacks = ["pierce", "slash", "bash", "kick", "backstab", "spell", "piercing winds", "polevault kick"]
    for attack in known_attacks:
        if attack in source_text.lower():
            return attack
    
    # Default to generic attack type
    return "attack"

def extract_name_and_attack(text):
    """
    Extract the character name and attack type from a combat text.
    Returns a tuple of (name, attack_type)
    """
    # Remove possessive marker if present
    if text.endswith("'s"):
        text = text[:-2]
    
    # Handle special case where >>> is attached to name
    text = text.replace(">>>", "").replace("<<<", "").strip()
    
    # Clean decorative characters like asterisks and equal signs
    text = re.sub(r'[*=<>]+', '', text)
    
    # First check if this is a known mob/weapon name
    # This handles cases like "a burrow guard's pointed staff"
    common_entities = [
        "a burrow guard's pointed staff",
        "a wood and stone dagger",
        "a wood and stone knife"
        # Add other common entities from your game
    ]
    
    for entity in common_entities:
        if entity in text.lower():
            return entity, ""
    
    # For player characters or other entities:
    parts = text.split()
    if not parts:
        return text, ""
    
    # If it's likely a player character (first letter uppercase, no "a"/"an" prefix)
    if parts[0][0].isupper() and not parts[0].lower() in ["a", "an"]:
        name = parts[0]
        attack = " ".join(parts[1:]) if len(parts) > 1 else ""
        return name, attack
    else:
        # For non-player entities, return whole text as name
        return text, ""


def should_skip_line(source, target):
    """Determine if a line should be skipped (not combat related)."""
    # Skip common non-combat messages
    skip_indicators = [
        "answers ", "ask ", "tells ", "tell ", "says ", 
        "gossips ", "yells ", "clans ", "quests ",
        "the group ", "OOC: ", "OOC Clan: ",
        "Bloodbath: ", "Kingdom: ", "radios ", "grats ",
        "shouts ", "[Newbie]: ", "auctions: "
    ]
    
    for indicator in skip_indicators:
        if indicator in source or indicator in target:
            return True
    
    return False


def analyze_damage_log(log_content, player_name="Player"):
    """Parse and analyze a DSL combat log, extracting damage information."""
    damage_values = {
        "scratches": 2.5,
        "grazes": 6.5,
        "hits": 10.5,
        "injures": 14.5,
        "wounds": 18.5,
        "mauls": 22.5,
        "decimates": 26.5,
        "devastates": 30.5,
        "maims": 34.5,
        "MUTILATES": 38.5,
        "DISEMBOWELS": 42.5,
        "DISMEMBERS": 46.5,
        "MASSACRES": 50.5,
        "MANGLES": 54.5,
        "DEMOLISHES": 58.5,
        "DEVASTATES": 68,
        "OBLITERATES": 88,
        "ANNIHILATES": 113,
        "ERADICATES": 138,
        "GHASTLY": 163,
        "HORRID": 188,
        "DREADFUL": 213,
        "HIDEOUS": 238,
        "INDESCRIBABLE": 263,
        "UNSPEAKABLE": 300
    }

    damage_data = {
        "damage_done": {},
        "damage_taken": {},
        "damage_details": {},
        "damage_types": {},
        "pvp_damage_done": {},  # PvP damage done
        "pvp_damage_taken": {}  # New table for PvP damage taken (PC to PC)
    }

    skip_patterns = [
        "answers ", "ask ", "tells ", "tell ", "says ", 
        "gossips ", "yells ", "clans ", "quests ",
        "the group ", "OOC: ", "OOC Clan: ",
        "Bloodbath: ", "Kingdom: ", "radios ", "grats ",
        "shouts ", "[Newbie]: ", "auctions: ",
        "draws life from", "is struck by lightning", "lightning bolt",
        "flash of holy power", "holy smite", "The bolt", 
        "lightning bolt leaps", "mighty blow from", 
        "hits the ground", "transfer to", "some "
    ]

    for line in log_content.splitlines():
        line = line.strip()
        if not line:
            continue

        if any(skip in line for skip in skip_patterns):
            continue
        if "floats" in line or "death cry" in line or "enters a panic" in line:
            continue
        if re.match(r'^\[\d+/\d+hp', line):
            continue

        # ✅ Special case: cut throat
        throat_match = re.search(
            r"\] (.*?)'s cut throat\s+<<<\s+([A-Z]+)\s+>>>\s+(.*?)(!|\.|$)", line)
        if "cut throat" in line and throat_match:
            source_raw = throat_match.group(1).strip()
            verb = throat_match.group(2).strip()
            target_raw = throat_match.group(3).strip()

            source = player_name if source_raw.lower() == "you" else source_raw
            target = player_name if target_raw.lower() == "you" else target_raw

            source = extract_entity_name(source, player_name)
            target = extract_entity_name(target, player_name)
            damage_value = damage_values.get(verb.upper(), 0)

            record_damage(damage_data, source, target, damage_value, "cut throat", player_name)
            continue

        # ✅ Standard damage types
        for verb, damage_value in damage_values.items():
            pattern = rf"(.*?)'s (.*?)\s+{verb.upper()}\s+(.*?)($|!|\.)"
            match = re.search(pattern, line, re.IGNORECASE)

            if not match:
                pattern_alt = rf"(.*?)\s+{verb.upper()}\s+(.*?)($|!|\.)"
                match = re.search(pattern_alt, line, re.IGNORECASE)

            if match and len(match.groups()) >= 3:
                if "'s" in match.group(1):
                    source_raw = match.group(1).split("'s")[0]
                    attack_type = match.group(2)
                else:
                    source_raw = match.group(1)
                    attack_type = match.group(2)

                target_raw = match.group(3).strip()
                attack_type = attack_type.strip()

                source = player_name if source_raw.strip().lower() == "you" else source_raw.strip()
                target = player_name if target_raw.strip().lower() == "you" else target_raw.strip()

                source = re.sub(r'\[\s*[^\]]+\s*\]', '', source)
                target = re.sub(r'\[\s*[^\]]+\s*\]', '', target)
                
                # Clean the attack type of decorative characters
                attack_type = re.sub(r'[*=<>]+', '', attack_type)

                record_damage(damage_data, source, target, damage_value, attack_type, player_name)
                break  # Done with this line

    calculate_percentages(damage_data)
    return damage_data


def record_damage(damage_data, source, target, damage_value, damage_type, player_name):
    """Record damage in the various tracking dictionaries."""
    if not source or not target:
        return

    # Clean names
    source = clean_entity_name(source, player_name)
    target = clean_entity_name(target, player_name)

    # Clean + normalize damage type
    damage_type = re.sub(r'[*=<>]+', '', damage_type).strip().lower()

    # Record damage done by source
    if source not in damage_data["damage_done"]:
        damage_data["damage_done"][source] = [0, 0]
    damage_data["damage_done"][source][0] += damage_value
    damage_data["damage_done"][source][1] += 1

    # Record damage taken by target
    if target not in damage_data["damage_taken"]:
        damage_data["damage_taken"][target] = [0, 0]
    damage_data["damage_taken"][target][0] += damage_value
    damage_data["damage_taken"][target][1] += 1

    # Record detailed damage
    detail_key = f"{source} -> {target}"
    if detail_key not in damage_data["damage_details"]:
        damage_data["damage_details"][detail_key] = [0, 0, damage_type]
    else:
        damage_data["damage_details"][detail_key][0] += damage_value
        damage_data["damage_details"][detail_key][1] += 1

    # Record damage by type
    type_key = f"{source} -> {damage_type}"
    if type_key not in damage_data["damage_types"]:
        damage_data["damage_types"][type_key] = [0, 0]
    damage_data["damage_types"][type_key][0] += damage_value
    damage_data["damage_types"][type_key][1] += 1

    # PvP damage tracking
    if is_player_character(source, player_name) and is_player_character(target, player_name):
        if source not in damage_data["pvp_damage_done"]:
            damage_data["pvp_damage_done"][source] = [0, 0]
        damage_data["pvp_damage_done"][source][0] += damage_value
        damage_data["pvp_damage_done"][source][1] += 1

        if target not in damage_data["pvp_damage_taken"]:
            damage_data["pvp_damage_taken"][target] = [0, 0]
        damage_data["pvp_damage_taken"][target][0] += damage_value
        damage_data["pvp_damage_taken"][target][1] += 1




def calculate_percentages(damage_data):
    """Calculate percentage contributions for damage statistics."""
    # Calculate percentages for each category
    for category in damage_data:
        # Skip empty categories
        if not damage_data[category]:
            continue
            
        # Calculate total damage in this category
        total_damage = sum(data[0] for data in damage_data[category].values())
        
        # Calculate percentage for each entry
        for key in damage_data[category]:
            # Add percentage as third element in the list (unless it's damage_details which already has damage_type)
            if category == "damage_details":
                damage_type = damage_data[category][key][2]
                if total_damage > 0:
                    percentage = (damage_data[category][key][0] / total_damage) * 100
                else:
                    percentage = 0
                
                # Add average as fourth element
                if damage_data[category][key][1] > 0:
                    average = damage_data[category][key][0] / damage_data[category][key][1]
                else:
                    average = 0
                    
                damage_data[category][key] = [
                    damage_data[category][key][0],  # total damage
                    damage_data[category][key][1],  # hit count
                    damage_type,                    # damage type
                    percentage,                     # percentage
                    average                         # average damage
                ]
            else:
                if total_damage > 0:
                    percentage = (damage_data[category][key][0] / total_damage) * 100
                else:
                    percentage = 0
                
                # Add average as fourth element
                if damage_data[category][key][1] > 0:
                    average = damage_data[category][key][0] / damage_data[category][key][1]
                else:
                    average = 0
                    
                damage_data[category][key].extend([percentage, average])


def display_damage_reports(damage_data, display_options, player_name):
    """Display damage reports in tables with the nice HTML styling."""
    
    # 1. Damage Done by Source
    if display_options["damage_done"] and damage_data["damage_done"]:
        st.subheader("🗡️ Damage Done by Source")
        
        # Create a DataFrame for sources
        source_data = []
        for source, values in damage_data["damage_done"].items():
            source_data.append({
                "Source": source,
                "Damage": round(values[0], 1),
                "Hits": values[1],
                "Average": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        
        # Convert to DataFrame, sort by damage, and display
        if source_data:
            df_source = pd.DataFrame(source_data)
            df_source = df_source.sort_values("Damage", ascending=False).reset_index(drop=True)
            
            # Display with sortable HTML table
            display_sortable_table(df_source, "damage-done-table")
    
    # 2. Damage Taken by Target
    if display_options["damage_taken"] and damage_data["damage_taken"]:
        st.subheader("🛡️ Damage Taken by Target")
        
        # Create a DataFrame for targets
        target_data = []
        for target, values in damage_data["damage_taken"].items():
            target_data.append({
                "Target": target,
                "Damage": round(values[0], 1),
                "Hits": values[1],
                "Average": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        
        # Convert to DataFrame, sort by damage, and display
        if target_data:
            df_target = pd.DataFrame(target_data)
            df_target = df_target.sort_values("Damage", ascending=False).reset_index(drop=True)
            
            # Display with sortable HTML table
            display_sortable_table(df_target, "damage-taken-table")
    
    # 3. PvP Damage Done
    if display_options["pvp_damage_done"] and damage_data["pvp_damage_done"]:
        st.subheader("⚔️ PvP Damage Done")
        
        # Create a DataFrame for PvP damage done
        pvp_data = []
        for source, values in damage_data["pvp_damage_done"].items():
            pvp_data.append({
                "Source": source,
                "Damage": round(values[0], 1),
                "Hits": values[1],
                "Average": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        
        # Convert to DataFrame, sort by damage, and display
        if pvp_data:
            df_pvp = pd.DataFrame(pvp_data)
            df_pvp = df_pvp.sort_values("Damage", ascending=False).reset_index(drop=True)
            
            # Display with sortable HTML table
            display_sortable_table(df_pvp, "pvp-damage-done-table")
        else:
            st.info("No player vs player damage done detected in this log.")
    
    # 4. PvP Damage Taken (New)
    if display_options["pvp_damage_taken"] and damage_data["pvp_damage_taken"]:
        st.subheader("🛡️ PvP Damage Taken")
        
        # Create a DataFrame for PvP damage taken
        pvp_taken_data = []
        for target, values in damage_data["pvp_damage_taken"].items():
            pvp_taken_data.append({
                "Target": target,
                "Damage": round(values[0], 1),
                "Hits": values[1],
                "Average": round(values[3], 1) if len(values) > 3 else 0,
                "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
            })
        
        # Convert to DataFrame, sort by damage, and display
        if pvp_taken_data:
            df_pvp_taken = pd.DataFrame(pvp_taken_data)
            df_pvp_taken = df_pvp_taken.sort_values("Damage", ascending=False).reset_index(drop=True)
            
            # Display with sortable HTML table
            display_sortable_table(df_pvp_taken, "pvp-damage-taken-table")
        else:
            st.info("No player vs player damage taken detected in this log.")
    
    # 5. Damage by Type with Source Filter
    if display_options["damage_types"] and damage_data["damage_types"]:
        st.subheader("🔥 Damage by Type")

        damage_type_data_full = []
        sources = set()

        for key, values in damage_data["damage_types"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source = parts[0]
                attack_type = parts[1]

                sources.add(source)

                damage_type_data_full.append({
                    "Source": source,
                    "Type": attack_type.title(),  # ← prettify casing
                    "Damage": round(values[0], 1),
                    "Hits": values[1],
                    "Average": round(values[3], 1) if len(values) > 3 else 0,
                    "%": f"{values[2]:.1f}%" if len(values) > 2 else "0.0%"
                })

        # Filters
        source_list = sorted(list(sources))
        source_options = ["Filter by Source"] + source_list

        if 'damage_type_source_filter' not in st.session_state:
            st.session_state.damage_type_source_filter = "Filter by Source"

        selected_source = st.selectbox(
            "Source Filter",
            source_options,
            index=source_options.index(st.session_state.damage_type_source_filter),
            key="damage_type_source_filter",
            label_visibility="collapsed"
        )

        df_type_full = pd.DataFrame(damage_type_data_full)
        if selected_source != "Filter by Source":
            df_type = df_type_full[df_type_full["Source"] == selected_source].reset_index(drop=True)
        else:
            df_type = df_type_full

        if not df_type.empty:
            df_type = df_type.sort_values("Damage", ascending=False).reset_index(drop=True)
            display_sortable_table(df_type, "damage-type-table")


    
    # 6. Damage Details (Source to Target breakdown) with Filters
    if display_options["damage_details"] and damage_data["damage_details"]:
        st.subheader("📝 Damage Details")

        damage_details_data = []
        unique_sources = set()
        unique_targets = set()

        for key, values in damage_data["damage_details"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source = parts[0]
                target = parts[1]

                unique_sources.add(source)
                unique_targets.add(target)

                damage_details_data.append({
                    "Source": source,
                    "Target": target,
                    "Damage": round(values[0], 1),
                    "Hits": values[1],
                    "Average": round(values[4], 1) if len(values) > 4 else 0,
                    "%": f"{values[3]:.1f}%" if len(values) > 3 else "0.0%"
                })

    source_list = sorted(list(unique_sources))
    target_list = sorted(list(unique_targets))
    source_options = ["Filter by Source"] + source_list
    target_options = ["Filter by Target"] + target_list

    # 🔐 Ensure persistent filters
    if 'details_source_filter' not in st.session_state:
        st.session_state.details_source_filter = "Filter by Source"
    if 'details_target_filter' not in st.session_state:
        st.session_state.details_target_filter = "Filter by Target"

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_source_details = st.selectbox(
            "Source Filter",
            source_options,
            index=source_options.index(st.session_state.details_source_filter),
            key="details_source_filter",
            label_visibility="collapsed"
        )
    with filter_col2:
        selected_target_details = st.selectbox(
            "Target Filter",
            target_options,
            index=target_options.index(st.session_state.details_target_filter),
            key="details_target_filter",
            label_visibility="collapsed"
        )

    # Convert to DataFrame and apply filters
    df_details_full = pd.DataFrame(damage_details_data)

    if selected_source_details != "Filter by Source" and selected_target_details != "Filter by Target":
        df_details = df_details_full[
            (df_details_full["Source"] == selected_source_details) &
            (df_details_full["Target"] == selected_target_details)
        ].reset_index(drop=True)
    elif selected_source_details != "Filter by Source":
        df_details = df_details_full[df_details_full["Source"] == selected_source_details].reset_index(drop=True)
    elif selected_target_details != "Filter by Target":
        df_details = df_details_full[df_details_full["Target"] == selected_target_details].reset_index(drop=True)
    else:
        df_details = df_details_full

    if not df_details.empty:
        df_details = df_details.sort_values("Damage", ascending=False).reset_index(drop=True)
        display_sortable_table(df_details, "damage-details-table")



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
    """
    Format the damage data for export based on the selected format.
    
    Args:
        damage_data: Dictionary containing damage calculation results
        export_format: String indicating the desired export format
        display_options: Dictionary of display preferences
        player_name: Optional player name to include in exports
    
    Returns:
        Formatted data string in the requested format
    """
    if not damage_data:
        return ""
    
    # Create output based on the format
    if export_format.lower() == "csv":
        output = []
        
        # Add header with player name
        if player_name:
            output.append(f"# Damage Report for {player_name}")
            output.append("")
        
        # Damage Done section
        if display_options.get("damage_done", True) and damage_data["damage_done"]:
            output.append("DAMAGE DONE BY SOURCE")
            output.append("Source,Damage,Hits,Average,%")
            
            # Sort entries by damage
            sorted_sources = sorted(damage_data["damage_done"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for source, values in sorted_sources:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"{source},{round(values[0], 1)},{values[1]},{round(average, 1)},{percentage:.1f}%")
            
            output.append("")
        
        # Damage Taken section
        if display_options.get("damage_taken", True) and damage_data["damage_taken"]:
            output.append("DAMAGE TAKEN BY TARGET")
            output.append("Target,Damage,Hits,Average,%")
            
            # Sort entries by damage
            sorted_targets = sorted(damage_data["damage_taken"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for target, values in sorted_targets:
                # Get the percentage if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"{target},{round(values[0], 1)},{values[1]},{round(average, 1)},{percentage:.1f}%")
            
            output.append("")
        
        # PvP Damage Done section
        if display_options.get("pvp_damage_done", True) and damage_data["pvp_damage_done"]:
            output.append("PVP DAMAGE DONE")
            output.append("Source,Damage,Hits,Average,%")
            
            # Sort entries by damage
            sorted_pvp = sorted(damage_data["pvp_damage_done"].items(), 
                               key=lambda x: x[1][0], 
                               reverse=True)
            
            for source, values in sorted_pvp:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"{source},{round(values[0], 1)},{values[1]},{round(average, 1)},{percentage:.1f}%")
            
            output.append("")
            
        # PvP Damage Taken section
        if display_options.get("pvp_damage_taken", True) and damage_data["pvp_damage_taken"]:
            output.append("PVP DAMAGE TAKEN")
            output.append("Target,Damage,Hits,Average,%")
            
            # Sort entries by damage
            sorted_pvp_taken = sorted(damage_data["pvp_damage_taken"].items(), 
                                     key=lambda x: x[1][0], 
                                     reverse=True)
            
            for target, values in sorted_pvp_taken:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"{target},{round(values[0], 1)},{values[1]},{round(average, 1)},{percentage:.1f}%")
            
            output.append("")
        
        # Damage by Type section
        if display_options.get("damage_types", True) and damage_data["damage_types"]:
            output.append("DAMAGE BY TYPE")
            output.append("Source,Type,Damage,Hits,Average,%")
            
            # Process data for sorting
            type_data = []
            for key, values in damage_data["damage_types"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    attack_type = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[2] if len(values) > 2 else 0
                    average = values[3] if len(values) > 3 else 0
                    
                    type_data.append((source, attack_type, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_types = sorted(type_data, key=lambda x: x[2], reverse=True)
            
            for source, attack_type, damage, hits, average, percentage in sorted_types:
                output.append(f"{source},{attack_type},{round(damage, 1)},{hits},{round(average, 1)},{percentage:.1f}%")
            
            output.append("")
        
        # Damage Details section
        if display_options.get("damage_details", True) and damage_data["damage_details"]:
            output.append("DAMAGE DETAILS")
            output.append("Source,Target,Damage,Hits,Average,%")
            
            # Process data for sorting
            detail_data = []
            for key, values in damage_data["damage_details"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    target = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[3] if len(values) > 3 else 0
                    average = values[4] if len(values) > 4 else 0
                    
                    detail_data.append((source, target, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_details = sorted(detail_data, key=lambda x: x[2], reverse=True)
            
            for source, target, damage, hits, average, percentage in sorted_details:
                output.append(f"{source},{target},{round(damage, 1)},{hits},{round(average, 1)},{percentage:.1f}%")
        
        return "\n".join(output)
    
    elif export_format.lower() == "excel":
        # For Excel format, we'll just return the CSV format since that can be easily opened in Excel
        return export_damage_data(damage_data, "csv", display_options, player_name)
    
    elif export_format.lower() == "markdown":
        output = []
        
        # Add header with player name
        if player_name:
            output.append(f"# Damage Report for {player_name}")
            output.append("")
        
        # Damage Done section
        if display_options.get("damage_done", True) and damage_data["damage_done"]:
            output.append("## DAMAGE DONE BY SOURCE")
            output.append("| Source | Damage | Hits | Average | % |")
            output.append("|--------|-------:|-----:|--------:|--:|")
            
            # Sort entries by damage
            sorted_sources = sorted(damage_data["damage_done"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for source, values in sorted_sources:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"| {source} | {round(values[0], 1)} | {values[1]} | {round(average, 1)} | {percentage:.1f}% |")
            
            output.append("")
        
        # Damage Taken section
        if display_options.get("damage_taken", True) and damage_data["damage_taken"]:
            output.append("## DAMAGE TAKEN BY TARGET")
            output.append("| Target | Damage | Hits | Average | % |")
            output.append("|--------|-------:|-----:|--------:|--:|")
            
            # Sort entries by damage
            sorted_targets = sorted(damage_data["damage_taken"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for target, values in sorted_targets:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"| {target} | {round(values[0], 1)} | {values[1]} | {round(average, 1)} | {percentage:.1f}% |")
            
            output.append("")
        
        # PvP Damage Done section
        if display_options.get("pvp_damage_done", True) and damage_data["pvp_damage_done"]:
            output.append("## PVP DAMAGE DONE")
            output.append("| Source | Damage | Hits | Average | % |")
            output.append("|--------|-------:|-----:|--------:|--:|")
            
            # Sort entries by damage
            sorted_pvp = sorted(damage_data["pvp_damage_done"].items(), 
                               key=lambda x: x[1][0], 
                               reverse=True)
            
            for source, values in sorted_pvp:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"| {source} | {round(values[0], 1)} | {values[1]} | {round(average, 1)} | {percentage:.1f}% |")
            
            output.append("")
            
        # PvP Damage Taken section
        if display_options.get("pvp_damage_taken", True) and damage_data["pvp_damage_taken"]:
            output.append("## PVP DAMAGE TAKEN")
            output.append("| Target | Damage | Hits | Average | % |")
            output.append("|--------|-------:|-----:|--------:|--:|")
            
            # Sort entries by damage
            sorted_pvp_taken = sorted(damage_data["pvp_damage_taken"].items(), 
                                     key=lambda x: x[1][0], 
                                     reverse=True)
            
            for target, values in sorted_pvp_taken:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                output.append(f"| {target} | {round(values[0], 1)} | {values[1]} | {round(average, 1)} | {percentage:.1f}% |")
            
            output.append("")
        
        # Damage by Type section
        if display_options.get("damage_types", True) and damage_data["damage_types"]:
            output.append("## DAMAGE BY TYPE")
            output.append("| Source | Type | Damage | Hits | Average | % |")
            output.append("|--------|------|-------:|-----:|--------:|--:|")
            
            # Process data for sorting
            type_data = []
            for key, values in damage_data["damage_types"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    attack_type = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[2] if len(values) > 2 else 0
                    average = values[3] if len(values) > 3 else 0
                    
                    type_data.append((source, attack_type, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_types = sorted(type_data, key=lambda x: x[2], reverse=True)
            
            for source, attack_type, damage, hits, average, percentage in sorted_types:
                output.append(f"| {source} | {attack_type} | {round(damage, 1)} | {hits} | {round(average, 1)} | {percentage:.1f}% |")
            
            output.append("")
        
        # Damage Details section
        if display_options.get("damage_details", True) and damage_data["damage_details"]:
            output.append("## DAMAGE DETAILS")
            output.append("| Source | Target | Damage | Hits | Average | % |")
            output.append("|--------|--------|-------:|-----:|--------:|--:|")
            
            # Process data for sorting
            detail_data = []
            for key, values in damage_data["damage_details"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    target = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[3] if len(values) > 3 else 0
                    average = values[4] if len(values) > 4 else 0
                    
                    detail_data.append((source, target, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_details = sorted(detail_data, key=lambda x: x[2], reverse=True)
            
            for source, target, damage, hits, average, percentage in sorted_details:
                output.append(f"| {source} | {target} | {round(damage, 1)} | {hits} | {round(average, 1)} | {percentage:.1f}% |")
        
        return "\n".join(output)
    
    else:  # Plain text format
        output = []
        
        # Add header with player name
        if player_name:
            output.append(f"Damage Report for {player_name}")
            output.append("=" * len(output[0]))
            output.append("")
        
        # Damage Done section
        if display_options.get("damage_done", True) and damage_data["damage_done"]:
            output.append("DAMAGE DONE BY SOURCE")
            output.append("-" * 60)
            
            # Create headers with proper spacing
            headers = ["Source", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 60)
            
            # Sort entries by damage
            sorted_sources = sorted(damage_data["damage_done"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for source, values in sorted_sources:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                cols = [
                    source[:col_widths[0]-1].ljust(col_widths[0]),
                    str(round(values[0], 1)).ljust(col_widths[1]),
                    str(values[1]).ljust(col_widths[2]),
                    str(round(average, 1)).ljust(col_widths[3]),
                    f"{percentage:.1f}%".ljust(col_widths[4])
                ]
                
                output.append(" ".join(cols))
            
            output.append("")
        
        # Damage Taken section
        if display_options.get("damage_taken", True) and damage_data["damage_taken"]:
            output.append("DAMAGE TAKEN BY TARGET")
            output.append("-" * 60)
            
            # Create headers with proper spacing
            headers = ["Target", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 60)
            
            # Sort entries by damage
            sorted_targets = sorted(damage_data["damage_taken"].items(), 
                                   key=lambda x: x[1][0], 
                                   reverse=True)
            
            for target, values in sorted_targets:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                cols = [
                    target[:col_widths[0]-1].ljust(col_widths[0]),
                    str(round(values[0], 1)).ljust(col_widths[1]),
                    str(values[1]).ljust(col_widths[2]),
                    str(round(average, 1)).ljust(col_widths[3]),
                    f"{percentage:.1f}%".ljust(col_widths[4])
                ]
                
                output.append(" ".join(cols))
            
            output.append("")
        
        # PvP Damage Done section
        if display_options.get("pvp_damage_done", True) and damage_data["pvp_damage_done"]:
            output.append("PVP DAMAGE DONE")
            output.append("-" * 60)
            
            # Create headers with proper spacing
            headers = ["Source", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 60)
            
            # Sort entries by damage
            sorted_pvp = sorted(damage_data["pvp_damage_done"].items(), 
                               key=lambda x: x[1][0], 
                               reverse=True)
            
            for source, values in sorted_pvp:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                cols = [
                    source[:col_widths[0]-1].ljust(col_widths[0]),
                    str(round(values[0], 1)).ljust(col_widths[1]),
                    str(values[1]).ljust(col_widths[2]),
                    str(round(average, 1)).ljust(col_widths[3]),
                    f"{percentage:.1f}%".ljust(col_widths[4])
                ]
                
                output.append(" ".join(cols))
            
            output.append("")
            
        # PvP Damage Taken section
        if display_options.get("pvp_damage_taken", True) and damage_data["pvp_damage_taken"]:
            output.append("PVP DAMAGE TAKEN")
            output.append("-" * 60)
            
            # Create headers with proper spacing
            headers = ["Target", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 60)
            
            # Sort entries by damage
            sorted_pvp_taken = sorted(damage_data["pvp_damage_taken"].items(), 
                                     key=lambda x: x[1][0], 
                                     reverse=True)
            
            for target, values in sorted_pvp_taken:
                # Get the percentage and average if available
                percentage = values[2] if len(values) > 2 else 0
                average = values[3] if len(values) > 3 else 0
                
                cols = [
                    target[:col_widths[0]-1].ljust(col_widths[0]),
                    str(round(values[0], 1)).ljust(col_widths[1]),
                    str(values[1]).ljust(col_widths[2]),
                    str(round(average, 1)).ljust(col_widths[3]),
                    f"{percentage:.1f}%".ljust(col_widths[4])
                ]
                
                output.append(" ".join(cols))
            
            output.append("")
        
        # Damage by Type section
        if display_options.get("damage_types", True) and damage_data["damage_types"]:
            output.append("DAMAGE BY TYPE")
            output.append("-" * 70)
            
            # Create headers with proper spacing
            headers = ["Source", "Type", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 15, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 70)
            
            # Process data for sorting
            type_data = []
            for key, values in damage_data["damage_types"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    attack_type = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[2] if len(values) > 2 else 0
                    average = values[3] if len(values) > 3 else 0
                    
                    type_data.append((source, attack_type, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_types = sorted(type_data, key=lambda x: x[2], reverse=True)
            
            for source, attack_type, damage, hits, average, percentage in sorted_types:
                cols = [
                    source[:col_widths[0]-1].ljust(col_widths[0]),
                    attack_type[:col_widths[1]-1].ljust(col_widths[1]),
                    str(round(damage, 1)).ljust(col_widths[2]),
                    str(hits).ljust(col_widths[3]),
                    str(round(average, 1)).ljust(col_widths[4]),
                    f"{percentage:.1f}%".ljust(col_widths[5])
                ]
                
                output.append(" ".join(cols))
            
            output.append("")
        
        # Damage Details section
        if display_options.get("damage_details", True) and damage_data["damage_details"]:
            output.append("DAMAGE DETAILS")
            output.append("-" * 70)
            
            # Create headers with proper spacing
            headers = ["Source", "Target", "Damage", "Hits", "Average", "%"]
            col_widths = [20, 20, 10, 6, 10, 8]
            
            header_line = " ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            output.append(header_line)
            output.append("-" * 70)
            
            # Process data for sorting
            detail_data = []
            for key, values in damage_data["damage_details"].items():
                parts = key.split(" -> ")
                if len(parts) == 2:
                    source = parts[0]
                    target = parts[1]
                    
                    # Get the percentage and average if available
                    percentage = values[3] if len(values) > 3 else 0
                    average = values[4] if len(values) > 4 else 0
                    
                    detail_data.append((source, target, values[0], values[1], average, percentage))
            
            # Sort by damage
            sorted_details = sorted(detail_data, key=lambda x: x[2], reverse=True)
            
            for source, target, damage, hits, average, percentage in sorted_details:
                cols = [
                    source[:col_widths[0]-1].ljust(col_widths[0]),
                    target[:col_widths[1]-1].ljust(col_widths[1]),
                    str(round(damage, 1)).ljust(col_widths[2]),
                    str(hits).ljust(col_widths[3]),
                    str(round(average, 1)).ljust(col_widths[4]),
                    f"{percentage:.1f}%".ljust(col_widths[5])
                ]
                
                output.append(" ".join(cols))
        
        return "\n".join(output)