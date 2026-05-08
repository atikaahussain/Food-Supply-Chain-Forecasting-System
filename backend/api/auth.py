"""
backend/api/auth.py
-------------------
Authentication endpoints.

POST /api/auth/login  — validate credentials, return JWT
GET  /api/auth/me     — return current user from token
"""
import os
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from backend.database.models import db, User

auth_bp = Blueprint('auth', __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: int, username: str, role: str) -> str:
    """Create a signed JWT valid for 24 hours."""
    secret = current_app.config.get('SECRET_KEY', 'dev-secret-key-atika')
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def _decode_token(token: str) -> dict | None:
    """Decode JWT; return payload dict or None on failure."""
    secret = current_app.config.get('SECRET_KEY', 'dev-secret-key-atika')
    try:
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Body: { "username": "admin", "password": "admin123" }
    Returns: { "token": "<jwt>", "user": { id, username, email, role } }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': 'username and password are required'}), 400

    # ---- 1. Try database lookup first ----
    user = db.session.query(User).filter_by(username=username).first()

    if user and user.check_password(password):
        token = _make_token(user.id, user.username, user.role)
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }
        }), 200

    # ---- 2. Fallback: built-in dev admin (no DB required) ----
    DEV_ADMIN_USER = os.getenv('DEV_ADMIN_USER', 'admin')
    DEV_ADMIN_PASS = os.getenv('DEV_ADMIN_PASS', 'admin123')

    if username == DEV_ADMIN_USER and password == DEV_ADMIN_PASS:
        token = _make_token(0, 'admin', 'admin')
        return jsonify({
            'token': token,
            'user': {
                'id': 0,
                'username': 'admin',
                'email': 'admin@restaurant.com',
                'role': 'admin',
            }
        }), 200

    return jsonify({'error': 'Invalid username or password'}), 401


@auth_bp.route('/me', methods=['GET'])
def me():
    """
    GET /api/auth/me
    Header: Authorization: Bearer <jwt>
    Returns: { "user": { id, username, role } }
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401

    token = auth_header[len('Bearer '):]
    payload = _decode_token(token)

    if payload is None:
        return jsonify({'error': 'Token is invalid or expired'}), 401

    return jsonify({
        'user': {
            'id': payload.get('sub'),
            'username': payload.get('username'),
            'role': payload.get('role'),
        }
    }), 200
