# CHARTORA.IN — REST API SPECIFICATION

## Base URLs
- Development: `http://localhost:8080/api`
- Production: `https://api.chartora.in/api`

---

## 1. System Health
- **`GET /health`**: Returns system operational status.
  - Response: `{"status": "UP", "timestamp": "...", "service": "Chartora.in SaaS Engine"}`
- **`GET /ready`**: Database connectivity readiness check.
  - Response: `{"status": "READY", "database": "connected"}`

---

## 2. Authentication (`/api/auth`)
- **`POST /api/auth/register`**: User account registration.
  - Request: `{"email": "...", "password": "...", "full_name": "...", "username": "..."}`
  - Response: Sets `session` HttpOnly cookie. Returns `{"success": true, "user": {...}}`
- **`POST /api/auth/login`**: User login.
  - Request: `{"email": "...", "password": "..."}`
  - Response: Sets `session` HttpOnly cookie. Returns `{"success": true, "user": {...}}`
- **`POST /api/auth/logout`**: Clears server session & cookie.
- **`GET /api/auth/me`**: Fetches authenticated user profile & entitlements.

---

## 3. Stripe Billing (`/api/stripe`)
- **`POST /api/stripe/checkout`**: Initiates Stripe Checkout session.
- **`GET /api/stripe/portal`**: Redirects to Stripe Customer Portal.
- **`POST /api/stripe/webhook`**: Receives signed Stripe webhook events.

---

## 4. Virtual Setup Performance Engine (`/api/performance`)
- **`GET /api/performance`**: Returns deterministic performance metrics & outcome logs.
  - Query Params: `?data_mode=LIVE&instrument=XAUUSD`
  - Response:
    ```json
    {
      "disclaimer": "Virtual/educational performance based on Chartora published setups.",
      "metrics": {
        "total_setups": 142,
        "wins": 91,
        "losses": 37,
        "breakeven": 14,
        "win_rate_pct": 64.1,
        "cumulative_virtual_r": 48.60,
        "profit_factor": 2.45
      },
      "outcomes": [...]
    }
    ```

---

## 5. Signals (`/api/signals`)
- **`GET /api/signals`**: Returns live setup alerts based on user entitlements.
- **`POST /api/signals`**: [Admin/Editor] Publishes new technical setup.

---

## 6. Controlled Telegram Service (`/api/telegram`)
- **`POST /api/telegram/request-invite`**: Generates single-use expiring invite link for active subscribers.

---

## 7. Admin Panel (`/api/admin`)
- **`GET /api/admin/metrics`**: Returns MRR, subscriber count, and system status.
- **`GET /api/admin/audit-logs`**: Returns system audit trail.
