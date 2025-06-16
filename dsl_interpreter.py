from lark import Lark, Tree, Token

class DSLInterpreter:
    def __init__(self, env=None):
        self.parser = Lark.open('dsl_grammar.lark', parser='lalr')
        self.env = env or {}
        self.functions = {}
        self.commands = {
            'mov': self.cmd_mov,
            'home': self.cmd_home,
            'gainiso': self.cmd_gainiso,
            'shutter': self.cmd_shutter,
            'lasers': self.cmd_lasers,
            'light': self.cmd_light,
        }

    def cmd_mov(self, *args):
        print('mov', *args)

    def cmd_home(self):
        print('home')

    def cmd_gainiso(self, val):
        print('gainiso', val)

    def cmd_shutter(self, val):
        print('shutter', val)

    def cmd_lasers(self, val):
        print('lasers', val)

    def cmd_light(self, channel, value):
        print('light', channel, value)

    def eval_expr(self, node):
        if isinstance(node, Tree):
            data = node.data
            if data == 'number':
                return float(node.children[0])
            if data == 'string':
                return node.children[0][1:-1]
            if data == 'var':
                return self.env.get(node.children[0].value, 0)
            if data == 'add':
                return self.eval_expr(node.children[0]) + self.eval_expr(node.children[1])
            if data == 'sub':
                return self.eval_expr(node.children[0]) - self.eval_expr(node.children[1])
            if data == 'mul':
                return self.eval_expr(node.children[0]) * self.eval_expr(node.children[1])
            if data == 'div':
                return self.eval_expr(node.children[0]) / self.eval_expr(node.children[1])
            if data == 'comparison':
                if len(node.children) == 1:
                    return self.eval_expr(node.children[0])
                left = self.eval_expr(node.children[0])
                op = node.children[1]
                right = self.eval_expr(node.children[2])
                if op == '>':
                    return left > right
                if op == '<':
                    return left < right
                if op == '>=':
                    return left >= right
                if op == '<=':
                    return left <= right
                if op == '==':
                    return left == right
                if op == '!=':
                    return left != right
            if data == 'arg_list':
                return [self.eval_expr(c) for c in node.children]
            if data == 'param_list':
                return [c for c in node.children]
        elif isinstance(node, Token):
            if node.type == 'NUMBER':
                return float(node.value)
            if node.type == 'NAME':
                return self.env.get(node.value, 0)
        return node

    def execute_block(self, block):
        for stmt in block.children:
            self.execute_statement(stmt)

    def execute_statement(self, stmt):
        if stmt.data == 'assign':
            name_tok = stmt.children[0]
            expr = stmt.children[1]
            val = self.eval_expr(expr)
            self.env[name_tok.value] = val
            return
        if stmt.data == 'set_cmd':
            name_tok = stmt.children[0]
            expr = stmt.children[1]
            self.env[name_tok.value] = self.eval_expr(expr)
            return
        if stmt.data == 'command':
            cmd_tok = stmt.children[0]
            args = []
            if len(stmt.children) > 1:
                args = self.eval_expr(stmt.children[1])
            # if a function with this name exists, call it
            name = cmd_tok.value
            if name in self.functions:
                self.call_function(cmd_tok, args)
            else:
                func = self.commands.get(name)
                if func:
                    func(*args)
                else:
                    print('unknown command', name)
            return
        if stmt.data == 'func_def':
            name_tok = stmt.children[0]
            params = []
            idx = 1
            if isinstance(stmt.children[1], Tree) and stmt.children[1].data == 'param_list':
                params = [p.value for p in stmt.children[1].children]
                idx += 1
            block = stmt.children[idx]
            self.functions[name_tok.value] = (params, block)
            return
        if stmt.data == 'func_call':
            name_tok = stmt.children[0]
            args = []
            if len(stmt.children) > 1:
                args = self.eval_expr(stmt.children[1])
            self.call_function(name_tok, args)
            return
        if stmt.data == 'if_statement':
            cond = self.eval_expr(stmt.children[0])
            if cond:
                self.execute_block(stmt.children[1])
            elif len(stmt.children) > 2:
                self.execute_block(stmt.children[2])
            return
        if stmt.data == 'while_statement':
            cond_node = stmt.children[0]
            block = stmt.children[1]
            while self.eval_expr(cond_node):
                self.execute_block(block)
            return
        if stmt.data == 'block':
            self.execute_block(stmt)
            return
        print('Unhandled statement', stmt.data)

    def call_function(self, name_tok, args):
        name = name_tok.value if isinstance(name_tok, Token) else name_tok
        if name in self.functions:
            params, block = self.functions[name]
            saved = dict(self.env)
            for p, v in zip(params, args):
                self.env[p] = v
            self.execute_block(block)
            self.env = saved
        else:
            print('unknown function', name)

    def run(self, text):
        tree = self.parser.parse(text)
        for stmt in tree.children:
            self.execute_statement(stmt)

if __name__ == '__main__':
    import sys
    code = open(sys.argv[1]).read()
    intr = DSLInterpreter()
    intr.run(code)
