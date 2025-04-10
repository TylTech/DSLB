import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from shared.supabase_client import supabase

def show_comparison_page():
    st.title("🧬 Race/Class Comparison")

    # Home button aligned to top-right
    col1, col2 = st.columns([8, 1])
    with col2:
        st.markdown("<div style='padding-top: 18px; padding-left: 8px;'>", unsafe_allow_html=True)
        if st.button("🏰 Home"):
            st.session_state["temp_page"] = "🏰 Welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    @st.cache_data(ttl=60)
    def load_combos():
        response = supabase.table("raceclass").select("*").execute()
        return pd.DataFrame(response.data)

    df = load_combos()
    if df.empty:
        st.warning("No race/class data found.")
        return

    # Prepare Comparison Filters - Dropdown filter with all options inside one dropdown
    with st.expander("🛠️ Prepare Comparison", expanded=True):
        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])

        with filter_col1:
            race_opts = ["All"] + sorted(df["Race"].dropna().unique().tolist())
            selected_races = st.selectbox("Race(s)", options=race_opts)
            if selected_races == "All":
                selected_races = df["Race"].unique().tolist()

        with filter_col2:
            class_opts = ["All"] + sorted(df["Class"].dropna().unique().tolist())
            selected_classes = st.selectbox("Class(es)", options=class_opts)
            if selected_classes == "All":
                selected_classes = df["Class"].unique().tolist()

        with filter_col3:
            boost_opts = ["All"] + sorted(df["Boost"].dropna().unique().tolist())
            selected_boosts = st.selectbox("Boost(s)", options=boost_opts)
            if selected_boosts == "All":
                selected_boosts = df["Boost"].unique().tolist()

        gender = st.radio("Gender", ["Male", "Female"], horizontal=True)

        # Clear Filters Button
        clear_button = st.button("Clear Filters")
        if clear_button:
            selected_races = ["All"]
            selected_classes = ["All"]
            selected_boosts = ["All"]
            gender = "Male"
            st.experimental_rerun()  # To reset the page and filters

    # Generate Comparison Button
    generate = st.button("🚀 Generate Comparison")

    # Generate comparison logic
    if generate:
        filtered_df = df.copy()

        # Ensure we handle the filters as lists
        if isinstance(selected_races, str):
            selected_races = [selected_races]
        if isinstance(selected_classes, str):
            selected_classes = [selected_classes]
        if isinstance(selected_boosts, str):
            selected_boosts = [selected_boosts]

        filtered_df = filtered_df[filtered_df["Race"].isin(selected_races)]
        filtered_df = filtered_df[filtered_df["Class"].isin(selected_classes)]
        filtered_df = filtered_df[filtered_df["Boost"].isin(selected_boosts)]

        if gender == "Male":
            filtered_df["STR"] += 2
        else:
            filtered_df["WIS"] += 2

        # Apply minimum stat filters
        min_str = st.number_input("Min Strength", 0, 100, 0, help="Minimum Strength")
        min_int = st.number_input("Min Intelligence", 0, 100, 0, help="Minimum Intelligence")
        min_wis = st.number_input("Min Wisdom", 0, 100, 0, help="Minimum Wisdom")
        min_dex = st.number_input("Min Dexterity", 0, 100, 0, help="Minimum Dexterity")
        min_con = st.number_input("Min Constitution", 0, 100, 0, help="Minimum Constitution")

        filtered_df = filtered_df[
            (filtered_df["STR"] >= min_str) &
            (filtered_df["INT"] >= min_int) &
            (filtered_df["WIS"] >= min_wis) &
            (filtered_df["DEX"] >= min_dex) &
            (filtered_df["CON"] >= min_con)
        ]

        # Calculating new columns
        filtered_df["TOT"] = filtered_df["STR"] + filtered_df["INT"] + filtered_df["WIS"] + filtered_df["DEX"] + filtered_df["CON"]
        filtered_df["S+D"] = filtered_df["STR"] + filtered_df["DEX"]
        filtered_df["S+D+I"] = filtered_df["STR"] + filtered_df["DEX"] + filtered_df["INT"]

        # Storing in session state for later use
        st.session_state["comparison_df"] = filtered_df
        st.experimental_rerun()

    # Display the resulting comparison table
    if "comparison_df" in st.session_state and not st.session_state["comparison_df"].empty:
        st.subheader("🧾 Matching Combinations")
        st.dataframe(
            st.session_state["comparison_df"].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No results yet. Use the filters above and click 🚀 Generate Comparison!")

    # Minimum stat requirements section in a horizontal row below the table
    st.markdown("### 📊 Minimum Stat Requirements")
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        min_str = st.number_input("Min Strength", 0, 100, 0)
    with col2:
        min_int = st.number_input("Min Intelligence", 0, 100, 0)
    with col3:
        min_wis = st.number_input("Min Wisdom", 0, 100, 0)
    with col4:
        min_dex = st.number_input("Min Dexterity", 0, 100, 0)
    with col5:
        min_con = st.number_input("Min Constitution", 0, 100, 0)
