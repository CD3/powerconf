from pyparsing import *

unbraced_variable = Combine(Literal("$") + Word(alphanums + "/_")("variable name"))
braced_variable = Combine(
    Literal("$") + QuotedString(quote_char="{", end_quote_char="}")("variable name")
)
variable = unbraced_variable | braced_variable
expression = Combine(Literal("$") + original_text_for(nested_expr())("expression body"))
