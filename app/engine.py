import asyncio
from typing import Dict, Any, Optional
from uuid import uuid4
from .models import GraphSpec, RunState, NodeSpec
from . import tools

# In-memory stores (assignment-friendly)
GRAPHS: Dict[str, GraphSpec] = {}
RUNS: Dict[str, RunState] = {}
TASKS: Dict[str, asyncio.Task] = {}  # run_id -> asyncio.Task

async def _execute_node(node_name: str, node_spec: NodeSpec, run_state: RunState):
    """Call the tool function for a node and merge results into run state."""
    fn = tools.get(node_spec.fn)
    params = node_spec.params or {}
    if asyncio.iscoroutinefunction(fn):
        result = await fn(run_state.state, params)
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, fn, run_state.state, params)
    # Merge result into shared state
    run_state.state.update(result)
    run_state.logs.append(f"Node {node_name} executed; updated keys: {list(result.keys())}")

async def run_graph(graph_id: str, initial_state: Dict[str, Any], run_id: Optional[str] = None) -> RunState:
    """
    Run a graph synchronously (to completion).
    If run_id is provided, use it for the RunState; otherwise generate a new one.
    Returns the final RunState.
    """
    if graph_id not in GRAPHS:
        raise KeyError("Graph not found")
    graph = GRAPHS[graph_id]
    if run_id is None:
        run_id = str(uuid4())
    run_state = RunState(
        run_id=run_id,
        graph_id=graph_id,
        current_node=graph.start_node,
        state=initial_state.copy(),
        logs=[],
        done=False
    )
    # store the RunState immediately so callers can poll it while running
    RUNS[run_id] = run_state

    current = graph.start_node
    visited = 0
    while current:
        visited += 1
        if visited > 1000:
            run_state.logs.append("Loop guard activated; aborting.")
            break
        node_spec = graph.nodes[current]
        run_state.current_node = current
        # execute node
        try:
            await _execute_node(current, node_spec, run_state)
        except Exception as e:
            run_state.logs.append(f"Node {current} error: {repr(e)}")
            run_state.done = True
            break

        # default next node from edges
        next_node = graph.edges.get(current)

        # support a simple loop_condition of form "key>=value" in node params
        cond = node_spec.params.get("loop_condition")
        if cond:
            try:
                key, op_value = cond.split(">=")
                key = key.strip()
                value = int(op_value.strip())
                if run_state.state.get(key, 0) >= value:
                    next_node = node_spec.params.get("on_success") or None
                else:
                    next_node = node_spec.params.get("on_failure") or current
            except Exception:
                run_state.logs.append("Invalid loop_condition; continuing default path.")

        run_state.logs.append(f"Transition: {current} -> {next_node}")
        if not next_node:
            run_state.done = True
            break
        current = next_node
        # yield to event loop so state is updated and visible to pollers
        await asyncio.sleep(0)

    run_state.current_node = None
    run_state.done = True
    return run_state

def start_graph_background(graph_id: str, initial_state: Dict[str, Any]) -> str:
    """
    Start the graph in the background, return run_id immediately.
    The background task will populate RUNS[run_id] as it executes.
    """
    run_id = str(uuid4())
    # create initial RunState placeholder so /graph/state can be polled immediately
    placeholder = RunState(
        run_id=run_id,
        graph_id=graph_id,
        current_node=None,
        state=initial_state.copy(),
        logs=["Run scheduled; waiting to start."],
        done=False
    )
    RUNS[run_id] = placeholder

    async def _bg_runner():
        try:
            # call run_graph passing the run_id so it uses our placeholder and updates it
            final_state = await run_graph(graph_id, initial_state, run_id=run_id)
            # ensure RUNS[run_id] points to the final RunState (run_graph already updated it)
            RUNS[run_id] = final_state
        except Exception as e:
            # capture exceptions in logs so the user can see failure reason
            RUNS[run_id].logs.append(f"Background run error: {repr(e)}")
            RUNS[run_id].done = True

    # schedule task
    task = asyncio.create_task(_bg_runner())
    TASKS[run_id] = task
    return run_id
