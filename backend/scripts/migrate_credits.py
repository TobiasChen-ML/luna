"""
Simple migration script to add new columns to existing SQLite database.
Run with: python scripts/migrate_credits.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'roxy.db')

def migrate():
    print(f"Migrating database at: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add new columns to users table
    new_columns = {
        'purchased_credits': 'REAL DEFAULT 0',
        'monthly_credits': 'REAL DEFAULT 0',
        'user_type': "TEXT DEFAULT 'free'",
        'subscription_period': 'TEXT',
        'subscription_start_date': 'TIMESTAMP',
        'subscription_end_date': 'TIMESTAMP',
        'last_monthly_credit_grant': 'TIMESTAMP',
        'signup_bonus_granted': 'INTEGER DEFAULT 0',
        'total_credits_earned': 'REAL DEFAULT 0',
        'total_credits_spent': 'REAL DEFAULT 0',
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {col_name} might already exist: {e}")
    
    # Create credit tables
    tables = [
        '''CREATE TABLE IF NOT EXISTS credit_cost_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_cost REAL DEFAULT 0.1,
            voice_cost REAL DEFAULT 0.2,
            image_cost INTEGER DEFAULT 2,
            video_cost INTEGER DEFAULT 4,
            voice_call_per_minute INTEGER DEFAULT 3,
            signup_bonus_credits INTEGER DEFAULT 10,
            premium_monthly_credits INTEGER DEFAULT 100,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS credit_packs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            bonus_credits INTEGER DEFAULT 0,
            is_popular INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT UNIQUE NOT NULL,
            price_cents INTEGER NOT NULL,
            monthly_equivalent_cents INTEGER NOT NULL,
            discount_percent INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            usage_type TEXT,
            credit_source TEXT,
            order_id TEXT,
            character_id TEXT,
            session_id TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
    ]
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"Created/verified table")
        except sqlite3.OperationalError as e:
            print(f"Table creation error: {e}")
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON credit_transactions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_credit_transactions_created ON credit_transactions(created_at)",
    ]
    
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except sqlite3.OperationalError:
            pass
    
    # Insert default credit config if not exists
    cursor.execute("SELECT COUNT(*) FROM credit_cost_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO credit_cost_config 
            (message_cost, voice_cost, image_cost, video_cost, voice_call_per_minute, signup_bonus_credits, premium_monthly_credits)
            VALUES (0.1, 0.2, 2, 4, 3, 10, 100)
        ''')
        print("Inserted default credit config")
    
    # Insert default subscription plans
    cursor.execute("SELECT COUNT(*) FROM subscription_plans")
    if cursor.fetchone()[0] == 0:
        plans = [
            ('1m', 1299, 1299, 0, 1),
            ('3m', 1797, 599, 54, 2),
            ('12m', 4788, 399, 70, 3),
        ]
        cursor.executemany(
            "INSERT INTO subscription_plans (period, price_cents, monthly_equivalent_cents, discount_percent, display_order) VALUES (?, ?, ?, ?, ?)",
            plans
        )
        print("Inserted default subscription plans")
    
    # Insert default credit packs
    cursor.execute("SELECT COUNT(*) FROM credit_packs")
    if cursor.fetchone()[0] == 0:
        packs = [
            ('pack_100', 'Starter', 100, 999, 0, 0, 1),
            ('pack_350', 'Popular', 350, 3499, 0, 1, 2),
            ('pack_550', 'Value', 550, 4999, 0, 0, 3),
            ('pack_1150', 'Power', 1150, 9999, 0, 0, 4),
            ('pack_2400', 'Big', 2400, 19999, 0, 0, 5),
            ('pack_3750', 'Ultimate', 3750, 29999, 0, 0, 6),
        ]
        cursor.executemany(
            "INSERT INTO credit_packs (pack_id, name, credits, price_cents, bonus_credits, is_popular, display_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            packs
        )
        print("Inserted default credit packs")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
