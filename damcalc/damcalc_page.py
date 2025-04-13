import streamlit as st
import re
import pandas as pd
import io

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
                "damage_done": st.checkbox("Total Damage Done by Source", value=True),
                "damage_taken": st.checkbox("Total Damage Taken by Target", value=True),
                "damage_types": st.checkbox("Total Damage Dealt by Type", value=True),
                "damage_details": st.checkbox("Total Damage Taken by Type", value=True)
            }
        
        with col2:
            st.subheader("Export Options")
            export_format = st.radio(
                "Export Format:",
                ["CSV", "Excel", "Text"],
                index=0
            )
    
    # Process and analyze log data when button is clicked
    if analyze_button:
        log_content = ""
        
        # Get log content from either text area or uploaded file
        if log_text:
            log_content = log_text
        elif uploaded_file is not None:
            log_content = uploaded_file.getvalue().decode("utf-8")
        
        # Process the log if we have content
        if log_content:
            # Set character name for replacing "You" in logs
            player_name = char_name if char_name else "Player"
            
            # Parse and analyze the log
            damage_data = analyze_damage_log(log_content, player_name)
            
            # Display results
            display_damage_reports(damage_data, display_options)
            
            # Export button
            st.download_button(
                label=f"💾 Export as {export_format}",
                data=export_damage_data(damage_data, export_format),
                file_name=f"damage_analysis.{export_format.lower()}",
                mime={"CSV": "text/csv", "Excel": "application/vnd.ms-excel", "Text": "text/plain"}[export_format]
            )
        else:
            st.warning("Please paste a combat log or upload a log file to analyze.")


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
    
    # Remove decorations and markers
    name = re.sub(r'[*=<>]+(.*?)[*=<>]+', r'\1', name)
    name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    name = re.sub(r"'s\s+", "", name)
    name = re.sub(r'[!.,]$', '', name)
    
    return name.strip()


def is_player_character(name):
    """
    Determine if a name is likely a player character.
    In many games, player names typically:
    - Have proper capitalization (first letter uppercase)
    - Don't contain 'a' or 'an' as first word
    - Don't have common mob descriptors
    """
    # Check if it starts with "a" or "an" (common for mobs)
    if re.match(r'^(a|an)\s', name.lower()):
        return False
    
    # Check if it's properly capitalized like a name
    if name and name[0].isupper() and not name.isupper():
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
    # Remove any decorations or formatting
    name = re.sub(r'[*=<>]+', '', text)
    
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
    # Define damage values for combat verbs
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
    
    # Initialize data structures
    damage_data = {
        "damage_done": {},         # Source -> [total_damage, hit_count]
        "damage_taken": {},        # Target -> [total_damage, hit_count]
        "damage_details": {},      # Source -> Target -> [total_damage, hit_count]
        "damage_types": {}         # Source -> Type -> [total_damage, hit_count]
    }
    
    # Skip patterns from CMUD's DMFakeCheck function
    skip_patterns = [
        # Chat patterns
        "answers ", "ask ", "tells ", "tell ", "says ", 
        "gossips ", "yells ", "clans ", "quests ",
        "the group ", "OOC: ", "OOC Clan: ",
        "Bloodbath: ", "Kingdom: ", "radios ", "grats ",
        "shouts ", "[Newbie]: ", "auctions: ",
        
        # Special weapon effects to skip
        "draws life from", "is struck by lightning", "lightning bolt",
        "flash of holy power", "holy smite", "The bolt", 
        "lightning bolt leaps", "mighty blow from", 
        "hits the ground", "transfer to", "some "
    ]
    
    # Process log line by line
    for line in log_content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Skip noise and fluff
        if any(skip in line for skip in skip_patterns):
            continue
        if "floats" in line or "death cry" in line or "enters a panic" in line:
            continue
        if re.match(r'^\[\d+/\d+hp', line):
            continue

        # ✅ Special case: cut throat
        # Handle cut throat with embedded ALL CAPS verbs like <<< ERADICATES >>>
        if "cut throat" in line:
            throat_match = re.search(
                r"\] (.*?)'s cut throat\s+<<<\s+([A-Z]+)\s+>>>\s+(.*?)(!|\.|$)", line)
            if throat_match:
                source_raw = throat_match.group(1).strip()
                verb = throat_match.group(2).strip()
                target_raw = throat_match.group(3).strip()

                # Clean up names and replace "you" if needed
                source = player_name if source_raw.lower() == "you" else source_raw
                target = player_name if target_raw.lower() == "you" else target_raw

                # Normalize both names
                source = extract_entity_name(source, player_name)
                target = extract_entity_name(target, player_name)

                # Get damage value from the big verb
                damage_value = damage_values.get(verb.upper(), 0)

                # Log it as a cut throat attack
                record_damage(damage_data, source, target, damage_value, "cut throat")
                continue


        # ✅ Standard damage types
        for verb, damage_value in damage_values.items():
            # Handle both normal and ALLCAPS (CMUD) verbs
            pattern = rf"\] (.*?) (?:{verb}s?|<<< {verb} >>>) (.*?)(!|\.|$)"
            match = re.search(pattern, line, re.IGNORECASE)
            if not match:
                continue

            source_raw = match.group(1).strip()
            target_raw = match.group(2).strip().replace("!", "").replace(".", "").strip()

            # Resolve attack type from source string (CMUD mode 3 style)
            if "'s " in source_raw:
                parts = source_raw.split("'s ", 1)
                source = parts[0].strip()
                attack_type = parts[1].strip()
            else:
                source = source_raw
                attack_type = verb.lower()

            # Replace "You" with player name
            if source.lower() == "you":
                source = player_name
            if target_raw.lower() == "you":
                target = player_name
            else:
                target = target_raw

            # Clean up square-bracketed room/location noise
            source = re.sub(r'\[\s*[^\]]+\s*\]', '', source)
            target = re.sub(r'\[\s*[^\]]+\s*\]', '', target)

            record_damage(damage_data, source, target, damage_value, attack_type)
            break  # We matched a damage verb, done with this line

    
    # Calculate percentages and sort data
    calculate_percentages(damage_data)
    
    return damage_data


