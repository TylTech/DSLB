import streamlit as st
from shared.supabase_client import supabase

def show_directions_page():
    st.header("🧭 Directions")

    try:
        response = supabase.table("directions").select("*").execute()
        data = response.data

        if not data:
            st.warning("No direction data found.")
        else:
            st.write("Directions Database:")
            st.dataframe(data)

    except Exception as e:
        st.error("Failed to load directions data from Supabase.")
        st.exception(e)
