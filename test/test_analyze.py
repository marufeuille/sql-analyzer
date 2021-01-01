from src.analyze import analyze
import sqlparse

def test_simple():
    sql = """
    WITH a AS (
        SELECT
            x
        FROM
            t0
    )
    SELECT
        x
    FROM
        a
    """
    expected = {
        "main": [
            {
                "name": "x",
                "from": ["a"]
            }
        ],
        "subqueries": {
            "a": [
                {
                    "name": "x",
                    "from": ["t0"]
                }
            ]
        }
    }
    assert analyze(sql) == expected, "Simple With"