# CHARTORA — DATABASE ARCHITECTURE & MIGRATION GUIDE

## 1. Database Overview
CHARTORA uses a normalized relational database design supporting **SQLite3** for development, local testing, and rapid prototyping, with seamless migration compatibility for **PostgreSQL** in production.

---

## 2. Core Schemas & Entities (26 Tables)

1. **`users`**: Core user accounts (`id`, `email`, `password_hash`, `role`, `is_email_verified`, `created_at`, `updated_at`).
2. **`sessions`**: Server-side session store for HttpOnly cookie authentication (`id`, `session_token`, `user_id`, `expires_at`, `created_at`, `user_agent`, `ip_address`).
3. **`profiles`**: User profile details (`id`, `user_id`, `full_name`, `username`, `avatar_url`, `country`, `timezone`, `trading_experience`, `trading_level`, `preferred_markets`, `telegram_username`, `updated_at`).
4. **`plans`**: Dynamic subscription plans (`id`, `name`, `slug`, `price_usd`, `billing_cycle`, `stripe_price_id`, `entitlements_json`, `is_active`, `created_at`).
5. **`subscriptions`**: User subscription lifecycle records (`id`, `user_id`, `plan_id`, `stripe_customer_id`, `stripe_subscription_id`, `status`, `current_period_start`, `current_period_end`, `cancel_at_period_end`, `created_at`).
6. **`payments`**: Invoice & transaction history (`id`, `user_id`, `subscription_id`, `stripe_invoice_id`, `amount_cents`, `currency`, `status`, `created_at`).
7. **`processed_webhooks`**: Idempotency tracking for Stripe events (`id`, `event_id`, `event_type`, `processed_at`).
8. **`entitlements`**: Defined platform permissions mapped to plans (`id`, `plan_id`, `entitlement_key`, `is_granted`).
9. **`signals`**: Technical setup records (`id`, `instrument`, `direction`, `timeframe`, `strategy`, `category`, `entry_price`, `sl_price`, `tp1_price`, `tp2_price`, `tp3_price`, `rr_ratio`, `status`, `chart_url`, `description`, `risk_note`, `author_id`, `data_mode`, `created_at`, `updated_at`).
10. **`signal_outcomes`**: Setup outcome logs for deterministic virtual performance (`id`, `signal_id`, `final_status`, `exit_price`, `exit_timestamp`, `r_multiple`, `win_loss_be`, `notes`, `recorded_by`).
11. **`performance_logs`**: Derived virtual setup metrics history (`id`, `signal_id`, `instrument`, `strategy`, `timeframe`, `session`, `direction`, `risk_amount`, `reward_amount`, `r_multiple`, `win_loss_be`, `data_mode`, `closed_at`).
12. **`markets`**: Asset class categories (`id`, `name`, `slug`, `category`, `description`, `is_active`).
13. **`instruments`**: Tradable instruments (`id`, `symbol`, `name`, `market_id`, `status`, `is_enabled`).
14. **`market_updates`**: Published market analysis & session outlooks (`id`, `title`, `summary`, `content`, `instrument_symbol`, `timeframe`, `session`, `status`, `author_id`, `created_at`).
15. **`news_articles`**: Market news articles (`id`, `headline`, `summary`, `source`, `impact_level`, `instrument_symbol`, `published_at`, `url`).
16. **`courses`**: Trading Academy courses (`id`, `title`, `slug`, `description`, `category`, `level`, `is_published`, `created_at`).
17. **`modules`**: Course modules (`id`, `course_id`, `title`, `order_num`).
18. **`lessons`**: Academy lessons (`id`, `module_id`, `title`, `slug`, `content_body`, `key_takeaway`, `order_num`, `is_free_preview`).
19. **`lesson_progress`**: User lesson completion progress (`id`, `user_id`, `lesson_id`, `is_completed`, `last_viewed_at`).
20. **`community_posts`**: In-app member feed posts (`id`, `user_id`, `category`, `title`, `body`, `post_type`, `is_pinned`, `likes_count`, `created_at`).
21. **`comments`**: Community post comments (`id`, `post_id`, `user_id`, `body`, `created_at`).
22. **`reactions`**: Post reactions (`id`, `post_id`, `user_id`, `reaction_type`, `created_at`).
23. **`telegram_connections`**: User Telegram account links (`id`, `user_id`, `telegram_username`, `telegram_user_id`, `status`, `invite_link`, `verified_at`).
24. **`telegram_memberships`**: Telegram channel access state (`id`, `user_id`, `channel_id`, `role`, `joined_at`, `status`).
25. **`telegram_access_logs`**: Telegram invitation & revocation audit log (`id`, `user_id`, `action`, `channel_id`, `invite_link`, `status`, `timestamp`).
26. **`audit_logs`**: System audit trail (`id`, `actor_id`, `action`, `target_type`, `target_id`, `details`, `ip_address`, `timestamp`).
27. **`telegram_users`**: Authoritative Telegram-to-Chartora identity link (`id`, `telegram_id`, `user_id`, `username`, `first_name`, `last_name`, `language_code`, `is_premium`, `auth_date`, `created_at`, `updated_at`).
28. **`user_watchlists`**: User-customized market watchlists (`id`, `user_id`, `symbol`, `category`, `notes`, `created_at`).
29. **`user_alerts`**: User price thresholds and trigger rules (`id`, `user_id`, `symbol`, `alert_type`, `target_price`, `condition`, `is_active`, `triggered_at`, `created_at`).
30. **`telegram_notifications`**: Persistent notification queue and Telegram dispatch logs (`id`, `user_id`, `telegram_id`, `event_type`, `title`, `message`, `payload_json`, `is_read`, `status`, `error`, `sent_at`, `created_at`).
31. **`telegram_bot_updates`**: Webhook idempotency ledger for deduplication (`id`, `update_id`, `update_type`, `processed_at`).
32. **`deep_link_tokens`**: Signed cryptographic deep link tokens (`id`, `token`, `action_type`, `payload_json`, `user_id`, `expires_at`, `used_at`, `created_at`).
33. **`user_preferences`**: Terminal and push alert preferences (`id`, `user_id`, `signal_alerts`, `price_alerts`, `news_alerts`, `haptic_feedback`, `sound_enabled`, `theme`, `language`, `timezone`, `updated_at`).

---

## 3. Migration Strategy to PostgreSQL

When moving to production PostgreSQL:

1. Set `DATABASE_URL` environment variable:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/chartora_db
   ```
2. Run database migration script:
   ```bash
   python3 scripts/migrate_db.py
   ```
3. PostgreSQL dialect considerations:
   - Uses native `TIMESTAMP WITH TIME ZONE` for UTC standard.
   - Converts SQLite `AUTOINCREMENT` to PostgreSQL `BIGSERIAL PRIMARY KEY`.
   - Uses `BOOLEAN` native types instead of `INTEGER (0/1)`.

---

## 4. Backup & Restore Procedures

### Development (SQLite)
- **Backup**:
  ```bash
  cp chartora.db backups/chartora_$(date +%Y%m%d_%H%M%S).db
  ```
- **Restore**:
  ```bash
  cp backups/chartora_20260809.db chartora.db
  ```

### Production (PostgreSQL)
- **Daily Automated Backup**:
  ```bash
  pg_dump -U chartora_user -h localhost chartora_db | gzip > backups/chartora_prod_$(date +%Y%m%d).sql.gz
  ```
- **Restore**:
  ```bash
  gunzip -c backups/chartora_prod_20260809.sql.gz | psql -U chartora_user -d chartora_db
  ```
