from textwrap import dedent
from collections import defaultdict
from typing import *


#MyPy type aliases
Grammar = Dict[str, Tuple[int, str]]  # Maps lhs to (rhs, idx) pairs I.e. the rule alternatives are numbered.

class SLL:
    @staticmethod
    def gen_table(grammar):
        acc = 0
        grammar: Grammar = {line[0]: [(acc := acc + 1, e) for e in line[1:]]
                            for _line in grammar.splitlines() for line in [_line.split()]}

        # Generate the parse table.

        # Entries default to the error entry.
        table = defaultdict(lambda: defaultdict(lambda: "error"))  # TODO wont work right, defaultdict gets replaced
        # For each alternative, create a map from the lhs and first character, to the rule.
        table.update({lhs: {rule[1][0]: rule for rule in rhs} for lhs, rhs in grammar.items()})
        # Fill the missing pop and accept entries. Due to laziness we use an explicit terminal list.
        table.update({c: {c: "pop" if c != "#" else "accept"} for c in "abcd#"})
        return table

    # Parse with the parse table.
    @staticmethod
    def parse(inp, table):
        anal, pred = list(), list("S")
        for c in inp:
            while True:
                print(anal, pred)
                if pred:  # TODO is this correct? # wrong, needs to empty simultaneously with hash and inp
                    action = table[pred.pop()][c]
                else:
                    action = "error"

                if action == "pop":
                    print(c)
                    break
                elif action == "error":
                    raise ValueError
                else:
                    pred.extend(reversed(action[1]))
                    anal.append(action[0])
        print(anal, pred)
        return anal, pred


def main():
    # Test with the grammar from the slides.
    grammar = dedent("""
        S aS bAc
        A bAc d
        """).strip()
    inp = iter("aabbdcc")
    SLL.parse(inp, SLL.gen_table(grammar))


if __name__ == "__main__":
    main()