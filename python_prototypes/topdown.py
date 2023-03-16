from textwrap import dedent
from typing import *
import unittest


# MyPy type aliases
Grammar = Dict[str, List[str]]


class Configuration:
    class LList(list):
        def __str__(self):
            return f"%s]" % " ".join(reversed(self))

    class RList(list):
        def __str__(self):
            return f"[%s" % " ".join(self)

    def __init__(self, state: str = None, pos: int = None, r_top: list = None, l_top: list = None):
        self.state = "q"
        self.pos = 0
        self.r_top = self.RList()
        self.l_top = self.LList("S")

        if state is not None:
            self.state = state
        if pos is not None:
            self.pos = pos
        if r_top is not None:
            self.r_top = self.RList(r_top)
        if l_top is not None:
            self.l_top = self.LList(reversed(l_top))

    def __repr__(self):
        return f"(%s, %s, %s, %s)" % (self.state, self.pos, self.r_top, self.l_top)

    def __eq__(self, other):
        # TODO meh violates duck typing?
        return isinstance(other, self.__class__) and self.state == other.state and self.pos == other.pos \
               and self.r_top == other.r_top and self.l_top == other.l_top


class TopDown:
    @staticmethod
    def check_backtrackable_alternative(grammar: Grammar, c: Configuration) -> Union[bool, Tuple[str, str]]:
        rule, idx = c.r_top[-1].split("_")
        idx = int(idx)
        for i, v in enumerate(grammar[rule][idx]):
            if not c.l_top[-i-1] == v:
                return False
            return rule, idx

    @staticmethod
    def read_grammar(s: str) -> Grammar:
        return {_l[0]: _l[1:] for line in s.splitlines()[3:] for _l in [line.split()]}

    @classmethod
    def in_language(cls, grammar: Grammar, inp: str):
        #TODO just split the lines
        #TODO assert chars in language
        inp = inp + "#"
        t = {e for _, v in grammar.items() for alt in v for e in alt if not e.isupper()}
        nt = {e for _, v in grammar.items() for alt in v for e in alt if e.isupper()} | grammar.keys()

        c = Configuration()

        yield c
        while c.state != "t":
            if c.state == "q":
                if c.l_top and c.l_top[-1] in nt:  # kiterjesztés
                    rule = c.l_top.pop()
                    c.r_top.append(f"{rule}_0")
                    c.l_top.extend(reversed(grammar[rule][0]))
                    yield c
                if c.l_top and c.l_top[-1] == inp[c.pos]:  # input illesztés sikeres
                    c.pos += 1
                    c.r_top.append(c.l_top.pop())
                    yield c
                if c.pos == len(inp)-1 and not c.l_top:  # sikeres elemzés  # TODO hash end
                    c.state = "t"
                    yield c
                    yield True  # TODO not strictly necessary
                    return
                if c.l_top and c.l_top[-1] in t and c.l_top[-1] != inp[c.pos]: # input illesztés sikertelen
                    c.state = "b"
                    yield c
            elif c.state == "b":
                if c.r_top[-1] in t:  # backtrack az inputban
                    c.l_top.append(c.r_top.pop())
                    c.pos -= 1
                    yield c
                elif tup := cls.check_backtrackable_alternative(grammar, c):  # backtrack a kiterjesztésben # in nt
                    rule, idx = tup
                    if len(grammar[rule])-1 > idx:  # "van j+1 alternativa"
                        c.state = "q"
                        c.r_top.pop()
                        c.r_top.append(f"{rule}_{idx+1}")
                        for i in range(len(grammar[rule][idx])):
                            c.l_top.pop()
                        c.l_top.extend(reversed(grammar[rule][idx+1]))
                        yield c
                    elif c.pos == 0 and rule == "S" and len(grammar[rule])-1 == idx:  # elemzett sztring nem elme a nyelvnek
                        yield c
                        yield False  # TODO not strictly necessary
                        return
                    else:
                        for i in range(len(grammar[rule][idx])):  #nincs tobb alternativa, visszaterunk az elozo szintre
                            c.l_top.pop()
                        c.l_top.append(c.r_top.pop().split("_")[0])
                        yield c
        yield c


class Test(unittest.TestCase):
    def test_success(self):
        grammar = dedent("""
                S
                a b +
                S T
                S T+S T
                T a b
                """).strip()
        grammar = TopDown.read_grammar(grammar)
        inp = "b+a"

        target = list(map(lambda x: Configuration(*x), [
            ("q", 0, [], ["S"]),
            ("q", 0, ["S_0"], ["T", "+", "S"]), # diában elírva
            ("q", 0, ["S_0", "T_0"], ["a", "+", "S"]),
            ("b", 0, ["S_0", "T_0"], ["a", "+", "S"]),
            ("q", 0, ["S_0", "T_1"], ["b", "+", "S"]),
            ("q", 1, ["S_0", "T_1", "b"], ["+", "S"]),
            ("q", 2, ["S_0", "T_1", "b", "+"], ["S"]),
            ("q", 2, ["S_0", "T_1", "b", "+", "S_0"], ["T", "+", "S"]),
            ("q", 2, ["S_0", "T_1", "b", "+", "S_0", "T_0"], ["a", "+", "S"]),
            ("q", 3, ["S_0", "T_1", "b", "+", "S_0", "T_0", "a"], ["+", "S"]),
            ("b", 3, ["S_0", "T_1", "b", "+", "S_0", "T_0", "a"], ["+", "S"]),
            ("b", 2, ["S_0", "T_1", "b", "+", "S_0", "T_0"], ["a", "+", "S"]),
            ("q", 2, ["S_0", "T_1", "b", "+", "S_0", "T_1"], ["b", "+", "S"]),
            ("b", 2, ["S_0", "T_1", "b", "+", "S_0", "T_1"], ["b", "+", "S"]),
            ("b", 2, ["S_0", "T_1", "b", "+", "S_0"], ["T", "+", "S"]),
            ("q", 2, ["S_0", "T_1", "b", "+", "S_1"], ["T"]),
            ("q", 2, ["S_0", "T_1", "b", "+", "S_1", "T_0"], ["a"]),
            ("q", 3, ["S_0", "T_1", "b", "+", "S_1", "T_0", "a"], []),  # diában elirva
            ("t", 3, ["S_0", "T_1", "b", "+", "S_1", "T_0", "a"], [])  # diában elírva
        ]))

        for i, s in enumerate(TopDown.in_language(grammar, inp)):
            try:
                print(s, (f" < {target[i]}" if s not in target else (" !! " if str(s) != str(target[i]) else "")))
                assert str(s) == str(target[i])
            except IndexError:
                pass #TODO
            e = s
        assert e is True

    # def test_fail(self):
    #     grammar = dedent("""
    #             S
    #             a b +
    #             S T
    #             S T+S T
    #             T a b
    #             """).strip()
    #
    #     inp = "b+c"
    #
    #     for i, s in enumerate(in_language(grammar, inp)):
    #         print(s)
    #         e = s
    #     assert e is False
    #
    # def test_stuck_backtracking(self):
    #     grammar = dedent("""
    #             S
    #             a b +
    #             S T
    #             S T T+S
    #             T a b
    #             """).strip()
    #
    #     inp = "b+c"
    #
    #     for i, s in enumerate(in_language(grammar, inp)):
    #         print(s)
    #         e = s
    #     assert e is False


if __name__ == "__main__":
    unittest.main()
