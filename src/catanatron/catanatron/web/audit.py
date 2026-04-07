"""
Module: 8. Backend API Server
Author: Forked
Date: 2025-12-03
Purpose: Implements the audit module for the backend API server, supporting request handling, services, or backend integration logic.
"""

import logging

from catanatron.web.models import UserStart, db


LOGGER = logging.getLogger(__name__)


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


def log_game_start(request) -> bool:
    ip_address = get_request_ip(request) or "unknown"

    try:
        db.session.add(UserStart.from_ip(ip_address))
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        LOGGER.exception("Failed to write game start audit log")
        return False
