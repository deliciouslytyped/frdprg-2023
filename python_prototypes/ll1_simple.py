from textwrap import dedent
from collections import namedtuple, defaultdict


def parse(inp, table):
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
                pred.extend(reversed(action[1]))
                anal.append(action[0])
    print(anal, pred)
    return anal, pred


def gen_table(grammar):
    acc = 0
    grammar = {l[0]: [(acc := acc + 1, e) for e in l[1:]] for line in grammar.splitlines() for l in [line.split()]}

    table = defaultdict(lambda: defaultdict(lambda: "error")) #TODO wont work right, defaultdict gets replaces
    table.update({lhs: {rule[1][0]: rule for rule in rhs} for lhs, rhs in grammar.items()})
    table.update({c: {c: "pop" if c != "#" else "accept"} for c in "abcd#"})
    return table

def main():
    grammar = dedent("""
        S aS bAc
        A bAc d
        """).strip()
    inp = iter("aabbdcc")
    parse(inp, gen_table(grammar))


if __name__ == "__main__":
    main()