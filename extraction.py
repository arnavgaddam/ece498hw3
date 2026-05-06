from typing import Optional

from pydantic import BaseModel

from common import get_instructor_client, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from memory import Lesson


EXTRACTION_PROMPT = """
You are a lesson extractor responsible for finding a way to improve an LLM's performance on a given problem. You will look at a problem statement, an LLM's attempted solution, and the solution's correctness as evaluated by a deterministic verifier. 
Input:
- Problem statement
- Attempted solution
- Outcome (pass/fail)
- Verifier reason (if failed)
Task:
Extract a Lesson object with fields:
- condition: When does this lesson apply?
- action: What should the agent do in that case?
- rationale: Why? (must reference an underlying principle)
- generality: one of [problem_specific, family_specific, domain_general]
Here are some hard requirements:
1) No verbatim leakage: do NOT restate numeric answers, specific constants, or named entities from the source problem.
2) Be honest. If the lesson is narrow to the exact problem instance, label it problem_specific so that it is not applied to other problems. 
3) The condition must reference the verifier reason and include at least one domain cue (e.g., ready/valid handshake, open-drain bus, async reset, clock divider, FSM sequencing). Avoid vague conditions like "when implementing a controller" that can be generalized to many different problems.
4) The action must be 2–3 concrete steps that directly mitigate the failure mode.
5) The rationale must cite a principle (timing/handshake correctness, protocol rule, synthesizability, etc.) and link it to the failure reason.
6) Default to family_specific unless you are confident it applies across multiple families.
7) If the problem is with syntax, ensure the lesson reinforces Verilog-2005 constraints (no SystemVerilog types, no unsized literals, explicit widths, no SV-only constructs).
8) If the failure reason indicates missing code, syntax errors, or SystemVerilog usage, explicitly mention output completeness and Verilog-2005 compliance in the action.
9) If the problem involves a named protocol (AXI, I2C, PWM, PID, so on), include that protocol name in the condition.
"""


class ExtractionInput(BaseModel):
    problem_statement: str
    attempted_solution: str
    outcome: str
    verifier_reason: Optional[str] = None


def extract_lesson(
    problem_statement: str,
    attempted_solution: str,
    outcome: str,
    verifier_reason: Optional[str] = None,
) -> Lesson:
    client = get_instructor_client()
    payload = ExtractionInput(
        problem_statement=problem_statement,
        attempted_solution=attempted_solution,
        outcome=outcome,
        verifier_reason=verifier_reason,
    )

    prompt = (
        f"Problem Statement:\n{payload.problem_statement}\n\n"
        f"Attempted Solution:\n{payload.attempted_solution}\n\n"
        f"Outcome: {payload.outcome}\n"
        f"Verifier Reason: {payload.verifier_reason or 'N/A'}\n"
    )

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_model=Lesson,
        temperature=DEFAULT_TEMPERATURE,
    )

    return response
