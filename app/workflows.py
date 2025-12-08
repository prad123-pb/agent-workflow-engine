from .models import GraphSpec, NodeSpec
from .engine import GRAPHS

def register_code_review_graph():
    nodes = {
        "extract": NodeSpec(name="extract", fn="extract_functions", params={}),
        "complexity": NodeSpec(name="complexity", fn="check_complexity", params={"threshold_name_len": 20}),
        "detect": NodeSpec(name="detect", fn="detect_issues", params={"max_line_len": 120}),
        "suggest": NodeSpec(name="suggest", fn="suggest_improvements", params={"loop_condition": "quality_score>=80", "on_success": None, "on_failure": "suggest"})
    }
    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
    }
    graph = GraphSpec(nodes=nodes, edges=edges, start_node="extract")
    graph_id = "code_review_v1"
    GRAPHS[graph_id] = graph
    return graph_id

def register_async_demo_graph():
    """
    Demo graph that includes a long-running async node.
    Node order: start -> long_task -> suggest
    """
    nodes = {
        "start": NodeSpec(name="start", fn="extract_functions", params={}),
        "long": NodeSpec(name="long", fn="long_task", params={"seconds": 6, "result_key": "long_done"}),
        "suggest": NodeSpec(name="suggest", fn="suggest_improvements", params={}),
    }
    edges = {
        "start": "long",
        "long": "suggest",
    }
    graph = GraphSpec(nodes=nodes, edges=edges, start_node="start")
    graph_id = "async_demo_v1"
    GRAPHS[graph_id] = graph
    return graph_id
