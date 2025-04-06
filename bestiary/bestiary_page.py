import streamlit as st
from shared.supabase_client import supabase

def show_bestiary_page():
    st.header("📖 Bestiary")

    try:
        response = supabase.table("bestiary").select("*").execute()
        data = response.data

        if data:
            st.write("Creatures of DSL:")
            st.dataframe(data, use_container_width=True)
        else:
            st.warning("No bestiary entries found.")
    except Exception as e:
        st.error("Failed to load bestiary data from Supabase.")
        st.exception(e)