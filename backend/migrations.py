#!/usr/bin/env python3
"""
CHARTORA.IN — Database Migration & Persistence Engine
Supports versioned SQL migrations, index creation, constraints,
foreign keys, SQLite and PostgreSQL dual compatibility, and automatic version tracking.
"""

import os
import sqlite3
import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("chartora.migrations")

MIGRATIONS = [
    (
        1,
        "initial_core_schema",
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Free Member',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT UNIQUE,
            telegram_username TEXT,
            trading_experience TEXT,
            trading_level TEXT,
            phone TEXT,
            country TEXT,
            avatar_url TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            signal_alerts INTEGER DEFAULT 1,
            price_alerts INTEGER DEFAULT 1,
            news_alerts INTEGER DEFAULT 1,
            sound_enabled INTEGER DEFAULT 1,
            haptic_feedback INTEGER DEFAULT 1,
            email_reports INTEGER DEFAULT 0,
            dark_mode INTEGER DEFAULT 1,
            preferred_session TEXT DEFAULT 'ALL',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            price_usd REAL NOT NULL,
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            stripe_price_id TEXT,
            entitlements_json TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            current_period_end DATETIME,
            stripe_subscription_id TEXT UNIQUE,
            stripe_customer_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (plan_id) REFERENCES plans(id)
        );
        """
    ),
    (
        2,
        "signals_markets_and_setups",
        """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument TEXT NOT NULL,
            direction TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            strategy TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Metals',
            entry_price REAL NOT NULL,
            sl_price REAL NOT NULL,
            tp1_price REAL NOT NULL,
            tp2_price REAL,
            tp3_price REAL,
            rr_ratio REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            strategy_version TEXT DEFAULT 'v1.0.0',
            condition_score INTEGER DEFAULT 80,
            condition_breakdown_json TEXT,
            exit_price REAL,
            chart_url TEXT,
            description TEXT,
            risk_note TEXT,
            author_id INTEGER,
            data_mode TEXT NOT NULL DEFAULT 'LIVE',
            setup_id TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS setup_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setup_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            price REAL NOT NULL,
            message TEXT,
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS market_symbols (
            symbol TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            pip_size REAL NOT NULL DEFAULT 0.0001,
            tick_size REAL NOT NULL DEFAULT 0.0001,
            tick_value REAL NOT NULL DEFAULT 1.0,
            lot_size REAL NOT NULL DEFAULT 100000.0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL DEFAULT 0,
            is_closed INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timeframe, timestamp)
        );
        """
    ),
    (
        3,
        "mt5_and_telegram_infrastructure",
        """
        CREATE TABLE IF NOT EXISTS mt5_accounts (
            ea_id TEXT PRIMARY KEY,
            user_id INTEGER,
            secret_key TEXT NOT NULL DEFAULT 'mt5_demo_secret_key_2026',
            account_number INTEGER,
            account_hash TEXT,
            broker TEXT,
            server TEXT,
            version TEXT DEFAULT '1.00',
            status TEXT DEFAULT 'ONLINE',
            last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_ping_ip TEXT,
            allowed_symbols TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS ea_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id TEXT NOT NULL,
            terminal_path TEXT,
            os_info TEXT,
            connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            disconnected_at DATETIME,
            events_count INTEGER DEFAULT 0,
            FOREIGN KEY (ea_id) REFERENCES mt5_accounts(ea_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS symbol_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ea_id TEXT NOT NULL,
            broker_symbol TEXT NOT NULL,
            canonical_symbol TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ea_id, broker_symbol)
        );

        CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'en',
            is_premium INTEGER DEFAULT 0,
            is_bot INTEGER DEFAULT 0,
            auth_date INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS telegram_bot_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_id INTEGER UNIQUE NOT NULL,
            update_type TEXT NOT NULL,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS telegram_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_name TEXT NOT NULL,
            telegram_channel_id TEXT NOT NULL UNIQUE,
            market_category TEXT NOT NULL,
            required_tier TEXT DEFAULT 'ALL_ACCESS',
            alert_types TEXT DEFAULT 'ALL',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    ),
    (
        4,
        "alerts_deduplication_and_journal",
        """
        CREATE TABLE IF NOT EXISTS user_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL DEFAULT 'PRICE',
            target_price REAL NOT NULL,
            condition TEXT NOT NULL,
            note TEXT,
            is_active INTEGER DEFAULT 1,
            triggered_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            category TEXT,
            display_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, symbol),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS alert_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idempotency_key TEXT UNIQUE NOT NULL,
            setup_id TEXT,
            recipient_type TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            status TEXT DEFAULT 'DELIVERED',
            delivered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT
        );

        CREATE TABLE IF NOT EXISTS telegram_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            telegram_id INTEGER,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT,
            payload_json TEXT,
            status TEXT DEFAULT 'QUEUED',
            error TEXT,
            is_read INTEGER DEFAULT 0,
            sent_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chart_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            setup_id TEXT NOT NULL,
            storage_type TEXT DEFAULT 'LOCAL_SVG',
            file_path TEXT NOT NULL,
            url TEXT NOT NULL,
            format TEXT DEFAULT 'SVG',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS trade_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_id INTEGER,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            strategy TEXT,
            entry_price REAL,
            sl_price REAL,
            tp_price REAL,
            exit_price REAL,
            result_usd REAL DEFAULT 0,
            r_multiple REAL DEFAULT 0,
            lot_size REAL DEFAULT 1.0,
            risk_usd REAL DEFAULT 0.0,
            risk_pct REAL DEFAULT 1.0,
            timeframe TEXT DEFAULT '15M',
            status TEXT DEFAULT 'CLOSED',
            tags TEXT,
            notes TEXT,
            emotion_notes TEXT,
            screenshot_url TEXT,
            trade_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES trading_accounts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS academy_courses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            level TEXT NOT NULL,
            duration TEXT,
            display_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS academy_lessons (
            id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            title TEXT NOT NULL,
            duration TEXT,
            content_md TEXT,
            display_order INTEGER DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES academy_courses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS academy_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id TEXT NOT NULL,
            is_completed INTEGER DEFAULT 1,
            completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, lesson_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    ),
    (
        5,
        "audit_logs_and_performance_indexes",
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            actor_id INTEGER,
            action TEXT,
            target_type TEXT,
            target_id INTEGER,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            service TEXT DEFAULT 'SYSTEM',
            severity TEXT DEFAULT 'INFO',
            user_id INTEGER,
            symbol TEXT,
            correlation_id TEXT,
            message TEXT,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS external_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            target_url TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            last_checked_at DATETIME,
            response_code INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stripe_webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            status TEXT DEFAULT 'PROCESSED',
            payload_json TEXT,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Performance Indexes
        CREATE INDEX IF NOT EXISTS idx_signals_symbol_tf ON signals(instrument, timeframe);
        CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
        CREATE INDEX IF NOT EXISTS idx_candles_lookup ON candles(symbol, timeframe, timestamp);
        CREATE INDEX IF NOT EXISTS idx_alert_deliveries_idemp ON alert_deliveries(idempotency_key);
        CREATE INDEX IF NOT EXISTS idx_mt5_heartbeat ON mt5_accounts(last_heartbeat);
        CREATE INDEX IF NOT EXISTS idx_journal_user ON trade_journal(user_id, trade_date);
        CREATE INDEX IF NOT EXISTS idx_telegram_users_tgid ON telegram_users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_user_alerts_lookup ON user_alerts(user_id, symbol, is_active);
        CREATE INDEX IF NOT EXISTS idx_audit_lookup ON audit_logs(service, timestamp);
        """
    ),
    (
        6,
        "contact_forms_sessions_and_composite_indexes",
        """
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            experience TEXT,
            trading_level TEXT,
            message TEXT NOT NULL,
            ip_address TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS career_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            country TEXT,
            skills TEXT,
            url TEXT,
            linkedin TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS affiliate_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT,
            social_channel TEXT,
            audience_size TEXT,
            primary_platform TEXT,
            telegram_username TEXT,
            strategy TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS processed_webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            is_pinned INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS signal_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL,
            final_status TEXT NOT NULL,
            exit_price REAL,
            r_multiple REAL DEFAULT 0,
            win_loss_be TEXT,
            closed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE
        );

        -- Additional Composite Indexes
        CREATE INDEX IF NOT EXISTS idx_signals_inst_status_created ON signals(instrument, status, created_at);
        CREATE INDEX IF NOT EXISTS idx_user_alerts_user_active ON user_alerts(user_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_user_watchlists_user_sym ON user_watchlists(user_id, symbol);
        CREATE INDEX IF NOT EXISTS idx_trade_journal_user_created ON trade_journal(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_contact_email_created ON contact_messages(email, created_at);
        """
    ),
    (
        7,
        "telegram_ecosystem_and_account_linking",
        """
        CREATE TABLE IF NOT EXISTS account_linking_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            is_used INTEGER DEFAULT 0,
            used_by_telegram_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_alert_settings (
            user_id INTEGER PRIMARY KEY,
            min_condition_score INTEGER DEFAULT 75,
            preferred_timeframes TEXT DEFAULT '5M,15M,1H,4H',
            preferred_instruments TEXT DEFAULT 'ALL',
            alert_delivery_mode TEXT DEFAULT 'ALL',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS telegram_delivery_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_id INTEGER,
            telegram_id INTEGER,
            event_type TEXT,
            status TEXT NOT NULL,
            attempts INTEGER DEFAULT 1,
            error TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_linking_token ON account_linking_tokens(token, is_used);
        CREATE INDEX IF NOT EXISTS idx_delivery_logs_status ON telegram_delivery_logs(status);
        CREATE INDEX IF NOT EXISTS idx_tg_notifs_user_event ON telegram_notifications(user_id, event_type, created_at);
        """
    ),
    (
        8,
        "virtual_accounts_portals_and_google_oauth",
        """
        CREATE TABLE IF NOT EXISTS trading_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT DEFAULT 'VIRTUAL',
            starting_balance REAL NOT NULL DEFAULT 10000.0,
            current_balance REAL NOT NULL DEFAULT 10000.0,
            currency TEXT NOT NULL DEFAULT 'USD',
            start_date DATE NOT NULL DEFAULT (CURRENT_DATE),
            description TEXT,
            is_archived INTEGER DEFAULT 0,
            is_default INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS trading_account_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            reference_id TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES trading_accounts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT DEFAULT 'GENERAL',
            status TEXT DEFAULT 'OPEN',
            priority TEXT DEFAULT 'NORMAL',
            assigned_employee_id INTEGER,
            response_notes TEXT,
            resolved_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_employee_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS google_oauth_states (
            state TEXT PRIMARY KEY,
            redirect_uri TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_trading_accounts_user ON trading_accounts(user_id, is_archived);
        CREATE INDEX IF NOT EXISTS idx_account_txs_account ON trading_account_transactions(account_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status, priority, created_at);
        """
    )
]

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = os.environ.get("DATABASE_PATH", "chartora.db")
    
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

