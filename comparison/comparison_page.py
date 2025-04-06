import streamlit as st
from shared.supabase_client import supabase

def show_comparison_page():
    st.header("🧬 Race/Class Comparison")

    try:
        response = supabase.table("raceclass").select("*").execute()
        data = response.data

        if not data:
            st.warning("No data found in the Race/Class database.")
        else:
            st.write("Race/Class Comparison Data:")
            st.dataframe(data)

    except Exception as e:
        st.error("Failed to load Race/Class data from Supabase.")
        st.exception(e)
