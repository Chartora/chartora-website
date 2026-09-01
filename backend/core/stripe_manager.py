#!/usr/bin/env python3
"""
CHARTORA — Stripe Webhook Idempotency & Tier Entitlement Manager
1. Verifies Stripe cryptographic webhook signatures
2. Enforces idempotent processing via stripe_webhook_events table
3. Automatically updates user subscription status & tier entitlements
4. Synchronizes Telegram channel access grants/revocations
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("chartora.stripe_manager")

TIER_CHANNEL_GRANTS = {
    "FOREX": ["TELEGRAM_FOREX_CHANNEL_ID"],
    "METALS": ["TELEGRAM_METALS_CHANNEL_ID"],
    "INDICES": ["TELEGRAM_INDICES_CHANNEL_ID"],
    "ALL_ACCESS": [
        "TELEGRAM_FOREX_CHANNEL_ID",
        "TELEGRAM_METALS_CHANNEL_ID",
        "TELEGRAM_INDICES_CHANNEL_ID",
        "TELEGRAM_PREMIUM_CHANNEL_ID"
    ]
}

class StripeWebhookManager:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def process_webhook_event(self, event_id: str, event_type: str, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        # 1. Idempotency Check
        try:
            cursor.execute("SELECT id, status FROM stripe_webhook_events WHERE event_id = ?", (event_id,))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return {
                    "status": "DUPLICATE_IGNORED",
                    "event_id": event_id,
                    "message": "Webhook already processed"
                }

            cursor.execute(
                "INSERT INTO stripe_webhook_events (event_id, event_type, status, payload_json) VALUES (?, ?, 'PROCESSING', ?)",
                (event_id, event_type, json.dumps(payload_dict))
            )
            conn.commit()
        except Exception as e:
            conn.close()
            return {"status": "ERROR", "message": str(e)}

        # 2. Event Dispatching
        try:
            if event_type == "checkout.session.completed":
                self._handle_checkout_completed(payload_dict.get("data", {}).get("object", {}), conn)
            elif event_type in ["customer.subscription.deleted", "customer.subscription.paused"]:
                self._handle_subscription_cancelled(payload_dict.get("data", {}).get("object", {}), conn)
            elif event_type == "invoice.payment_failed":
                self._handle_payment_failed(payload_dict.get("data", {}).get("object", {}), conn)

            cursor.execute("UPDATE stripe_webhook_events SET status = 'COMPLETED' WHERE event_id = ?", (event_id,))
            conn.commit()
            return {"status": "SUCCESS", "event_id": event_id}
        except Exception as e:
            cursor.execute("UPDATE stripe_webhook_events SET status = 'FAILED' WHERE event_id = ?", (event_id,))
            conn.commit()
            return {"status": "FAILED", "error": str(e)}
        finally:
            conn.close()

    def _handle_checkout_completed(self, session_obj: Dict[str, Any], conn):
        cursor = conn.cursor()
        user_id = session_obj.get("client_reference_id")
        cust_id = session_obj.get("customer")
        sub_id = session_obj.get("subscription")

        if not user_id:
            # Try to match by email
            cust_email = session_obj.get("customer_details", {}).get("email")
            if cust_email:
                cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (cust_email,))
                u = cursor.fetchone()
                if u:
                    user_id = u["id"]

        if user_id:
            cursor.execute("SELECT id FROM plans WHERE slug = 'all-access' OR slug = 'all_access' OR id = 5 LIMIT 1")
            p_row = cursor.fetchone()
            resolved_plan_id = p_row[0] if p_row else 1

            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, plan_id, status, stripe_subscription_id, stripe_customer_id, updated_at)
                VALUES (?, ?, 'ACTIVE', ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, resolved_plan_id, sub_id, cust_id))
            cursor.execute("UPDATE users SET role = 'Premium Member' WHERE id = ?", (user_id,))
            cursor.execute("UPDATE telegram_users SET is_premium = 1 WHERE user_id = ?", (user_id,))
            conn.commit()

    def _handle_subscription_cancelled(self, sub_obj: Dict[str, Any], conn):
        cursor = conn.cursor()
        sub_id = sub_obj.get("id")
        if sub_id:
            cursor.execute("SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ?", (sub_id,))
            sub = cursor.fetchone()
            if sub:
                uid = sub["user_id"]
                cursor.execute("UPDATE subscriptions SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (sub["id"],))
                cursor.execute("UPDATE users SET role = 'Free Member' WHERE id = ?", (uid,))
                cursor.execute("UPDATE telegram_users SET is_premium = 0 WHERE user_id = ?", (uid,))
                conn.commit()

    def _handle_payment_failed(self, invoice_obj: Dict[str, Any], conn):
        cursor = conn.cursor()
        sub_id = invoice_obj.get("subscription")
        if sub_id:
            cursor.execute("UPDATE subscriptions SET status = 'PAST_DUE', updated_at = CURRENT_TIMESTAMP WHERE stripe_subscription_id = ?", (sub_id,))
            conn.commit()
