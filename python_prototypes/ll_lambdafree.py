# This file is very similar to ll_lambda

import string
from textwrap import dedent
from collections import defaultdict
from typing import *
import unittest

Rule = Tuple[str, int]
Grammar = Dict[str, List[Rule]]  # same as ll_lambda
Table = Dict[str, Dict[str, Rule]]


class LLLF:
    @staticmethod
    def is_t(sym: str) -> bool:
        return sym in string.punctuation or sym.islower()

    @staticmethod
    def read_grammar(s: str) -> Grammar:
        acc = 0
        return {e[0]: [(v, acc := acc + 1) for v in e[1:]] for line in s.splitlines() for e in [line.split()]}

    #TODO this doesnt exactly follow C&H algorithm
    # homogeneous treatment of nt and t
    @classmethod
    def FIRST(cls, grammar: Grammar, _sym: str, parentset: Set[str] = None) -> FrozenSet[str]:  # TODO may need modifications on the recursion checking if
        _sym = _sym[0] # extract the sym from the (rule, idx) pair in the grammar

        if parentset is None:
            parentset = set()

        if cls.is_t(_sym):
            return frozenset((_sym,))

        return frozenset.union(*[(set() if sym in parentset else cls.FIRST(grammar, sym, parentset | {sym})) # union is invariant over left recursion
                           for alt in grammar[_sym] for sym in [alt[0][0]]])  # TODO handle empty when not lambdafree?

    # as an implementation detail we assume here that there are no first/first conflicts and the language is ll;
    # the dictionary maps >rules of a nt< to each of their respective first terminals,
    # so if multiple alternatives in a rule have a same first terminal the behaviour is undefined
    @classmethod
    def gen_table(cls, grammar: Grammar, terminalish: str = "#") -> Table:
        err = lambda: "error"
        table = defaultdict(lambda: defaultdict())
        #table.update({lhs: {rule[1][0]: rule for rule in rhs} for lhs, rhs in grammar.items()})
        table.update({lhs: defaultdict(err, {list(cls.FIRST(grammar, rule[0]))[0]: rule for rule in rhs}) for lhs, rhs in grammar.items()})
        table.update({c: defaultdict(err, {c: "pop" if c != "#" else "accept"}) for c in terminalish})

        return table

    @classmethod
    def parse(cls, inp: Iterable[str], table: Table) -> Union[bool, Tuple[List[int], List[str]]]:
        anal, pred = list(), list("S")
        for c in inp:
            while True:
                print(anal, pred)
                if pred:  # TODO is this correct? # wrong, needs to empty simultaneously with hash and inp
                    action = table[(v := pred.pop())][c]
                else:
                    action = "error"

                if action == "pop":
                    print(c)
                    break
                elif action == "error":
                    raise ValueError
                else:
                    pred.extend(reversed(action[0]))
                    anal.append(action[1])
        print(anal, pred)
        return anal, pred


class Test(unittest.TestCase):
    def test1(self):
        grammar = dedent("""
            S ab
            B b aBb
            """).strip()

        grammar = LLLF.read_grammar(grammar)
        assert LLLF.FIRST(grammar, "S") == {'a'}
        assert LLLF.FIRST(grammar, "B") == {'a', 'b'}

    # from G & J
    def test2(self):
        grammar = dedent("""
            S FS Q (S)S
            F !s
            Q ?s
            """).strip()

        grammar = LLLF.read_grammar(grammar)
        assert LLLF.FIRST(grammar, "S") == {'?', '!', '('}
        assert LLLF.FIRST(grammar, "F") == {'!'}
        assert LLLF.FIRST(grammar, "Q") == {'?'}

        table = LLLF.gen_table(grammar, "!?()s")
        inp = "!s(!s?s)?s"
        print(LLLF.parse(inp, table))
        # TODO assert table

if __name__ == "__main__":
    unittest.main()
