import streamlit as st
import datetime
import re

def show_moon_page():
    st.title("🌕 Moon Tracker")

    result_container = st.container()  # Placeholder for results display

    moon_color = None
    current_phase = None
    cycles_remaining = None
    triggered = False

    # Manual entry
    with st.expander("🌗 Enter Moon Data", expanded=False):
        moon_color = st.selectbox("Moon Color", ["red", "white", "black"])
        current_phase = st.selectbox("Current Phase", [
            "full",
            "waning 3/4",
            "half waning",
            "crescent waning",
            "empty",
            "crescent waxing",
            "half waxing",
            "waxing 3/4"
        ])
        cycles_remaining = st.number_input("Cycles Remaining", min_value=0, step=1)

        if st.button("🔮 Calculate Phase"):
            triggered = True

    # Pasted input
    with st.expander("📋 Paste Moon Data From Client", expanded=False):
        st.write("""
            Paste **only the relevant lines** from your client for one moon.

            Example:
            ```
            The red moon is crescent waxing and not visible.
            [Mana +10%] [Saves -2] [Casting +2] [Regen 0%] [Cycles remaining 19 (9 1/2 Hours)]
            ```
        """)
        user_input = st.text_area("Moon Data:", height=150)

        if st.button("🔮 Calculate Phase "):
            moon_color, current_phase, cycles_remaining = parse_single_moon_data(user_input)
            if not (moon_color and current_phase and cycles_remaining is not None):
                st.warning("Unable to parse all required information (moon color, phase, cycles remaining). Please check your pasted data.")
                return
            triggered = True

    # Show results at the top of the page if triggered
    if triggered and moon_color and current_phase and cycles_remaining is not None:
        ticks_per_phase = {
            "white": 108,
            "red":   86,
            "black": 66
        }.get(moon_color, 86)

        results = compute_upcoming_phases(
            moon_color=moon_color,
            current_phase=current_phase,
            cycles_remaining=cycles_remaining,
            ticks_per_phase=ticks_per_phase
        )

        with result_container:
            if results:
                st.subheader(f"Upcoming Phases for the {moon_color.capitalize()} Moon")
                st.dataframe(results, use_container_width=True)
            else:
                st.info("No upcoming phases could be computed. Check your data format.")


def parse_single_moon_data(user_input: str):
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

    cleaned_lines = []
    for line in lines:
        line = line.replace("three-quarters", "3/4")
        cleaned_lines.append(line.strip())

    for line in cleaned_lines:
        if "red moon" in line:
            moon_color = "red"
        elif "white moon" in line:
            moon_color = "white"
        elif "black moon" in line:
            moon_color = "black"

        for phase in moon_phases:
            if phase in line:
                current_phase = phase
                break

        match = re.search(r'cycles remaining\s+(\d+)', line)
        if match:
            cycles_remaining = int(match.group(1))

    return moon_color, current_phase, cycles_remaining


def compute_upcoming_phases(moon_color: str, current_phase: str,
                            cycles_remaining: int, ticks_per_phase: int):
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

        cycles_remaining += ticks_per_phase

    return results


def format_duration(seconds: int) -> str:
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
