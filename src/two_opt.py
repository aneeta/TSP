import logging
import time

from util import get_edge_sum

logging.basicConfig(format='%(asctime)s %(message)s', level=10)

def two_opt(problem):
    
    #get graph
    G = problem.get_graph()
    
    nodes = list(G.nodes)
    n_nodes = len(G.nodes)
    
    # start time
    stime = time.perf_counter()
    
    # get nn-tour
    logging.info("Choosing best initial path")
    path_len, path = _nearest_neighbour_tour(G, nodes, n_nodes)
    
    # 2-opt
    logging.info("Swapping edges")
    improvement = True
    swap_magnitudes = [i for i in range(1, n_nodes-1)][::-1]
    best_path_len = path_len
    
    try:
        while improvement:
            new_path = path
            new_best = best_path_len
            for i in range(nodes[0], nodes[-1]+1):
                for item in swap_magnitudes[i:]:
                    swap_path = _2change_index(path, i, i+item)
                    new_path_len = sum([G[swap_path[i]][swap_path[(i+1)%n_nodes]]["weight"] for i in range(n_nodes)])
                    if new_path_len < best_path_len:
                        new_path = swap_path
                        new_best = new_path_len

            if new_best < best_path_len:
                best_path_len = new_best
                path = new_path
            else:
                improvement = False

    except:
        logging.info("Terminating search")

    #finish time
    ftime = time.perf_counter()

    sol = {
        "path_length": best_path_len,
        "path": path,
        "time": ftime-stime
    }

    return sol


def _find_min_neighbour(G, node, visited):

    nodes = list(G.nodes)
    
    weights = {j: G[node][j]["weight"] for j in range(nodes[0], nodes[-1]+1)}
    sorted_w = dict(sorted(weights.items(), key=lambda item: item[1]))
    sorted_nodes = list(sorted_w.keys())
    
    try:
        i=0
        while sorted_nodes[i] in visited + [node]:
            i += 1
        return sorted_nodes[i]
    except (IndexError,ValueError):
        return visited[0]


def _nearest_neighbour_tour(G, nodes, n_nodes):
    
    paths = {}
    
    # repeat for every possible staring node
    for i in range(nodes[0], nodes[-1]+1):
        path = []
        next_node = i
        while next_node not in path:
            path.append(next_node)
            next_node = _find_min_neighbour(G, next_node, path)

        path_len = sum([G[path[i]][path[(i+1)%n_nodes]]["weight"] for i in range(n_nodes)])
        
        paths[i]= {
            "path_len": path_len,
            "path": path
                 }

    #get best nn
    path_lengths = [paths[i]["path_len"] for i in range(nodes[0], nodes[-1]+1)]
    
    return paths[path_lengths.index(min(path_lengths))].values()


def _2change_index(tour, index_1, index_2):
    if index_1 < index_2:
        a = index_1
        b = index_2
    else:
        b = index_1
        a = index_2
        
    chunk1 = tour[:a]
    chunk2 = tour[a:b+1]
    chunk3 = tour[b+1:]

    return chunk1 + chunk2[::-1] + chunk3