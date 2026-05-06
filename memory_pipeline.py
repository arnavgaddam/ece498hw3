import json
import os
from typing import Dict, Any, List, Optional

from common import (
    PROBLEMS,
    Problems,
    get_instructor_client,
    build_problem_prompt,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    SOLUTION_MODELS,
)
from verifier import verify
from taxonomy import FailureCategory, categorize_reason
from memory import (
    MemoryStore,
    MemoryEntry,
    Lesson,
    generate_entry_id,
    current_timestamp,
)
from extraction import extract_lesson


DEFAULT_MEMORY_PATH = "memory_dump.json"
DEFAULT_TOP_K = 3


def normalize_text(text: str) -> List[str]:
    tokens = []
    for raw in text.lower().split():
        token = "".join(ch for ch in raw if ch.isalnum())
        if token:
            tokens.append(token)
    return tokens


def score_overlap(query: str, candidate: str) -> int:
    query_tokens = set(normalize_text(query))
    candidate_tokens = set(normalize_text(candidate))
    return len(query_tokens.intersection(candidate_tokens))


def build_problem_features(problem_id: str) -> str:
    problem = Problems.get(problem_id)
    parts = [
        f"family={problem.family}",
        f"difficulty={problem.difficulty}",
        problem.name,
        problem.statement,
        " ".join(f"{k}: {v}" for k, v in problem.specs.items()),
    ]
    return "\n".join(parts)


def retrieve_lessons(
    store: MemoryStore,
    problem_id: str,
    top_k: int = DEFAULT_TOP_K,
) -> List[MemoryEntry]:
    if top_k <= 0:
        return []

    problem_features = build_problem_features(problem_id)
    candidates = []
    for entry in store.read_all():
        if entry.source_problem_id == problem_id:
            continue
        if entry.lesson.generality == "problem_specific":
            continue
        candidate_text = f"{entry.problem_features}\n{entry.lesson.condition}\n{entry.lesson.action}\n{entry.lesson.rationale}"
        score = score_overlap(problem_features, candidate_text)
        if score > 0:
            candidates.append((score, entry))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in candidates[:top_k]]


def format_lessons_for_prompt(lessons: List[MemoryEntry]) -> str:
    if not lessons:
        return ""
    lines = ["## Retrieved Lessons (use if relevant)"]
    for idx, entry in enumerate(lessons, start=1):
        lesson = entry.lesson
        lines.append(
            f"{idx}. Condition: {lesson.condition}\n"
            f"   Action: {lesson.action}\n"
            f"   Rationale: {lesson.rationale}\n"
            f"   Generality: {lesson.generality}\n"
            f"   Source: {entry.source_problem_id}"
        )
    return "\n".join(lines)


def solve_problem_with_memory(
    problem_id: str,
    store: MemoryStore,
    top_k: int = DEFAULT_TOP_K,
    extra_system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    prompt = build_problem_prompt(problem_id, include_tool=False)
    solution_model = SOLUTION_MODELS[problem_id]

    retrieved = retrieve_lessons(store, problem_id, top_k=top_k)
    memory_prompt = format_lessons_for_prompt(retrieved)

    system_content = "You are a Verilog engineer. Provide only the Verilog module code in JSON format."
    if memory_prompt:
        system_content = system_content + "\n\n" + memory_prompt
    if extra_system_prompt:
        system_content = system_content + "\n\n" + extra_system_prompt

    client = get_instructor_client()
    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        response_model=solution_model,
        temperature=DEFAULT_TEMPERATURE,
    )

    solution_data = response.model_dump()

    result = verify(problem_id, solution_data)
    outcome = "pass" if result["pass"] else "fail"
    failure_type = None
    if not result["pass"]:
        failure_type_id = categorize_reason(result.get("reason", ""))
        failure_type = FailureCategory.get_name(failure_type_id)

    attempted_solution = json.dumps(solution_data, indent=2)
    lesson = extract_lesson(
        problem_statement=Problems.get(problem_id).statement,
        attempted_solution=attempted_solution,
        outcome=outcome,
        verifier_reason=result.get("reason", ""),
    )

    entry = MemoryEntry(
        entry_id=generate_entry_id(),
        source_problem_id=problem_id,
        problem_features=build_problem_features(problem_id),
        outcome=outcome,
        failure_type=failure_type,
        lesson=lesson,
        timestamp=current_timestamp(),
    )
    store.write(entry)

    return {
        "problem_id": problem_id,
        "solution": solution_data,
        "result": result,
        "retrieved": [e.model_dump() for e in retrieved],
        "stored_entry": entry.model_dump(),
    }


def run_retrieval_ablation(
    problem_ids: List[str],
    top_k_values: List[int],
    memory_path: str = DEFAULT_MEMORY_PATH,
) -> Dict[str, Dict[int, List[bool]]]:
    results: Dict[str, Dict[int, List[bool]]] = {pid: {} for pid in problem_ids}
    for k in top_k_values:
        store = MemoryStore(path=memory_path)
        store.reset()
        for pid in problem_ids:
            solve_out = solve_problem_with_memory(pid, store, top_k=k)
            passed = solve_out["result"]["pass"]
            results[pid].setdefault(k, []).append(passed)
    return results


def load_memory_store(path: str = DEFAULT_MEMORY_PATH) -> MemoryStore:
    return MemoryStore(path=path)


def main():
    problem_ids = [f"P{i}" for i in range(1, 11)]
    store = MemoryStore(path=DEFAULT_MEMORY_PATH)
    store.reset()

    for pid in problem_ids:
        print(f"\n=== Solving {pid} with memory ===")
        result = solve_problem_with_memory(pid, store, top_k=DEFAULT_TOP_K)
        print(f"Result: {'PASS' if result['result']['pass'] else 'FAIL'}")
        if not result["result"]["pass"]:
            print(f"Reason: {result['result'].get('reason', '')[:120]}")


if __name__ == "__main__":
    main()
