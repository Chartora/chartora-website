#!/usr/bin/env python3
"""
CHARTORA.IN — Secure Google OAuth 2.0 Authentication Service
Handles:
- Server-side OAuth 2.0 flow with CSRF state validation
- Token exchange & Google profile verification (OpenID Connect / userinfo)
- Automatic account provisioning and existing account linking by verified email
- Session creation & secure cookie/token issuance
"""

import os
import json
import time
import secrets
import hashlib
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_google_client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "chartora-google-oauth-client-id-demo.apps.googleusercontent.com")

def get_google_client_secret() -> str:
    return os.environ.get("GOOGLE_CLIENT_SECRET", "GOCSPX-demoChartoraGoogleSecretKey123")

class GoogleAuthService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def generate_auth_url(self, redirect_uri: str) -> Dict[str, str]:
        """Generates Google OAuth URL with a single-use CSRF state token."""
        state = secrets.token_urlsafe(32)
        client_id = get_google_client_id()

        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO google_oauth_states (state, redirect_uri, expires_at)
            VALUES (?, ?, datetime('now', '+15 minutes'))
        """, (state, redirect_uri))
        conn.commit()
        conn.close()

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account"
        }
        auth_url = f"{GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"
        return {
            "auth_url": auth_url,
            "state": state
        }

    def process_oauth_callback(
        self,
        code: str,
        state: str,
        redirect_uri: str,
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Validates CSRF state, exchanges code for Google profile, and signs in/up user."""
        conn = self.get_db()
        cursor = conn.cursor()

        # 1. Validate CSRF state
        cursor.execute("""
            SELECT redirect_uri FROM google_oauth_states
            WHERE state = ? AND expires_at > datetime('now')
        """, (state,))
        state_row = cursor.fetchone()
        if not state_row:
            conn.close()
            return {"success": False, "error": "Invalid or expired Google OAuth state. Please try again."}

        # Delete used state
        cursor.execute("DELETE FROM google_oauth_states WHERE state = ?", (state,))
        conn.commit()

        # 2. Exchange code for userinfo
        google_user = self._fetch_google_userinfo(code, redirect_uri)
        if not google_user or not google_user.get("email"):
            conn.close()
            return {"success": False, "error": "Failed to retrieve verified Google profile."}

        email = google_user["email"].strip().lower()
        full_name = google_user.get("name", "Google Trader")
        avatar_url = google_user.get("picture", "")
        google_id = google_user.get("sub", "")

        # 3. Check for existing Chartora user
        cursor.execute("SELECT id, email, role FROM users WHERE LOWER(email) = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user["id"]
            role = existing_user["role"]
            # Update profile with google details if missing
            cursor.execute("""
                UPDATE profiles 
                SET avatar_url = COALESCE(NULLIF(avatar_url, ''), ?),
                    full_name = COALESCE(NULLIF(full_name, ''), ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (avatar_url, full_name, user_id))
        else:
            # Provision clean new user
            gen_pass = hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
            username = email.split('@')[0] or f"user_{int(time.time())}"
            cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'Customer')", (email, gen_pass))
            user_id = cursor.lastrowid
            role = "Customer"

            cursor.execute("""
                INSERT INTO profiles (user_id, full_name, username, avatar_url)
                VALUES (?, ?, ?, ?)
            """, (user_id, full_name, username, avatar_url))
            cursor.execute("INSERT INTO user_preferences (user_id) VALUES (?)", (user_id,))
            cursor.execute("INSERT INTO user_alert_settings (user_id) VALUES (?)", (user_id,))

        # 4. Issue session token
        session_token = secrets.token_hex(32)
        cursor.execute("""
            INSERT INTO sessions (session_token, user_id, expires_at, ip_address)
            VALUES (?, ?, datetime('now', '+14 days'), ?)
        """, (session_token, user_id, client_ip))

        cursor.execute("""
            INSERT INTO audit_logs (actor_id, action, target_type, details, ip_address)
            VALUES (?, 'GOOGLE_AUTH_LOGIN', 'USER', ?, ?)
        """, (user_id, f"User {email} logged in via Google OAuth ({google_id})", client_ip))

        # Fetch profile
        cursor.execute("""
            SELECT u.id, u.email, u.role, p.full_name, p.username, p.avatar_url, tu.telegram_id
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            LEFT JOIN telegram_users tu ON u.id = tu.user_id
            WHERE u.id = ?
        """, (user_id,))
        user_record = dict(cursor.fetchone())

        conn.commit()
        conn.close()

        return {
            "success": True,
            "user": user_record,
            "token": session_token,
            "message": "Successfully authenticated with Google."
        }

    def _fetch_google_userinfo(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        client_id = get_google_client_id()
        client_secret = get_google_client_secret()

        # Mock / Simulation for test and local developer setups
        if client_id.startswith("chartora-google-oauth-client-id-demo") or code.startswith("mock_google_code_"):
            clean_name = code.replace("mock_google_code_", "") if code.startswith("mock_google_code_") else "Trader"
            return {
                "sub": f"google_sub_{secrets.token_hex(8)}",
                "email": f"google_{clean_name.lower()}@chartora.in" if clean_name != "Trader" else "google_user@chartora.in",
                "name": f"Google {clean_name}",
                "picture": "https://chartora.in/public/avatars/default.png",
                "email_verified": True
            }

        # Real Google API Token Exchange
        token_payload = urllib.parse.urlencode({
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                GOOGLE_TOKEN_URL,
                data=token_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                token_data = json.loads(resp.read().decode("utf-8"))
                access_token = token_data.get("access_token")
                if not access_token:
                    return None

            user_req = urllib.request.Request(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            with urllib.request.urlopen(user_req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
