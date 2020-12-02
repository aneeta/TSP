import logging
import time

import networkx as nx
import pyomo.environ as pyo

from util import *

logging.basicConfig(format='%(asctime)s %(message)s', level=10)

def mtz(problem, SOLVER_NAME="cplex", TIME_LIMIT=600):
    """ LP MTZ formulation

    Args:
        problem ([TSPLIB object]): problem to be solved
        SOLVER_NAME (str, optional): solver to be used. Defaults to "cplex".
        TIME_LIMIT (int, optional): solver time limit in seconds. Defaults to 600.

    Raises:
        Exception: Pyomo or solver exceptions

    Returns:
        [dict]: contains the solution comprising of path_length, path, time
        [Pyomo model]: solved Pyomo model
    """

    if SOLVER_NAME.lower() not in ["glpk", "cplex", "gurobi", "ipopt"]:
        raise ValueError('Solver not implemented. Choose from: "glpk", "cplex", "gurobi", "ipopt"')

    #initialize solver
    solver = pyo.SolverFactory(SOLVER_NAME, solver_io="python")
    setup_solver_time_limit(solver, SOLVER_NAME, TIME_LIMIT)
    
    # start time
    stime = time.perf_counter()
    
    G = problem.get_graph()
    shifted_idx= shifted_index(G)

    cost_matrix = nx.convert_matrix.to_numpy_array(G)
    
    ## change zero to an arbitrarily large number since np.inf won't work with pyomo
    cost_matrix[cost_matrix == 0] = 10**7
    
    n = len(cost_matrix)
    
    # initiate model
    logging.info("Building the model")
    model = pyo.ConcreteModel()

    # Indexes for the cities
    model.M = pyo.RangeSet(n)                
    model.N = pyo.RangeSet(n)

    # Index for the dummy variable u
    model.U = pyo.RangeSet(2,n) #assuming we are starting at city 1

    # Decision variables x_ij 
    model.x = pyo.Var(model.N,model.M, within=pyo.Binary)

    # Dummy variable u_i
    model.u=pyo.Var(model.N, within=pyo.NonNegativeIntegers,bounds=(0,n-1))

    # Cost Matrix c_ij
    model.c = pyo.Param(model.N, model.M, initialize=lambda model, i, j: cost_matrix[i-1][j-1])

    #Objective function
    model.objective = pyo.Objective(rule=lambda model: sum(model.x[i,j] * model.c[i,j] for i in model.N for j in model.M), sense=pyo.minimize)
    
    # Only 1 leaves each city
    model.const1 = pyo.Constraint(model.M, rule=lambda model,M: sum(model.x[i,M] for i in model.N if i!=M ) == 1)
    
    # Only 1 enters each city
    model.rest2 = pyo.Constraint(model.N, rule=lambda model, N: sum(model.x[N,j] for j in model.M if j!=N) == 1)
    
    #Subtour constraint 
    def rule_const3(model,i,j):
        if i != j: 
            return model.u[i] - model.u[j] + model.x[i,j] * n <= n-1
        else:
            return model.u[i] - model.u[i] == 0 
    
    model.rest3 = pyo.Constraint(model.U, model.N, rule=rule_const3)

    # solve    
    logging.info("Solving the model")
    result = solver.solve(model, tee = False)
    
    # extract results
    logging.info("Compiling results")
    List = list(model.x.keys())
    edges = []
    for i in List:
        if model.x[i]() != 0: #nonzero values
            edges.append(i)
            

    if shifted_idx:
        edges = [(i[0]-1,i[1]-1) for i in edges]
            
    H = G.edge_subgraph(edges)
    
    new_edges = transform_edge_list(edges)
    
            
    # finish time
    ftime = time.perf_counter()
    
    sol = {
        "path_length": H.size(weight='weight'),
        "path": new_edges,
        "time": ftime-stime
    }
    
    return sol, result
