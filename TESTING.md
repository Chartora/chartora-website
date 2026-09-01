# CHARTORA — AUTOMATED TESTING & VERIFICATION SUITE

## 1. Overview
CHARTORA features a comprehensive Python test suite (`tests/test_saas_platform.py`) validating authentication security, Stripe webhook idempotency, Telegram invite limits, deterministic R calculations, and API entitlement enforcement.

---

## 2. Test Execution Commands

Run the full automated test suite:
```bash
python3 tests/test_saas_platform.py
```

Run HTML link & SPA route audit script:
```bash
python3 scripts/audit_links.py
```

---

## 3. Test Coverage Summary

1. **`test_user_registration_and_auth_session`**: Validates user signup, password hashing, and HttpOnly session cookie generation.
2. **`test_rbac_and_unauthorized_access`**: Verifies Guest users receive 401/403 when requesting premium setup endpoints.
3. **`test_stripe_webhook_idempotency`**: Simulates duplicate Stripe webhook events (`checkout.session.completed`) and verifies `processed_webhooks` prevents duplicate subscription mutations.
4. **`test_telegram_single_use_expiring_invite`**: Validates single-use expiring invite generation (`member_limit: 1`, `expire_date: +3 days`) and checks rate limiting.
5. **`test_directional_r_multiple_math`**: Validates direction-aware risk/reward calculations for both BUY and SELL technical setups.
6. **`test_signal_lifecycle_state_machine`**: Verifies valid transitions (`WATCHING` → `ACTIVE` → `TP1_HIT` → `TP2_HIT` → `SL_HIT`).
7. **`test_link_and_route_audit`**: Ensures all HTML navigation targets have registered JavaScript route handlers.