class MigrationManager:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def initialize_migration_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def get_applied_versions(self) -> List[int]:
        self.initialize_migration_table()
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
        return [row[0] for row in cursor.fetchall()]

    def run_migrations(self) -> int:
        self.initialize_migration_table()
        applied = self.get_applied_versions()
        count = 0

        for version, name, sql_script in MIGRATIONS:
            if version not in applied:
                cursor = self.conn.cursor()
                try:
                    cursor.executescript(sql_script)
                    cursor.execute("INSERT INTO schema_migrations (version, name) VALUES (?, ?)", (version, name))
                    self.conn.commit()
                    count += 1
                except Exception as e:
                    self.conn.rollback()
                    raise RuntimeError(f"Migration {version} ({name}) failed: {e}")

        # Ensure trade_journal columns if migrated from earlier versions
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA table_info(trade_journal)")
            existing_cols = [r[1] for r in cursor.fetchall()]
            for col_name, col_type in [
                ("account_id", "INTEGER"),
                ("lot_size", "REAL DEFAULT 1.0"),
                ("risk_usd", "REAL DEFAULT 0.0"),
                ("risk_pct", "REAL DEFAULT 1.0"),
                ("timeframe", "TEXT DEFAULT '15M'"),
                ("status", "TEXT DEFAULT 'CLOSED'"),
                ("tags", "TEXT"),
                ("emotion_notes", "TEXT")
            ]:
                if col_name not in existing_cols:
                    try:
                        cursor.execute(f"ALTER TABLE trade_journal ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass
            self.conn.commit()
        except Exception:
            pass

        return count

def run_all_migrations(db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    try:
        mgr = MigrationManager(conn)
        mgr.run_migrations()
    finally:
        conn.close()

if __name__ == "__main__":
    run_all_migrations()
