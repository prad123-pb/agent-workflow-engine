from typing import Dict, Callable, Any

# --- Tool registry ---
Tool = Callable[[dict, dict], dict]

_registry: Dict[str, Tool] = {}

def register(name: str):
    def _wrap(fn: Tool):
        _registry[name] = fn
        return fn
    return _wrap

def get(name: str) -> Tool:
    if name not in _registry:
        raise KeyError(f"Tool '{name}' not found in registry")
    return _registry[name]

# --- Synchronous / simple tools ---
@register("extract_functions")
def extract_functions(state: dict, params: dict) -> dict:
    code = state.get("code", "")
    functions = []
    for line in code.splitlines():
        line = line.strip()
        if line.startswith("def "):
            name = line.split("(")[0].replace("def ","").strip()
            functions.append(name)
    return {"functions": functions, "issues": 0}

@register("check_complexity")
def check_complexity(state: dict, params: dict) -> dict:
    issues = state.get("issues", 0)
    functions = state.get("functions", [])
    complexity = {fn: len(fn) for fn in functions}
    for fn, val in complexity.items():
        if val > params.get("threshold_name_len", 20):
            issues += 1
    return {"complexity": complexity, "issues": issues}

@register("detect_issues")
def detect_issues(state: dict, params: dict) -> dict:
    code = state.get("code", "")
    issues = state.get("issues", 0)
    for line in code.splitlines():
        if len(line) > params.get("max_line_len", 120):
            issues += 1
    return {"issues": issues}

@register("suggest_improvements")
def suggest_improvements(state: dict, params: dict) -> dict:
    issues = state.get("issues", 0)
    suggestions = []
    if issues == 0:
        suggestions.append("Code looks fine.")
    else:
        suggestions.append(f"Found {issues} issues. Consider refactoring and reducing long lines.")
    quality = max(0, 100 - issues * 10)
    return {"suggestions": suggestions, "quality_score": quality}

# --- Asynchronous tool(s) ---
import asyncio as _asyncio  # alias to avoid confusion

@register("long_task")
async def long_task(state: dict, params: dict) -> dict:
    """
    Simulates a long-running I/O-bound task.
    Accepts params: seconds (int) to wait, result_key (str) to store outcome.
    """
    seconds = int(params.get("seconds", 5))
    result_key = params.get("result_key", "long_result")
    # simulate async work
    await _asyncio.sleep(seconds)
    return {result_key: f"completed after {seconds}s"}
