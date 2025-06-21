import unittest
from dsl_parser import parse_script


def parse_old_eval(text):
    env = {}
    results = []
    for line in text.splitlines():
        if len(line) == 0 or ('#' in line):
            continue
        parts = line.split(' ', 1)
        cmd = parts[0]
        if len(parts) > 1:
            arg_line = parts[1].replace(' ', '').replace('"', '')
            args = arg_line.split(',')
            if cmd in ('set', 'root', 'snap3d', 'message'):
                pass
            elif cmd in ('snap', 'contsnap'):
                args[1] = float(args[1])
            elif cmd in ('pause',):
                args[0] = float(args[0])
            else:
                args = [float(a) for a in args]
        else:
            args = None
        if cmd == 'set' and args is not None:
            env[args[0]] = args[1]
        if args is not None:
            def repl(a):
                if isinstance(a, str) and a.startswith('${') and a.endswith('}'):
                    key = a[2:-1]
                    return env.get(key, a)
                return a
            args = [repl(a) for a in args]
        results.append((cmd, args))
    return results


class ParserCompatTest(unittest.TestCase):
    def test_sample_script4(self):
        with open('script/sampleScript4.txt') as f:
            code = f.read()
        expected = parse_old_eval(code)
        ast = parse_script(code)
        actual = []
        for node in ast:
            if node[0] == 'set':
                actual.append((node[0], [str(node[1]), node[2]]))
            elif node[0] == 'command':
                actual.append((node[1], node[2]))
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()

