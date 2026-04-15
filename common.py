import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Type
import instructor

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TEMPERATURE = 1


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def get_instructor_client():
    """Initialize and return instructor-patched OpenAI client."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    client = OpenAI(api_key=OPENAI_API_KEY)
    return instructor.from_openai(client)


class P1Solution(BaseModel):
    """Solution for P1: 4-bit Carry-Lookahead Adder"""

    cla_module: str = Field(
        description="""Verilog module code. The module MUST be named 'cla_4bit' 
        with exact ports: input [3:0] A, input [3:0] B, input cin, 
        output [3:0] sum, output cout. Use structural implementation with 
        generate statements and full adder components."""
    )


class P2Solution(BaseModel):
    """Solution for P2: VGA Controller"""

    vga_controller_module: str = Field(
        description="""Verilog module code. The module MUST be named 'vga_controller' 
        with exact ports: input clk, input rst_n, output hsync, output vsync, 
        output video_on, output [9:0] pixel_x, output [9:0] pixel_y.
        640x480 @ 60Hz: horizontal period=800, vertical period=525."""
    )


class P3Solution(BaseModel):
    """Solution for P3: I2C Master Controller"""

    i2c_master_module: str = Field(
        description="""Verilog module code. The module MUST be named 'i2c_master' 
        with exact ports: input clk, input rst_n, input start, input [7:0] data_tx, 
        input rw, output [7:0] data_rx, output sda, output scl, output busy, output error.
        Support full I2C protocol: START, address+R/W, ACK, data bytes, STOP.
        Slave address 0x50, open-drain SDA/SCL outputs."""
    )


class P4Solution(BaseModel):
    """Solution for P4: AXI Stream FIFO"""

    axi_stream_fifo_module: str = Field(
        description="""Verilog module code. The module MUST be named 'axi_stream_fifo' 
        with exact ports: input clk, input rst_n, input s_valid, input s_ready, 
        input s_last, input [31:0] s_data, input [3:0] s_strb, output m_valid, 
        output m_ready, output m_last, output [31:0] m_data, output [3:0] m_strb,
        output [3:0] packet_count.
        AXI-Stream protocol with packet boundary tracking, 16 beat depth."""
    )


class P5Solution(BaseModel):
    """Solution for P5: AXI4 Full Master"""

    axi_master_module: str = Field(
        description="""Verilog module code. The module MUST be named 'axi_master' 
        with exact ports: input clk, rst_n, start, addr[31:0], wdata[31:0], size[1:0], 
        write_en, arready, awready, wready, bid, bresp, bvalid, rid, rdata_in, 
        rresp, rvalid; output rdata[31:0], valid, ready, arid, araddr, arvalid, 
        awid, awaddr, awvalid, wdata_out, wstrb, wvalid, bready, rready.
        Full AXI4 protocol with all 5 channels (AW,W,B,AR,R)."""
    )


SOLUTION_MODELS: Dict[str, Type[BaseModel]] = {
    "P1": P1Solution,
    "P2": P2Solution,
    "P3": P3Solution,
    "P4": P4Solution,
    "P5": P5Solution,
}


PROBLEMS = {
    "P1": {
        "name": "4-bit Carry-Lookahead Adder",
        "statement": """Design a 4-bit Carry-Lookahead Adder (CLA) in Verilog using structural modeling.

Requirements:
- Implement using full adders and carry lookahead logic
- Use generate statements for structural composition
- Input: two 4-bit operands (A[3:0], B[3:0])
- Input: cin (carry in)
- Output: sum[3:0] (4-bit sum)
- Output: cout (carry out)
- The adder should produce correct results for all 256 input combinations

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)

