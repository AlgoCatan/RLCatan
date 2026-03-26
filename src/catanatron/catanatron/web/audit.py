import logging
import os
from datetime import datetime, timezone
from functools import lru_cache

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - handled gracefully when dependency is absent
    MongoClient = None


LOGGER = logging.getLogger(__name__)
MONGODB_DATABASE = "CatanArena"
MONGODB_COLLECTION = "users"


@lru_cache(maxsize=1)
def _get_collection():
    uri = os.environ.get("MONGODB_URI")
    if not uri or MongoClient is None:
        return None

    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return client[MONGODB_DATABASE][MONGODB_COLLECTION]


def get_request_ip(request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.remote_addr


def log_game_start(request):
    collection = _get_collection()
    if collection is None:
        return

    timestamp = datetime.now(timezone.utc)
    document = {
        "_id": timestamp,
        "ip": get_request_ip(request),
        "timestamp": timestamp,
    }

    try:
        collection.insert_one(document)
    except Exception:
        LOGGER.exception("Failed to write game start audit log")
