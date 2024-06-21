from fspathtree import fspathtree
import networkx as nx


DependencyGraph = nx.DiGraph

def get_dependency_chains(graph: DependencyGraph, node:fspathtree.PathType):
    """Given a node, return the chain of nodes that depend on it. If multiple paths exists, each is returned. If node does not have any predecessors, an empty list is returned."""

    chains = []
    for pred in graph.predecessors(node):
        this_chain = []
        this_chain.append(node)



    pass
