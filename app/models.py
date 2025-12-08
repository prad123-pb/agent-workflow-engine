from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class NodeSpec(BaseModel):
    name: str
    fn: str
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)

class GraphSpec(BaseModel):
    nodes: Dict[str, NodeSpec]
    edges: Dict[str, str]
    start_node: str

class RunCreate(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)

class RunState(BaseModel):
    run_id: str
    graph_id: str
    current_node: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
    done: bool = False
