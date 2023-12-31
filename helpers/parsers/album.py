from lark import Lark


from configs.parser import *





dirname_parser = Lark(r"""
value: dict
        | list
        | ESCAPED_STRING
        | SIGNED_NUMBER
        | "true" | "false" | "null"

list : "[" [value ("," value)*] "]"

dict : "{" [pair ("," pair)*] "}"
pair : ESCAPED_STRING ":" value

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS

""", start='value')