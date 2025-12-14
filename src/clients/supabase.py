from supabase import create_client, Client
from configs.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY.get_secret_value())
