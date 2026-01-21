"""
API Module - Flask REST API

Exporta:
- app: Aplicação Flask principal
- socketio: Socket.IO para tempo real
"""

from .flask_api_fixed import app, socketio

__all__ = [
    'app',
    'socketio'
]
