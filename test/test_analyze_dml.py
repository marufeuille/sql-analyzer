from src.analyze import analyze_dml, iter_subqueries
import sqlparse

# test analyze dml
def test_simple_select():
    sql = "SELECT x FROM t0"
    expected = [
        {
            "name": "x",
            "from": ["t0"]
        }
    ]
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "single column select"

    sql = "SELECT x, y FROM t0"
    expected = [
        {
            "name": "x",
            "from": ["t0"]
        },
        {
            "name": "y",
            "from": ["t0"]
        }
    ]
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "multiple columns select"

    sql = "SELECT x AS x2 FROM t0"
    expected = [
        {
            "name": "x2",
            "original_name": "x",
            "from": ["t0"]
        }
    ]

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "has alias column"

def test_inference_types():
    sql = "SELECT x, y FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = [
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


    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "inference types"


def test_inference_asterisk():
    sql = "SELECT * FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = [
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

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "inference from static table definition"

    sql = "SELECT * EXCEPT(y) FROM t0"
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = [
        {
            "name": "x",
            "type": "INTEGER",
            "from": ["t0"]
        }
    ]


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
    table_definitions[sql1_output_tablename] = analyze_dml(subqueries[0], table_definitions=table_definitions)
    sql2 = "SELECT x, y FROM t1 WHERE y < 0"
    expected = [
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

    subqueries = list(iter_subqueries(sqlparse.parse(sql2)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "multiple inference"

def test_brace_started_dml():
    sql = """
    (
        SELECT
            x, y
        FROM
            t0
    )
    """
    expected = [
        {
            "name": "x",
            "from": ["t0"]
        },
        {
            "name": "y",
            "from": ["t0"]
        }
    ]
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "brace started dml"

def test_agg_functions():
    sql = """
    SELECT
        SUM(x)
    FROM
        t0
    """
    expected = [
            {
                "name": "no_name",
                "from": ["t0"],
                "agg_func": "SUM",
                "agg_columns": ["x"]
            }
        ]

    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0]) == expected, "simple aggregate"

    # table definitions are no effect for aggregate function output type
    sql = """
    SELECT
        SUM(x)
    FROM
        t0
    """
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = [
            {
                "name": "no_name",
                "from": ["t0"],
                "agg_func": "SUM",
                "agg_columns": ["x"]
            }
        ]
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "table definitions are no effect"

    sql = """
    SELECT
        SUM(x) AS sum_x, y
    FROM
        t0
    """
    table_definitions = {"t0": [
        {"name":"x", "type":"INTEGER", "mode": "NULLABLE"},
        {"name":"y", "type":"INTEGER", "mode": "NULLABLE"},
    ]}
    expected = [
            {
                "name": "sum_x",
                "from": ["t0"],
                "agg_func": "SUM",
                "agg_columns": ["x"]
            },
            {
                "name": "y",
                "from": ["t0"],
                "type": "INTEGER"
            }
        ]
    subqueries = list(iter_subqueries(sqlparse.parse(sql)[0]))
    assert analyze_dml(subqueries[0], table_definitions=table_definitions) == expected, "with table definition column"