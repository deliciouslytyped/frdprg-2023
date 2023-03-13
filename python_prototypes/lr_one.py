from textwrap import dedent
from collections import defaultdict
from itertools import chain
import unittest
from typing import *


Sym = NewType("Sym", str)
Grammar = Dict[str, Set[str]]
Item = Tuple[str, str]  # "A->b.C l" item with 1 lookahead
Rule = Tuple[int, str]  # TODO can't figure out how to NewType this
Action = Mapping[int, Union[str, int]]
Goto = Mapping[int, Mapping[str, int]]


error = lambda: "error"


class LRO:
    @staticmethod
    def is_nt(sym: Sym):
        assert len(sym) == 1
        return sym.isupper()

    @staticmethod
    def read_grammar(s: str) -> Tuple[Grammar, Sequence[Rule]]:
        grammar = {line[0]: line[1:] for _line in s.splitlines() for line in [_line.split()]}
        rules = [(lhs, alt) for lhs, alts in grammar.items() for alt in alts]
        return grammar, rules

    # TODO this doesnt exactly follow C&H algorithm
    # homogeneous treatment of nt and t
    @classmethod
    def FIRST(cls, grammar: Grammar, sym: Sym, parentset: Set[str] = None) -> FrozenSet[str]:  # TODO may need modifications on the recursion checking if
        if parentset is None:
            parentset = set()
        if sym in parentset:
            return frozenset()

        if not cls.is_nt(sym):
            return frozenset((sym,))

        return frozenset.union(*[(cls.FIRST(grammar, fsym, parentset | {sym}))
                                 # union is invariant over left recursion
                                 for alt in grammar[sym] for fsym in
                                 [alt[0]]])  # TODO handle empty when not lambdafree?

    @classmethod
    def closure(cls, grammar: Grammar, items: AbstractSet[Item], parentset: Set[Item] = None) -> FrozenSet[Item]:
        if parentset is None:
            parentset = set()

        rest = set()
        for pair in items:  # for each item
            item, lah = pair
            if pair in parentset:
                continue

            tail = item[item.index(".")+1:]
            if tail and cls.is_nt(nextSym := tail[0]):  # if the symbol after . is a non-terminal
                for f in (cls.FIRST(grammar, tail[1]) if tail[1:] else cls.FIRST(grammar, lah)): # on the slides its FIRST(beta a) but we are assuming no epsilons here?
                    cl = lambda alt: (cls.closure(grammar, {(f"{nextSym} -> .{alt}", f)}, parentset | {pair}))
                    rest |= frozenset.union(*map(cl, grammar[nextSym]))  # integrate the closure of the non-terminal
        return frozenset(items) | rest


    # A -> b.Xc to TODO
    @classmethod
    def read(cls, grammar: Grammar, items: AbstractSet[Item], sym: Sym) -> FrozenSet[Item]:
        r = set()
        for item, lah in items:
            if item.endswith("."):  # We aren't trying to read past the end of the rule
                #r |= {item}  #TODO is this correct?
                continue
            dot = item.index(".")
            if item[dot+1] == sym:
                head, sym, rest = item[:dot], item[dot+1], item[dot+2:] if len(item[dot:]) > 1 else ""
                r |= cls.closure(grammar, {(f'{head}{sym}.{rest}', lah)})
        return frozenset() | r

    @classmethod
    def gen_table(cls, grammar: Grammar, rules: Sequence[Rule]) -> Tuple[Action, Goto]:
        # TODO restriction; as of python 3.7 dicts are ordered by default, which we require here to get the last added "highest" entry https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        states = defaultdict(lambda: len(states), {cls.closure(grammar, {("Z -> .S", "#")}): 0})  # TODO gensym # TODO document arrow syntax
        goto = defaultdict(lambda: defaultdict(error))
        action = defaultdict(lambda: defaultdict(error))
        idx = 0
        while idx < len(states):
            state = list(states)[idx]
            for nextsym in {item[dot+1] for item, lah in state for dot in (item.index("."), ) if item[dot+1:]}:
                goto[idx][nextsym] = states[cls.read(grammar, state, nextsym)]

            for item, lah in state:
                # TODO is it a theorem that a state with a dot at the end of a rule only has such rules?, etc
                if "Z -> S." == item:  # TODO document we use Z as special S' rule , though not totally sure why this is necessary
                    action[idx][lah] = "accept"
                elif item.endswith("."):
                    action[idx][lah] = rules.index(tuple(item.replace(".", "").split(" -> ")))  # reduction #todo find a better way to do this
                elif v := cls.read(grammar, state, item[item.index(".")+1]) in states: #TODO
                    action[idx][item[item.index(".")+1]] = "shift"
            idx += 1
        return action, goto, states

    @staticmethod
    def parse(rules, actions, goto, inp):
        stack = [0]

        for c in chain(inp, "#"):
            # Needed so we can do multiple reductions while using "for" on
            # inp which requires one iteration per input symbol
            while True:
                state = stack[-1]
                action = actions[state][c]

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
    def ptest(f):
        def w(*args, **kwargs):
            print(f.__name__)
            f(*args, **kwargs)
            print()
            print()
        return w

    # @ptest
    # def test1(self):
    #     grammar = dedent("""
    #         S E
    #         E E-T T
    #         T n (E)
    #         """).strip()
    #     grammar, rules = LRO.read_grammar(grammar)
    #     action, goto = LRO.gen_table(grammar, rules)
    #     inp = "n-n-n"
    #     assert LRO.parse(rules, action, goto, inp)
    #     print()

    @ptest
    def test2(self):
        grammar = dedent("""
           S AA
           A aA b
           """).strip()
        grammar, rules = LRO.read_grammar(grammar)
        test = [ # factored out for debugging to reverse-map, important: this is in the order on the slides
            # [i for k, v  in states.items() for i, vv in enumerate(test) if k == vv]
            #pprint(sorted([(i,k) for k, v  in states.items() for i, vv in enumerate(test) if k == vv]))
            # pprint(sorted(list((action[v],v,i) for k, v in states.items() for i, vv in enumerate(test) if k == vv), key=lambda x: x[2]))
            #pprint(sorted([(i,k, action[i]) for k, v  in states.items() for i, vv in enumerate(test) if k == vv]))
            {('Z -> .S', '#'), ('A -> .aA', 'a'), ('A -> .aA', 'b'), ('A -> .b', 'a'), ('A -> .b', 'b'), ('S -> .AA', '#')},
            {("Z -> S.", "#")},
            {("S -> A.A", "#"), ("A -> .aA", "#"), ("A -> .b", "#")},
            {("A -> a.A", "a"), ("A -> a.A", "b"), ("A -> .aA", "a"), ("A -> .aA", "b"), ("A -> .b", "a"), ("A -> .b", "b")},
            {("A -> b.", "a"), ("A -> b.", "b")},
            {("S -> AA.", "#"), ("S -> AA.", "#")},
            {("A -> a.A", "#"), ("A -> .aA", "#"), ("A -> .b", "#")},
            {("A -> b.", "#")},
            {("A -> aA.", "a"), ("A -> aA.", "b")},
            {("A -> aA.", "#")}
        ]
        it = iter(test)
        assert (h0 := LRO.closure(grammar, {("Z -> .S", "#")})) == next(it)
        assert (h1 := LRO.read(grammar, h0, "S")) == next(it)
        assert (h2 := LRO.read(grammar, h0, "A")) == next(it)
        assert (h3 := LRO.read(grammar, h0, "a")) == next(it)
        assert (h4 := LRO.read(grammar, h0, "b")) == next(it)
        assert (h5 := LRO.read(grammar, h2, "A")) == next(it)
        assert (h6 := LRO.read(grammar, h2, "a")) == next(it)
        assert (h7 := LRO.read(grammar, h2, "b")) == next(it)
        assert (h8 := LRO.read(grammar, h3, "A")) == next(it)
        assert LRO.read(grammar, h3, "a") == h3
        assert LRO.read(grammar, h3, "b") == h4
        assert (h9 := LRO.read(grammar, h6, "A")) == next(it)
        assert LRO.read(grammar, h6, "a") == h6

        action, goto, states = LRO.gen_table(grammar, rules)
        # TODO not sure how to check these assert action[state]

        inp = "abb"
        assert LRO.parse(rules, action, goto, inp)
        print()


if __name__ == "__main__":
    unittest.main()
