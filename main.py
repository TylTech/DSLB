import streamlit as st
from weapons.weapons_page import show_weapons_page
from effects.effects_page import show_effects_page
from directions.directions_page import show_directions_page
from gateposts.gateposts_page import show_gateposts_page
from summons.summons_page import show_summons_page
from bestiary.bestiary_page import show_bestiary_page
from comparison.comparison_page import show_comparison_page
from moon.moon_page import show_moon_page

st.set_page_config(page_title="DSL Buddy", layout="wide")

# ✅ Handle welcome page button nav without breaking widget key binding
if "temp_page" in st.session_state:
    st.session_state.page = st.session_state.temp_page
    del st.session_state.temp_page

# 💅 Style tweaks
st.markdown("""
    <style>
    div[data-baseweb="radio"] > div {
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: none;
        color: #444;
        font-size: 18px;
        text-align: left;
        padding: 0;
        margin: 0 0 2px 0;
        border: none;
        cursor: pointer;
    }
    .stButton>button:hover {
        text-decoration: underline;
        color: black;
    }
    /* 🔒 Hide GitHub footer link */
    footer {visibility: hidden;}
    .css-164nlkn {display: none;}  /* Extra layer for some Streamlit versions */
    </style>
""", unsafe_allow_html=True)

# 📍 Sidebar nav
with st.sidebar:
    st.title("DSL Buddy")
    page = st.radio("Choose a tab:", [
        "🏰 Welcome",
        "⚔️ Weapons",
        "🧭 Directions",
        "💫 Spell & Skill Effects", 
        "🌀 Gateposts",
        "✨ Summons",
        "📖 Bestiary",
        "🧬 Race/Class Comparison",
        "🌕 Moon Tracker"
    ], key="page")

# 🧙 Welcome screen
def show_welcome_page():
    st.title("🧙‍♂️ Welcome to DSL Buddy")
    st.markdown("""
        <div style='font-size:20px; margin-top:1rem;'>
            Your personal buddy for all things DSL!
        </div>
        <div style='margin-top:2rem;'>
    """, unsafe_allow_html=True)

    nav_links = [
        ("⚔️ Weapons!", "⚔️ Weapons"),
        ("🧭 Directions!", "🧭 Directions"),
        ("💫 Spell & Skill Effects!", "💫 Spell & Skill Effects"),
        ("🌀 Gateposts!", "🌀 Gateposts"),
        ("✨ Summons!", "✨ Summons"),
        ("📖 Bestiary!", "📖 Bestiary"),
        ("🧬 Race/Class Comparison!", "🧬 Race/Class Comparison"),
        ("🌕 Moon Tracker FOR MAXIMUM GAINS!", "🌕 Moon Tracker"),
    ]

    for text, tab in nav_links:
        if st.button(text, key=tab):
            st.session_state.temp_page = tab
            st.rerun()

    st.markdown("""
        </div>
        <div style='margin-top:3rem; font-size:16px; color:gray;'>
            © Tyltech, 2025. 🧙‍♂️👊
        </div>
    """, unsafe_allow_html=True)

# 🧭 Page router
if page == "🏰 Welcome":
    show_welcome_page()
elif page == "⚔️ Weapons":
    show_weapons_page()
elif page == "🧭 Directions":
    show_directions_page()
elif page == "💫 Spell & Skill Effects":
    show_effects_page()
elif page == "🌀 Gateposts":
    show_gateposts_page()
elif page == "✨ Summons":
    show_summons_page()
elif page == "📖 Bestiary":
    show_bestiary_page()
elif page == "🧬 Race/Class Comparison":
    show_comparison_page()
elif page == "🌕 Moon Tracker":
    show_moon_page()