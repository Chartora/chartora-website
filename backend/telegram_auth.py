#!/usr/bin/env python3
"""
CHARTORA — Telegram Authentication & Deep Link Verification Engine
Implements strict server-side validation for Telegram Mini App initData (HMAC-SHA256)
and cryptographic signed deep link token generation and validation.
"""

import hashlib
import hmac
import json
import os
import time
import urllib.parse
import secrets

DEFAULT_MAX_AUTH_AGE_SECONDS = 86400  # 24 hours

def compute_init_data_hash(data_check_string: str, bot_token: str) -> str:
    """
    Computes HMAC-SHA256 hash according to Telegram WebApp specifications:
    secret_key = HMAC_SHA256("WebAppData", bot_token)
    hash = hex(HMAC_SHA256(secret_key, data_check_string))
    """
    secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return calculated_hash

def validate_init_data(init_data_str: str, bot_token: str, max_age_seconds: int = DEFAULT_MAX_AUTH_AGE_SECONDS) -> dict:
    """
    Validates Telegram WebApp initData query string.
    Returns parsed dictionary containing user, auth_date, query_id, etc., if valid.
    Raises ValueError with a descriptive message if invalid or expired.
    """
    if not init_data_str or not isinstance(init_data_str, str):
        raise ValueError("initData string is missing or empty")
    
    if not bot_token:
        raise ValueError("Bot token is required for validation")

    # Parse query string preserving encoded parameters
    parsed_params = urllib.parse.parse_qsl(init_data_str, keep_blank_values=True)
    params_dict = dict(parsed_params)

    if 'hash' not in params_dict:
        raise ValueError("Missing 'hash' parameter in initData")

    received_hash = params_dict.pop('hash')

    # Also pop 'signature' if present (used in 3rd party Ed25519) so it doesn't taint HMAC data_check_string
    if 'signature' in params_dict:
        params_dict.pop('signature')

    # Sort remaining parameters alphabetically by key
    sorted_items = sorted(params_dict.items(), key=lambda x: x[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)

    expected_hash = compute_init_data_hash(data_check_string, bot_token)

    if not hmac.compare_digest(received_hash, expected_hash):
        raise ValueError("Invalid initData HMAC-SHA256 signature")

    # Validate auth_date freshness
    if 'auth_date' not in params_dict:
        raise ValueError("Missing 'auth_date' parameter in initData")

    try:
        auth_date = int(params_dict['auth_date'])
    except ValueError:
        raise ValueError("Invalid auth_date format")

    now = int(time.time())
    if max_age_seconds > 0 and (now - auth_date > max_age_seconds):
        raise ValueError(f"initData expired: auth_date={auth_date}, current={now}, max_age={max_age_seconds}")

    # Parse JSON fields (e.g. 'user', 'receiver', 'chat')
    result = dict(params_dict)
    result['auth_date'] = auth_date
    if 'user' in result:
        try:
            result['user'] = json.loads(result['user'])
        except Exception:
            pass

    return result

def create_deep_link_payload(action: str, reference: str = "", user_id: int = None, secret_key: str = None) -> str:
    """
    Creates a compact tamper-evident deep-link payload:
    Format: v1_<action>_<reference>_<user_id>_<timestamp>_<sig>
    """
    if not secret_key:
        secret_key = os.environ.get('JWT_SECRET', 'chartora_secret_jwt_key_2026')
    
    timestamp = int(time.time())
    uid = user_id if user_id is not None else 0
    data = f"{action}:{reference}:{uid}:{timestamp}"
    sig = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()[:12]
    payload = f"v1_{action}_{reference}_{uid}_{timestamp}_{sig}"
    return payload

def verify_deep_link_payload(payload_str: str, secret_key: str = None, max_age_seconds: int = 86400 * 7) -> dict:
    """
    Verifies and parses a deep-link payload.
    """
    if not secret_key:
        secret_key = os.environ.get('JWT_SECRET', 'chartora_secret_jwt_key_2026')

    if not payload_str or not payload_str.startswith('v1_'):
        # Fallback simple start payload (e.g., ref_code or mkt_symbol)
        return {"action": "direct", "reference": payload_str or "", "valid": True}

    parts = payload_str.split('_')
    if len(parts) == 6:
        _, action, reference, uid_str, timestamp_str, received_sig = parts
    elif len(parts) == 5:
        _, action, reference, timestamp_str, received_sig = parts
        uid_str = "0"
    else:
        return {"action": "unknown", "reference": payload_str, "valid": False, "error": "Invalid format"}

    try:
        timestamp = int(timestamp_str)
        uid = int(uid_str)
    except ValueError:
        return {"action": action, "reference": reference, "valid": False, "error": "Invalid timestamp or uid"}

    now = int(time.time())
    if max_age_seconds > 0 and (now - timestamp > max_age_seconds):
        return {"action": action, "reference": reference, "valid": False, "error": "Expired payload"}

    # Validate signature
    data = f"{action}:{reference}:{uid}:{timestamp}"
    expected_sig = hmac.new(secret_key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()[:12]
    is_valid = hmac.compare_digest(received_sig, expected_sig)

    return {
        "action": action,
        "reference": reference,
        "user_id": uid,
        "timestamp": timestamp,
        "valid": is_valid
    }
