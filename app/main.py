from fastapi import FastAPI, HTTPException
from .models import GraphSpec, RunCreate
from .engine import GRAPHS, RUNS, TASKS, run_graph, start_graph_background
from .workflows import register_code_review_graph, register_async_demo_graph

app = FastAPI(title="Mini Workflow Engine")

@app.on_event("startup")
async def startup_event():
    # register demo graphs at startup
    register_code_review_graph()
    register_async_demo_graph()

@app.post("/graph/create")
async def create_graph(spec: GraphSpec):
    graph_id = f"graph_{len(GRAPHS)+1}"
    GRAPHS[graph_id] = spec
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def graph_run(payload: RunCreate):
    if payload.graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail="graph not found")
    # Start the run in the background and return immediately
    run_id = start_graph_background(payload.graph_id, payload.initial_state)
    return {"run_id": run_id, "status": "started"}

@app.get("/graph/state/{run_id}")
async def graph_state(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="run_id not found")
    # Show task status if available
    task_info = {}
    task = TASKS.get(run_id)
    if task:
        task_info["done"] = task.done()
        if task.cancelled():
            task_info["cancelled"] = True
    state = RUNS[run_id]
    # Return RunState plus task metadata
    return {"run": state, "task": task_info}
