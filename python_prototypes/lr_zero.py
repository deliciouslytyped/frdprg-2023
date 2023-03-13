from textwrap import dedent
from collections import defaultdict
from itertools import chain
import unittest


error = lambda: "error"

class LRZ:
    @staticmethod
    def is_nt(sym):
        assert len(sym) == 1
        return sym.isupper()

    @staticmethod
    def read_grammar(s):
        grammar = {line[0]: line[1:] for _line in s.splitlines() for line in [_line.split()]}
        rules = [(lhs, alt) for lhs, alts in grammar.items() for alt in alts]
        return grammar, rules

    @classmethod
    def closure(cls, grammar, items):
        rest = set()
        for item in items:  # for each item
            tail = item[item.index(".")+1:]
            if tail and cls.is_nt(nextSym := tail[0]):  # if the symbol after . is a non-terminal
                cl = lambda alt: cls.closure(grammar, {f"{nextSym} -> .{alt}"})
                rest |= frozenset.union(*map(cl, grammar[nextSym]))  # integrate the closure of the non-terminal
        return frozenset(items) | rest


    # A -> b.Xc to TODO
    @classmethod
    def read(cls, grammar, items, sym):
        r = set()
        for item in items:
            assert not item.endswith(".")  # We aren't trying to read past the end of the rule
            dot = item.index(".")
            if item[dot+1] == sym:
                head, sym, rest = item[:dot], item[dot+1], item[dot+2:] if len(item[dot:]) > 1 else ""
                r |= cls.closure(grammar, {f'{head}{sym}.{rest}'})
        return frozenset() | r

    @classmethod
    def gen_table(cls, grammar, rules: list):
        # TODO restriction; as of python 3.7 dicts are ordered by default, which we require here to get the last added "highest" entry https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        states = defaultdict(lambda: len(states), {cls.closure(grammar, {"Z -> .S"}): 0})  # TODO gensym # TODO document arrow syntax
        goto = defaultdict(lambda: defaultdict(error))
        action = defaultdict(error)
        idx = 0
        while idx < len(states):
            for item in list(states)[idx]: #TODO dont convert to a list every iteration
                dot = item.index(".")
                if item[dot+1:]:  # TODO what if its an end item?
                    nextsym = item[dot + 1]
                    goto[idx][nextsym] = states[cls.read(grammar, cls.closure(grammar, {item}), nextsym)] #TODO make sure this is correct

                # TODO is it a theorem that a state with a dot at the end of a rule only has such rules?, etc
                if "Z -> S." in item:  #TODO document we use Z as special S' rule , though not totally sure why this is necessary
                    action[idx] = "accept"
                elif item.endswith("."):
                    action[idx] = rules.index(tuple(item.replace(".", "").split(" -> "))) # reduction #todo find a better way to do this
                else:
                    action[idx] = "shift"
            idx += 1
        return action, goto

    @staticmethod
    def parse(rules, actions, goto, inp):
        stack = [0]

        for c in chain(inp, "#"):
            # Needed so we can do multiple reductions while using "for" on
            # inp which requires one iteration per input symbol
            while True:
                state = stack[-1]
                action = actions[state]

                if action == "accept":
                    return True
                elif action == "error":
                    print(stack)
                    raise ValueError
                elif action == "shift":
                    stack.extend([c, goto[state][c]])  # TODO this makes erroring weird? shifts "error" onto the stack
                    print(c, stack)
                    break
                else:  # reduce (by rule num stored in action table)
                    lhs, rhs = rules[action]
                    for sym in reversed(rhs):
                        stack.pop()  # pop state
                        assert stack.pop() == sym  # pop sym
                    stack.extend([lhs, goto[stack[-1]][lhs]])  # note the state changes because of the pops
                    print(f'{rhs} -> {lhs}\n{stack}')
        return True


class Test(unittest.TestCase):
    def test(f):
        def w(*args, **kwargs):
            print(f.__name__)
            f(*args, **kwargs)
            print()
            print()
        return w

    @test
    def test_closure(self):
        grammar = dedent("""
            S aAd
            A bA c
            """).strip()
        grammar, rules = LRZ.read_grammar(grammar)
        assert LRZ.closure(grammar, {"T -> .S"}) == {"T -> .S", "S -> .aAd"}
        assert LRZ.closure(grammar, {"T -> S."}) == {"T -> S."}
        assert LRZ.closure(grammar, {"S -> a.Ad"}) == {"S -> a.Ad", "A -> .bA", "A -> .c"}

    @test
    def test_parse(self):
        rules = [("T", "S"), ("S", "aAd"), ("A", "bA"), ("A", "c")]
        action = ["shift", "accept", "shift", "shift", "shift", 3, 1, 2]
        # noinspection PyTypeChecker
        goto = defaultdict(error, {
            0: defaultdict(error, {"S": 1, "a": 2}),
            2: defaultdict(error, {"A": 3, "b": 4, "c": 5}),
            3: defaultdict(error, {"d": 6}),
            4: defaultdict(error, {"A": 7, "b": 4, "c": 5})
        })
        inp = "abbcd"
        assert LRZ.parse(rules, action, goto, inp)

    @test
    def test1(self):
        grammar = dedent("""
            S aAd
            A bA c
            """).strip()

        grammar, rules = LRZ.read_grammar(grammar)
        action, goto = LRZ.gen_table(grammar, rules)
        inp = "abbcd"
        assert LRZ.parse(rules, action, goto, inp)

    @test
    def test2(self):
        grammar = dedent("""
            S aAd
            A bA c
            """).strip()

        grammar, rules = LRZ.read_grammar(grammar)
        action, goto = LRZ.gen_table(grammar, rules)
        inp = "aa"
        self.assertRaises(ValueError, lambda: LRZ.parse(rules, action, goto, inp))


if __name__ == "__main__":
    unittest.main()