Deliverables:
- Structural Verilog module named 'cla_4bit' with the exact port list above
- Do not use behavioral modeling (no always @ blocks for combinational logic)
- Use proper hierarchical design with generate blocks""",
        "specs": {
            "port_list": "Input: A[3:0], B[3:0], cin; Output: sum[3:0], cout",
            "structural": "Uses generate statements, no behavioral always @ blocks",
            "all_combinations": "Correct for all 256 input combinations",
            "hierarchical": "Composed of full adder modules",
        },
        "success_criteria": [
            "Module compiles without errors",
            "Correct sum for random test vectors",
            "Correct carry out propagation",
        ],
        "difficulty": "easy",
        "difficulty_justification": "Textbook algorithm, small design space, well-defined structure",
    },
    "P2": {
        "name": "VGA Controller",
        "statement": """Design a VGA Controller for 640x480 resolution at 60Hz refresh in Verilog.

Requirements:
- Generate correct horizontal and vertical sync signals
- Input: clk (pixel clock - 25MHz or scaled equivalent)
- Input: rst_n (active-low asynchronous reset)
- Output: hsync (horizontal sync, active-low)
- Output: vsync (vertical sync, active-low)
- Output: video_on (active-high when in active video region)
- Output: pixel_x[9:0] (current x position, 0-639)
- Output: pixel_y[9:0] (current y position, 0-479)

Timing for 640x480@60Hz:
- Horizontal: 800 pixel clocks per line (including 656 blanking)
  - Active: 640 pixels
  - Front porch: 16
  - Sync pulse: 96  
  - Back porch: 48
- Vertical: 525 lines per frame
  - Active: 480 lines
  - Front porch: 10
  - Sync pulse: 2
  - Back porch: 33

