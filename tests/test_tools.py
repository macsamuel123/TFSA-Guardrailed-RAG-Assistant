import pytest
from app.db import get_connection
from app.tools import calculate_tfsa_room
from script.seed import MEMBERS


@pytest.fixture
def conn():
    with get_connection() as c:
        yield c


def get_member_id(conn, first_name):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT member_id FROM members WHERE first_name = %s AND last_name = 'Testcase'",
            (first_name,),
        )
        return cur.fetchone()[0]


@pytest.mark.parametrize("m", MEMBERS, ids=[m["key"] for m in MEMBERS])
def test_tfsa_room(conn, m):
    member_id = get_member_id(conn, m["first_name"])
    assert calculate_tfsa_room(conn, member_id) == m["expected_room_2025"]