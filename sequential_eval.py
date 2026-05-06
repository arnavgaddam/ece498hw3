import json
import os
import time
from typing import Dict, Any, List

from common import Problems, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from memory_pipeline import solve_problem_with_memory, load_memory_store


NUM_TRIALS = 5
PROBLEM_IDS = [f"P{i}" for i in range(1, 11)]

MEMORY_PATH = "memory_dump.json"
TOP_K = 3
SLEEP_SECONDS = 0.5
DEBUG_DIR = "debug_outputs_memory"


def setup_debug_dir() -> None:
    os.makedirs(DEBUG_DIR, exist_ok=True)


def save_debug_output(problem_id: str, trial: int, payload: Dict[str, Any]) -> None:
    filename = os.path.join(DEBUG_DIR, f"{problem_id}_trial{trial}.json")
    with open(filename, "w") as f:
        json.dump(payload, f, indent=2)


def run_sequential_eval() -> Dict[str, List[Dict[str, Any]]]:
    results: Dict[str, List[Dict[str, Any]]] = {pid: [] for pid in PROBLEM_IDS}
    setup_debug_dir()

    for trial in range(NUM_TRIALS):
        print("\n" + "=" * 70)
        print(f"TRIAL {trial + 1}/{NUM_TRIALS} (Memory on, sequential P1->P10)")
        print("=" * 70)

        store = load_memory_store(MEMORY_PATH)
        store.reset()

        for pid in PROBLEM_IDS:
            problem = Problems.get(pid)
            print(f"\n=== {pid}: {problem.name} ({problem.family}) ===")
            solve_out = solve_problem_with_memory(pid, store, top_k=TOP_K)
            passed = solve_out["result"]["pass"]

            save_debug_output(
                pid,
                trial + 1,
                {
                    "problem_id": pid,
                    "trial": trial + 1,
                    "solution": solve_out.get("solution", {}),
                    "result": solve_out.get("result", {}),
                    "retrieved": solve_out.get("retrieved", []),
                    "stored_entry": solve_out.get("stored_entry", {}),
                },
            )

            results[pid].append(
                {
                    "trial": trial + 1,
                    "pass": passed,
                    "reason": solve_out["result"].get("reason", ""),
                    "solution": solve_out.get("solution", {}),
                    "retrieved": solve_out.get("retrieved", []),
                    "stored_entry": solve_out.get("stored_entry", {}),
                }
            )

            print(f"Result: {'PASS' if passed else 'FAIL'}")
            if not passed:
                print(f"Reason: {solve_out['result'].get('reason', '')[:120]}")

            time.sleep(SLEEP_SECONDS)

    return results


def save_results(results: Dict[str, List[Dict[str, Any]]], path: str) -> None:
    with open(path, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    print("=" * 70)
    print("SEQUENTIAL EVAL (Memory On)")
    print("=" * 70)
    print(f"Model: {DEFAULT_MODEL}, Temperature: {DEFAULT_TEMPERATURE}")
    print(f"Trials: {NUM_TRIALS}, Top-k: {TOP_K}")

    results = run_sequential_eval()
    save_results(results, "sequential_eval_log.json")
    print("\nSaved results to sequential_eval_log.json")