Deliverables:
- Module named 'vga_controller' with exact ports above
- Correct sync pulse widths and positions
- Proper active video region timing
- Use scaled clock (1 cycle = 1 us) for simulation efficiency

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        "specs": {
            "port_list": "Input: clk, rst_n; Output: hsync, vsync, video_on, pixel_x[9:0], pixel_y[9:0]",
            "h_timing": "800 cycles per line (active=640, sync=96, porch=64)",
            "v_timing": "525 lines per frame (active=480, sync=2, porch=43)",
            "sync_polarity": "Both hsync and vsync active-low",
            "scaled_clock": "Uses 1MHz clock (1us per cycle) for simulation",
        },
        "success_criteria": [
            "Module compiles without errors",
            "HSYNC period = 800 cycles",
            "VSYNC period = 525 lines",
            "Active region positioned correctly (after sync pulses)",
            "video_on high only in active 640x480 region",
        ],
        "difficulty": "easy",
        "difficulty_justification": "Textbook video timing, well-documented timing parameters, straightforward counter design",
    },
    "P3": {
        "name": "I2C Master Controller",
        "statement": """Design a complete I2C Master Controller in Verilog supporting all standard I2C operations.

Requirements:
- Master initiates all transactions, slave device at 7-bit address 0x50 (EEPROM simulation)
- Input: clk (100MHz system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: start (pulse high to begin transaction)
- Input: [7:0] data_tx (byte to send to slave)
- Input: rw (0=write, 1=read)
- Output: [7:0] data_rx (byte received from slave)
- Output: sda (I2C data line)
- Output: scl (I2C clock line)
- Output: busy (high during transaction)
- Output: error (high on NACK or failure)

I2C Protocol Requirements:
- Generate START condition at beginning
- Send 7-bit slave address + R/W bit
- Wait for ACK from slave (check SDA during ACK bit)
- If write: send data byte, wait for ACK
- If read: receive byte, send ACK (except last byte sends NACK)
- Generate STOP condition at end
- Use clock stretching (wait for SCL high before proceeding)
- Open-drain outputs (SDA and SCL)

Deliverables:
- Module named 'i2c_master' with exact ports above
- Proper I2C START/STOP condition generation
- ACK/NACK detection and handling
- 100kHz SCL generation from 100MHz clock (divide by 1000)
- Error flag on NACK or bus fault

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        "specs": {
            "port_list": "Input: clk, rst_n, start, data_tx[7:0], rw; Output: data_rx[7:0], sda, scl, busy, error",
            "protocol": "Full I2C master (START, address, R/W, ACK, data, STOP)",
            "slave_addr": "0x50 (7-bit)",
            "clock_stretch": "Support clock stretching from slave",
            "ack_check": "Detect NACK and set error flag",
            "sda_scl_od": "Open-drain outputs for SDA and SCL",
        },
        "success_criteria": [
            "Module compiles without errors",
            "Correct START condition generation",
            "Correct 7-bit address + R/W transmission",
            "ACK/NACK detection working",
            "STOP condition at end of transaction",
            "Error flag set on NACK",
        ],
        "difficulty": "hard",
        "difficulty_justification": "Complex multi-state protocol, open-drain bus dynamics, ACK timing critical, clock stretching edge case",
    },
    "P4": {
        "name": "AXI Stream FIFO",
        "statement": """Design an AXI Stream FIFO with packet boundary tracking in Verilog.

Requirements:
- Implement a streaming FIFO with AXI-Stream protocol interfaces
- Input: clk (axis clock)
- Input: rst_n (active-low asynchronous reset)
- Input: s_valid (sender valid)
- Input: s_ready (sender ready - from downstream)
- Input: s_last (packet boundary - asserted on last beat of packet)
- Input: [31:0] s_data (input data)
- Input: s_strb (byte strobe, 4 bits)
- Output: m_valid (output valid)
- Output: m_ready (output ready - from upstream) 
- Output: m_last (output packet boundary)
- Output: [31:0] m_data (output data)
- Output: m_strb (byte strobe, 4 bits)
- Output: [3:0] packet_count (current packet length)

AXI-Stream Protocol Rules:
- Handshaking: valid AND ready must be high for data transfer
- When s_valid & s_ready: capture s_data, s_last, s_strb
- When m_valid & m_ready: release data to downstream
- packet_count tracks size of current packet (increment on each beat when s_valid & s_ready, reset on m_last & m_ready)
- Store up to 16 data beats
- Full when 16 entries, empty when 0 entries
- Must preserve packet boundaries (m_last aligned with last data beat)

Deliverables:
- Module named 'axi_stream_fifo' with exact ports above
- Proper AXI-Stream handshaking on both interfaces
- Packet boundary preservation (no splitting or merging packets)
- packet_count output accurate within packet
- Overflow protection (backpressure when full)
- Underflow prevention (m_valid low when empty)

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        "specs": {
            "port_list": "Input: clk, rst_n, s_valid, s_ready, s_last, s_data[31:0], s_strb[3:0]; Output: m_valid, m_ready, m_last, m_data[31:0], m_strb[3:0], packet_count[3:0]",
            "protocol": "AXI-Stream with packet boundaries",
            "depth": "16 beats",
            "handshake": "valid/ready on both interfaces",
            "packet_tracking": "Track and output packet size",
        },
        "success_criteria": [
            "Module compiles without errors",
            "AXI-Stream handshaking works both directions",
            "Packet boundaries preserved (no truncation)",
            "packet_count accurate",
            "No data loss on overflow",
            "No invalid data on underflow",
        ],
        "difficulty": "hard",
        "difficulty_justification": "Complex bidirectional handshaking, packet boundary state machine, dual-clock-domain-like coordination, edge case handling for backpressure",
    },
    "P5": {
        "name": "AXI4 Full Read/Write Master",
        "statement": """Design a complete AXI4 Full Master interface in Verilog for controlling external memory.

Requirements:
- Implement an AXI4 Full Master that can perform read and write transactions to memory-mapped devices
- Input: clk (AXI clock)
- Input: rst_n (active-low asynchronous reset)
- Input: start (pulse to initiate transaction)
- Input: [31:0] addr (transaction address, must be 32-bit aligned)
- Input: [31:0] wdata (write data)
- Input: [1:0] size (0=byte, 1=halfword, 2=word)
- Input: write_en (1=write, 0=read)
- Output: [31:0] rdata (read data)
- Output: valid (high when rdata is valid after read)
- Output: ready (high when ready for new transaction)
- Output: [3:0] arid (read address channel ID)
- Output: [31:0] araddr (read address)
- Output: arvalid (read address valid)
- Input: arready (read address ready)
- Output: [3:0] awid (write address channel ID)
- Output: [31:0] awaddr (write address)
- Output: awvalid (write address valid)
- Input: awready (write address ready)
- Output: [31:0] wdata_out (write data)
- Output: [3:0] wstrb (write strobe)
- Output: wvalid (write data valid)
- Input: wready (write data ready)
- Input: [3:0] bid (write response ID)
- Input: [1:0] bresp (write response)
- Input: bvalid (write response valid)
- Output: bready (write response ready)
- Input: [3:0] rid (read response ID)
- Input: [31:0] rdata_in (read data)
- Input: [1:0] rresp (read response)
- Input: rvalid (read data valid)
- Output: rready (read response ready)

AXI4 Requirements:
- Handle all 5 AXI channels (AW, W, B, AR, R) independently
- Generate unique IDs for each transaction
- Wrap bursts NOT required (use INCR only)
- Maximum burst length: 16 beats
- Handle backpressure on all channels
- Wait for write response before completing write transaction
- Wait for read data before completing read transaction
- Proper handshaking on all channels (valid/ready protocol)
- Support byte, halfword, and word accesses via size and wstrb

Deliverables:
- Module named 'axi_master' with exact ports above
- Independent state machines for AW/W/B and AR/R channels
- Proper AXI handshaking on all 5 channels
- ID tracking for outstanding transactions
- Error handling for DECERR (slave response)

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        "specs": {
            "port_list": "Input: clk, rst_n, start, addr[31:0], wdata[31:0], size[1:0], write_en, arready, awready, wready, bid[3:0], bresp[1:0], bvalid, rid[3:0], rdata_in[31:0], rresp[1:0], rvalid; Output: rdata[31:0], valid, ready, arid[3:0], araddr[31:0], arvalid, awid[3:0], awaddr[31:0], awvalid, wdata_out[31:0], wstrb[3:0], wvalid, bready, rready",
            "protocol": "AXI4 Full with 5 independent channels",
            "burst_type": "INCR only, max 16 beats",
            "handshake": "valid/ready on all channels",
            "error_handling": "Handle DECERR responses",
        },
        "success_criteria": [
            "Module compiles without errors",
            "AW/W channel handshaking works",
            "B channel response handling works",
            "AR/R channel handshaking works",
            "Write completes only after BVALID",
            "Read data captured after RVALID",
            "No deadlocks or livelocks",
        ],
        "difficulty": "hard",
        "difficulty_justification": "Extremely complex multi-channel protocol, independent state machines per channel, ID tracking for out-of-order capability, complex handshaking deadlock avoidance, full AXI4 compliance is industry-grade challenge",
    },
}


def build_problem_prompt(
    problem_id: str, include_tool: bool = False, tool_description: str = None
) -> str:
    """Build the prompt for a given problem."""
    if problem_id not in PROBLEMS:
        raise ValueError(f"Unknown problem: {problem_id}")

    problem = PROBLEMS[problem_id]

    prompt = f"""You are a Verilog engineer. Solve the following problem.

## Problem: {problem["name"]}

{problem["statement"]}

## Specifications:
"""
    for key, value in problem["specs"].items():
        prompt += f"- {key}: {value}\n"

    prompt += "\n## Success Criteria:\n"
    for criterion in problem["success_criteria"]:
        prompt += f"- {criterion}\n"

    if include_tool and tool_description:
        prompt += f"\n## Available Tool:\n{tool_description}\n"

    field_hints = {
        "P1": "Output JSON with field 'cla_module' containing the Verilog code. Module MUST be named 'cla_4bit'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P2": "Output JSON with field 'vga_controller_module' containing the Verilog code. Module MUST be named 'vga_controller'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P3": "Output JSON with field 'i2c_master_module' containing the Verilog code. Module MUST be named 'i2c_master'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P4": "Output JSON with field 'axi_stream_fifo_module' containing the Verilog code. Module MUST be named 'axi_stream_fifo'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P5": "Output JSON with field 'axi_master_module' containing the Verilog code. Module MUST be named 'axi_master'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
    }
    prompt += f"\n## Output Format:\n{field_hints[problem_id]}\n"

    return prompt


def get_problem_by_id(problem_id: str) -> Dict[str, Any]:
    """Get problem definition by ID."""
    return PROBLEMS.get(problem_id)
