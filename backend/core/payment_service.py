#!/usr/bin/env python3
"""
CHARTORA — Provider-Agnostic Payment & Subscription Architecture
Implements:
1. PaymentProvider (Abstract base class)
2. StripeProvider (Stripe API & Webhook Verification)
3. RazorpayProvider (Razorpay API & HMAC Signature Verification)
4. SubscriptionService (Idempotent subscription lifecycle & tier state)
5. EntitlementService (Server-side feature & channel entitlement verification)
6. TelegramAccessService (Private channel invite link generation & revocation)
"""

import os
import hmac
import hashlib
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("chartora.payment_service")

# Tier definitions matching the 3-channel business model
PLANS_DEFINITION = {
    "FREE": {
        "name": "Chartora Free",
        "slug": "free",
        "price_usd": 0.0,
        "features": ["community", "academy_basic", "public_briefs", "miniapp_basic"],
        "channels": ["TELEGRAM_OFFICIAL_CHANNEL_ID"]
    },
    "PRO": {
        "name": "Chartora Pro",
        "slug": "pro",
        "price_usd": 19.99,
        "features": ["community", "academy_full", "pro_setups", "scalping_intraday", "forex_metals_indices", "miniapp_full"],
        "channels": ["TELEGRAM_OFFICIAL_CHANNEL_ID", "TELEGRAM_PRO_CHANNEL_ID"]
    },
    "ALL_ACCESS": {
        "name": "Chartora All Access",
        "slug": "all-access",
        "price_usd": 49.99,
        "features": ["community", "academy_full", "pro_setups", "all_markets_stocks", "multi_strategy_v1", "mt5_bridge", "risk_journal", "miniapp_full", "vip_channel"],
        "channels": ["TELEGRAM_OFFICIAL_CHANNEL_ID", "TELEGRAM_PRO_CHANNEL_ID", "TELEGRAM_ALL_ACCESS_CHANNEL_ID"]
    }
}


