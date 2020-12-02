import logging
import time

import networkx as nx

logging.basicConfig(format='%(asctime)s %(message)s', level=10)

def christofides(problem, source=None):
    """ Christofides algorithm

    Args:
        problem ([TSPLIB object]): problem to be solved
        source (int, optional): Starting node of the solution. Defaults to None.

    Returns:
        [dict]: contains the solution comprising of path_length, path, time
    """    
    
    #get graph
    base_G = problem.get_graph()
    
    #timing        
    stime = time.perf_counter()
    
    if nx.is_directed(base_G):
        base_G = base_G.to_undirected()
    
    # minimum spanning tree - MST
    MST = nx.minimum_spanning_tree(base_G)
    
    # get odd degree nodes
    odd_MST_G = base_G.subgraph([i for (i,j) in MST.degree if j % 2 == 1])
    
    # minimum cost perfect matching
    reverse_G = nx.Graph()
    # inverting the numbers and using max_weight_matching function
    for i, j in odd_MST_G.edges:
        if i == j:
            reverse_G.add_edge(i, j, weight=-10**8)
        else:
            reverse_G.add_edge(i, j, weight=(base_G[i][j]["weight"]*-1))

    T_set = nx.algorithms.matching.max_weight_matching(reverse_G, maxcardinality = True)
    
    #graph T
    T = nx.Graph()
    T.add_weighted_edges_from([(i, j, base_G[i][j]["weight"]) for (i,j) in T_set])  
    
    #combine MST and M
    H = nx.MultiGraph(MST)
    H.add_weighted_edges_from([(i, j, k['weight']) for (i, j, k) in T.edges(data=True)])

    # find Eulearian circuit and vertices with degree > 2
    eul_circuit = _find_eul_circuit(H)
    
    #shortcutting
    visited = []
    for i in eul_circuit:
        if i[0] not in visited:
            visited.append(i[0])

    n = len(visited)
    new_eges = [(visited[i], visited[(i+1)%n]) for i in range(n)]
    
    H = base_G.edge_subgraph(new_eges)
    
    path_len = H.size(weight='weight')
        
    #timing        
    ftime = time.perf_counter()
    
    solution = {
        "path_len": path_len,
        "path": visited,
        "time": ftime-stime
    }
    
    return solution

def _find_eul_circuit(H):
    
    # find Eulearian circuit
    if not nx.algorithms.euler.is_eulerian(H):
        H = nx.algorithms.euler.eulerize(H)

    # Eulearian circuit
    ec = nx.algorithms.euler.eulerian_circuit(H)
    eul_c = list(ec)
    
    return eul_c
    