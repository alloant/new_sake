from broadcaster import Broadcast

# Create ONLY ONE instance here
# Use a production-ready URL (e.g., from env vars)
broadcast = Broadcast("redis://localhost:6379")
