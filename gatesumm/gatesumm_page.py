import streamlit as st
from shared.supabase_client import supabase

def show_gatesumm_page():
    st.header("🚪 Gateposts & Summons")
    try:
        response = supabase.table("gateposts").select("*").execute()
        data = response.data
        st.write("Gateposts data:")
        st.dataframe(data)
    except Exception as e:
        st.error("Failed to load gateposts from Supabase.")
        st.exception(e)
