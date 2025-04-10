import streamlit as st
import datetime
import re
import pytz

# Eastern Time Zone
eastern = pytz.timezone('US/Eastern')

def show_moon_page():
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🌕 Moon Tracker")

        # 🧩 Tight spacing: expanders under header
        with st.expander("🌗 Enter Moon Data Manually", expanded=False):
            colf1, colf2, colf3 = st.columns([3, 3, 3])

            # Moon Color Dropdown (capitalized options, placeholder)
            moon_color = colf1.selectbox(
                label="",
                options=["Red", "White", "Black"],
                index=None,
                placeholder="🌈 Color",
                key="moon_color"
            )

            # Current Phase Dropdown (capitalized options, placeholder)
            current_phase = colf2.selectbox(
                label="",
                options=[
                    "Full", "Waning 3/4", "Half Waning", "Crescent Waning",
                    "Empty", "Crescent Waxing", "Half Waxing", "Waxing 3/4"
                ],
                index=None,
                placeholder="🌓 Phase",
                key="current_phase"
            )

            # Cycles Remaining text input
            cycles_remaining = colf3.text_input(
                label="",
                value="",
                key="cycles_remaining",
                placeholder="⏳ Cycles Remaining"
            )

            if st.button("🔮 Calculate Phase"):
                if not moon_color or not current_phase:
                    st.warning("Please select both Color and Phase.")
                else:
                    try:
                        cycles_remaining_int = int(cycles_remaining) if cycles_remaining else 0
                        st.session_state["moon_triggered"] = True
                        st.session_state["moon_color"] = moon_color.lower()
                        st.session_state["current_phase"] = current_phase.lower()
                        st.session_state["cycles_remaining"] = cycles_remaining_int
                    except ValueError:
                        st.warning("Please enter a valid number for Cycles Remaining.")



        with st.expander("📋 Paste Moon Data From Client", expanded=False):
            user_input = st.text_area("Moon Data:", height=100)

            if st.button("🔮 Calculate Phase "):
                moon_color, current_phase, cycles_remaining = parse_single_moon_data(user_input)
                if not (moon_color and current_phase and cycles_remaining is not None):
                    st.warning("Unable to parse all required information (moon color, phase, cycles remaining). Please check your pasted data.")
                    return
                st.session_state["moon_triggered"] = True
                st.session_state["moon_color"] = moon_color
                st.session_state["current_phase"] = current_phase
                st.session_state["cycles_remaining"] = cycles_remaining

            st.markdown(
                """
                <style>
                textarea {
                    font-size: 0.8em;
                }
                </style>
                """, unsafe_allow_html=True)
            st.markdown("""
            Paste the relevant lines from your client. For example:
            <div style="
                font-size: 1.0em; 
                background-color: rgba(240,242,246,0.15); 
                padding: 0px 4px 6px 4px; 
                border-radius: 5px; 
                white-space: pre-wrap; 
                line-height: 1.2;
            ">The red moon is crescent waxing and not visible.
               [Mana +10%] [Saves -2] [Casting +2] [Regen 0%] [Cycles remaining 69 (34 1/2 Hours)]
            </div>
            """, unsafe_allow_html=True)









    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("moon_triggered") and all(k in st.session_state for k in ["moon_color", "current_phase", "cycles_remaining"]):
        ticks_per_phase = {"white": 108, "red": 86, "black": 66}.get(st.session_state["moon_color"], 86)
        results = compute_upcoming_phases(
            moon_color=st.session_state["moon_color"],
            current_phase=st.session_state["current_phase"],
            cycles_remaining=int(st.session_state["cycles_remaining"]),
            ticks_per_phase=ticks_per_phase
        )

        if results:
            st.subheader(f"Upcoming Phases for the {st.session_state['moon_color'].capitalize()} Moon")
            st.dataframe(results, use_container_width=True)
        else:
            st.info("No upcoming phases could be computed. Check your data format.")

def parse_single_moon_data(user_input: str):
    moon_phases = ["full", "waning 3/4", "half waning", "crescent waning",
                   "empty", "crescent waxing", "half waxing", "waxing 3/4"]

    lines = user_input.lower().split("\n")
    moon_color = current_phase = cycles_remaining = None
    red_line = white_line = black_line = ""

    cleaned_lines = [line.replace("three-quarters", "3/4").strip() for line in lines]

    for line in cleaned_lines:
        if "red moon" in line: red_line = line
        elif "white moon" in line: white_line = line
        elif "black moon" in line: black_line = line

        for phase in moon_phases:
            if phase in line:
                current_phase = phase
                break

        match = re.search(r'cycles remaining\s+(\d+)', line)
        if match:
            cycles_remaining = int(match.group(1))

    if cycles_remaining is not None:
        if "red moon" in red_line: moon_color = "red"
        elif "white moon" in white_line: moon_color = "white"
        elif "black moon" in black_line: moon_color = "black"

    return moon_color, current_phase, cycles_remaining

def compute_upcoming_phases(moon_color, current_phase, cycles_remaining, ticks_per_phase):
    SECONDS_PER_TICK = 42
    moon_phases = ["full", "waning 3/4", "half waning", "crescent waning",
                   "empty", "crescent waxing", "half waxing", "waxing 3/4"]

    if current_phase not in moon_phases: return []

    phase_index = moon_phases.index(current_phase)
    now = datetime.datetime.now(eastern)
    results = []

    for _ in range(24):
        phase_index = (phase_index + 1) % len(moon_phases)
        upcoming_phase = moon_phases[phase_index]

        seconds_until_phase = cycles_remaining * SECONDS_PER_TICK
        phase_start_time = now + datetime.timedelta(seconds=seconds_until_phase)
        phase_start_time = phase_start_time.astimezone(eastern)

        results.append({
            "Moon": moon_color.capitalize(),
            "Upcoming Phase": upcoming_phase,
            "Phase Begins": phase_start_time.strftime("%I:%M %p, %m/%d"),
            "Time Until": format_duration(seconds_until_phase)
        })

        cycles_remaining += ticks_per_phase

    return results

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0: parts.append(f"{hours} hr")
    if minutes > 0: parts.append(f"{minutes} min")
    if seconds > 0: parts.append(f"{seconds} sec")
    return " ".join(parts)
