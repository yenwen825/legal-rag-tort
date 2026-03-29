from redis import Redis
import os
from dotenv import load_dotenv
import logging
load_dotenv()


_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try: 
            redis_url = os.getenv('REDIS_URL')
            if redis_url is None or redis_url.strip() == '':
                logging.warning("REDIS_URL is not set")
                return None
            _redis_client = Redis.from_url(redis_url)
            ping = _redis_client.ping()
            if not ping:
                logging.warning("Failed to connect to Redis")
                _redis_client = None
                return None
        except Exception as e:
            logging.warning(f"Failed to connect to Redis: {e}")
            return None
    return _redis_client

def close_redis_client():
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
        except Exception as e:
            logging.warning(f"Failed to close Redis: {e}")
        _redis_client = None