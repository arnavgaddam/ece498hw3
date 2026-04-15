import os
import json
import time
from typing import Dict, Any, List
from common import (
    PROBLEMS,
    get_instructor_client,
    build_problem_prompt,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    SOLUTION_MODELS,
)
from verifier import verify

NUM_TRIALS = 5
PROBLEM_IDS = ["P1", "P2", "P3", "P4", "P5"]

DEBUG_DIR = "debug_outputs"


def setup_debug_dir():
    """Create debug output directory if it doesn't exist."""
    os.makedirs(DEBUG_DIR, exist_ok=True)


def save_debug_output(problem_id: str, trial: int, solution: Dict[str, Any]):
    """Save LLM output to debug file for analysis."""
    filename = os.path.join(DEBUG_DIR, f"{problem_id}_trial{trial}.json")
    with open(filename, "w") as f:
        json.dump(solution, f, indent=2)


def solve_problem(client, problem_id: str) -> Dict[str, Any]:
    """Solve a single problem using the LLM without tools (with instructor)."""
    prompt = build_problem_prompt(problem_id, include_tool=False)
    solution_model = SOLUTION_MODELS[problem_id]

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a Verilog engineer. Provide only the Verilog module code in JSON format.",
            },
            {"role": "user", "content": prompt},
        ],
        response_model=solution_model,
        temperature=DEFAULT_TEMPERATURE,
    )

    solution_data = response.model_dump()
    return solution_data


def run_baseline_evaluation() -> Dict[str, List[bool]]:
    """Run baseline evaluation (no tools) for all problems."""
    client = get_instructor_client()
    setup_debug_dir()

    results = {pid: [] for pid in PROBLEM_IDS}

    for problem_id in PROBLEM_IDS:
        print(f"\n=== Running {problem_id} ({PROBLEMS[problem_id]['name']}) ===")

        for trial in range(NUM_TRIALS):
            print(f"  Trial {trial + 1}/{NUM_TRIALS}...", end=" ")

            try:
                solution = solve_problem(client, problem_id)
                save_debug_output(problem_id, trial + 1, solution)
                result = verify(problem_id, solution)

                passed = result["pass"]
                results[problem_id].append(passed)

                print(f"{'PASS' if passed else 'FAIL'}")

                if not passed:
                    print(f"    Reason: {result['reason']}")

            except Exception as e:
                print(f"ERROR: {e}")
                results[problem_id].append(False)

            time.sleep(0.5)

    return results


def print_results_table(results: Dict[str, List[bool]]):
    """Print results in table format."""
    print("\n" + "=" * 80)
    print("BASELINE RESULTS (No Tools)")
    print("=" * 80)
    print(
        f"{'Problem':<8} {'Difficulty':<12} {'T1':<4} {'T2':<4} {'T3':<4} {'T4':<4} {'T5':<4} {'Pass Rate':<10}"
    )
    print("-" * 80)

    for pid in PROBLEM_IDS:
        difficulty = PROBLEMS[pid]["difficulty"]
        passes = results[pid]
        pass_rate = sum(passes) / len(passes)

        t1 = "P" if passes[0] else "F"
        t2 = "P" if passes[1] else "F"
        t3 = "P" if passes[2] else "F"
        t4 = "P" if passes[3] else "F"
        t5 = "P" if passes[4] else "F"

        print(
            f"{pid:<8} {difficulty:<12} {t1:<4} {t2:<4} {t3:<4} {t4:<4} {t5:<4} {pass_rate}/5"
        )

    print("=" * 80)


if __name__ == "__main__":
    print("Starting baseline evaluation (no tools)...")
    print(f"Running {NUM_TRIALS} trials for each of {len(PROBLEM_IDS)} problems")

    results = run_baseline_evaluation()
    print_results_table(results)
