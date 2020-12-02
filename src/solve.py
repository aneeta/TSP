import logging
import itertools
import pprint
import re

import click
import pathlib
import tsplib95

from mtz import mtz
from dfj import dfj
from two_opt import two_opt
from christofides import christofides


logging.basicConfig(format='%(asctime)s %(message)s', level=10)


def load_problems(n):
    source = pathlib.Path.home() / 'Desktop/TSP/TSPLIB' #hardcoded source, change later
    p_path = source / 'problems'
    s_path =  source / 'solutions'

    problems = sorted(list(p_path.glob('*.tsp')))[:n]
    solutions = sorted(list(s_path.glob('*.opt.tour')))[:n]
    p_s = list(zip(problems, solutions))

    problems = {
        i.stem: {
            'n_nodes': int(re.split(r'\D', i.stem)[-1]),
            'problem': tsplib95.load(i),
            'opt_path': tsplib95.load(j).tours,
        } for (i,j) in p_s
    }

    for k, v in problems.items():
        pnodes = min(list(v['problem'].get_nodes()))
        snodes = min(v['opt_path'][0])

        if  pnodes == 0 and snodes == 1:
            problems[k]['opt_sol'] = v['problem'].trace_tours([[i-1 for i in v['opt_path'][0]]])[0]
        elif (pnodes == 1 and snodes == 1) or (pnodes == 0 and snodes == 0):
            problems[k]['opt_sol'] = v['problem'].trace_tours([v['opt_path'][0]])[0]
        elif pnodes == 1 and snodes == 0:
            problems[k]['opt_sol'] = v['problem'].trace_tours([[i+1 for i in v['opt_path'][0]]])[0]
        else:
            raise ValueError("Problem nodes have abnormal indices")
    
    return problems

# setting up parameters, hard coded - change later
pyomo_solvers = [ "cplex", "gurobi", "ipopt"]
# potentially add "glpk"

methods = {
    "dfj": {
        "solver": pyomo_solvers,
        "TIME_LIMIT": [60, 150, 300],
        "F_TIME_LIMIT": [600, 1500, 3000]
    },
    "mtz": {
        "solvers": pyomo_solvers,
        "TIME_LIMIT": [600, 1500, 3000]
    },
    "two_opt": {
        "F_TIME_LIMIT": [60, 150, 300]
    },
    "christofides": {}
}

# output results

@click.command()
@click.option(
    '--n', type=click.IntRange(1, 32, clamp=True),
    help='Number of problems to solve'
    )
@click.option(
    '--m', type=click.Choice(['dfj', 'mtz', 'two_opt', 'christofides'], case_sensitive=False),
    multiple=True, default=['dfj', 'mtz', 'two_opt', 'christofides'],
    help='Solution methods to use, defaults to all'
    )
def main(n, m):
    # initialize results object
    results = {}
    # load problems
    problems = load_problems(n)

    for k, v in methods.items():
        if k not in list(m):
            continue
        logging.info("Solving with method {}".format(str(k)))
        results[k] = {}
        for i, j in problems.items():
            logging.info("Solving problem {}".format(i))
            results[k][i] = {"optimal_solution": j["opt_sol"], "solutions": {}}
            if v:
                options = list(itertools.product(*[i for i in v.values()]))
                results[k][i]["solutions"] = { op: {} for op in options}
                for op in options:
                    logging.info("Solving with option {}".format(str(op)))
                    results[k][i]["solutions"][op] = eval(k+'(j["problem"], *op)')
            else:
                logging.info("Solving without options")
                results[k][i]["solutions"] = eval(k+'(j["problem"])')
    
    print(results)

if __name__ == "__main__":
    main()