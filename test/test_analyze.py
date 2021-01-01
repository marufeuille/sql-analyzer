from src.analyze import analyze
import sqlparse

def test_cte():
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

def test_subquery():
    sql = """
    SELECT
        x
    FROM (
        SELECT
            x
        FROM
            t0
    )
    """
    expected = {
        "main": [
            {
                "name": "x",
                "from": ["___tmp__0"]
            }
        ],
        "subqueries": {
            "___tmp__0": [
                {
                    "name": "x",
                    "from": ["t0"]
                }
            ]
        }
    }
    assert analyze(sql) == expected, "Simple With"

def test_comb_cte_sub():
    sql = """
    WITH a AS (
        SELECT
            x
        FROM
            t0
    )
    SELECT
        x
    FROM (
        SELECT
            x
        FROM
            a
    )
    """
    expected = {
        "main": [
            {
                "name": "x",
                "from": ["___tmp__0"]
            }
        ],
        "subqueries": {
            "___tmp__0": [
                {
                    "name": "x",
                    "from": ["a"]
                }
            ],
            "a": [
                {
                    "name": "x",
                    "from": ["t0"]
                }
            ]
        },
    }
    assert analyze(sql) == expected, "Simple With"
