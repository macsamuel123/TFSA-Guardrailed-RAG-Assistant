import os
import psycopg

def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg.connect(url)
    return conn

def create_tables(connection):
    with connection.cursor() as cursor:
            
            
            create_tables_script = """
            CREATE TABLE IF NOT EXISTS annual_limits (
                id            SERIAL PRIMARY KEY,
                year          INTEGER NOT NULL,
                account_type  TEXT NOT NULL CHECK (account_type IN ('TFSA', 'RRSP', 'FHSA')),
                dollar_limit  NUMERIC(10, 2) NOT NULL,
                source        TEXT NOT NULL,
                source_page   INTEGER,
                UNIQUE (year, account_type)
            );

            CREATE TABLE IF NOT EXISTS penalty_rates (
                id            SERIAL PRIMARY KEY,
                account_type  TEXT NOT NULL CHECK (account_type IN ('TFSA', 'RRSP', 'FHSA')),
                rule          TEXT NOT NULL,
                rate          NUMERIC(6, 4) NOT NULL,
                unit          TEXT NOT NULL,
                source        TEXT NOT NULL,
                source_page   INTEGER,
                UNIQUE (account_type, rule)
            );

            CREATE TABLE IF NOT EXISTS product_catalog (
                product_id     SERIAL PRIMARY KEY,
                name           TEXT NOT NULL UNIQUE,
                account_type   TEXT NOT NULL CHECK (account_type IN ('TFSA', 'RRSP', 'FHSA')),
                interest_rate  NUMERIC(5, 4) NOT NULL,
                monthly_fee    NUMERIC(8, 2) NOT NULL DEFAULT 0,
                min_balance    NUMERIC(10, 2) NOT NULL DEFAULT 0,
                description    TEXT
            );

            CREATE TABLE IF NOT EXISTS members (
                member_id       SERIAL PRIMARY KEY,
                first_name      TEXT NOT NULL,
                last_name       TEXT NOT NULL,
                birth_year      INTEGER NOT NULL CHECK (birth_year BETWEEN 1900 AND 2026),
                province        TEXT NOT NULL,
                resident_since  INTEGER NOT NULL,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE TABLE IF NOT EXISTS accounts (
                account_id    SERIAL PRIMARY KEY,
                member_id     INTEGER NOT NULL REFERENCES members(member_id),
                product_id    INTEGER NOT NULL REFERENCES product_catalog(product_id),
                account_type  TEXT NOT NULL CHECK (account_type IN ('TFSA', 'RRSP', 'FHSA')),
                opened_on     DATE NOT NULL,
                balance       NUMERIC(12, 2) NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS transactions (
                txn_id      SERIAL PRIMARY KEY,
                account_id  INTEGER NOT NULL REFERENCES accounts(account_id),
                txn_date    DATE NOT NULL,
                txn_type    TEXT NOT NULL CHECK (txn_type IN ('contribution', 'withdrawal')),
                amount      NUMERIC(12, 2) NOT NULL CHECK (amount > 0)
            );

            CREATE INDEX IF NOT EXISTS idx_accounts_member ON accounts(member_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, txn_date);
            """
            
            # Execute the entire script at once
            cursor.execute(create_tables_script)
            print("All 6 tables created successfully!")


