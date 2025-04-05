import streamlit as st
import datetime
import re

def show_moon_page():
    st.subheader("Moon Tracker (Single Moon)")
    st.write(
        "Paste **only the relevant lines** from your client for one moon.\n\n"
        "Example:\n"
        "```\n"
        "The red moon is crescent waxing and not visible.\n"
        "[Mana +10%] [Saves -2] [Casting +2] [Regen 0%] [Cycles remaining 19 (9 1/2 Hours)]\n"
        "```"
    )

    user_input = st.text_area("Moon Data:", height=150)

    if st.button("Calculate Next Phases"):
        # Attempt to parse the moon color, current phase, and cycles remaining
        moon_color, current_phase, cycles_remaining = parse_single_moon_data(user_input)

        if not (moon_color and current_phase and cycles_remaining is not None):
            st.warning(
                "Unable to parse all required information (moon color, phase, cycles remaining).\n"
                "Please check your pasted data."
            )
            return

        # Determine tick count based on which moon
        ticks_per_phase = {
            "white": 108,
            "red":   86,
            "black": 66
        }.get(moon_color, 86)  # Default to 86 if color unknown

        # Compute the next 8 phases
        results = compute_upcoming_phases(
            moon_color=moon_color,
            current_phase=current_phase,
            cycles_remaining=cycles_remaining,
            ticks_per_phase=ticks_per_phase
        )

        # Display results
        if results:
            st.dataframe(results)
        else:
            st.info("No upcoming phases could be computed. Check your data format.")


def parse_single_moon_data(user_input: str):
    """
    Searches the user_input for:
      - 'red moon', 'white moon', or 'black moon'
      - A recognized phase from the cycle
      - The integer cycles_remaining
    Returns (moon_color, current_phase, cycles_remaining) or (None, None, None).
    """
    moon_phases = [
        "full",
        "waning 3/4",
        "half waning",
        "crescent waning",
        "empty",
        "crescent waxing",
        "half waxing",
        "waxing 3/4"
    ]

    lines = user_input.lower().split("\n")
    
    moon_color = None
    current_phase = None
    cycles_remaining = None

    # Normalize 'three-quarters' -> '3/4' if present
    cleaned_lines = []
    for line in lines:
        line = line.replace("three-quarters", "3/4")
        cleaned_lines.append(line.strip())
    
    for line in cleaned_lines:
        # Detect the color of moon
        if "red moon" in line:
            moon_color = "red"
        elif "white moon" in line:
            moon_color = "white"
        elif "black moon" in line:
            moon_color = "black"
        
        # Detect a known phase
        for phase in moon_phases:
            if phase in line:
                current_phase = phase
                break

        # Detect the cycles remaining
        match = re.search(r'cycles remaining\s+(\d+)', line)
        if match:
            cycles_remaining = int(match.group(1))

    return moon_color, current_phase, cycles_remaining


def compute_upcoming_phases(moon_color: str, current_phase: str,
                            cycles_remaining: int, ticks_per_phase: int):
    """
    Given the current phase and cycles_remaining for a single moon,
    compute the next 8 phases and when they begin.
    """
    # Each 'tick' is about 42 seconds in your original code
    SECONDS_PER_TICK = 42

    moon_phases = [
        "full",
        "waning 3/4",
        "half waning",
        "crescent waning",
        "empty",
        "crescent waxing",
        "half waxing",
        "waxing 3/4"
    ]
    if current_phase not in moon_phases:
        return []
    
    phase_index = moon_phases.index(current_phase)
    now = datetime.datetime.now()
    results = []

    # Generate next 8 phases
    for _ in range(8):
        phase_index = (phase_index + 1) % len(moon_phases)
        upcoming_phase = moon_phases[phase_index]

        seconds_until_phase = cycles_remaining * SECONDS_PER_TICK
        phase_start_time = now + datetime.timedelta(seconds=seconds_until_phase)

        results.append({
            "Moon": moon_color.capitalize(),
            "Upcoming Phase": upcoming_phase,
            "Phase Begins": phase_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Time Until": format_duration(seconds_until_phase)
        })

        # Move to the next set of cycles
        cycles_remaining += ticks_per_phase

    return results


def format_duration(seconds: int) -> str:
    """Convert a total number of seconds into a more readable string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours} hr")
    if minutes > 0:
        parts.append(f"{minutes} min")
    if seconds > 0:
        parts.append(f"{seconds} sec")
    return " ".join(parts)
