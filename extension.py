import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

redis_url = os.environ.get("REDIS_URL", "memory://")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
    # Default global rate limit (max 1000 requests per day)
    default_limits=["1000 per day"]
)
