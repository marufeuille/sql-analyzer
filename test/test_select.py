from src.analyze import analyze_dml, iter_subqueries
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
    assert analyze_dml(subqueries[0]) == expected, "single column select"

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
    assert analyze_dml(subqueries[0]) == expected, "multiple columns select"

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
    assert analyze_dml(subqueries[0]) == expected, "has alias column"

def test_inference_types():
    sql = "SELECT x, y FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "type": "INTEGER",
                "from": ["t0"]
            },
            {
                "name": "y",
                "type": "INTEGER",
                "from": ["t0"]
            }
        ]
    }

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "inference types"


def test_inference_asterisk():
    sql = "SELECT * FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "type": "INTEGER",
                "from": ["t0"]
            },
            {
                "name": "y",
                "type": "INTEGER",
                "from": ["t0"]
            }
        ]
    }

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "inference from static table definition"

    sql = "SELECT * EXCEPT(y) FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "type": "INTEGER",
                "from": ["t0"]
            }
        ]
    }

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "inference with one EXCEPT"

def test_inference_from_ancestor():
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    sql1 = "SELECT x, y FROM t0 WHERE x > 0"
    sql1_output_tablename = "t1"
    subqueries = list(iter_subqueries(sqlparse.parse(sql1)[0]))
    table_definitions[sql1_output_tablename] = analyze_dml(subqueries[0], table_definitions=table_definitions)["COLUMNS"]
    sql2 = "SELECT x, y FROM t1 WHERE y < 0"
    expected = {
        "COLUMNS": [
            {
                "name": "x",
                "type": "INTEGER",
                "from": ["t1"]
            },
            {
                "name": "y",
                "type": "INTEGER",
                "from": ["t1"]
            }
        ]
    }

    subqueries = list(iter_subqueries(sqlparse.parse(sql2)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "multiple inference"

def test_cte():
    sql = """
    WITH t1 AS (
        SELECT
            a, b
        FROM
            t0
    )
    SELECT
        a, b
    FROM
        t1
    """
    expected = {
        "COLUMNS": [{
            {
                "name": "a",
                "from": ["t1"]
            },
            {
                "name": "b",
                "from": ["t1"]
            },
        }],
        "CTE": {
            "t1": [
                {
                    "name": "a",
                    "from": ["t0"]
                },
                {
                    "name": "a",
                    "from": ["t0"]
                },

            ]
        }
    }
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], ) == expected, "simple cte"

def test_agg_functions():
    sql = """
    SELECT
        SUM(x)
    FROM
        t0
    """
    expected = {
        "COLUMNS": [
            {
                "name": "no_name",
                "type": "INTEGER",
                "from": ["t1"],
                "aggregator": "sum",
                "agg_columns": ["x"]
            },
            {
                "name": "y",
                "type": "INTEGER",
                "from": ["t1"]
            }
        ]
    }

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "simple aggregate"