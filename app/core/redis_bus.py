from broadcaster import Broadcast
from app.core.config import settings

# Create ONLY ONE instance here
# Use a production-ready URL (e.g., from env vars)
broadcast = Broadcast(settings.REDIS_URL)
