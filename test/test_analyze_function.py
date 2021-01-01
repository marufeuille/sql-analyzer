import sqlparse
from src.analyze import analyze_function

def test_analyze_function():
    sql = """
        SELECT
            SUM(x)
    """
    expected = {"agg_func": "SUM", "name": "no_name", "agg_columns": ["x"], "from": []}
    func = [t for t in sqlparse.parse(sql)[0].tokens if not t.is_whitespace][-1]
    assert analyze_function(func) == expected