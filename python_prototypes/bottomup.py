# Terms: lhs - left hand side, rhs - right hand side

# Note the specification (The slides) use 1-based indexing, so some of the index math gets a little funky.

from textwrap import dedent
import unittest
from typing import *
from collections import namedtuple

# MyPy type aliases
State = namedtuple("State", ["s", "i", "rtop", "ltop"])
Rule = namedtuple("Rule", ["lhs", "rhs", "idx"])

Grammar = Dict[str, List[str]]  # map from lhs to list of rhs'
Rules = Sequence[Rule]  # list of (lhs, rhs, index), this is how we number alternatives #TODO adding index is probably redundant


class BottomUp:
    # We define nonterminals as one-length uppercase strings
    @staticmethod
    def is_nt(s: str) -> bool:
        return len(s) == 1 and s.isupper()

    @staticmethod
    def read_grammar(s: str) -> Tuple[Grammar, Rules]:
        grammar = {line[0]: line[1:] for _line in s.splitlines() for line in [_line.split()]}
        acc = 0
        rules = [Rule(lhs, alt, acc := acc + 1) for lhs, alts in grammar.items() for alt in alts]
        return grammar, rules


    #TODO coded as if we are creating new states every time but the stacks are by reference
    @classmethod
    def parse(cls, grammar: Grammar, rules: Rules, inp: str) -> Iterator[Union[State, bool]]:
        inp += "#"
        inplen = len(inp)
        s = State("q", 1, [], [])

        # We factor out the matching function of reduction because it's used twice.
        def match(s, min_idx=1):
            # for each rule
            for lhs, rhs, j in rules[min_idx-1:]:
                # check if any of the characters in the rule do not match the stack, first fail -
                # if they dont match, try the next rule
                for i, sym in enumerate(rhs):  # TODO accidentally did enumerate(reversed(rhs)), which lead to oscillation. Shouldnt the osscillation not happen even then?
                    if len(s.rtop) < len(rhs) or s.rtop[-1 - i] != sym:
                        break
                # if we didn't break from the above loop, the rule matches.
                else:
                    return State(s.s, s.i, s.rtop[:-len(rhs)] + [lhs], s.ltop + [str(j)])

        irreducible = False
        yield s
        while s.s != "t":
            if s.s == "q":
                while s.rtop:  # redukálás
                    # TODO assert noncyclic
                    m = match(s)
                    if m is None:  # If no match is found, we can't reduce futher so we exit the reduction loop.
                        break
                    else:  # If we matched, the stack changed, keep trying to reduce.
                        s = m
                        yield s
                        continue
                if s.i < inplen:  # léptetés
                    s = State(s.s, s.i+1, s.rtop + [inp[s.i-1]], s.ltop + ["s"])
                    yield s
                    continue
                if s.i == inplen and s.rtop == ["S"]:  # sikeres befejezés
                    s = State("t", s.i, s.rtop, s.ltop)
                    yield s
                    continue
                if s.i == inplen and s.rtop != ["S"]:  # átmenet backtrack állapotba
                    s = State("b", s.i, s.rtop, s.ltop)
                    yield s
                    continue
            elif s.s == "b":
                # I.
                # If the top of stack has a nonterminal, and we haven't failed this alternative yet,
                # try to swap the top rule on the stack for another one matching part of the same common suffix
                if cls.is_nt(s.rtop[-1]) and not irreducible:
                    A, j = s.rtop.pop(), int(s.ltop.pop())
                    s.rtop.extend(rules[j].rhs)
                    m = match(s, j+1)
                    if m is None:
                        # We can't reduce; we mark this for the next loop, to trigger the other alternatives,
                        # since "these steps are disjunct"
                        irreducible = True
                        continue
                    else:  # I. success
                        s = State("q", *m[1:])
                        yield s
                        continue
                # II.
                elif irreducible and cls.is_nt(s.rtop[-1]):
                    irreducible = False
                    newpos = s.i + 1
                    A, j = s.rtop.pop(), int(s.ltop.pop())
                    s = State("q", newpos, s.rtop + list(grammar[A][j]) + [inp[newpos-1]], s.ltop + ["s"])
                    yield s
                    continue
                # III.
                elif irreducible and s.i == inplen:
                    irreducible = False
                    A, j = s.rtop.pop(), int(s.ltop.pop())
                    s = State(s.s, s.i, s.rtop + list(grammar[A][j]), s.ltop)
                    yield s
                    continue
                # IV.
                elif s.i > 1 and s.rtop and not cls.is_nt(s.rtop[-1]) and s.ltop and s.ltop[-1] == "s":
                        s = State(s.s, s.i, s.rtop[:-1], s.ltop[:-1])
                        yield s
                        continue
                # V.
                elif s.i == 1 and s.rtop and not cls.is_nt(s.rtop[-1]) and s.ltop and s.ltop[-1] == "s":
                    yield s
                    yield False
                    return
        yield True
        return


class Test(unittest.TestCase):
    # Test grammar from the slides
    def test1(self):
        grammar = dedent("""
            S T+S T
            T a b
            """).strip()
        grammar, rules = BottomUp.read_grammar(grammar)
        inp = "b+a"

        # TODO backtracking isn't tested
        steps = [
            ("q", 1, [], []),
            ("q", 2, ["b"], ["s"]),
            ("q", 2, ["T"], ["4", "s"]),
            ("q", 2, ["S"], ["2", "4", "s"]),
            ("q", 3, ["S", "+"], ["s", "2", "4", "s"]),
            ("q", 4, ["S", "+", "a"], ["s", "s", "2", "4", "s"]),
            ("q", 4, ["S", "+", "T"], ["3", "s", "s", "2", "4", "s"]),
            ("q", 4, ["S"], ["1", "3", "s", "s", "2", "4", "s"]),
            ("t", 4, ["S"], ["1", "3", "s", "s", "2", "4", "s"]),
            True
        ]

        for i, e in enumerate(BottomUp.parse(grammar, rules, inp)):
            print(e)
            if isinstance(e, bool):
                assert e == steps[i]
            else:
                assert State(*e[:3], list(reversed(e.ltop))) == State(*steps[i])


if __name__ == "__main__":
    unittest.main()
