from app.db import get_connection

def calculate_tfsa_room(connection, member_id, year=2025):
    """Return a member's TFSA contribution room for the given year.

    Room = limits since first eligible year
           - contributions up to and including this year
           + withdrawals from previous years (restored the following year)

    A negative result means the member is over-contributed.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT birth_year, resident_since FROM members WHERE member_id = %s",
            (member_id,),
        )
        row=cursor.fetchone()        
        if row is None:
            raise ValueError(f"Member {member_id} not found")

        birth_year, resident_year = row
        first_year = max(2009,birth_year + 18,resident_year)

        if first_year > year:
            return 0
        # 3. Total room earned: every annual limit from first_year to this year
        cursor.execute(
            """
            SELECT COALESCE(SUM(dollar_limit), 0)
            FROM annual_limits
            WHERE account_type = 'TFSA'
              AND year BETWEEN %s AND %s
            """,
            (first_year, year),
        )
        total_limits = cursor.fetchone()[0]

        # 4. Total contributed, up to and including this year
        cursor.execute(
            """
            SELECT COALESCE(SUM(t.amount), 0)
            FROM transactions t
            JOIN accounts a ON a.account_id = t.account_id
            WHERE a.member_id = %s
              AND a.account_type = 'TFSA'
              AND t.txn_type = 'contribution'
              AND EXTRACT(YEAR FROM t.txn_date) <= %s
            """,
            (member_id, year),
        )
        contributions = cursor.fetchone()[0]

        # 5. Withdrawals restore room, but only from the following year on (strict <)
        cursor.execute(
            """
            SELECT COALESCE(SUM(t.amount), 0)
            FROM transactions t
            JOIN accounts a ON a.account_id = t.account_id
            WHERE a.member_id = %s
              AND a.account_type = 'TFSA'
              AND t.txn_type = 'withdrawal'
              AND EXTRACT(YEAR FROM t.txn_date) < %s
            """,
            (member_id, year),
        )
        withdrawals_restored = cursor.fetchone()[0]

         # 6. The formula
        return total_limits - contributions + withdrawals_restored