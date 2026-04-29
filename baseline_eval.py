import os
import json
import time
from typing import Dict, Any, List
from common import (
    Problems,
    get_instructor_client,
    build_problem_prompt,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    SOLUTION_MODELS,
)
from verifier import verify

NUM_TRIALS = 5
PROBLEM_IDS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]

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


def run_baseline_evaluation() -> Dict[str, List[Dict[str, Any]]]:
    """Run baseline evaluation (no tools) for all problems."""
    client = get_instructor_client()
    setup_debug_dir()

    results = {pid: [] for pid in PROBLEM_IDS}

    for problem_id in PROBLEM_IDS:
        problem = Problems.get(problem_id)
        print(f"\n=== Running {problem_id}: {problem.name} ({problem.family}) ===")

        for trial in range(NUM_TRIALS):
            print(f"  Trial {trial + 1}/{NUM_TRIALS}...", end=" ")

            try:
                solution = solve_problem(client, problem_id)
                save_debug_output(problem_id, trial + 1, solution)
                result = verify(problem_id, solution)

                passed = result["pass"]
                results[problem_id].append(
                    {
                        "trial": trial + 1,
                        "pass": passed,
                        "reason": result.get("reason", ""),
                        "details": result.get("details", {}),
                    }
                )

                print(f"{'PASS' if passed else 'FAIL'}")

                if not passed:
                    print(f"    Reason: {result['reason'][:100]}")

            except Exception as e:
                print(f"ERROR: {e}")
                results[problem_id].append(
                    {
                        "trial": trial + 1,
                        "pass": False,
                        "reason": f"Exception: {str(e)[:100]}",
                        "details": {},
                    }
                )

            time.sleep(0.5)

    return results


def save_results_to_json(results: Dict[str, List[Dict[str, Any]]]):
    """Save results to baseline_log.json."""
    with open("baseline_log.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to baseline_log.json")


def print_results_table(results: Dict[str, List[Dict[str, Any]]]):
    """Print results in table format."""
    print("\n" + "=" * 100)
    print("BASELINE RESULTS (No Memory)")
    print("=" * 100)
    print(
        f"{'Problem':<8} {'Family':<10} {'Difficulty':<10} {'T1':<4} {'T2':<4} {'T3':<4} {'T4':<4} {'T5':<4} {'Rate':<10}"
    )
    print("-" * 100)

    for pid in PROBLEM_IDS:
        problem = Problems.get(pid)
        difficulty = problem.difficulty
        family = problem.family
        passes = results[pid]
        pass_rate = sum(1 for p in passes if p["pass"]) / len(passes)

        t1 = "P" if passes[0]["pass"] else "F"
        t2 = "P" if passes[1]["pass"] else "F"
        t3 = "P" if passes[2]["pass"] else "F"
        t4 = "P" if passes[3]["pass"] else "F"
        t5 = "P" if passes[4]["pass"] else "F"

        print(
            f"{pid:<8} {family:<10} {difficulty:<10} {t1:<4} {t2:<4} {t3:<4} {t4:<4} {t5:<4} {pass_rate}/5"
        )

    print("=" * 100)


def print_family_summary(results: Dict[str, List[Dict[str, Any]]]):
    """Print family-level summary."""
    print("\n" + "=" * 60)
    print("FAMILY-LEVEL SUMMARY")
    print("=" * 60)

    for family in ["FamilyA", "FamilyB"]:
        family_probs = [
            pid for pid in PROBLEM_IDS if Problems.get(pid).family == family
        ]
        total_trials = len(family_probs) * NUM_TRIALS
        total_passes = sum(
            sum(1 for p in results[pid] if p["pass"]) for pid in family_probs
        )
        family_rate = total_passes / total_trials if total_trials > 0 else 0
        print(f"{family}: {total_passes}/{total_trials} = {family_rate:.1%}")

    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("BASELINE EVALUATION (No Memory)")
    print("=" * 60)
    print(f"Running {NUM_TRIALS} trials for each of {len(PROBLEM_IDS)} problems")
    print(f"Total solves: {NUM_TRIALS * len(PROBLEM_IDS)}")
    print(f"Model: {DEFAULT_MODEL}, Temperature: {DEFAULT_TEMPERATURE}")

    results = run_baseline_evaluation()
    save_results_to_json(results)
    print_results_table(results)
    print_family_summary(results)

    print("\n" + "=" * 60)
    print("Evaluation complete!")
    print("=" * 60)
