import os
from dataclasses import dataclass
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


@dataclass
class Problem:
    """Container for a single problem definition."""

    id: str
    name: str
    statement: str
    specs: Dict[str, str]
    success_criteria: list
    difficulty: str
    family: str
    difficulty_justification: str


class FamilyA:
    """Family A: Sequential/Protocol Controllers with FSM-based interfaces."""

    P1 = Problem(
        id="P1",
        name="4-bit Carry-Lookahead Adder",
        statement="""Design a 4-bit Carry-Lookahead Adder (CLA) in Verilog using structural modeling.

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
        specs={
            "port_list": "Input: A[3:0], B[3:0], cin; Output: sum[3:0], cout",
            "structural": "Uses generate statements, no behavioral always @ blocks",
            "all_combinations": "Correct for all 256 input combinations",
            "hierarchical": "Composed of full adder modules",
        },
        success_criteria=[
            "Module compiles without errors",
            "Correct sum for random test vectors",
            "Correct carry out propagation",
        ],
        difficulty="easy",
        family="FamilyA",
        difficulty_justification="Textbook algorithm, small design space, well-defined structure",
    )

    P2 = Problem(
        id="P2",
        name="VGA Controller",
        statement="""Design a VGA Controller for 640x480 resolution at 60Hz refresh in Verilog.

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
        specs={
            "port_list": "Input: clk, rst_n; Output: hsync, vsync, video_on, pixel_x[9:0], pixel_y[9:0]",
            "h_timing": "800 cycles per line (active=640, sync=96, porch=64)",
            "v_timing": "525 lines per frame (active=480, sync=2, porch=43)",
            "sync_polarity": "Both hsync and vsync active-low",
            "scaled_clock": "Uses 1MHz clock (1us per cycle) for simulation",
        },
        success_criteria=[
            "Module compiles without errors",
            "HSYNC period = 800 cycles",
            "VSYNC period = 525 lines",
            "Active region positioned correctly (after sync pulses)",
            "video_on high only in active 640x480 region",
        ],
        difficulty="easy",
        family="FamilyA",
        difficulty_justification="Textbook video timing, well-documented timing parameters, straightforward counter design",
    )

    P3 = Problem(
        id="P3",
        name="I2C Master Controller",
        statement="""Design a complete I2C Master Controller in Verilog supporting all standard I2C operations.

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
        specs={
            "port_list": "Input: clk, rst_n, start, data_tx[7:0], rw; Output: data_rx[7:0], sda, scl, busy, error",
            "protocol": "Full I2C master (START, address, R/W, ACK, data, STOP)",
            "slave_addr": "0x50 (7-bit)",
            "clock_stretch": "Support clock stretching from slave",
            "ack_check": "Detect NACK and set error flag",
            "sda_scl_od": "Open-drain outputs for SDA and SCL",
        },
        success_criteria=[
            "Module compiles without errors",
            "Correct START condition generation",
            "Correct 7-bit address + R/W transmission",
            "ACK/NACK detection working",
            "STOP condition at end of transaction",
            "Error flag set on NACK",
        ],
        difficulty="hard",
        family="FamilyA",
        difficulty_justification="Complex multi-state protocol, open-drain bus dynamics, ACK timing critical, clock stretching edge case",
    )

    P4 = Problem(
        id="P4",
        name="AXI Stream FIFO",
        statement="""Design an AXI Stream FIFO with packet boundary tracking in Verilog.

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
        specs={
            "port_list": "Input: clk, rst_n, s_valid, s_ready, s_last, s_data[31:0], s_strb[3:0]; Output: m_valid, m_ready, m_last, m_data[31:0], m_strb[3:0], packet_count[3:0]",
            "protocol": "AXI-Stream with packet boundaries",
            "depth": "16 beats",
            "handshake": "valid/ready on both interfaces",
            "packet_tracking": "Track and output packet size",
        },
        success_criteria=[
            "Module compiles without errors",
            "AXI-Stream handshaking works both directions",
            "Packet boundaries preserved (no truncation)",
            "packet_count accurate",
            "No data loss on overflow",
            "No invalid data on underflow",
        ],
        difficulty="hard",
        family="FamilyA",
        difficulty_justification="Complex bidirectional handshaking, packet boundary state machine, dual-clock-domain-like coordination, edge case handling for backpressure",
    )

    P5 = Problem(
        id="P5",
        name="AXI4 Full Read/Write Master",
        statement="""Design a complete AXI4 Full Master interface in Verilog for controlling external memory.

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
        specs={
            "port_list": "Input: clk, rst_n, start, addr[31:0], wdata[31:0], size[1:0], write_en, arready, awready, wready, bid[3:0], bresp[1:0], bvalid, rid[3:0], rdata_in[31:0], rresp[1:0], rvalid; Output: rdata[31:0], valid, ready, arid[3:0], araddr[31:0], arvalid, awid[3:0], awaddr[31:0], awvalid, wdata_out[31:0], wstrb[3:0], wvalid, bready, rready",
            "protocol": "AXI4 Full with 5 independent channels",
            "burst_type": "INCR only, max 16 beats",
            "handshake": "valid/ready on all channels",
            "error_handling": "Handle DECERR responses",
        },
        success_criteria=[
            "Module compiles without errors",
            "AW/W channel handshaking works",
            "B channel response handling works",
            "AR/R channel handshaking works",
            "Write completes only after BVALID",
            "Read data captured after RVALID",
            "No deadlocks or livelocks",
        ],
        difficulty="hard",
        family="FamilyA",
        difficulty_justification="Extremely complex multi-channel protocol, independent state machines per channel, ID tracking for out-of-order capability, complex handshaking deadlock avoidance, full AXI4 compliance is industry-grade challenge",
    )


class FamilyB:
    """Family B: Control Systems with PWM and feedback loops."""

    P6 = Problem(
        id="P6",
        name="PWM Generator",
        statement="""Design a PWM (Pulse-Width Modulation) Generator in Verilog with configurable duty cycle.

Requirements:
- Generate PWM output at fixed frequency with variable duty cycle
- Input: clk (system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: [7:0] duty_cycle (0-255, maps to 0-100% duty cycle)
- Output: pwm_out (PWM output signal)
- Output: [7:0] period_count (current position in PWM period)

PWM Specifications:
- PWM frequency: 10 kHz (period = 100 clock cycles at 100MHz clk)
- duty_cycle = 0: 0% duty cycle (always low)
- duty_cycle = 255: 100% duty cycle (always high)
- Linear mapping from duty_cycle input to pulse width
- Active-high PWM output

Deliverables:
- Module named 'pwm_generator' with exact ports above
- Accurate duty cycle mapping (duty_cycle[7:0] / 255 * period)
- Clean PWM output (no glitches)
- period_count output for testing

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        specs={
            "port_list": "Input: clk, rst_n, duty_cycle[7:0]; Output: pwm_out, period_count[7:0]",
            "frequency": "10 kHz PWM (100 clock cycles per period)",
            "duty_mapping": "duty_cycle / 255 * 100 percent",
            "polarity": "Active-high PWM output",
        },
        success_criteria=[
            "Module compiles without errors",
            "PWM frequency accurate (100 cycles per period)",
            "0% duty cycle when duty_cycle=0",
            "100% duty cycle when duty_cycle=255",
            "Linear duty cycle scaling",
        ],
        difficulty="easy",
        family="FamilyB",
        difficulty_justification="Simple counter-based PWM, straightforward mapping from input to output pulse width",
    )

    P7 = Problem(
        id="P7",
        name="Motor Speed Controller",
        statement="""Design a Motor Speed Controller with closed-loop feedback in Verilog.

Requirements:
- Implement proportional closed-loop speed control
- Input: clk (system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: [7:0] target_speed (desired speed, 0-255)
- Input: [7:0] actual_speed (feedback from encoder, 0-255)
- Output: [7:0] pwm_duty (PWM duty cycle command)
- Output: [15:0] error (signed error for debugging)

Control Algorithm (Proportional):
- error = target_speed - actual_speed
- pwm_duty = error * Kp (where Kp = 1, saturated to 0-255)
- If target_speed > actual_speed: increase duty
- If target_speed < actual_speed: decrease duty

Deliverables:
- Module named 'motor_controller' with exact ports above
- Accurate proportional control
- Error calculation output for verification
- Proper saturation (no overflow)

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        specs={
            "port_list": "Input: clk, rst_n, target_speed[7:0], actual_speed[7:0]; Output: pwm_duty[7:0], error[15:0]",
            "control": "Proportional control (Kp=1)",
            "error_calc": "target_speed - actual_speed (signed 16-bit)",
            "saturation": "pwm_duty clamped to 0-255",
            "frequency": "Update every cycle",
        },
        success_criteria=[
            "Module compiles without errors",
            "Correct error calculation",
            "pwm_duty increases when target > actual",
            "pwm_duty decreases when target < actual",
            "No overflow in error calculation",
        ],
        difficulty="easy",
        family="FamilyB",
        difficulty_justification="Simple proportional control with signed arithmetic, straightforward error calculation",
    )

    P8 = Problem(
        id="P8",
        name="Quadrature Encoder Interface",
        statement="""Design a Quadrature Encoder Interface in Verilog for position and velocity tracking.

Requirements:
- Decode quadrature signals (A and B phases) to determine position and direction
- Input: clk (system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: enc_a (encoder phase A)
- Input: enc_b (encoder phase B)
- Output: [15:0] position (cumulative position count)
- Output: direction (0=counterclockwise, 1=clockwise)
- Output: [15:0] velocity (position change per 1000 cycles)

Quadrature Decoding Rules:
- A leads B: clockwise (direction = 1), increment position
- B leads A: counterclockwise (direction = 0), decrement position
- Same state: no change
- Debounce: require stable signal for 2 cycles

Deliverables:
- Module named 'quadrature_encoder' with exact ports above
- Accurate position tracking
- Direction detection from phase relationship
- Velocity calculation (position delta per 1000 cycles)

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        specs={
            "port_list": "Input: clk, rst_n, enc_a, enc_b; Output: position[15:0], direction, velocity[15:0]",
            "decoding": "A leads B = clockwise, B leads A = CCW",
            "debounce": "2-cycle stability requirement",
            "velocity": "Position delta per 1000 cycles",
            "range": "16-bit position (-32768 to 32767)",
        },
        success_criteria=[
            "Module compiles without errors",
            "Increment position when A leads B",
            "Decrement position when B leads A",
            "Correct direction output",
            "Velocity tracking accurate",
        ],
        difficulty="medium",
        family="FamilyB",
        difficulty_justification="FSM for phase detection, velocity calculation requires averaging over time window",
    )

    P9 = Problem(
        id="P9",
        name="PID Controller",
        statement="""Design a PID (Proportional-Integral-Derivative) Controller in Verilog.

Requirements:
- Implement full PID control algorithm
- Input: clk (system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: [15:0] setpoint (desired value)
- Input: [15:0] feedback (measured value)
- Input: enable (1 = controller active)
- Output: [15:0] control_output (PID output)
- Output: [15:0] error (current error = setpoint - feedback)
- Output: [15:0] p_term (proportional component)
- Output: [15:0] i_term (integral component)
- Output: [15:0] d_term (derivative component)

PID Parameters:
- Kp (proportional gain) = 1
- Ki (integral gain) = 0.1 (scaled: 1/10)
- Kd (derivative gain) = 0.5 (scaled: 1/2)
- Integral saturation: limit to prevent windup
- Derivative: use previous error

Control Law:
- P = Kp * error
- I = I + Ki * error (accumulated)
- D = Kd * (error - prev_error)
- output = P + I + D (saturated to 16-bit)

Deliverables:
- Module named 'pid_controller' with exact ports above
- Correct PID algorithm implementation
- Integral windup protection
- Derivative with previous error

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        specs={
            "port_list": "Input: clk, rst_n, setpoint[15:0], feedback[15:0], enable; Output: control_output[15:0], error[15:0], p_term[15:0], i_term[15:0], d_term[15:0]",
            "kp": "1 (1/1)",
            "ki": "0.1 (1/10 scaled)",
            "kd": "0.5 (1/2 scaled)",
            "integral_saturation": "Limit accumulated integral",
            "derivative": "Uses previous error",
        },
        success_criteria=[
            "Module compiles without errors",
            "P term = Kp * error",
            "I term accumulates with Ki * error",
            "D term = Kd * (error - prev_error)",
            "No integral windup",
            "Output saturated properly",
        ],
        difficulty="hard",
        family="FamilyB",
        difficulty_justification="Complex control algorithm with multiple state variables (P, I, D terms), careful scaling and saturation",
    )

    P10 = Problem(
        id="P10",
        name="Servo Position Controller",
        statement="""Design a complete Servo Position Controller integrating PWM, encoder feedback, and PID control.

Requirements:
- Closed-loop position control for servo motor
- Input: clk (system clock)
- Input: rst_n (active-low asynchronous reset)
- Input: [15:0] target_position (desired position)
- Input: enc_a (quadrature encoder A)
- Input: enc_b (quadrature encoder B)
- Output: pwm_out (PWM to motor driver)
- Output: [15:0] actual_position (current position from encoder)
- Output: [15:0] control_signal (PID output)

System Integration:
- Quadrature decoder for position measurement (like P8)
- PID controller for error correction (like P9)
- PWM generator for motor command (like P6)
- All subsystems integrated

Deliverables:
- Module named 'servo_controller' with exact ports above
- Position feedback from encoder
- PID control output
- PWM command to motor
- Complete closed-loop operation

IMPORTANT: Use Verilog-2005 (NOT SystemVerilog). Do NOT use:
- SystemVerilog types (int, logic, bit, etc.)
- Unsized literals ('0, '1, 'hFF, etc.) - always specify full width
- localparam without assignment
- Use 'width'hvalue format (e.g., 8'h0, not '0)""",
        specs={
            "port_list": "Input: clk, rst_n, target_position[15:0], enc_a, enc_b; Output: pwm_out, actual_position[15:0], control_signal[15:0]",
            "encoder": "Quadrature decoder for position",
            "pid": "Full PID control",
            "pwm": "10kHz PWM output",
            "integration": "Encoder + PID + PWM",
        },
        success_criteria=[
            "Module compiles without errors",
            "Position tracking from encoder",
            "PID generates correct control signal",
            "PWM follows PID output",
            "Closed-loop convergence",
        ],
        difficulty="hard",
        family="FamilyB",
        difficulty_justification="Multi-subsystem integration (encoder + PID + PWM), requires coordinating all subsystems correctly",
    )


class Problems:
    """Nested namespace for accessing problems by family."""

    FamilyA = FamilyA
    FamilyB = FamilyB

    @staticmethod
    def get(problem_id: str) -> Problem:
        """Get problem by ID from any family."""
        all_problems = [
            FamilyA.P1,
            FamilyA.P2,
            FamilyA.P3,
            FamilyA.P4,
            FamilyA.P5,
            FamilyB.P6,
            FamilyB.P7,
            FamilyB.P8,
            FamilyB.P9,
            FamilyB.P10,
        ]
        for problem in all_problems:
            if problem.id == problem_id:
                return problem
        raise ValueError(f"Unknown problem: {problem_id}")


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


class P6Solution(BaseModel):
    """Solution for P6: PWM Generator"""

    pwm_generator_module: str = Field(
        description="""Verilog module code. The module MUST be named 'pwm_generator'
        with exact ports: input clk, input rst_n, input [7:0] duty_cycle,
        output pwm_out, output [7:0] period_count.
        PWM frequency: 10kHz (100 clock cycles per period), 0-100% duty cycle."""
    )


class P7Solution(BaseModel):
    """Solution for P7: Motor Speed Controller"""

    motor_controller_module: str = Field(
        description="""Verilog module code. The module MUST be named 'motor_controller'
        with exact ports: input clk, input rst_n, input [7:0] target_speed,
        input [7:0] actual_speed, output [7:0] pwm_duty, output [15:0] error.
        Proportional control: pwm_duty = target_speed - actual_speed."""
    )


class P8Solution(BaseModel):
    """Solution for P8: Quadrature Encoder Interface"""

    quadrature_encoder_module: str = Field(
        description="""Verilog module code. The module MUST be named 'quadrature_encoder'
        with exact ports: input clk, input rst_n, input enc_a, input enc_b,
        output [15:0] position, output direction, output [15:0] velocity.
        A leads B = clockwise, B leads A = counterclockwise."""
    )


class P9Solution(BaseModel):
    """Solution for P9: PID Controller"""

    pid_controller_module: str = Field(
        description="""Verilog module code. The module MUST be named 'pid_controller'
        with exact ports: input clk, input rst_n, input [15:0] setpoint,
        input [15:0] feedback, input enable, output [15:0] control_output,
        output [15:0] error, output [15:0] p_term, output [15:0] i_term,
        output [15:0] d_term.
        Full PID with Kp=1, Ki=0.1, Kd=0.5."""
    )


class P10Solution(BaseModel):
    """Solution for P10: Servo Position Controller"""

    servo_controller_module: str = Field(
        description="""Verilog module code. The module MUST be named 'servo_controller'
        with exact ports: input clk, input rst_n, input [15:0] target_position,
        input enc_a, input enc_b, output pwm_out, output [15:0] actual_position,
        output [15:0] control_signal.
        Integrates encoder (P8) + PID (P9) + PWM (P6)."""
    )


SOLUTION_MODELS: Dict[str, Type[BaseModel]] = {
    "P1": P1Solution,
    "P2": P2Solution,
    "P3": P3Solution,
    "P4": P4Solution,
    "P5": P5Solution,
    "P6": P6Solution,
    "P7": P7Solution,
    "P8": P8Solution,
    "P9": P9Solution,
    "P10": P10Solution,
}


PROBLEMS: Dict[str, Dict[str, Any]] = {
    pid: {
        "name": Problems.get(pid).name,
        "statement": Problems.get(pid).statement,
        "specs": Problems.get(pid).specs,
        "success_criteria": Problems.get(pid).success_criteria,
        "difficulty": Problems.get(pid).difficulty,
        "difficulty_justification": Problems.get(pid).difficulty_justification,
    }
    for pid in [f"P{i}" for i in range(1, 11)]
}


def build_problem_prompt(
    problem_id: str, include_tool: bool = False, tool_description: str = None
) -> str:
    """Build the prompt for a given problem."""
    problem = Problems.get(problem_id)

    prompt = f"""You are a Verilog engineer. Solve the following problem.

## Problem: {problem.name}

{problem.statement}

## Specifications:
"""
    for key, value in problem.specs.items():
        prompt += f"- {key}: {value}\n"

    prompt += "\n## Success Criteria:\n"
    for criterion in problem.success_criteria:
        prompt += f"- {criterion}\n"

    if include_tool and tool_description:
        prompt += f"\n## Available Tool:\n{tool_description}\n"

    field_hints = {
        "P1": "Output JSON with field 'cla_module' containing the Verilog code. Module MUST be named 'cla_4bit'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P2": "Output JSON with field 'vga_controller_module' containing the Verilog code. Module MUST be named 'vga_controller'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P3": "Output JSON with field 'i2c_master_module' containing the Verilog code. Module MUST be named 'i2c_master'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P4": "Output JSON with field 'axi_stream_fifo_module' containing the Verilog code. Module MUST be named 'axi_stream_fifo'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P5": "Output JSON with field 'axi_master_module' containing the Verilog code. Module MUST be named 'axi_master'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P6": "Output JSON with field 'pwm_generator_module' containing the Verilog code. Module MUST be named 'pwm_generator'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P7": "Output JSON with field 'motor_controller_module' containing the Verilog code. Module MUST be named 'motor_controller'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P8": "Output JSON with field 'quadrature_encoder_module' containing the Verilog code. Module MUST be named 'quadrature_encoder'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P9": "Output JSON with field 'pid_controller_module' containing the Verilog code. Module MUST be named 'pid_controller'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
        "P10": "Output JSON with field 'servo_controller_module' containing the Verilog code. Module MUST be named 'servo_controller'. Use Verilog-2005 only - no SystemVerilog types or unsized literals.",
    }
    prompt += f"\n## Output Format:\n{field_hints[problem_id]}\n"

    return prompt


def get_problem_by_id(problem_id: str) -> Dict[str, Any]:
    """Get problem definition by ID."""
    problem = Problems.get(problem_id)
    return {
        "name": problem.name,
        "statement": problem.statement,
        "specs": problem.specs,
        "success_criteria": problem.success_criteria,
        "difficulty": problem.difficulty,
        "difficulty_justification": problem.difficulty_justification,
        "family": problem.family,
    }
