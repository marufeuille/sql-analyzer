import sqlparse

from re import sub
from sqlparse.tokens import DML, Keyword, Punctuation
from sqlparse.sql import Identifier, IdentifierList, TokenList, Token

def iter_subqueries(token: Token):
    if token.ttype == sqlparse.tokens.DML:
        yield token.parent
    if not isinstance(token, TokenList): # リーフノードの場合は子を探索しない
        return
    for t in token:
        yield from iter_subqueries(t)


def analyze_identifier(identifier: Identifier):
    alias = identifier.get_alias()
    real_name = identifier.get_real_name()
    if alias:
        return {"name": alias, "original_name": real_name, "from": []}
    else:
        return {"name": real_name, "from": []}

def analyze_select(statement:sqlparse.sql.Statement):

    current_idx = 0
    t = statement.token_first(skip_ws=True, skip_cm=True)
    table_info = {
        "COLUMNS": []
    }
    from_table = None
    while t is not None:
        print(t, t.ttype)
        if t.ttype == DML:
            current_idx, t = statement.token_next(current_idx)
            print(t, t.ttype, isinstance(t, TokenList))
            if (isinstance(t, TokenList)):
                if isinstance(t, Identifier):
                    table_info["COLUMNS"].append(analyze_identifier(t))
                elif isinstance(t, IdentifierList):
                    for ident in t.get_identifiers():
                        table_info["COLUMNS"].append(analyze_identifier(ident))

        if t.ttype == Keyword and t.value.lower() == "from":
            current_idx, t = statement.token_next(current_idx)
            if (isinstance(t, TokenList)):
                print("list")
            from_table = t.value
        current_idx, t = statement.token_next(current_idx)
    for c in table_info["COLUMNS"]:
        c["from"].append(from_table)
    print(table_info)
    return table_info