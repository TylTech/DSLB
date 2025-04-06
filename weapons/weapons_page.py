import streamlit as st
from shared.supabase_client import supabase

def show_weapons_page():
    st.header("⚔️ Weapons")

    try:
        response = supabase.table("weapons").select("*").execute()
        data = response.data

        if not data:
            st.warning("No weapon data found.")
        else:
            st.write("Weapons Database:")
            st.dataframe(data)

    except Exception as e:
        st.error("Failed to load weapons data from Supabase.")
        st.exception(e)
