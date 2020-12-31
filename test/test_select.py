from src.analyze import analyze_select, iter_subqueries
import pytest
import sqlparse

def test_simple_select():
    sql = "SELECT x FROM t0"
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "from": ["t0"]
            }
        ]
    }
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_select(subqueries[0]) == expected, "single column select"

    sql = "SELECT x, y FROM t0"
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "from": ["t0"]
            },
            {
                "name": "y",
                "from": ["t0"]
            }
        ]
    }
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_select(subqueries[0]) == expected, "multiple columns select"

    sql = "SELECT x AS x2 FROM t0"
    expected = {
        "COLUMNS": [
            {
                "name": "x2",
                "original_name": "x",
                "from": ["t0"]
            }
        ]
    }
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_select(subqueries[0]) == expected, "has alias column"