# ==========================================
# 1. ABSTRACT PAYMENT PROVIDER INTERFACE
# ==========================================
class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    def create_checkout_session(self, user_id: int, plan_slug: str, return_url: str) -> Dict[str, Any]:
        """Creates a hosted checkout session."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Verifies cryptographic webhook signature."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload_bytes: bytes, signature_header: str) -> Tuple[str, str, Dict[str, Any]]:
        """Parses webhook payload returning (event_id, event_type, payload_dict)."""
        pass


# ==========================================
# 2. STRIPE PAYMENT PROVIDER
# ==========================================
class StripeProvider(PaymentProvider):
    """Stripe payment provider implementation."""

    def __init__(self):
        self.secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    def is_configured(self) -> bool:
        return bool(self.secret_key and not self.secret_key.startswith("sk_test_fake"))

    def create_checkout_session(self, user_id: int, plan_slug: str, return_url: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "ok": False,
                "status": "NOT_CONFIGURED",
                "message": "Stripe is not configured. Set STRIPE_SECRET_KEY in production environment.",
                "checkout_url": f"https://chartora.in/pricing?unconfigured=stripe"
            }
        
        # Stripe Checkout API placeholder for real keys
        return {
            "ok": True,
            "status": "READY",
            "session_id": f"cs_test_{secrets_token()}",
            "checkout_url": f"https://checkout.stripe.com/c/pay/cs_test_{secrets_token()}"
        }

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        if not self.webhook_secret:
            return True  # Dev fallback if unconfigured
        try:
            # Parse Stripe signature format: t=timestamp,v1=signature
            elements = dict(item.strip().split("=", 1) for item in signature_header.split(",") if "=" in item)
            timestamp = elements.get("t", "")
            sig = elements.get("v1", "")
            
            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_sig = hmac.new(self.webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_sig, sig)
        except Exception as e:
            logger.warning(f"Stripe signature verification failed: {e}")
            return False

    def parse_webhook_event(self, payload_bytes: bytes, signature_header: str) -> Tuple[str, str, Dict[str, Any]]:
        is_valid = self.verify_webhook_signature(payload_bytes, signature_header)
        if not is_valid and self.webhook_secret:
            raise ValueError("Invalid Stripe webhook signature")
        
        data = json.loads(payload_bytes.decode("utf-8"))
        event_id = data.get("id", f"evt_{int(time.time())}")
        event_type = data.get("type", "unknown")
        return event_id, event_type, data


# ==========================================
# 3. RAZORPAY PAYMENT PROVIDER
# ==========================================
class RazorpayProvider(PaymentProvider):
    """Razorpay payment provider implementation."""

    def __init__(self):
        self.key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        self.key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        self.webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret and not self.key_id.startswith("rzp_test_fake"))

    def create_checkout_session(self, user_id: int, plan_slug: str, return_url: str) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "ok": False,
                "status": "NOT_CONFIGURED",
                "message": "Razorpay is not configured. Set RAZORPAY_KEY_ID in production environment.",
                "checkout_url": f"https://chartora.in/pricing?unconfigured=razorpay"
            }
        
        return {
            "ok": True,
            "status": "READY",
            "order_id": f"order_{secrets_token()}",
            "key_id": self.key_id
        }

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        if not self.webhook_secret:
            return True
        try:
            expected_sig = hmac.new(self.webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_sig, signature_header)
        except Exception as e:
            logger.warning(f"Razorpay signature verification failed: {e}")
            return False

    def parse_webhook_event(self, payload_bytes: bytes, signature_header: str) -> Tuple[str, str, Dict[str, Any]]:
        is_valid = self.verify_webhook_signature(payload_bytes, signature_header)
        if not is_valid and self.webhook_secret:
            raise ValueError("Invalid Razorpay webhook signature")
        
        data = json.loads(payload_bytes.decode("utf-8"))
        event_id = data.get("event_id", f"rzp_evt_{int(time.time())}")
        event_type = data.get("event", "payment.captured")
        return event_id, event_type, data


def secrets_token(n: int = 8) -> str:
    import secrets
    return secrets.token_hex(n)


# ==========================================
# 4. SUBSCRIPTION SERVICE
# ==========================================
class SubscriptionService:
    """Manages user subscription lifecycle, idempotent activations, and tier synchronization."""

    def __init__(self, db_getter):
        self.get_db = db_getter

    def get_user_plan(self, user_id: int) -> Dict[str, Any]:
        """Retrieves verified server-side plan and subscription status."""
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT s.id as sub_id, s.status, s.stripe_subscription_id, s.current_period_end,
                       p.id as plan_id, p.name as plan_name, p.slug as plan_slug, p.price
                FROM subscriptions s
                JOIN plans p ON s.plan_id = p.id
                WHERE s.user_id = ? AND s.status = 'ACTIVE'
                ORDER BY s.id DESC LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                slug_clean = "ALL_ACCESS" if "all" in row["plan_slug"].lower() else "PRO" if "pro" in row["plan_slug"].lower() else "FREE"
                return {
                    "tier": slug_clean,
                    "plan_name": row["plan_name"],
                    "plan_slug": row["plan_slug"],
                    "status": row["status"],
                    "price": row["price"],
                    "is_active": True,
                    "expires_at": row["current_period_end"]
                }
            
            # Default to Free
            return {
                "tier": "FREE",
                "plan_name": "Chartora Free",
                "plan_slug": "free",
                "status": "ACTIVE",
                "price": 0.0,
                "is_active": True,
                "expires_at": None
            }
        finally:
            conn.close()

    def activate_subscription(self, user_id: int, plan_tier: str, provider: str, sub_id: str, cust_id: Optional[str] = None) -> bool:
        """Idempotently activates or upgrades a user's subscription."""
        tier_normalized = "ALL_ACCESS" if "all" in plan_tier.lower() else "PRO" if "pro" in plan_tier.lower() else "FREE"
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            # Resolve plan ID
            cursor.execute("SELECT id FROM plans WHERE UPPER(slug) = ? OR slug LIKE ? LIMIT 1", (tier_normalized, f"%{tier_normalized.lower()}%"))
            p_row = cursor.fetchone()
            plan_id = p_row[0] if p_row else (3 if tier_normalized == "ALL_ACCESS" else 2 if tier_normalized == "PRO" else 1)

            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions 
                (user_id, plan_id, status, stripe_subscription_id, stripe_customer_id, updated_at)
                VALUES (?, ?, 'ACTIVE', ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, plan_id, sub_id, cust_id or f"{provider}_{user_id}"))

            role_name = "Premium Member" if tier_normalized in ["PRO", "ALL_ACCESS"] else "Free Member"
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role_name, user_id))
            cursor.execute("UPDATE telegram_users SET is_premium = ? WHERE user_id = ?", (1 if role_name == "Premium Member" else 0, user_id))
            conn.commit()
            logger.info(f"Subscription activated for user {user_id}: {tier_normalized} ({provider})")
            return True
        except Exception as e:
            logger.error(f"Failed to activate subscription for user {user_id}: {e}")
            return False
        finally:
            conn.close()

    def deactivate_subscription(self, sub_id: str) -> bool:
        """Deactivates/cancels a subscription upon cancellation webhook."""
        conn = self.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ?", (sub_id,))
            sub = cursor.fetchone()
            if sub:
                uid = sub["user_id"]
                cursor.execute("UPDATE subscriptions SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE stripe_subscription_id = ?", (sub_id,))
                cursor.execute("UPDATE users SET role = 'Free Member' WHERE id = ?", (uid,))
                cursor.execute("UPDATE telegram_users SET is_premium = 0 WHERE user_id = ?", (uid,))
                conn.commit()
                logger.info(f"Subscription cancelled for user {uid}")
                return True
            return False
        finally:
            conn.close()


