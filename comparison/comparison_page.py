import streamlit as st
import pandas as pd
from shared.supabase_client import supabase
import streamlit.components.v1 as components

def show_comparison_page():
    st.title("🧬 Race/Class Comparison")

    if "comparison_df" not in st.session_state:
        st.session_state["comparison_df"] = pd.DataFrame()

    st.subheader("🧾 Matching Combinations")
    st.dataframe(
        st.session_state["comparison_df"].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    # Format copy output using monospaced, aligned text
    copy_df = st.session_state["comparison_df"].copy()
    if not copy_df.empty:
        all_columns = copy_df.columns.tolist()
        for col in all_columns:
            max_len = copy_df[col].astype(str).map(len).max()
            copy_df[col] = copy_df[col].astype(str).map(lambda x: x.ljust(max_len))
        tsv_output = copy_df.to_string(index=False)

    col_gen, col_copy = st.columns([1, 1])
    with col_gen:
        generate = st.button("🚀 Generate Comparison!")
    with col_copy:
        if not st.session_state["comparison_df"].empty:
            components.html(f"""
                <textarea id="copyTarget" style="display:none;">{tsv_output}</textarea>
                <button onclick="copyToClipboard()" style="font-size:16px; padding:6px 12px; cursor:pointer; margin-top:6px;">
                    📋 Copy Comparison
                </button>
                <script>
                    function copyToClipboard() {{
                        var textArea = document.getElementById("copyTarget");
                        textArea.style.display = "block";
                        textArea.select();
                        document.execCommand("copy");
                        textArea.style.display = "none";
                    }}
                </script>
            """, height=100)

    @st.cache_data(ttl=60)
    def load_combos():
        response = supabase.table("raceclass").select("*").execute()
        return pd.DataFrame(response.data)

    df = load_combos()
    if df.empty:
        st.warning("No race/class data found.")
        return

    st.subheader("🎯 Filter Options")

    all_races = sorted(df["Race"].unique())
    all_classes = sorted(df["Class"].unique())
    all_boosts = sorted(df["Boost"].dropna().unique())

    selected_races = st.multiselect("Select Race(s)", all_races)
    all_races_toggle = st.checkbox("All Races", value=False)
    if all_races_toggle:
        selected_races = all_races

    selected_classes = st.multiselect("Select Class(es)", all_classes)
    all_classes_toggle = st.checkbox("All Classes", value=False)
    if all_classes_toggle:
        selected_classes = all_classes

    selected_boosts = st.multiselect("Select Boost(s)", all_boosts)
    all_boosts_toggle = st.checkbox("All Boosts", value=False)
    if all_boosts_toggle:
        selected_boosts = all_boosts

    gender = st.radio("Gender", ["Male", "Female"], horizontal=True)

    with st.expander("📊 Minimum Stat Requirements", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            min_str = st.number_input("Min Strength", 0, 100, 0)
            min_int = st.number_input("Min Intelligence", 0, 100, 0)
            min_wis = st.number_input("Min Wisdom", 0, 100, 0)
        with col2:
            min_dex = st.number_input("Min Dexterity", 0, 100, 0)
            min_con = st.number_input("Min Constitution", 0, 100, 0)

    if generate:
        filtered_df = df.copy()

        for col in filtered_df.columns:
            if col.lower() == "id":
                filtered_df = filtered_df.drop(columns=[col])

        stat_cols = ["STR", "INT", "WIS", "DEX", "CON"]
        filtered_df[stat_cols] = filtered_df[stat_cols].apply(pd.to_numeric, errors="coerce")

        if selected_races:
            filtered_df = filtered_df[filtered_df["Race"].isin(selected_races)]
        if selected_classes:
            filtered_df = filtered_df[filtered_df["Class"].isin(selected_classes)]
        if not all_boosts_toggle and selected_boosts:
            filtered_df = filtered_df[filtered_df["Boost"].isin(selected_boosts)]

        if gender == "Male":
            filtered_df["STR"] += 2
        else:
            filtered_df["WIS"] += 2

        filtered_df = filtered_df[
            (filtered_df["STR"] >= min_str) &
            (filtered_df["INT"] >= min_int) &
            (filtered_df["WIS"] >= min_wis) &
            (filtered_df["DEX"] >= min_dex) &
            (filtered_df["CON"] >= min_con)
        ]

        filtered_df["TOT"] = filtered_df["STR"] + filtered_df["INT"] + filtered_df["WIS"] + filtered_df["DEX"] + filtered_df["CON"]
        filtered_df["S+D"] = filtered_df["STR"] + filtered_df["DEX"]
        filtered_df["S+D+I"] = filtered_df["STR"] + filtered_df["DEX"] + filtered_df["INT"]

        all_stat_cols = ["STR", "INT", "WIS", "DEX", "CON", "TOT", "S+D", "S+D+I"]
        filtered_df[all_stat_cols] = filtered_df[all_stat_cols].astype(str)

        st.session_state["comparison_df"] = filtered_df
        st.rerun()
