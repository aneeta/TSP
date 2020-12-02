
def transform_edge_list(edges, short = True):
    edges_dict = dict(edges)
    elem = edges[0][0]  # start point in the new list
    transformed = [] 
    
    for _ in range(len(edges)):
        transformed.append((elem, edges_dict[elem]))
        elem = edges_dict[elem]
        if elem not in edges_dict:
            # Raise exception in case list of tuples is not circular
            raise Exception('key {} not found in dict'.format(elem))
    if short:
        return [i[0] for i in transformed]
    return transformed

def setup_solver_time_limit(solver, SOLVER_NAME, TIME_LIMIT):
    if SOLVER_NAME == 'cplex':
        solver.options['timelimit'] = TIME_LIMIT
    elif SOLVER_NAME == 'glpk':         
        solver.options['tmlim'] = TIME_LIMIT
    elif SOLVER_NAME == 'gurobi':           
        solver.options['TimeLimit'] = TIME_LIMIT
    elif SOLVER_NAME == "ipopt":
        solver.options["max_cpu_time"]  = TIME_LIMIT

def shifted_index(G):
    return list(G.edges)[0] == (0,0)