def record_damage(damage_data, source, target, damage_value, damage_type):
    """Record damage in the various tracking dictionaries."""
    # Skip invalid entries
    if not source or not target:
        return
        
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
    
    # Record detailed source->target damage
    detail_key = f"{source} -> {target}"
    if detail_key not in damage_data["damage_details"]:
        damage_data["damage_details"][detail_key] = [0, 0, damage_type]
    else:
        damage_data["damage_details"][detail_key][0] += damage_value
        damage_data["damage_details"][detail_key][1] += 1
        # Keep the original damage type
    
    # Record damage by type for each source
    type_key = f"{source} -> {damage_type}"
    if type_key not in damage_data["damage_types"]:
        damage_data["damage_types"][type_key] = [0, 0]
    damage_data["damage_types"][type_key][0] += damage_value
    damage_data["damage_types"][type_key][1] += 1


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


def display_damage_reports(damage_data, display_options):
    """Display damage reports based on the selected options."""
    
    # 1. Total Damage Done by Source
    if display_options["damage_done"] and damage_data["damage_done"]:
        st.subheader("🗡️ Total Damage Done by Source")
        
        # Create a DataFrame for sources
        source_data = []
        for source, values in damage_data["damage_done"].items():
            source_data.append({
                "Source": source,
                "Amount": round(values[0], 1),
                "Percentage": f"{values[2]:.1f}%"
            })
        
        # Convert to DataFrame, sort by damage, and display
        if source_data:
            df_source = pd.DataFrame(source_data)
            df_source = df_source.sort_values("Amount", ascending=False).reset_index(drop=True)
            st.dataframe(df_source, use_container_width=True)
            
    
    # 2. Total Damage Taken by Target
    if display_options["damage_taken"] and damage_data["damage_taken"]:
        st.subheader("🛡️ Total Damage Taken by Target")
        
        # Create a DataFrame for targets
        target_data = []
        for target, values in damage_data["damage_taken"].items():
            target_data.append({
                "Target": target,
                "Percentage": f"{values[2]:.1f}%",
                "Amount": round(values[0], 1)
            })
        
        # Convert to DataFrame, sort by damage, and display
        if target_data:
            df_target = pd.DataFrame(target_data)
            df_target = df_target.sort_values("Amount", ascending=False).reset_index(drop=True)
            st.dataframe(df_target, use_container_width=True)
    
    # 3. Total Damage by Attack Type for each Source
    if display_options["damage_types"] and damage_data["damage_types"]:
        st.subheader("🔥 Damage by Attack Type")
        
        # Create DataFrame for damage by attack type
        damage_type_data = []
        
        # Extract attack type data
        for key, values in damage_data["damage_types"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source = parts[0]
                attack_type = parts[1]
                
                damage_type_data.append({
                    "Source": source,
                    "Attack Type": attack_type,
                    "Amount": round(values[0], 1),
                    "Hits": values[1],
                    "Avg. Damage": round(values[3], 1),
                    "Percentage": f"{values[2]:.1f}%"
                })
        
        # Convert to DataFrame, sort, and display
        if damage_type_data:
            df_type = pd.DataFrame(damage_type_data)
            df_type = df_type.sort_values(["Source", "Amount"], ascending=[True, False]).reset_index(drop=True)
            st.dataframe(df_type, use_container_width=True)
    
    # 4. Total Damage Taken by Type
    if display_options["damage_details"] and damage_data["damage_details"]:
        st.subheader("📝 Total Damage Taken by Type")
        
        # Create DataFrame for damage taken by type
        damage_taken_data = []
        
        # We need to extract data from the detailed records, but reorganize for the taken perspective
        for key, values in damage_data["damage_details"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source, target = parts
                damage_type = values[2]  # Type is stored in position 2
                
                damage_taken_data.append({
                    "Target": target,
                    "Type": damage_type,
                    "Amount": round(values[0], 1),
                    "Source": source,
                    "Hits": values[1],
                    "Avg. Damage": round(values[4], 1),
                    "Percentage": f"{values[3]:.1f}%"
                })
        
        # Convert to DataFrame, sort, and display
        if damage_taken_data:
            df_taken = pd.DataFrame(damage_taken_data)
            df_taken = df_taken.sort_values(["Target", "Amount"], ascending=[True, False]).reset_index(drop=True)
            st.dataframe(df_taken, use_container_width=True)


def export_damage_data(damage_data, format_type):
    """Export damage data in the specified format."""
    # Create DataFrames for each category using the same format as the display function
    dataframes = {}
    
    # 1. Total Damage Done by Source
    if damage_data["damage_done"]:
        source_data = []
        for source, values in damage_data["damage_done"].items():
            source_data.append({
                "Source": source,
                "Amount": values[0],
                "Percentage": values[2] if len(values) > 2 else 0
            })
        
        if source_data:
            df_source = pd.DataFrame(source_data)
            df_source = df_source.sort_values("Amount", ascending=False).reset_index(drop=True)
            dataframes["Total Damage Done by Source"] = df_source
    
    # 2. Total Damage Taken by Target
    if damage_data["damage_taken"]:
        target_data = []
        for target, values in damage_data["damage_taken"].items():
            target_data.append({
                "Target": target,
                "Amount": values[0],
                "Percentage": values[2] if len(values) > 2 else 0
            })
        
        if target_data:
            df_target = pd.DataFrame(target_data)
            df_target = df_target.sort_values("Amount", ascending=False).reset_index(drop=True)
            dataframes["Total Damage Taken by Target"] = df_target
    
    # 3. Total Damage by Attack Type
    if damage_data["damage_types"]:
        damage_type_data = []
        for key, values in damage_data["damage_types"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source = parts[0]
                attack_type = parts[1]
                
                damage_type_data.append({
                    "Source": source,
                    "Attack Type": attack_type,
                    "Amount": values[0],
                    "Hits": values[1],
                    "Avg. Damage": values[3] if len(values) > 3 else values[0]/values[1],
                    "Percentage": values[2] if len(values) > 2 else 0
                })
        
        if damage_type_data:
            df_type = pd.DataFrame(damage_type_data)
            df_type = df_type.sort_values(["Source", "Amount"], ascending=[True, False]).reset_index(drop=True)
            dataframes["Total Damage by Attack Type"] = df_type
    
    # 4. Total Damage Taken by Type
    if damage_data["damage_details"]:
        damage_taken_data = []
        for key, values in damage_data["damage_details"].items():
            parts = key.split(" -> ")
            if len(parts) == 2:
                source, target = parts
                damage_type = values[2] if len(values) > 2 else "unknown"
                
                damage_taken_data.append({
                    "Target": target,
                    "Type": damage_type,
                    "Amount": values[0],
                    "Source": source,
                    "Hits": values[1],
                    "Avg. Damage": values[4] if len(values) > 4 else values[0]/values[1],
                    "Percentage": values[3] if len(values) > 3 else 0
                })
        
        if damage_taken_data:
            df_taken = pd.DataFrame(damage_taken_data)
            df_taken = df_taken.sort_values(["Target", "Amount"], ascending=[True, False]).reset_index(drop=True)
            dataframes["Total Damage Taken by Type"] = df_taken
    
    # Export based on format type
    if format_type == "CSV":
        # Combine all DataFrames with headers
        buffer = io.StringIO()
        for name, df in dataframes.items():
            buffer.write(f"--- {name} ---\n")
            df.to_csv(buffer, index=False)
            buffer.write("\n\n")
        return buffer.getvalue()
        
    elif format_type == "Excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            for name, df in dataframes.items():
                sheet_name = name[:31]  # Excel limits sheet names to 31 chars
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        buffer.seek(0)
        return buffer.getvalue()
        
    else:  # Text format
        buffer = io.StringIO()
        for name, df in dataframes.items():
            buffer.write(f"{'=' * 30} {name.upper()} {'=' * 30}\n")
            
            # Format based on which table we're displaying
            if "Attack Type" in name:
                buffer.write("%-20s %-15s %12s %5s %8s %5s\n" % 
                           ("SOURCE", "ATTACK TYPE", "AMOUNT", "HITS", "AVG.DMG", "PERC"))
                buffer.write("-" * 100 + "\n")
                
                for _, row in df.iterrows():
                    buffer.write("%-20s %-15s %12.1f %5d %8.1f %5.1f%%\n" % (
                        str(row["Source"])[:20],
                        str(row["Attack Type"])[:15],
                        row["Amount"],
                        row["Hits"],
                        row["Avg. Damage"],
                        row["Percentage"] if isinstance(row["Percentage"], (int, float)) else 
                            float(str(row["Percentage"]).rstrip("%"))
                    ))
            elif "Taken by Type" in name:
                buffer.write("%-20s %-15s %12s %-20s %5s %8s %5s\n" % 
                           ("TARGET", "TYPE", "AMOUNT", "SOURCE", "HITS", "AVG.DMG", "PERC"))
                buffer.write("-" * 100 + "\n")
                
                for _, row in df.iterrows():
                    buffer.write("%-20s %-15s %12.1f %-20s %5d %8.1f %5.1f%%\n" % (
                        str(row["Target"])[:20],
                        str(row["Type"])[:15],
                        row["Amount"],
                        str(row["Source"])[:20],
                        row["Hits"],
                        row["Avg. Damage"],
                        row["Percentage"] if isinstance(row["Percentage"], (int, float)) else 
                            float(str(row["Percentage"]).rstrip("%"))
                    ))
            else:
                # Source or Target summary reports
                column = "Source" if "Done by Source" in name else "Target"
                buffer.write("%-30s %12s %5s\n" % 
                           (column.upper(), "AMOUNT", "PERC"))
                buffer.write("-" * 50 + "\n")
                
                for _, row in df.iterrows():
                    buffer.write("%-30s %12.1f %5.1f%%\n" % (
                        str(row[column])[:30],
                        row["Amount"],
                        row["Percentage"] if isinstance(row["Percentage"], (int, float)) else 
                            float(str(row["Percentage"]).rstrip("%"))
                    ))
            
            buffer.write("\n\n")
        
        return buffer.getvalue()