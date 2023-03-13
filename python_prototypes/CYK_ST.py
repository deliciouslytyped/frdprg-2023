from CYK import *
from collections import defaultdict, deque


class Sym(str):
    def __init__(self, s):
        # dont need to pass on s because of (new) weirdness
        super().__init__()
        if isinstance(s, self.__class__):
            self.l = s.l
            self.r = s.r
        else:
            self.l = None
            self.r = None

    def __add__(self, other):
        s = Sym(super().__add__(other))
        s.l = self
        s.r = other
        return s


class RefSet(set):
    def __init__(self, orig, items):
        super().__init__(items)
        self.orig = orig

    def add(self, *args, **kwargs):
        self.orig.add(*args, **kwargs)


class _Index(defaultdict):
    def __getitem__(self, item):
        itm = super().__getitem__(item)
        def setup(sym):
            if isinstance(item, Sym):
                sym.l = item.l
                sym.r = item.r
            else:
                if len(item) > 1:
                    pass # because initialization raise ValueError
                else:
                    sym.l = Sym(item)
            return sym
        return RefSet(itm, map(setup, map(Sym, itm)))

#
# Since all grammar operations done in offline_cyk and online_cyk go through the index,
# we construct a special index object which yields special sym objects that behave
# like strings, but that keep track of their children, so that at the end we can
# extract the parse tree.
#
# The operation that need to be implemented are what lhs_set_of uses, and + on strings


def get_parse_trees(table: Table): # TODO needs changed sym repr
    root = table[-1][0]
    for r in root:
        q = deque([(r, 0)]) # breadth first traversal so we can print line by line
        while q:
            e, d = q.popleft()
            if e.l:
                q.append((e.l, d + 1))
            if e.r:
                q.append((e.r, d + 1))
            print(e, end="")
            if not q or d < q[0][1]:
                print()

# recursive function to draw binary trees
# Its assumed the areas are rectangular, and that child
# diagrams have their roots centered in their top line,
# they may be of unequal heights and widths
#
# algorithm: for 1-1 diagonals, the left and right must be the same height
#   the distance between the centers must be the same?
#
#   so take the max of the heights and widths,
#
#   a minimum is needed because otherwise we will collide with the bounding box
#   and I dont want to figure out how to write into that
#
#   the minimum height means the diagonal wont cut the boundig box, so its at least box width / 2 of the larger box
def print_tree(root):
    root = list(root)[0]
    def traverse(root, l, r):
        ldiag, rdiag = None, None
        if l:
            ldiag = traverse(l, l.l, l.r)

        if r:
            if r:
                rdiag = traverse(r, r.l, r.r)
            else:
                rdiag = None

        #if not (hasattr(l, "children") or hasattr(r, "children")):
        return CYK._print_tree(root, ldiag if ldiag else l, rdiag if rdiag else r)

    for line in traverse(root, root.l, root.r):
        print(line)


def _print_tree(root, left, right=None):
    assert root
    assert not (not left and right)
    if isinstance(left, str.__class__):
        lw = len(left)
        left = [left]
        lh = 1
    else: #assume list of lines
        lw = len(left[0]) if left else 0
        lh = len(left) if left else 0
        left = []

    if isinstance(right, str.__class__):
        rw = len(right)
        right = [right]
        rh = 1
    elif right is not None: # assume list of lines
        rw = len(right[0])
        rh = len(right)
    else:
        rw = 0
        rh = 0
        right = []
    #TODO this should only be a string
    if isinstance(root, str.__class__):
        _rootw = len(root)
        root = [root]
        _rooth = len(root)
    else: # assume list of lines
        _rootw = len(root[0])
        _rooth = len(root)

    lines = list()
    def print(s):
        lines.append(s)

    rootw = max((lw+rw)//2, abs(rh-lh))
    rooth = rootw/2
    diagram_width = (lw + rw)//2 + (rootw-(lw+rw)//2)
    for i, line in enumerate(root):
        print((" " * (lw//2)) + line.center(rootw)) #TODO not center
    for j in range(len(root), rootw//2):
        print((" " * (lw//2 + (rootw//2-(j+2)))) + "/" + ((" " * 2 * j) + "\\" if right else ""))
    for line in (left[lh-rh:rh:-1] if left and lh > rh else (right[rh-lh:lh:-1] if right else [])): #TODO boundaries
        print(("" if lh > rh else (" " * (diagram_width-rw))) + line + ((" " * (diagram_width-lw)) if lh > rh else ""))
    for a,b in zip(left[abs(lh-rh)-1 if lh >= rh else 0:] if left else [""]*len(right), right[abs(lh-rh)-1 if rh > lh else 0:] if right else [""]*len(left)):
        print(a + ((diagram_width-(rootw-(lw+lh)//2)) * " ") + b)

    return lines


if __name__ == "__main__":
    get_parse_trees(offline_table)
    print_tree(offline_table[-1][0])

    index = defaultdict(set)  # CYK._Index(set) # TODO