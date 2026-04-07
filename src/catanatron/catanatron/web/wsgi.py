"""
Module: 8. Backend API Server
Author: Forked
Date: 2026-01-29
Purpose: Implements the wsgi module for the backend API server, supporting request handling, services, or backend integration logic.
"""

from catanatron.web import create_app

app = create_app()
