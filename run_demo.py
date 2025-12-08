import time
import requests

BASE = "http://127.0.0.1:8000"

def run_demo():
    print("Starting async workflow run...")

    # 1. Trigger async run
    payload = {
        "graph_id": "async_demo_v1",
        "initial_state": {
            "code": "def a():\n    pass"
        }
    }

    r = requests.post(f"{BASE}/graph/run", json=payload)
    data = r.json()
    run_id = data["run_id"]

    print("Run started with ID:", run_id)
    print("Polling state...\n")

    # 2. Poll until done
    while True:
        resp = requests.get(f"{BASE}/graph/state/{run_id}")
        info = resp.json()

        run = info["run"]
        task = info["task"]

        print("Current node:", run["current_node"])
        print("Done:", run["done"])
        print("Logs:", run["logs"][-1] if run["logs"] else None)
        print("-" * 40)

        if run["done"]:
            print("\nFinal state:", run["state"])
            break

        time.sleep(1)


if __name__ == "__main__":
    run_demo()
