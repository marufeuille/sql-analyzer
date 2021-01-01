from src.analyze import analyze_identifier
import sqlparse


def test_analyze_identifier():
    sql = """
        SELECT
            SUM(x) AS sum_x
    """
    expected = {"agg_func": "SUM", "name": "sum_x", "agg_columns": ["x"], "from": []}
    func = [t for t in sqlparse.parse(sql)[0].tokens if not t.is_whitespace][-1]
    assert analyze_identifier(func) == expected

    sql = """
        SELECT
            CONCAT(str1, str2) AS concats
    """
    expected = {"agg_func": "CONCAT", "name": "concats", "agg_columns": ["str1", "str2"], "from": []}
    func = [t for t in sqlparse.parse(sql)[0].tokens if not t.is_whitespace][-1]
    assert analyze_identifier(func) == expected