from os.path import normpath

# import matplotlib.pyplot as plt
import networkx as nx
from fspathtree import fspathtree

from powerconf import parsing


def test_creating_graph():
    """This is just a function for experimenting with the networkx library."""
    config = fspathtree(
        {
            "grid": {
                "res": "1 um",
                "x": {
                    "max": "1 cm",
                    "min": "0 cm",
                    "res": "${../res}",
                    "N": "($max - $min)/$res + 1",
                },
                "y": {
                    "max": "1 cm",
                    "min": "0 cm",
                    "res": "${../res}",
                    "N": "($max - $min)/$res + 1",
                },
            }
        }
    )

    G = nx.DiGraph()
    G.add_nodes_from(config.get_all_leaf_node_paths())
    for node in list(G.nodes):
        variables = [
            fspathtree.PathType(r["variable name"])
            for r in parsing.variable.search_string(config[node])
        ]
        for v in variables:
            dep = fspathtree.PathType(
                normpath(v if v.is_absolute() else node.parent / v)
            )
            G.add_edge(node, dep)

    # out_degrees are the number of other nodes a given node depends on.
    # in_degrees are the number of other nodes that depend on given node.
    # print()
    # print("out")
    # for e in G.out_degree:
    #     print(e)
    # print("in")
    # for e in G.in_degree:
    #     print(e)

    out_degrees = dict(G.out_degree)
    in_degrees = dict(G.in_degree)
    # at the bottom of a dependency tree is a node that does not depend on anything (out_degree == 0)
    # and has one or more nodes that depends on it (in_node > 0)
    root_dependencies = list(
        filter(
            lambda k: in_degrees[k] > 0,
            filter(lambda k: out_degrees[k] == 0, out_degrees.keys()),
        )
    )

    # print(">>>>", root_dependencies[0])
    # print(":::::", sorted(nx.ancestors(G, root_dependencies[0])))

    all_dep_chains = []
    for root in root_dependencies:
        for node in nx.ancestors(G, root):
            all_dep_chains += nx.all_simple_paths(G, node, root)
    uniq_dep_chains = []
    for chain1 in all_dep_chains:
        contained = False
        for chain2 in all_dep_chains:
            if len(set(chain1).intersection(set(chain2))) == len(chain1):
                contained = True
        if not contained:
            uniq_dep_chains.append(chain1)
    # print(">>>", all_dep_chains)
    # print("<<<", uniq_dep_chains)

    # evaluate any expressions in parameters that don't depend on any others
    for node in list(map(lambda e: e[0], filter(lambda e: e[1] == 0, G.out_degree))):
        # eval....
        pass

    for node in root_dependencies:
        for nnode in nx.algorithms.traversal.depth_first_search.dfs_postorder_nodes(
            G, node
        ):
            pass

    # nx.draw(G, with_labels=True)
    # plt.show()


def test_find_all_paths_ending_on_node():
    G = nx.DiGraph()

    G.add_node("a")
    G.add_node("b")
    G.add_node("c")
    G.add_node("d")

    G.add_edge("a", "b")
    G.add_edge("a", "c")
    G.add_edge("b", "d")
    G.add_edge("c", "d")

    all_paths = []
    for a in nx.ancestors(G, "d"):
        all_paths += nx.all_simple_paths(G, a, "d")

    # prune paths that are parts of longer paths
    longest_paths = []
    print()
    for p1 in all_paths:
        save = True
        for p2 in all_paths:
            if p1 == p2:
                continue
            if p2[-len(p1) :] == p1:
                save = False
                break
        if save:
            longest_paths.append(p1)

    assert len(longest_paths) == 2
    assert ["a", "b", "d"] in longest_paths
    assert ["a", "c", "d"] in longest_paths
