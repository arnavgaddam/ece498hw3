import json
import time
from typing import Dict, Any, List
from common import (
    PROBLEMS,
    get_instructor_client,
    get_openai_client,
    build_problem_prompt,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    P5Solution,
)
from verifier import verify, run_verilog_simulation

NUM_TRIALS = 5
MAX_REFINEMENT_TURNS = 2
PROBLEM_ID = "P5"

MAX_TOOL_TURNS = 3

TOOL_DEFINITION = {
    "name": "run_verilog_simulation",
    "description": "Compiles and runs Verilog code with Icarus Verilog. Use this to verify your Verilog module works correctly. Returns whether simulation passed and any errors.",
    "parameters": {
        "type": "object",
        "properties": {
            "module_code": {
                "type": "string",
                "description": "The Verilog module code to simulate (not including testbench)",
            },
            "testbench": {
                "type": "string",
                "description": "The Verilog testbench code to use for simulation",
            },
        },
        "required": ["module_code", "testbench"],
    },
}

TOOL_DESCRIPTION = """You have access to the following tool:

**run_verilog_simulation**
- Purpose: Compile and run Verilog code with Icarus Verilog to verify functionality
- Parameters:
  - module_code: The Verilog module to test
  - testbench: Testbench code to drive the simulation
- Returns: {"passed": bool, "errors": list, "output": str}

When you write Verilog code, use this tool to verify it compiles and produces correct results before finalizing your answer."""


def generate_testbench(problem_id: str) -> str:
    """Generate a testbench for the given problem."""
    testbenches = {
        "P5": """`timescale 1ns / 1ps
module testbench;
    reg clk;
    reg rst_n;
    reg start;
    reg [31:0] addr;
    reg [31:0] wdata;
    reg [1:0] size;
    reg write_en;
    reg arready;
    reg awready;
    reg wready;
    reg [3:0] bid;
    reg [1:0] bresp;
    reg bvalid;
    reg [3:0] rid;
    reg [31:0] rdata_in;
    reg [1:0] rresp;
    reg rvalid;
    wire [31:0] rdata;
    wire valid;
    wire ready;
    wire [3:0] arid;
    wire [31:0] araddr;
    wire arvalid;
    wire [3:0] awid;
    wire [31:0] awaddr;
    wire awvalid;
    wire [31:0] wdata_out;
    wire [3:0] wstrb;
    wire wvalid;
    wire bready;
    wire rready;
    axi_master uut (.clk(clk), .rst_n(rst_n), .start(start), .addr(addr), .wdata(wdata), .size(size), .write_en(write_en), .arready(arready), .awready(awready), .wready(wready), .bid(bid), .bresp(bresp), .bvalid(bvalid), .rid(rid), .rdata_in(rdata_in), .rresp(rresp), .rvalid(rvalid), .rdata(rdata), .valid(valid), .ready(ready), .arid(arid), .araddr(araddr), .arvalid(arvalid), .awid(awid), .awaddr(awaddr), .awvalid(awvalid), .wdata_out(wdata_out), .wstrb(wstrb), .wvalid(wvalid), .bready(bready), .rready(rready));
    initial begin clk = 0; forever #5 clk = ~clk; end
    initial begin rst_n = 0; start = 0; addr = 32'h1000; wdata = 32'hDEADBEEF; size = 2'd2; write_en = 0; arready = 1; awready = 1; wready = 1; bid = 4'd0; bresp = 2'd0; bvalid = 0; rid = 4'd0; rdata_in = 32'h12345678; rresp = 2'd0; rvalid = 0; #20 rst_n = 1; #10 start = 1; #10 start = 0; #100 $finish; end
endmodule""",
    }
    return testbenches.get(problem_id, "")


