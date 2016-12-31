#!/usr/bin/python


from toposort import toposort

def main():
    seqs = [
        [ 1, 4, 7 ],
        [ 1, 2, 4 ],
        [ 3, 5, 6, 7 ],
        [ 2, 3, 6 ],
    ]
    o = total_order(seqs)
    print o

# Merge partial orderings into a total ordering by constructing order graph and doing a topo sort
def total_order(seqs):
    ordering = {}
    for seq in seqs:
        if len(seq) <= 1:
            continue
        for i in range(0, len(seq)-1):
            if seq[i+1] not in ordering:
                ordering[seq[i+1]] = set()
            ordering[seq[i+1]].add(seq[i])
    result = []
    for ties in toposort(ordering):
        sorted = list(ties)
        sorted.sort()
        for item in sorted:
            result.append(item)
    return result

main()
