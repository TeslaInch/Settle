from supabase import create_client, Client

from core.config import settings

# Initialize Supabase client for backend operations
# Using service key for full access (backend only)
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
)
