import streamlit as st
import pandas as pd
from shared.supabase_client import supabase

def show_comparison_page():
    @st.cache_data(ttl=60)
    def load_combos():
        response = supabase.table("raceclass").select("*").execute()
        return pd.DataFrame(response.data)

    df = load_combos()
    if df.empty:
        st.warning("No race/class data found.")
        return

    # 🔽 Option Sets
    race_opts = sorted(df["Race"].dropna().unique().tolist())
    class_opts = sorted(df["Class"].dropna().unique().tolist())
    boost_opts = sorted(df["Boost"].dropna().unique().tolist())

    race_display = ["All Races"] + race_opts
    class_display = ["All Classes"] + class_opts
    boost_display = ["All Boosts"] + boost_opts

    # 🏰 Header + Filter Row
    col1, col2 = st.columns([8, 1])
    with col1:
        st.header("🧬 Race/Class Comparison")

        # 🎛️ Filters (tight under header)
        colf1, colf2, colf3, colf4 = st.columns([3, 3, 3, 3])  # keep uniform column widths
        with colf1:
            selected_races = st.multiselect("", race_display, placeholder="Race")
            if "All Races" in selected_races:
                selected_races = race_opts
        with colf2:
            selected_classes = st.multiselect("", class_display, placeholder="Class")
            if "All Classes" in selected_classes:
                selected_classes = class_opts
        with colf3:
            selected_boosts = st.multiselect("", boost_display, placeholder="Boost")
            if "All Boosts" in selected_boosts:
                selected_boosts = boost_opts
        with colf4:
            gender = st.selectbox("", options=["Male", "Female"])  # ← shows full label now



    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 🚀 Generate Comparison
    if st.button("🚀 Generate Comparison", use_container_width=True):
        filtered_df = df.copy()

        if selected_races:
            filtered_df = filtered_df[filtered_df["Race"].isin(selected_races)]
        if selected_classes:
            filtered_df = filtered_df[filtered_df["Class"].isin(selected_classes)]
        if selected_boosts:
            filtered_df = filtered_df[filtered_df["Boost"].isin(selected_boosts)]

        if gender == "Male":
            filtered_df["STR"] += 2
        else:
            filtered_df["WIS"] += 2

        def get_stat(key):
            val = st.session_state.get(key, "0")
            return int(val) if str(val).isdigit() else 0

        filtered_df = filtered_df[
            (filtered_df["STR"] >= get_stat("min_str")) &
            (filtered_df["INT"] >= get_stat("min_int")) &
            (filtered_df["WIS"] >= get_stat("min_wis")) &
            (filtered_df["DEX"] >= get_stat("min_dex")) &
            (filtered_df["CON"] >= get_stat("min_con"))
        ]

        filtered_df["TOT"] = (
            filtered_df["STR"] + filtered_df["INT"] +
            filtered_df["WIS"] + filtered_df["DEX"] +
            filtered_df["CON"]
        )
        filtered_df["S+D"] = filtered_df["STR"] + filtered_df["DEX"]
        filtered_df["S+D+I"] = filtered_df["STR"] + filtered_df["DEX"] + filtered_df["INT"]

        st.session_state["comparison_df"] = filtered_df
        st.experimental_rerun()

    # 🧾 Results
    if "comparison_df" in st.session_state and not st.session_state["comparison_df"].empty:
        st.subheader("🧾 Matching Combinations")
        st.dataframe(
            st.session_state["comparison_df"].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown("""
        <div style="
            background-color: #fafafa;
            padding: 12px 16px;
            border-radius: 6px;
            color: #444;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        ">
            No results yet.
        </div>
        """, unsafe_allow_html=True)

    # 📊 Minimum Stat Requirements
    with st.expander("📊 Minimum Stat Requirements", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        st.session_state["min_str"] = col1.text_input("Strength", value=st.session_state.get("min_str", "0"))
        st.session_state["min_int"] = col2.text_input("Intelligence", value=st.session_state.get("min_int", "0"))
        st.session_state["min_wis"] = col3.text_input("Wisdom", value=st.session_state.get("min_wis", "0"))
        st.session_state["min_dex"] = col4.text_input("Dexterity", value=st.session_state.get("min_dex", "0"))
        st.session_state["min_con"] = col5.text_input("Constitution", value=st.session_state.get("min_con", "0"))
