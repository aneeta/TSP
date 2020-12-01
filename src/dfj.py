import logging
import time

import networkx as nx
import pyomo.environ as pyo

from util import *

logging.basicConfig(format='%(asctime)s %(message)s', level=10)

def DFJ(problem, SOLVER_NAME="cplex", TIME_LIMIT=60, F_TIME_LIMIT=600):
    """
    subtour method 
    
    problem [TSPLIB object] - representation of the problem
    """
    if SOLVER_NAME.lower() not in ["glpk", "cplex", "gurobi", "ipopt"]:
        raise ValueError('Solver not implemented. Choose from: "glpk", "cplex", "gurobi", "ipopt"')
    
    #solver setup
    solver = pyo.SolverFactory(SOLVER_NAME, solver_io="python")
    setup_solver_time_limit(solver, SOLVER_NAME, TIME_LIMIT)
    
    # start time
    stime = time.perf_counter()

    # Grpah object
    G = problem.get_graph()
    cost_matrix = nx.convert_matrix.to_numpy_array(G)
    
    shifted_idx = shifted_index(G)
    
    ## change zero to an arbitrarily large number since np.inf won't work with pyomo
    cost_matrix[cost_matrix == 0] = 10**7
    
    n = len(cost_matrix)
    
    #initiate model
    logging.info("Building the model")
    model = pyo.ConcreteModel() #change to Abstract?

    #Indexes for the cities
    model.M = pyo.RangeSet(n)                
    model.N = pyo.RangeSet(n)

    #Decision variables x_ij 
    model.x = pyo.Var(model.N,model.M, within=pyo.Binary)
    
    #Cost Matrix c_ij
    model.c = pyo.Param(model.N, model.M, initialize=lambda model, i, j: cost_matrix[i-1][j-1])
    
    #Objective function
    model.objective = pyo.Objective(rule=lambda model: sum(model.x[i,j] * model.c[i,j] for i in model.N for j in model.M), sense=pyo.minimize)
    
    #Only 1 leaves each city
    model.const1 = pyo.Constraint(model.M, rule=lambda model,M: sum(model.x[i,M] for i in model.N if i!=M ) == 1)
    
    #Only 1 enters each city
    model.rest2 = pyo.Constraint(model.N, rule=lambda model, N: sum(model.x[N,j] for j in model.M if j!=N) == 1)

    #Other constraints object
    model.cuts = pyo.ConstraintList()

    # solve
    logging.info("Solving the model")
    result = solver.solve(model, tee = False)
    
    #transforming the solution into a usable format
    edges = []
    for i in list(model.x.keys()):
        if model.x[i]() != 0: #nonzero values
            edges.append(i)
            
    if shifted_idx:
        edges = [(i[0]-1,i[1]-1) for i in edges]
        
    H = G.edge_subgraph(edges)

    while not nx.algorithms.euler.is_eulerian(H) and (time.perf_counter()-stime < F_TIME_LIMIT):
        
        subtours = _find_subtours(H, G, shifted_idx)
        
        for S in subtours:
            try:
                model.cuts.add(
                    sum(model.x[i,j] for i in S for j in S if (i != j) and (len(S) >= 2 and len(S) <= n-1)) <= len(S) - 1
                )
            except ValueError: # if trivial constraint
                pass

        result = solver.solve(model, tee = False)

        edges = []
        for i in list(model.x.keys()):
            if model.x[i]() != 0: #nonzero values
                edges.append(i)
                
        if shifted_idx:
            edges = [(i[0]-1,i[1]-1) for i in edges]

        H = G.edge_subgraph(edges)
    
    new_edges = transform_edge_list(edges)

    # finish time
    ftime = time.perf_counter()
        
    sol = {
        "path_length": get_edge_sum(H),
        "path": new_edges,
        "path_qa": len(new_edges),
        "time": ftime-stime
    }
    
    return sol

def _find_subtours(H, G, shifted_idx):

    if nx.is_directed(H):
        H = H.to_undirected()
    subtours = list(nx.algorithms.components.connected_components(H))
    if len(subtours) > 1:
        subtours = [list(s) for s in subtours]
    if len(subtours) == 1:
        subtours = nx.algorithms.cycles.minimum_cycle_basis(H)

    if shifted_idx:
            subtours = [[item+1 for item in s] for s in subtours]
    return subtours