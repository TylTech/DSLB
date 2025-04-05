import streamlit as st
from weapons.weapons_page import show_weapons_page
from directions.directions_page import show_directions_page
from gatesumm.gatesumm_page import show_gatesumm_page
from bestiary.bestiary_page import show_bestiary_page
from comparison.comparison_page import show_comparison_page
from moon.moon_page import show_moon_page

st.set_page_config(page_title="DSL Buddy", layout="wide")

# Inject a little style to space out the radio buttons
st.markdown("""
    <style>
    div[data-baseweb="radio"] > div {
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("DSL Buddy")

    page = st.radio("Choose a tab:", [
        "🌕 Moon Tracker",
        "⚔️ Weapons",
        "🧭 Directions",
        "🚪 Gateposts & Summons",
        "📖 Bestiary",
        "🧬 Race/Class Comparison"
    ])

# Page routing logic
if page == "⚔️ Weapons":
    show_weapons_page()
elif page == "🧭 Directions":
    show_directions_page()
elif page == "🚪 Gateposts & Summons":
    show_gatesumm_page()
elif page == "📖 Bestiary":
    show_bestiary_page()
elif page == "🧬 Race/Class Comparison":
    show_comparison_page()
elif page == "🌕 Moon Tracker":
    show_moon_page()
