import streamlit as st
from weapons.weapons_page import show_weapons_page
from directions.directions_page import show_directions_page
from gateposts.gateposts_page import show_gateposts_page
from summons.summons_page import show_summons_page
from bestiary.bestiary_page import show_bestiary_page
from comparison.comparison_page import show_comparison_page
from moon.moon_page import show_moon_page

st.set_page_config(page_title="DSL Buddy", layout="wide")

# Style tweaks
st.markdown("""
    <style>
    div[data-baseweb="radio"] > div {
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar nav
with st.sidebar:
    st.title("DSL Buddy")

    page = st.radio("Choose a tab:", [
        "🏠 Welcome",
        "🌕 Moon Tracker",
        "⚔️ Weapons",
        "🧭 Directions",
        "🚪 Gateposts",
        "🪄 Summons",
        "📖 Bestiary",
        "🧬 Race/Class Comparison"
    ])

# Snazzy landing page
def show_welcome_page():
    st.title("🎉 Welcome to DSL Buddy")
    st.markdown("""
        <div style='font-size:20px; margin-top:1rem;'>
            ✨ Your personal sidekick for all things DSL!  
            Explore spells, weapons, monsters, and more — all in one place.
        </div>
        <div style='margin-top:2rem;'>
            <ul style='font-size:18px;'>
                <li>🌙 Track the moon cycles</li>
                <li>🗡️ Manage your weapons arsenal</li>
                <li>📍 Navigate zones with clear directions</li>
                <li>🚪 Plan gateposts and summons with ease</li>
                <li>📚 Browse beasts in the bestiary</li>
                <li>🧬 Compare races and classes side-by-side</li>
            </ul>
        </div>
        <div style='margin-top:3rem; font-size:16px; color:gray;'>
            Built with love, coffee, and a whole lotta spell slots. 🧙‍♂️
        </div>
    """, unsafe_allow_html=True)

# Page logic
if page == "🏠 Welcome":
    show_welcome_page()
elif page == "⚔️ Weapons":
    show_weapons_page()
elif page == "🧭 Directions":
    show_directions_page()
elif page == "🚪 Gateposts":
    show_gateposts_page()
elif page == "🪄 Summons":
    show_summons_page()
elif page == "📖 Bestiary":
    show_bestiary_page()
elif page == "🧬 Race/Class Comparison":
    show_comparison_page()
elif page == "🌕 Moon Tracker":
    show_moon_page()
