import redis
from config import VALKEY_HOST, VALKEY_PORT

r = redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT, decode_responses=True)

def ping() -> bool:
    try:
        return r.ping()
    except Exception:
        return False

def get_client():
    return r
