import sqlparse

from re import sub
from sqlparse.tokens import DML, Keyword, Punctuation
from sqlparse.sql import Function, Identifier, IdentifierList, Parenthesis, TokenList, Token
from sqlparse.tokens import Name

def analyze(sql: str):
    statement = sqlparse.parse(sql)[0]
    _subqueries = [q for q in iter_subqueries(statement) if isinstance(q, Parenthesis)]
    tmp_prefix = "___tmp__"
    idx = 0
    table_definitions = {}
    result = {}
    for q in _subqueries:
        if isinstance(q.parent, Identifier):
            name = q.parent.get_name()
        else:
            name = f"{tmp_prefix}{idx}"
            idx += 1
        r = analyze_dml(q)
        if "subqueries" not in result:
            result["subqueries"] = {}
        result["subqueries"][name] = r
        table_definitions[name] = r
    result["main"] = analyze_dml(statement, table_definitions=table_definitions)
    return result

def iter_subqueries(token: Token):
    """https://blog.hoxo-m.com/entry/sqlparse_parse"""
    if token.ttype == sqlparse.tokens.DML:
        yield token.parent
    if not isinstance(token, TokenList):
        return
    for t in token:
        yield from iter_subqueries(t)

def analyze_function(func: Function): # currently only one argument function is OK
    name = func.get_name()

    agg_columns = []
    for ident in func.get_parameters():
        agg_columns.append(ident.value)

    return {"agg_func": name, "name": "no_name", "agg_columns": agg_columns, "from": []}

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
    token = identifier.token_first(skip_cm=True, skip_ws=True)
    alias = identifier.get_alias()
    real_name = identifier.get_real_name()
    if token.ttype == Name:
        if alias:
            return {"name": alias, "original_name": real_name, "from": []}
        else:
            return {"name": real_name, "from": []}
    elif isinstance(token, Function):
        agg_columns = []
        for ident in token.get_parameters():
            agg_columns.append(ident.value)

        return {"agg_func": real_name, "name": alias if alias else "no_name", "agg_columns": agg_columns, "from": []}


def analyze_dml(statement:Token, table_definitions:dict=None):
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

    t = statement.token_first(skip_ws=True, skip_cm=True)
    current_idx = statement.token_index(t)
    table_info = []
    from_table = None
    if t.ttype == Punctuation and t.ttype == "(":
        current_idx, t = statement.token_next(current_idx, skip_ws=True, skip_cm=True)

    while t is not None:
        print(t, t.__class__)
        if t.ttype == DML: # currently, only select is OK
            current_idx, t = statement.token_next(current_idx, skip_ws=True, skip_cm=True)
            print("\t", t, t.__class__)
            # case SELECT x FROM xxx
            if isinstance(t, Identifier):
                print("\t\t", t, t.__class__)
                table_info.append(analyze_identifier(t))
            #case SELECT x,y,z,... FROM xxx
            elif isinstance(t, IdentifierList):
                print("\t\t", t, t.__class__)
                for ident in t.get_identifiers():
                    table_info.append(analyze_identifier(ident))
            # case SELECT SUM(x) FROM xxx
            elif isinstance(t, Function):
                print("\t\t", t, t.__class__)
                table_info.append(analyze_function(t))
            # case SELECT * FROM xxx
            elif isinstance(t, Token) and t.value == "*":
                # * is represents as Token class instance
                _idx, _t = statement.token_next(current_idx)
                print("\t\t", _t, _t.__class__)
                except_columns = []
                # case SELECT * EXCEPT(xxx,xxx,xxx) FROM xxx
                if isinstance(_t, Function) and _t.get_name().lower() == "except":
                    for params in _t.get_parameters():
                        except_columns.append(params.get_name())
                table_info.append({"name": "*", "from": [], "except": except_columns})

        elif t.ttype == Keyword and t.value.lower() == "from":
            current_idx, t = statement.token_next(current_idx)
            from_table = t.value
        current_idx, t = statement.token_next(current_idx)

    print(table_info)
    for c in table_info:
        c["from"].append(from_table)
        if table_definitions and from_table in table_definitions:
            key = c["name"]
            for c_def in table_definitions[from_table]:
                print(1, c_def)
                if c_def["name"] == key and "type" in c_def:
                    c["type"] = c_def["type"]

    asterisk_column = None
    for c in table_info:
        if c["name"] == "*":
            except_columns = c["except"]
            asterisk_column = c
            _from_table = c["from"][0]
            for definition in table_definitions[_from_table]:
                if definition["name"] not in except_columns:
                    table_info.append({
                        "name": definition["name"],
                        "type": definition["type"],
                        "from": [_from_table]
                    })
    if asterisk_column:
        table_info = [c for c in table_info if c != asterisk_column]
    print(table_info)
    return table_info
