import sqlparse

from re import sub
from sqlparse.tokens import DML, Keyword
from sqlparse.sql import Identifier, IdentifierList, TokenList, Token

def iter_subqueries(token: Token):
    """https://blog.hoxo-m.com/entry/sqlparse_parse"""
    if token.ttype == sqlparse.tokens.DML:
        yield token.parent
    if not isinstance(token, TokenList):
        return
    for t in token:
        yield from iter_subqueries(t)


def analyze_identifier(identifier: Identifier):
    """get necesarry information from Identifier Object

    Parameters
    ----------
    identifier : Identifier

    Returns
    -------
    dict
        identifier basic information
    """
    alias = identifier.get_alias()
    real_name = identifier.get_real_name()
    if alias:
        return {"name": alias, "original_name": real_name, "from": []}
    else:
        return {"name": real_name, "from": []}

def analyze_select(statement:sqlparse.sql.Statement, table_definitons:dict=None):
    """Analyze Select Query Statement

    Parameters
    ----------
    statement : Statement
        Select Statement Object

    Returns
    -------
    dict
        analyze result
    """

    current_idx = 0
    t = statement.token_first(skip_ws=True, skip_cm=True)
    table_info = {
        "COLUMNS": []
    }
    from_table = None
    while t is not None:
        if t.ttype == DML: # currently, only select is OK
            current_idx, t = statement.token_next(current_idx)
            print(t.__class__)
            if isinstance(t, Identifier):
                table_info["COLUMNS"].append(analyze_identifier(t))
            elif isinstance(t, IdentifierList):
                for ident in t.get_identifiers():
                    table_info["COLUMNS"].append(analyze_identifier(ident))
            elif t.value == "*":
                table_info["COLUMNS"].append({"name": "*", "from": []})

        elif t.ttype == Keyword and t.value.lower() == "from":
            current_idx, t = statement.token_next(current_idx)
            from_table = t.value
        current_idx, t = statement.token_next(current_idx)

    print(table_info)
    for c in table_info["COLUMNS"]:
        c["from"].append(from_table)

    asterisk = None
    for c in table_info["COLUMNS"]:
        if c["name"] == "*":
            asterisk = c
            _from_table = c["from"][0]
            for definition in table_definitons[_from_table]:
                table_info["COLUMNS"].append({
                    "name": definition["name"],
                    "type": definition["type"],
                    "from": [_from_table]
                })
    if asterisk:
        table_info["COLUMNS"] = [c for c in table_info["COLUMNS"] if c != asterisk]
    print(table_info)
    return table_info
