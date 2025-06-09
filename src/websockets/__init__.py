#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analyDesign WebSocket模块
提供实时通信功能
"""

from .websocket_server import app, socketio, create_app

__all__ = [
    'app',
    'socketio', 
    'create_app'
]

__version__ = "1.0.0"
__description__ = "analyDesign WebSocket实时通信模块" 