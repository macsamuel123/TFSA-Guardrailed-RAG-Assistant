from app.db import create_tables,get_connection

TFSA_LIMITS=[(2009, 5000),
 (2010, 5000),
 (2011, 5000),
 (2012, 5000),
 (2013, 5500),
 (2014, 5500),
 (2015, 10000),
 (2016, 5500),
 (2017, 5500),
 (2018, 5500),
 (2019, 6000),
 (2020, 6000),
 (2021, 6000),
 (2022, 6000),
 (2023, 6500),
 (2024, 7000),
 (2025, 7000)]

PRODUCTS = [
    # (name, account_type, interest_rate, monthly_fee, min_balance, description)
    ("Northpine TFSA High-Interest Savings", "TFSA", 0.0310, 0, 0, "High-interest TFSA savings with no fees"),
    ("Northpine TFSA Starter Savings", "TFSA", 0.0150, 0, 0, "Basic TFSA savings, no minimum balance"),
    ("Riverstone TFSA 1-Year GIC", "TFSA", 0.0375, 0, 500, "Locked-in TFSA term deposit for one year"),
    ("Lakeshore TFSA Managed Portfolio", "TFSA", 0.0000, 5, 1000, "Managed investment portfolio inside a TFSA, returns vary"),
    ("Northpine RRSP High-Interest Savings", "RRSP", 0.0290, 0, 0, "High-interest RRSP savings with no fees"),
    ("Riverstone RRSP 3-Year GIC", "RRSP", 0.0400, 0, 1000, "Locked-in RRSP term deposit for three years"),
    ("Lakeshore RRSP Managed Portfolio", "RRSP", 0.0000, 5, 1000, "Managed investment portfolio inside an RRSP, returns vary"),
    ("Northpine FHSA Savings", "FHSA", 0.0300, 0, 0, "First Home Savings Account savings, no fees"),
    ("Riverstone FHSA 1-Year GIC", "FHSA", 0.0360, 0, 500, "Locked-in FHSA term deposit for one year"),
    ("Summit Trail FHSA Starter", "FHSA", 0.0100, 0, 0, "Entry-level FHSA savings account"),
]

PENALTIES = [
    # (account_type, rule, rate, unit, source, source_page)
    ("TFSA", "excess_contribution_tax", 0.0100, "per month", "RC4466", None),
    # Replace None with the page where the 1% rule is stated in the guide.
]


MEMBERS = [
    {
        "key": "over_contributor",
        "first_name": "Priya", "last_name": "Testcase",
        "birth_year": 1985, "province": "BC", "resident_since": 2009,
        "product": "Northpine TFSA High-Interest Savings",
        "opened_on": "2009-01-15",
        "balance": 118000.00,
        "max_through": 2024,
        "transactions": [
            ("2025-02-10", "contribution", 9000),
        ],
        "expected_room_2025": -2000,
    },
    {
        "key": "withdrawal_trap",
        "first_name": "Marcus", "last_name": "Testcase",
        "birth_year": 1990, "province": "ON", "resident_since": 2009,
        "product": "Northpine TFSA Starter Savings",
        "opened_on": "2009-01-15",
        "balance": 109000.00,
        "max_through": 2024,
        "transactions": [
            ("2025-01-20", "contribution", 7000),
            ("2025-03-05", "withdrawal", 5000),
            ("2025-06-12", "contribution", 5000),
        ],
        "expected_room_2025": -5000,
    },
    {
        "key": "new_adult",
        "first_name": "Aisha", "last_name": "Testcase",
        "birth_year": 2005, "province": "AB", "resident_since": 2005,
        "product": "Northpine TFSA Starter Savings",
        "opened_on": "2025-09-01",
        "balance": 0.00,
        "max_through": None,
        "transactions": [],
        "expected_room_2025": 20500,
    },
    {
        "key": "newcomer",
        "first_name": "Daniel", "last_name": "Testcase",
        "birth_year": 1980, "province": "BC", "resident_since": 2020,
        "product": "Riverstone TFSA 1-Year GIC",
        "opened_on": "2021-03-01",
        "balance": 11200.00,
        "max_through": None,
        "transactions": [
            ("2021-03-01", "contribution", 4000),
            ("2023-05-15", "contribution", 6000),
        ],
        "expected_room_2025": 28500,
    },
    {
        "key": "maxed_out",
        "first_name": "Grace", "last_name": "Testcase",
        "birth_year": 1975, "province": "NS", "resident_since": 2009,
        "product": "Lakeshore TFSA Managed Portfolio",
        "opened_on": "2009-01-15",
        "balance": 145000.00,
        "max_through": 2025,
        "transactions": [],
        "expected_room_2025": 0,
    },
    {
        "key": "withdrawal_restored",
        "first_name": "Tobi", "last_name": "Testcase",
        "birth_year": 1988, "province": "MB", "resident_since": 2009,
        "product": "Northpine TFSA High-Interest Savings",
        "opened_on": "2009-01-15",
        "balance": 92000.00,
        "max_through": 2024,
        "transactions": [
            ("2024-08-20", "withdrawal", 10000),
        ],
        "expected_room_2025": 17000,
    },
]

def seed_limits(connection):
    with connection.cursor() as cursor:
        for year, limit in TFSA_LIMITS:
            cursor.execute(
                "INSERT INTO annual_limits (year, account_type, dollar_limit, source, source_page) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (year, account_type) DO NOTHING",
                (year, "TFSA", limit, "RC4466", 8),)
            
def seed_products(connection):
    # name, account_type, interest_rate, monthly_fee, min_balance, description)
    with connection.cursor() as cursor:
        for name, account_type, interest_rate, monthly_fee, min_balance, description in PRODUCTS:
            cursor.execute(
                "INSERT INTO product_catalog(name, account_type, interest_rate, monthly_fee, min_balance, description)"
                "VALUES (%s,%s,%s,%s,%s,%s)"
                "ON CONFLICT(name) DO NOTHING",
                (name, account_type, interest_rate, monthly_fee, min_balance, description),
            ) 

def seed_penalties(connection):
    with connection.cursor() as cursor:
        for account_type, rule, rate, unit, source, page in PENALTIES:
            cursor.execute("INSERT INTO penalty_rates (account_type, rule, rate, unit, source, page )"
            "VALUES (%s,%s,%s,%s,%s)"
            "ON CONFLICT(account_type, rule) DO NOTHING",
            (account_type, rule, rate, unit, source, page )
            )

def seed_members(connection):
    with connection.cursor() as cursor:
        for m in MEMBERS:
            cursor.execute(
                "INSERT INTO members(first_name, last_name, birth_year, province, resident_since)"
                "VALUES (%s,%s,%s,%s,%s)"
                "RETURNING member_id",
                ( m["first_name"], m["last_name"], m["birth_year"], m["province"], m["resident_since"])
            )
        member_id=cursor,fetchone()[0]
if __name__ == "__main__":
    with get_connection() as conn:
        create_tables(conn)
        seed_limits(conn)
        seed_penalties(conn)
        seed_products(conn)