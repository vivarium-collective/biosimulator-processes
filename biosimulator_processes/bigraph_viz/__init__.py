import pprint
from biosimulator_processes.bigraph_viz.diagram import plot_bigraph, generate_types
from biosimulator_processes.bigraph_viz.dict_utils import replace_regex_recursive
from biosimulator_processes.bigraph_schema import TypeSystem


pretty = pprint.PrettyPrinter(indent=2)


def pf(x):
    return pretty.pformat(x)
