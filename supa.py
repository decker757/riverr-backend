from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
db: Client = create_client(url, key)
