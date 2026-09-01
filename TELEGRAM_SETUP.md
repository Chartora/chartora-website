# CHARTORA — CONTROLLED TELEGRAM BOT & CHANNEL SETUP GUIDE

## 1. Overview
CHARTORA uses an automated Telegram Bot API service layer to deliver single-use expiring invite links for private setup channels.

**Security Policy**: Permanent public invite links to premium channels are **never** exposed. Invites are generated dynamically per user, rate-limited, and automatically revoked when subscriptions cancel or expire.

---

## 2. Environment Variables

```env
# Telegram Mode: active | disabled
TELEGRAM_MODE=active

# Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ

# Channel Chat IDs (Format: -100xxxxxxxxxx)
TELEGRAM_FREE_CHANNEL_ID=-1001234567890
TELEGRAM_PREMIUM_CHANNEL_ID=-1009876543210
```

---

## 3. Bot Setup Checklist

1. Create Bot via `@BotFather` on Telegram (`/newbot`).
2. Add the created Bot as an **Administrator** in both public and private channels.
3. Grant Administrator Rights:
   - `Add Users` / `Invite Users via Link`
   - `Manage Chat`
   - `Ban/Unban Users` (for automated revocation queue processing)
4. Record Channel Chat IDs (use `@userinfobot` or Bot API `getUpdates`).

---

## 4. Single-Use Invite Generation Flow

```
User Clicks "Join Premium Telegram" (/api/telegram/request-invite)
                              │
                              ▼
           Server Verifies Entitlement & Subscription State
                   (Status MUST be ACTIVE / TRIALING)
                              │
                              ▼
           Server Calls Telegram Bot API: createChatInviteLink
           - member_limit: 1 (Single Use)
           - expire_date: +3 Days (259,200 seconds)
                              │
                              ▼
           Record in telegram_access_logs (user_id, invite_link, status)
                              │
                              ▼
           Return Private Single-Use Invite Link to User UI
```

---

## 5. Automated Revocation Queue

When a subscription transitions to `CANCELLED`, `EXPIRED`, or `UNPAID`:
1. Server updates user's `telegram_connections` status to `PENDING_REVOCATION`.
2. Admin panel / background task executes `banChatMember` followed immediately by `unbanChatMember` (which removes the user from the channel without permanently blocking re-joining upon future resubscription).
