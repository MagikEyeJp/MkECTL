# DSL Script Grammar

This document summarizes the grammar of the new MkECTL scripting language as implemented with Lark.

```
start       : line*
line        : statement NEWLINE
            | NEWLINE
            | statement

# In the parse tree each line is represented as a `stmt` node.

?statement  : assignment
            | command_call
            | func_def
            | func_call
            | if_statement
            | while_statement

assignment  : NAME "=" expr
            | "set" NAME "," expr

command_call: NAME [arg_list]
arg_list    : expr ("," expr)*

func_call   : NAME "(" [arg_list] ")"

if_statement: "if" expr "{" block "}" ["else" "{" block "}"]
while_statement: "while" expr "{" block "}"

func_def    : "function" NAME "(" [param_list] ")" "{" block "}"
param_list  : NAME ("," NAME)*

block       : statement*

?expr       : comparison
?comparison : arith (COMP_OP arith)?
COMP_OP     : ">"|"<"|">="|"<="|"=="|"!="
?arith      : arith "+" term   -> add
            | arith "-" term   -> sub
            | term
?term       : term "*" factor -> mul
            | term "/" factor -> div
            | factor
?factor     : NUMBER
            | STRING
            | NAME
            | "${" NAME "}"
            | "(" expr ")"
```

The grammar roughly follows C-like syntax. Numbers and strings can appear in expressions. Variables can be referenced with `$\{name\}` or simply by name. Basic arithmetic and comparisons are supported.

Functions are defined with the `function` keyword. Control statements `if` and `while` use braces `{}` to delimit blocks.

For concrete command syntax see [README.md](README.md).
