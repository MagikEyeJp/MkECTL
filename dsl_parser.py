from lark import Lark, Transformer, v_args

class ScriptEnvironment(dict):
    pass

class Evaluator(Transformer):
    def __init__(self, env):
        super().__init__()
        self.env = env

    def NEWLINE(self, _):
        return None

    def stmt(self, items):
        return items[0] if items else None

    def empty(self, items):
        return None

    def number(self, n):
        return float(n[0])

    def string(self, s):
        return s[0][1:-1]

    def var(self, name):
        return self.env.get(name[0], 0)

    def var_dollar(self, items):
        return self.env.get(str(items[0]), 0)

    def add(self, items):
        return items[0] + items[1]

    def sub(self, items):
        return items[0] - items[1]

    def mul(self, items):
        return items[0] * items[1]

    def div(self, items):
        return items[0] / items[1]

    def COMP_OP(self, token):
        return token.value

    def comparison(self, items):
        if len(items) == 1:
            return items[0]
        left, op, right = items[0], items[1], items[2]
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right

    def assign(self, items):
        self.env[items[0]] = items[1]
        return ('assign', items[0], items[1])

    def set_cmd(self, items):
        self.env[items[0]] = items[1]
        return ('set', items[0], items[1])

    def command(self, items):
        cmd = items[0].value
        args = items[1] if len(items) > 1 else []
        return ('command', cmd, args)

    def call(self, items):
        name = items[0]
        args = items[1] if len(items) > 1 else []
        return ('call', name, args)

    def arg_list(self, items):
        return items

    def param_list(self, items):
        return [str(i) for i in items]

    def func_def(self, items):
        name = str(items[0])
        params = items[1] if isinstance(items[1], list) else []
        block = items[-1]
        self.env[name] = ('function', params, block)
        return ('function', name, params, block)

    def block(self, items):
        return items

    def if_statement(self, items):
        cond = items[0]
        true_block = items[1]
        false_block = items[2] if len(items) > 2 else []
        return ('if', cond, true_block, false_block)

    def while_statement(self, items):
        cond = items[0]
        block = items[1]
        return ('while', cond, block)

    def start(self, items):
        return [i for i in items if i is not None]


def parse_script(text, env=None):
    env = env or ScriptEnvironment()
    parser = Lark.open('dsl_grammar.lark', parser='lalr')
    tree = parser.parse(text)
    evaluator = Evaluator(env)
    return evaluator.transform(tree)

if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    with open(path) as f:
        code = f.read()
    ast = parse_script(code)
    from pprint import pprint
    pprint(ast)