def solve_with_refinement() -> Dict[str, Any]:
    """Solve P5 with tool-augmented self-refinement.

    Flow per refinement turn:
    1. INITIAL: Get code via instructor with response_model
    2. TOOL LOOP: Let LLM call run_verilog_simulation to verify
    3. FINAL: Parse final content via instructor with response_model
    4. VERIFY: Check if solution passes
    5. If fail: Feed verifier's reason back, repeat (up to MAX_REFINEMENT_TURNS)
    """
    problem = PROBLEMS[PROBLEM_ID]
    field_name = "axi_master_module"

    print(f"\n{'=' * 60}")
    print(f"Solving {PROBLEM_ID}: {problem['name']}")
    print(f"{'=' * 60}\n")

    prompt = build_problem_prompt(
        PROBLEM_ID, include_tool=True, tool_description=TOOL_DESCRIPTION
    )

    instructor_client = get_instructor_client()
    openai_client = get_openai_client()

    for refinement_turn in range(MAX_REFINEMENT_TURNS + 1):
        print(f"\n{'=' * 40}")
        print(f"REFINEMENT TURN {refinement_turn + 1}")
        print(f"{'=' * 40}\n")

        if refinement_turn == 0:
            print("[INITIAL] Step 1: Getting initial solution via instructor...")
            print("-" * 40)

            initial_response = instructor_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Verilog engineer. Provide only the Verilog module code in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_model=P5Solution,
                temperature=DEFAULT_TEMPERATURE,
            )

            initial_solution = initial_response.model_dump()
            initial_code = initial_solution.get(field_name, "")
            print(f"[INITIAL] Got initial code ({len(initial_code)} chars)")
            print(f"[INITIAL] Code preview:\n{initial_code[:300]}...")
            print()

            current_code = initial_code
        else:
            print(f"[REFINEMENT] Using refined code from previous turn")
            print(f"[REFINEMENT] Code preview:\n{current_code[:300]}...")
            print()

        print("[TOOL LOOP] Step 2: Tool-calling loop...")
        print("-" * 40)

        messages = [
            {
                "role": "system",
                "content": "You are a Verilog engineer. You can use the run_verilog_simulation tool to verify your code. When done, output JSON with your solution.",
            },
            {
                "role": "user",
                "content": prompt + "\n\n## Your Solution:\n" + current_code,
            },
        ]

        final_content = None

        for tool_turn in range(MAX_TOOL_TURNS):
            print(f"[TOOL LOOP {tool_turn + 1}] Sending request to LLM...")

            response = openai_client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=[{"type": "function", "function": TOOL_DEFINITION}],
                temperature=DEFAULT_TEMPERATURE,
            )

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                func = tool_call.function
                args = json.loads(func.arguments)

                print(f"[TOOL LOOP {tool_turn + 1}] LLM called tool: {func.name}")

                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [message.model_dump()["tool_calls"][0]],
                    }
                )

                if func.name == "run_verilog_simulation":
                    module_code = args.get("module_code", "")
                    testbench_code = args.get("testbench", "") or generate_testbench(
                        PROBLEM_ID
                    )

                    print(f"[TOOL] Module code: {module_code[:100]}...")
                    print(f"[TOOL] Testbench: {testbench_code[:100]}...")
                    print("[TOOL] Executing simulation...")

                    try:
                        sim_result = run_verilog_simulation(
                            module_code, testbench_code, timeout=10
                        )
                    except Exception as e:
                        print(f"[TOOL] Simulation error: {e}")
                        sim_result = {
                            "passed": False,
                            "errors": [str(e)],
                            "output": "",
                            "stage": "error",
                        }

                    tool_result = {
                        "passed": sim_result["passed"],
                        "errors": sim_result.get("errors", []),
                        "output": sim_result.get("output", "")[:500]
                        if sim_result.get("output")
                        else "",
                    }

                    print(f"[TOOL] Result: passed={sim_result['passed']}")
                    if sim_result.get("errors"):
                        print(f"[TOOL] Errors: {sim_result['errors'][:2]}")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result),
                        }
                    )

                    if sim_result["passed"]:
                        print(
                            f"[TOOL LOOP {tool_turn + 1}] Simulation passed, using this code"
                        )
                        final_content = module_code
                        break
                    else:
                        print(
                            f"[TOOL LOOP {tool_turn + 1}] Simulation failed, continuing loop"
                        )
            else:
                content = message.content or ""
                print(
                    f"[TOOL LOOP {tool_turn + 1}] No tool calls, got text response ({len(content)} chars)"
                )
                final_content = content

        if final_content is None:
            final_content = current_code
            print("[TOOL LOOP] No final content, using current code")

        print()

        print("[FINAL] Step 3: Parsing final content via instructor...")
        print("-" * 40)

        final_prompt = f"""Here is the final Verilog module code. Please parse it into the required JSON format.

Module code:
{final_content}

Output JSON with field 'axi_master_module' containing the Verilog code. Module MUST be named 'axi_master'. Use Verilog-2005 only - no SystemVerilog types or unsized literals."""

        final_response = instructor_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Verilog engineer. Parse the provided code into the required JSON format.",
                },
                {"role": "user", "content": final_prompt},
            ],
            response_model=P5Solution,
            temperature=DEFAULT_TEMPERATURE,
        )

        final_solution = final_response.model_dump()
        print(f"[FINAL] Got structured solution: {list(final_solution.keys())}")
        print(f"[FINAL] Code preview:\n{final_solution.get(field_name, '')[:200]}...")
        print()

        print("[VERIFY] Step 4: Running verifier...")
        print("-" * 40)

        result = verify(PROBLEM_ID, final_solution)

        print(f"[VERIFY] Result: pass={result['pass']}")
        if result["pass"]:
            print(f"[VERIFY] {result['reason']}")
            return final_solution
        else:
            print(f"[VERIFY] Failed: {result['reason']}")
            current_code = final_solution.get(field_name, "")

            feedback_prompt = f"""The previous solution failed verification. Here is the reason:

{result["reason"]}

Please fix the issues and provide an improved solution. Use the run_verilog_simulation tool to verify your fix before finalizing."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a Verilog engineer. Fix the issues based on the feedback. You can use the run_verilog_simulation tool to verify your code.",
                },
                {
                    "role": "user",
                    "content": prompt
                    + "\n\n## Previous Solution:\n"
                    + current_code
                    + "\n\n## Feedback:\n"
                    + feedback_prompt,
                },
            ]

            for tool_turn in range(MAX_TOOL_TURNS):
                print(
                    f"[REFINE TOOL {tool_turn + 1}] Sending refinement request to LLM..."
                )

                response = openai_client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=messages,
                    tools=[{"type": "function", "function": TOOL_DEFINITION}],
                    temperature=DEFAULT_TEMPERATURE,
                )

                message = response.choices[0].message

                if message.tool_calls:
                    tool_call = message.tool_calls[0]
                    func = tool_call.function
                    args = json.loads(func.arguments)

                    print(f"[REFINE TOOL {tool_turn + 1}] LLM called tool: {func.name}")

                    messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [message.model_dump()["tool_calls"][0]],
                        }
                    )

                    if func.name == "run_verilog_simulation":
                        module_code = args.get("module_code", "")
                        testbench_code = args.get(
                            "testbench", ""
                        ) or generate_testbench(PROBLEM_ID)

                        print(f"[TOOL] Module code: {module_code[:100]}...")
                        print("[TOOL] Executing simulation...")

                        try:
                            sim_result = run_verilog_simulation(
                                module_code, testbench_code, timeout=10
                            )
                        except Exception as e:
                            print(f"[TOOL] Simulation error: {e}")
                            sim_result = {
                                "passed": False,
                                "errors": [str(e)],
                                "output": "",
                                "stage": "error",
                            }

                        tool_result = {
                            "passed": sim_result["passed"],
                            "errors": sim_result.get("errors", []),
                            "output": sim_result.get("output", "")[:500]
                            if sim_result.get("output")
                            else "",
                        }

                        print(f"[TOOL] Result: passed={sim_result['passed']}")

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result),
                            }
                        )

                        if sim_result["passed"]:
                            current_code = module_code
                            break
                else:
                    content = message.content or ""
                    print(f"[REFINE TOOL {tool_turn + 1}] Got text response")
                    current_code = content

            print()

    print(f"\n[FINAL] Max refinement turns reached, returning last solution")
    return final_solution


def run_refinement_evaluation() -> List[Dict[str, Any]]:
    """Run refinement evaluation on P5."""
    results = []

    print("=" * 60)
    print(f"Self-Refinement + Tools on {PROBLEM_ID}")
    print(f"{NUM_TRIALS} trials, up to {MAX_REFINEMENT_TURNS} refinement turns")
    print("=" * 60)

    for trial in range(NUM_TRIALS):
        print(f"\n{'#' * 60}")
        print(f"TRIAL {trial + 1}/{NUM_TRIALS}")
        print(f"{'#' * 60}")

        try:
            solution = solve_with_refinement()
            result = verify(PROBLEM_ID, solution)

            passed = result["pass"]

            print(f"\n{'=' * 60}")
            print(f"TRIAL {trial + 1} RESULT: {'PASS' if passed else 'FAIL'}")
            if not passed:
                print(f"Reason: {result['reason']}")
            print(f"{'=' * 60}")

            results.append(
                {
                    "trial": trial + 1,
                    "pass": passed,
                }
            )

        except Exception as e:
            print(f"\nERROR: {e}")
            results.append(
                {
                    "trial": trial + 1,
                    "pass": False,
                }
            )

        time.sleep(0.5)

    return results


def print_refinement_table(results: List[Dict[str, Any]]):
    """Print refinement results in table format."""
    print("\n" + "=" * 80)
    print("SELF-REFINEMENT + TOOLS RESULTS ON P5")
    print("=" * 80)
    print(f"{'Trial':<8} {'Result':<10}")
    print("-" * 80)

    for r in results:
        result_str = "PASS" if r["pass"] else "FAIL"
        print(f"{r['trial']:<8} {result_str:<10}")

    final_passes = sum(1 for r in results if r["pass"])
    print(f"\nPass rate: {final_passes}/{NUM_TRIALS}")
    print("=" * 80)


if __name__ == "__main__":
    results = run_refinement_evaluation()
    print_refinement_table(results)
