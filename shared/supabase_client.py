from supabase import create_client
import os

# Load from environment or hardcode for now
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ilzmnjncspqnlfblludv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlsem1uam5jc3BxbmxmYmxsdWR2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwNDIwOTMsImV4cCI6MjA1OTYxODA5M30.MprmH1nNY9bY28dhN9mo4lHhW0dwA6HEHd9nUbIa2js")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
