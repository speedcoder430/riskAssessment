from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_API_KEY")

supabase: Client = create_client(url, key)
