from supabase import create_client
import os

# Load from environment or hardcode for now
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bwbpqfqlmygtdgknxtco.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ3YnBxZnFsbXlndGRna254dGNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4ODIyMTEsImV4cCI6MjA1OTQ1ODIxMX0.VlSTC-zr0COPginV8CVjpc1auFldlfAws2bos5-VjEg")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