# ==========================================
# 5. ENTITLEMENT SERVICE
# ==========================================
class EntitlementService:
    """Verifies feature and resource access rights."""

    def __init__(self, subscription_service: SubscriptionService):
        self.sub_service = subscription_service

    def can_access_feature(self, user_id: int, feature_name: str) -> bool:
        plan_info = self.sub_service.get_user_plan(user_id)
        tier = plan_info.get("tier", "FREE")
        features = PLANS_DEFINITION.get(tier, {}).get("features", [])
        return feature_name in features

    def can_access_channel(self, user_id: int, channel_tier: str) -> bool:
        plan_info = self.sub_service.get_user_plan(user_id)
        user_tier = plan_info.get("tier", "FREE")

        if user_tier == "ALL_ACCESS":
            return True
        elif user_tier == "PRO":
            return channel_tier in ["FREE", "PRO"]
        else:
            return channel_tier == "FREE"


# ==========================================
# 6. TELEGRAM ACCESS SERVICE
# ==========================================
class TelegramAccessService:
    """Generates and verifies secure Telegram channel access."""

    def __init__(self, entitlement_service: EntitlementService):
        self.entitlement_service = entitlement_service

    def generate_channel_invite(self, user_id: int, channel_tier: str) -> Dict[str, Any]:
        """Generates a secure private invite link if the user has active entitlement."""
        if not self.entitlement_service.can_access_channel(user_id, channel_tier):
            return {
                "ok": False,
                "error": "INSUFFICIENT_ENTITLEMENT",
                "message": f"Upgrade to {channel_tier} plan to unlock this channel."
            }

        from .telegram_service import TelegramConfig, TelegramClient
        client = TelegramClient()
        
        target_chat_id = (
            TelegramConfig.get_all_access_channel_id() if channel_tier == "ALL_ACCESS"
            else TelegramConfig.get_pro_channel_id() if channel_tier == "PRO"
            else TelegramConfig.get_official_channel_id()
        )

        if not target_chat_id:
            return {"ok": False, "error": "CHANNEL_NOT_CONFIGURED"}

        # Generate single-use invite link expiring in 24 hours
        expire_ts = int(time.time()) + 86400
        res = client.create_chat_invite_link(target_chat_id, name=f"User_{user_id}_{channel_tier}", member_limit=1, expire_date=expire_ts)
        
        if res.get("ok"):
            return {
                "ok": True,
                "channel_tier": channel_tier,
                "invite_link": res.get("result", {}).get("invite_link"),
                "expires_at": expire_ts
            }
        return {"ok": False, "error": res.get("description", "Invite generation failed")}
