import streamlit as st
import os
import base64
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

# 🧠 Helper functions to load background images
def _get_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "dslb_mascot.png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def _get_mobile_base64_image():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "dslb_mascot_mobile.png")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 💅 Global style tweaks (mascot + mobile handling)
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
    footer {visibility: hidden;}
    .css-164nlkn {display: none;}

    /* 🧙 Background Mascot */
    .mascot-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: url("data:image/png;base64,%s");
        background-repeat: no-repeat;
        background-position: right center;
        background-size: cover;
        opacity: 1.0;
        z-index: 0;
        pointer-events: none;
    }

    /* 📱 Mobile mascot image – centered, scaled, clean */
    @media screen and (max-width: 768px) {
        .mascot-background {
            background-image: url("data:image/png;base64,%s");
            background-position: center top;
            background-size: contain;
            width: 100vw;
            height: 100vh;
            opacity: 1.0;
        }
    }

    .welcome-foreground {
        position: relative;
        z-index: 1;
    }

    html, body {
        overflow: hidden;
    }
    </style>
""" % (_get_base64_image(), _get_mobile_base64_image()), unsafe_allow_html=True)

# 📍 Sidebar nav
with st.sidebar:
    st.title("DSL Buddy")
    page = st.radio("Choose a tab:", [
        "🏰 Welcome",
        "🧭 Directions", 
        "⚔️ Weapons",
        "💫 Spell & Skill Effects", 
        "🌀 Gateposts",
        "✨ Summons",
        "📖 Bestiary",
        "🌕 Moon Tracker",
        "🧬 Race/Class Comparison"
    ], key="page")

# 🧙 Welcome screen
def show_welcome_page():
    st.markdown('<div class="mascot-background"></div>', unsafe_allow_html=True)
    st.markdown('<div class="welcome-foreground">', unsafe_allow_html=True)

    st.title("🧙‍♂️ Welcome to DSL Buddy")

    st.markdown("""
        <div style='font-size:20px; margin-top:1rem;'>
            Your personal buddy for all things DSL!
        </div>
        <div style='margin-top:2rem;'>
    """, unsafe_allow_html=True)

    nav_links = [
        ("🧭 Directions!", "🧭 Directions"),
        ("⚔️ Weapons!", "⚔️ Weapons"),
        ("💫 Spell & Skill Effects!", "💫 Spell & Skill Effects"),
        ("🌀 Gateposts!", "🌀 Gateposts"),
        ("✨ Summons!", "✨ Summons"),
        ("📖 Bestiary!", "📖 Bestiary"),
        ("🌕 Moon Tracker FOR MAXIMUM GAINS!", "🌕 Moon Tracker"),
        ("🧬 Race/Class Comparison!", "🧬 Race/Class Comparison"),
    ]

    for text, tab in nav_links:
        if st.button(text, key=tab):
            st.session_state.temp_page = tab
            st.rerun()

    st.markdown("""
        </div> <!-- close buttons div -->
        <div style='margin-top:3rem; font-size:20px; color:gray;'>
            © Tyltech, 2025. 🧙‍♂️👊
        </div>
        </div> <!-- close welcome-foreground -->
    """, unsafe_allow_html=True)

# 🔀 Page router
if page == "🏰 Welcome":
    show_welcome_page()
elif page == "🧭 Directions":
    show_directions_page()
elif page == "⚔️ Weapons":
    show_weapons_page()
elif page == "💫 Spell & Skill Effects":
    show_effects_page()
elif page == "🌀 Gateposts":
    show_gateposts_page()
elif page == "✨ Summons":
    show_summons_page()
elif page == "📖 Bestiary":
    show_bestiary_page()
elif page == "🌕 Moon Tracker":
    show_moon_page()
elif page == "🧬 Race/Class Comparison":
    show_comparison_page()
