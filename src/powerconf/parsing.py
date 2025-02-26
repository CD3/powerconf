import pyparsing as pp

unbraced_variable = pp.Combine(
    pp.Literal("$") + pp.Word(pp.alphanums + "/_")("variable name")
)
braced_variable = pp.Combine(
    pp.Literal("$")
    + pp.QuotedString(quote_char="{", end_quote_char="}")("variable name")
)
variable = unbraced_variable | braced_variable
expression = pp.Combine(
    pp.Literal("$") + pp.original_text_for(pp.nested_expr())("expression body")
)
