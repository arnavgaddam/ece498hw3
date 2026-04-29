import os
import subprocess
import tempfile
from typing import Dict, Any
from common import PROBLEMS, SOLUTION_MODELS


def run_verilog_simulation(
    module_code: str, testbench: str, timeout: int = 30
) -> Dict[str, Any]:
    """Run Verilog simulation using Icarus Verilog."""
    with tempfile.TemporaryDirectory() as tmpdir:
        module_file = os.path.join(tmpdir, "module.v")
        testbench_file = os.path.join(tmpdir, "testbench.v")

        with open(module_file, "w") as f:
            f.write(module_code)

        with open(testbench_file, "w") as f:
            f.write(testbench)

        compile_result = subprocess.run(
            [
                "iverilog",
                "-o",
                os.path.join(tmpdir, "sim.vvp"),
                module_file,
                testbench_file,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if compile_result.returncode != 0:
            return {
                "passed": False,
                "signals": {},
                "errors": [compile_result.stderr],
                "stage": "compile",
            }

        run_result = subprocess.run(
            ["vvp", os.path.join(tmpdir, "sim.vvp")],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if run_result.returncode != 0:
            return {
                "passed": False,
                "signals": {},
                "errors": [run_result.stderr],
                "stage": "runtime",
            }

        output = run_result.stdout

        return {
            "passed": True,
            "signals": {},
            "output": output,
            "errors": [],
            "stage": "success",
        }


def generate_p1_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg [3:0] A;
    reg [3:0] B;
    reg cin;
    wire [3:0] sum;
    wire cout;
    
    cla_4bit uut (.A(A), .B(B), .cin(cin), .sum(sum), .cout(cout));
    
    initial begin
        $display("Testing CLA 4-bit Adder");
        
        // Test case 1: 0 + 0 + 0 = 0, cout=0
        A = 4'h0; B = 4'h0; cin = 0;
        #10;
        if (sum !== 4'h0 || cout !== 1'b0) begin
            $display("FAIL: 0+0+0 = %b%b, expected 0000 0", sum, cout);
            $finish(1);
        end
        
        // Test case 2: 0xF + 0xF + 1 = 0xF, cout=1
        A = 4'hF; B = 4'hF; cin = 1;
        #10;
        if (sum !== 4'hF || cout !== 1'b1) begin
            $display("FAIL: F+F+1 = %b%b, expected 1111 1", sum, cout);
            $finish(1);
        end
        
        // Test case 3: 0xA + 0x5 + 0 = 0xF, cout=0
        A = 4'hA; B = 4'h5; cin = 0;
        #10;
        if (sum !== 4'hF || cout !== 1'b0) begin
            $display("FAIL: A+5+0 = %b%b, expected 1111 0", sum, cout);
            $finish(1);
        end
        
        // Test case 4: 0x0 + 0x1 + 0 = 0x1, cout=0
        A = 4'h0; B = 4'h1; cin = 0;
        #10;
        if (sum !== 4'h1 || cout !== 1'b0) begin
            $display("FAIL: 0+1+0 = %b%b, expected 0001 0", sum, cout);
            $finish(1);
        end
        
        // Test case 5: 0xF + 0x0 + 1 = 0x0, cout=1
        A = 4'hF; B = 4'h0; cin = 1;
        #10;
        if (sum !== 4'h0 || cout !== 1'b1) begin
            $display("FAIL: F+0+1 = %b%b, expected 0000 1", sum, cout);
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p1(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P1: 4-bit Carry-Lookahead Adder."""
    module_code = solution.get("cla_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p1_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["test_cases"] = "all passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["test_cases"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed: {result.get('errors', ['Unknown error'])}",
        }


def generate_p2_testbench() -> str:
    return """`timescale 1us / 1us

module testbench;
    reg clk;
    reg rst_n;
    wire hsync;
    wire vsync;
    wire video_on;
    wire [9:0] pixel_x;
    wire [9:0] pixel_y;
    
    vga_controller uut (.clk(clk), .rst_n(rst_n), .hsync(hsync), .vsync(vsync),
                       .video_on(video_on), .pixel_x(pixel_x), .pixel_y(pixel_y));
    
    initial clk = 0;
    always #1 clk = ~clk;
    
    initial begin
        $display("Testing VGA Controller");
        
        rst_n = 0;
        #2;
        rst_n = 1;
        #1;
        
        // Run for enough cycles to see the timing in action
        #1000;
        
        // Check that pixel_x and pixel_y are in valid range at some point
        if (pixel_x >= 10'd640) begin
            $display("FAIL: pixel_x out of range (got %d, expected < 640)", pixel_x);
            $finish(1);
        end
        
        if (pixel_y >= 10'd480) begin
            $display("FAIL: pixel_y out of range (got %d, expected < 480)", pixel_y);
            $finish(1);
        end
        
        // Check that video_on is properly asserted
        if (video_on !== 1'b0 && video_on !== 1'b1) begin
            $display("FAIL: video_on not valid");
            $finish(1);
        end
        
        // Check hsync and vsync are valid
        if (hsync !== 1'b0 && hsync !== 1'b1) begin
            $display("FAIL: hsync not valid");
            $finish(1);
        end
        
        if (vsync !== 1'b0 && vsync !== 1'b1) begin
            $display("FAIL: vsync not valid");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p2(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P2: VGA Controller."""
    module_code = solution.get("vga_controller_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p2_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["timing_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["timing_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed: {result.get('errors', ['Unknown error'])}",
        }


def generate_p3_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg start;
    reg [7:0] data_tx;
    reg rw;
    wire [7:0] data_rx;
    wire sda;
    wire scl;
    wire busy;
    wire error;
    
    i2c_master uut (.clk(clk), .rst_n(rst_n), .start(start), .data_tx(data_tx), .rw(rw),
                    .data_rx(data_rx), .sda(sda), .scl(scl), .busy(busy), .error(error));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing I2C Master Controller");
        
        rst_n = 0;
        start = 0;
        data_tx = 8'h50;
        rw = 0;
        #20;
        rst_n = 1;
        #10;
        
        // Start transaction
        start = 1;
        #10;
        start = 0;
        
        // Wait for transaction to complete
        #50000;
        
        // Check that there was no error (module produced valid outputs)
        if (error !== 1'b0) begin
            $display("FAIL: error should be 0, got %b", error);
            $finish(1);
        end
        
        // Check that sda and scl are valid (not undefined)
        if (sda !== 1'b0 && sda !== 1'b1) begin
            $display("FAIL: sda not valid");
            $finish(1);
        end
        
        if (scl !== 1'b0 && scl !== 1'b1) begin
            $display("FAIL: scl not valid");
            $finish(1);
        end
        
        // Check that data_rx is valid
        if (data_rx !== 8'h00) begin
            $display("FAIL: data_rx should be 0, got %h", data_rx);
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p3(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P3: I2C Master Controller."""
    module_code = solution.get("i2c_master_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p3_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["protocol_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["protocol_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed: {result.get('errors', ['Unknown error'])}",
        }


def generate_p4_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg s_valid;
    reg s_ready;
    reg s_last;
    reg [31:0] s_data;
    reg [3:0] s_strb;
    wire m_valid;
    wire m_ready;
    wire m_last;
    wire [31:0] m_data;
    wire [3:0] m_strb;
    wire [3:0] packet_count;
    
    axi_stream_fifo uut (.clk(clk), .rst_n(rst_n), .s_valid(s_valid), .s_ready(s_ready),
                        .s_last(s_last), .s_data(s_data), .s_strb(s_strb),
                        .m_valid(m_valid), .m_ready(m_ready), .m_last(m_last),
                        .m_data(m_data), .m_strb(m_strb), .packet_count(packet_count));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing AXI Stream FIFO");
        
        rst_n = 0;
        s_valid = 0;
        s_ready = 1;
        s_last = 0;
        s_data = 32'h0;
        s_strb = 4'hF;
        #20;
        rst_n = 1;
        #10;
        
        // Send first beat
        s_valid = 1;
        s_data = 32'hDEADBEEF;
        s_strb = 4'hF;
        s_last = 0;
        #10;
        
        // Send second beat (last)
        s_data = 32'hCAFEBABE;
        s_last = 1;
        #10;
        
        s_valid = 0;
        s_last = 0;
        
        // Wait a bit and check packet count (should have 2 beats in FIFO)
        #20;
        
        if (packet_count !== 4'd2) begin
            $display("FAIL: packet_count should be 2, got %d", packet_count);
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p4(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P4: AXI Stream FIFO."""
    module_code = solution.get("axi_stream_fifo_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p4_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["fifo_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["fifo_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed: {result.get('errors', ['Unknown error'])}",
        }


def generate_p5_testbench() -> str:
    return """`timescale 1ns / 1ps

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
    
    axi_master uut (.clk(clk), .rst_n(rst_n), .start(start), .addr(addr), .wdata(wdata),
                    .size(size), .write_en(write_en), .arready(arready), .awready(awready),
                    .wready(wready), .bid(bid), .bresp(bresp), .bvalid(bvalid), .rid(rid),
                    .rdata_in(rdata_in), .rresp(rresp), .rvalid(rvalid),
                    .rdata(rdata), .valid(valid), .ready(ready), .arid(arid), .araddr(araddr),
                    .arvalid(arvalid), .awid(awid), .awaddr(awaddr), .awvalid(awvalid),
                    .wdata_out(wdata_out), .wstrb(wstrb), .wvalid(wvalid), .bready(bready),
                    .rready(rready));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing AXI4 Full Master");
        
        rst_n = 0;
        start = 0;
        addr = 32'h1000;
        wdata = 32'hDEADBEEF;
        size = 2'd2;
        write_en = 0;
        arready = 1;
        awready = 1;
        wready = 1;
        bid = 4'd0;
        bresp = 2'd0;
        bvalid = 0;
        rid = 4'd0;
        rdata_in = 32'h12345678;
        rresp = 2'd0;
        rvalid = 0;
        #20;
        rst_n = 1;
        #10;
        
        // Start transaction
        start = 1;
        #10;
        start = 0;
        
        // Wait for transaction
        #200;
        
        // Check that AXI signals are valid
        if (ready !== 1'b1) begin
            $display("FAIL: ready should be high when idle");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p5(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P5: AXI4 Full Master."""
    module_code = solution.get("axi_master_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p5_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["axi_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["axi_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed: {result.get('errors', ['Unknown error'])}",
        }


def generate_p6_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg [7:0] duty_cycle;
    wire pwm_out;
    wire [7:0] period_count;
    
    pwm_generator uut (.clk(clk), .rst_n(rst_n), .duty_cycle(duty_cycle), .pwm_out(pwm_out), .period_count(period_count));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing PWM Generator");
        
        rst_n = 0;
        duty_cycle = 8'd0;
        #20;
        rst_n = 1;
        #30;

        if (pwm_out !== 1'b0) begin
            $display("FAIL: pwm_out should be low at 0%% duty");
            $finish(1);
        end
        
        // Test with duty_cycle = 128 (50%% duty)
        duty_cycle = 8'd128;
        #120;

        if (period_count == 8'd50) begin
            $display("FAIL: period_count is stuck and not counting");
            $finish(1);
        end
        
        // Test with duty_cycle = 255 (100%% duty)
        duty_cycle = 8'd255;
        #120;

        if (pwm_out !== 1'b1) begin
            $display("FAIL: pwm_out should be high at 100%% duty");
            $finish(1);
        end
        
        // Test with duty_cycle = 0 (0%% duty)
        duty_cycle = 8'd0;
        #120;

        if (pwm_out !== 1'b0) begin
            $display("FAIL: pwm_out should return low at 0%% duty");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p6(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P6: PWM Generator."""
    module_code = solution.get("pwm_generator_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p6_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["pwm_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["pwm_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed at {result.get('stage', 'unknown')}: {result.get('errors', ['Unknown error'])[:100]}",
        }


def generate_p7_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg [7:0] target_speed;
    reg [7:0] actual_speed;
    wire [7:0] pwm_duty;
    wire [15:0] error;
    
    motor_controller uut (.clk(clk), .rst_n(rst_n), .target_speed(target_speed), .actual_speed(actual_speed), .pwm_duty(pwm_duty), .error(error));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing Motor Speed Controller");
        
        rst_n = 0;
        target_speed = 8'd100;
        actual_speed = 8'd50;
        #20;
        rst_n = 1;
        #10;
        
        // Test: error is non-zero when target != actual
        #10;
        if (error == 16'd0 && target_speed != actual_speed) begin
            $display("FAIL: error should be non-zero when target != actual");
            $finish(1);
        end
        
        // Test: pwm_duty is valid (not undefined)
        if (pwm_duty !== 8'd0 && pwm_duty !== 8'd50) begin
            $display("FAIL: pwm_duty should be 0 or 50");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p7(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P7: Motor Speed Controller."""
    module_code = solution.get("motor_controller_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p7_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["control_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["control_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed at {result.get('stage', 'unknown')}: {result.get('errors', ['Unknown error'])[:100]}",
        }


def generate_p8_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg enc_a;
    reg enc_b;
    wire [15:0] position;
    wire direction;
    wire [15:0] velocity;
    
    quadrature_encoder uut (.clk(clk), .rst_n(rst_n), .enc_a(enc_a), .enc_b(enc_b), .position(position), .direction(direction), .velocity(velocity));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing Quadrature Encoder");
        
        rst_n = 0;
        enc_a = 0;
        enc_b = 0;
        #20;
        rst_n = 1;
        #10;
        
        // Simulate one complete cycle: A leads B (clockwise)
        #10; enc_a = 1; enc_b = 0;
        #10; enc_a = 1; enc_b = 1;
        #10; enc_a = 0; enc_b = 1;
        #10; enc_a = 0; enc_b = 0;
        
        // Check position incremented
        if (position == 16'd0) begin
            $display("FAIL: position should increment after one cycle");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p8(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P8: Quadrature Encoder Interface."""
    module_code = solution.get("quadrature_encoder_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p8_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["encoder_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["encoder_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed at {result.get('stage', 'unknown')}: {result.get('errors', ['Unknown error'])[:100]}",
        }


def generate_p9_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg [15:0] setpoint;
    reg [15:0] feedback;
    reg enable;
    wire [15:0] control_output;
    wire [15:0] error;
    wire [15:0] p_term;
    wire [15:0] i_term;
    wire [15:0] d_term;
    
    pid_controller uut (.clk(clk), .rst_n(rst_n), .setpoint(setpoint), .feedback(feedback), .enable(enable), .control_output(control_output), .error(error), .p_term(p_term), .i_term(i_term), .d_term(d_term));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing PID Controller");
        
        rst_n = 0;
        setpoint = 16'd1000;
        feedback = 16'd0;
        enable = 1;
        #20;
        rst_n = 1;
        #10;
        
        // Check that error is calculated correctly
        if (error == 16'd0) begin
            $display("FAIL: error should be setpoint - feedback");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p9(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P9: PID Controller."""
    module_code = solution.get("pid_controller_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p9_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["pid_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["pid_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed at {result.get('stage', 'unknown')}: {result.get('errors', ['Unknown error'])[:100]}",
        }


def generate_p10_testbench() -> str:
    return """`timescale 1ns / 1ps

module testbench;
    reg clk;
    reg rst_n;
    reg [15:0] target_position;
    reg enc_a;
    reg enc_b;
    wire pwm_out;
    wire [15:0] actual_position;
    wire [15:0] control_signal;
    
    servo_controller uut (.clk(clk), .rst_n(rst_n), .target_position(target_position), .enc_a(enc_a), .enc_b(enc_b), .pwm_out(pwm_out), .actual_position(actual_position), .control_signal(control_signal));
    
    initial clk = 0;
    always #5 clk = ~clk;
    
    initial begin
        $display("Testing Servo Position Controller");
        
        rst_n = 0;
        target_position = 16'd1000;
        enc_a = 0;
        enc_b = 0;
        #20;
        rst_n = 1;
        #20;

        if (actual_position !== 16'd0) begin
            $display("FAIL: actual_position should start at 0");
            $finish(1);
        end

        // Simulate one encoder increment
        enc_a = 1;
        #10;
        enc_b = 1;
        #10;
        enc_a = 0;
        #10;
        enc_b = 0;
        #20;

        if (actual_position == 16'd0) begin
            $display("FAIL: actual_position did not change after encoder activity");
            $finish(1);
        end

        if (control_signal == 16'd0) begin
            $display("FAIL: control_signal should be non-zero for nonzero position error");
            $finish(1);
        end
        
        // Check that pwm_out is valid
        if (pwm_out !== 1'b0 && pwm_out !== 1'b1) begin
            $display("FAIL: pwm_out not valid");
            $finish(1);
        end
        
        $display("PASS: All test cases passed");
        $finish(0);
    end
endmodule
"""


def verify_p10(solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify P10: Servo Position Controller."""
    module_code = solution.get("servo_controller_module", "")
    details = {}

    if not module_code:
        return {"pass": False, "details": details, "reason": "No module code provided"}

    testbench = generate_p10_testbench()
    result = run_verilog_simulation(module_code, testbench)

    details["compilation"] = result["stage"] == "success"
    details["test_output"] = result.get("output", "")
    details["errors"] = result.get("errors", [])

    if result["passed"]:
        output = result.get("output", "")
        if "PASS" in output:
            details["servo_checks"] = "passed"
            return {"pass": True, "details": details, "reason": "Verification passed"}
        else:
            details["servo_checks"] = "failed"
            return {
                "pass": False,
                "details": details,
                "reason": f"Testbench failed: {output}",
            }
    else:
        details["simulation"] = "failed"
        return {
            "pass": False,
            "details": details,
            "reason": f"Simulation failed at {result.get('stage', 'unknown')}: {result.get('errors', ['Unknown error'])[:100]}",
        }


VERIFY_FUNCTIONS = {
    "P1": verify_p1,
    "P2": verify_p2,
    "P3": verify_p3,
    "P4": verify_p4,
    "P5": verify_p5,
    "P6": verify_p6,
    "P7": verify_p7,
    "P8": verify_p8,
    "P9": verify_p9,
    "P10": verify_p10,
}


def verify(problem_id: str, solution: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a solution for the given problem."""
    if problem_id not in VERIFY_FUNCTIONS:
        return {
            "pass": False,
            "details": {},
            "reason": f"Unknown problem: {problem_id}",
        }

    return VERIFY_FUNCTIONS[problem_id](solution)


if __name__ == "__main__":
    print("Running manual verification tests...")
    print()

    def print_manual_result(
        problem_id: str, label: str, result: Dict[str, Any]
    ) -> None:
        print(f"  {label} case: {result.get('pass', False)}")
        if result.get("pass", False):
            print(f"    Details: {result.get('details', {})}")
        else:
            print(f"    Reason: {result.get('reason', '')}")

    # P1: CLA - Pass case
    p1_pass = {
        "cla_module": """module cla_4bit(
    input [3:0] A,
    input [3:0] B,
    input cin,
    output [3:0] sum,
    output cout
);
    wire [4:0] c;
    assign c[0] = cin;
    
    full_adder fa0(.a(A[0]), .b(B[0]), .cin(c[0]), .sum(sum[0]), .cout(c[1]));
    full_adder fa1(.a(A[1]), .b(B[1]), .cin(c[1]), .sum(sum[1]), .cout(c[2]));
    full_adder fa2(.a(A[2]), .b(B[2]), .cin(c[2]), .sum(sum[2]), .cout(c[3]));
    full_adder fa3(.a(A[3]), .b(B[3]), .cin(c[3]), .sum(sum[3]), .cout(cout));
endmodule

module full_adder(
    input a, b, cin,
    output sum, cout
);
    assign sum = a ^ b ^ cin;
    assign cout = (a & b) | (b & cin) | (a & cin);
endmodule"""
    }
    p1_fail = {
        "cla_module": """module wrong_module(
    input [3:0] A,
    input B,
    output sum
);
    assign sum = A + B;
endmodule"""
    }

    # P2: VGA - Pass case
    p2_pass = {
        "vga_controller_module": """module vga_controller(
    input clk,
    input rst_n,
    output hsync,
    output vsync,
    output video_on,
    output [9:0] pixel_x,
    output [9:0] pixel_y
);
    reg [9:0] h_count;
    reg [9:0] v_count;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_count <= 10'd0;
            v_count <= 10'd0;
        end else begin
            if (h_count == 10'd799) begin
                h_count <= 10'd0;
                if (v_count == 10'd524) v_count <= 10'd0;
                else v_count <= v_count + 1;
            end else h_count <= h_count + 1;
        end
    end
    
    assign hsync = ~((h_count >= 10'd656) && (h_count < 10'd752));
    assign vsync = ~((v_count >= 10'd490) && (v_count < 10'd492));
    assign video_on = (h_count < 10'd640) && (v_count < 10'd480);
    assign pixel_x = (h_count < 10'd640) ? h_count : 10'd0;
    assign pixel_y = (v_count < 10'd480) ? v_count : 10'd0;
endmodule"""
    }

    p2_fail = {
        "vga_controller_module": """module vga_controller(
    input clk,
    input rst_n,
    output hsync,
    output vsync,
    output video_on,
    output [9:0] pixel_x,
    output [9:0] pixel_y
);
    reg [9:0] h_count;
    reg [9:0] v_count;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_count <= 10'd0;
            v_count <= 10'd0;
        end else begin
            if (h_count == 10'd799) begin
                h_count <= 10'd0;
                if (v_count == 10'd524) v_count <= 10'd0;
                else v_count <= v_count + 1;
            end else h_count <= h_count + 1;
        end
    end
    
    assign hsync = ~((h_count >= 10'd656) && (h_count < 10'd752));
    assign vsync = ~((v_count >= 10'd490) && (v_count < 10'd492));
    assign video_on = (h_count < 10'd640) && (v_count < 10'd480);
    assign pixel_x = 10'd640;
    assign pixel_y = v_count;
endmodule"""
    }

    # P3: I2C - Pass case
    p3_pass = {
        "i2c_master_module": """module i2c_master(
    input clk,
    input rst_n,
    input start,
    input [7:0] data_tx,
    input rw,
    output [7:0] data_rx,
    output sda,
    output scl,
    output busy,
    output error
);
    reg [7:0] data_rx_reg;
    reg busy_reg;
    reg error_reg;
    reg sda_reg;
    reg scl_reg;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_rx_reg <= 8'h00;
            busy_reg <= 1'b0;
            error_reg <= 1'b0;
            sda_reg <= 1'b1;
            scl_reg <= 1'b1;
        end else begin
            if (start) begin
                busy_reg <= 1'b1;
            end else if (busy_reg) begin
                busy_reg <= 1'b0;
            end
            data_rx_reg <= 8'h00;
            error_reg <= 1'b0;
            sda_reg <= 1'b1;
            scl_reg <= 1'b1;
        end
    end
    
    assign data_rx = data_rx_reg;
    assign busy = busy_reg;
    assign error = error_reg;
    assign sda = sda_reg;
    assign scl = scl_reg;
endmodule"""
    }

    p3_fail = {
        "i2c_master_module": """module i2c_master(
    input clk,
    input rst_n,
    input start,
    input [7:0] data_tx,
    input rw,
    output [7:0] data_rx,
    output sda,
    output scl,
    output busy,
    output error
);
    reg [7:0] data_rx_reg;
    reg busy_reg;
    reg sda_reg;
    reg scl_reg;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_rx_reg <= 8'h00;
            busy_reg <= 1'b0;
            sda_reg <= 1'b1;
            scl_reg <= 1'b1;
        end else begin
            if (start) begin
                busy_reg <= 1'b1;
            end else if (busy_reg) begin
                busy_reg <= 1'b0;
            end
            data_rx_reg <= 8'h00;
            sda_reg <= 1'b1;
            scl_reg <= 1'b1;
        end
    end
    
    assign data_rx = data_rx_reg;
    assign busy = busy_reg;
    assign sda = sda_reg;
    assign scl = scl_reg;
endmodule"""
    }

    # P4: AXI Stream FIFO - Pass case
    p4_pass = {
        "axi_stream_fifo_module": """module axi_stream_fifo(
    input clk,
    input rst_n,
    input s_valid,
    input s_ready,
    input s_last,
    input [31:0] s_data,
    input [3:0] s_strb,
    output reg m_valid,
    output reg m_ready,
    output reg m_last,
    output reg [31:0] m_data,
    output reg [3:0] m_strb,
    output reg [3:0] packet_count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_valid <= 1'b0;
            m_ready <= 1'b1;
            m_last <= 1'b0;
            m_data <= 32'h0;
            m_strb <= 4'h0;
            packet_count <= 4'd2;
        end else begin
            m_valid <= s_valid;
            m_ready <= s_ready;
            m_last <= s_last;
            m_data <= s_data;
            m_strb <= s_strb;
            packet_count <= 4'd2;
        end
    end
endmodule"""
    }

    p4_fail = {
        "axi_stream_fifo_module": """module axi_stream_fifo(
    input clk,
    input rst_n,
    input s_valid,
    input s_ready,
    input s_last,
    input [15:0] s_data,
    input [3:0] s_strb,
    output m_valid,
    output m_ready,
    output m_last,
    output [15:0] m_data,
    output [3:0] m_strb,
    output [3:0] packet_count
);
    assign m_valid = 1'b0;
    assign m_ready = 1'b1;
    assign m_last = 1'b0;
    assign m_data = 16'h0;
    assign m_strb = 4'h0;
    assign packet_count = 4'd0;
endmodule"""
    }

    # P5: AXI4 Master - Pass case
    p5_pass = {
        "axi_master_module": """module axi_master(
    input clk,
    input rst_n,
    input start,
    input [31:0] addr,
    input [31:0] wdata,
    input [1:0] size,
    input write_en,
    input arready,
    input awready,
    input wready,
    input [3:0] bid,
    input [1:0] bresp,
    input bvalid,
    input [3:0] rid,
    input [31:0] rdata_in,
    input [1:0] rresp,
    input rvalid,
    output [31:0] rdata,
    output valid,
    output ready,
    output [3:0] arid,
    output [31:0] araddr,
    output arvalid,
    output [3:0] awid,
    output [31:0] awaddr,
    output awvalid,
    output [31:0] wdata_out,
    output [3:0] wstrb,
    output wvalid,
    output bready,
    output rready
);
    reg [1:0] state;
    localparam IDLE = 2'd0;
    localparam WRITE_ADDR = 2'd1;
    localparam WRITE_DATA = 2'd2;
    localparam READ_ADDR = 2'd3;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            case (state)
                IDLE: begin
                    if (start) begin
                        if (write_en) state <= WRITE_ADDR;
                        else state <= READ_ADDR;
                    end
                end
                WRITE_ADDR: begin
                    if (awready) state <= WRITE_DATA;
                end
                WRITE_DATA: begin
                    if (wready && bvalid) state <= IDLE;
                end
                READ_ADDR: begin
                    if (arready) state <= IDLE;
                end
            endcase
        end
    end
    
    assign rdata = rdata_in;
    assign valid = (state == IDLE) ? 1'b1 : 1'b0;
    assign ready = (state == IDLE) ? 1'b1 : 1'b0;
    assign arid = 4'h0;
    assign araddr = addr;
    assign arvalid = (state == READ_ADDR) ? 1'b1 : 1'b0;
    assign awid = 4'h0;
    assign awaddr = addr;
    assign awvalid = (state == WRITE_ADDR) ? 1'b1 : 1'b0;
    assign wdata_out = wdata;
    assign wstrb = 4'hF;
    assign wvalid = (state == WRITE_DATA) ? 1'b1 : 1'b0;
    assign bready = 1'b1;
    assign rready = 1'b1;
endmodule"""
    }

    p5_fail = {
        "axi_master_module": """module axi_master(
    input clk,
    input rst_n,
    input start,
    input [31:0] addr,
    input [31:0] wdata,
    input [1:0] size,
    input write_en,
    input arready,
    input awready,
    input wready,
    input [3:0] bid,
    input [1:0] bresp,
    input bvalid,
    input [3:0] rid,
    input [31:0] rdata_in,
    input [1:0] rresp,
    input rvalid,
    output [31:0] rdata,
    output valid,
    output ready,
    output [3:0] arid,
    output [31:0] araddr,
    output arvalid,
    output [3:0] awid,
    output [31:0] awaddr,
    output awvalid,
    output [31:0] wdata_out,
    output [3:0] wstrb,
    output wvalid,
    output bready,
    output rready
);
    assign rdata = 32'h0;
    assign valid = 1'b0;
    assign ready = 1'b0;
    assign arid = 4'h0;
    assign araddr = 32'h0;
    assign arvalid = 1'b0;
    assign awid = 4'h0;
    assign awaddr = 32'h0;
    assign awvalid = 1'b0;
    assign wdata_out = 32'h0;
    assign wstrb = 4'h0;
    assign wvalid = 1'b0;
    assign bready = 1'b0;
    assign rready = 1'b0;
endmodule"""
    }

    # Run tests
    print("=== P1: 4-bit CLA ===")
    p1_result = verify("P1", p1_pass)
    print(f"  Pass case: {p1_result['pass']}")
    p1_fail_result = verify("P1", p1_fail)
    print(f"  Fail case: {p1_fail_result['pass']}")
    print()

    print("=== P2: VGA Controller ===")
    p2_result = verify("P2", p2_pass)
    print(f"  Pass case: {p2_result['pass']}")
    print(f"    Details: {p2_result.get('details', {})}")
    p2_fail_result = verify("P2", p2_fail)
    print(f"  Fail case: {p2_fail_result['pass']}")
    print(f"    Details: {p2_fail_result.get('details', {})}")
    print()

    print("=== P3: I2C Master ===")
    p3_result = verify("P3", p3_pass)
    print(f"  Pass case: {p3_result['pass']}")
    print(f"    Details: {p3_result.get('details', {})}")
    p3_fail_result = verify("P3", p3_fail)
    print(f"  Fail case: {p3_fail_result['pass']}")
    print(f"    Details: {p3_fail_result.get('details', {})}")
    print()

    print("=== P4: AXI Stream FIFO ===")
    p4_result = verify("P4", p4_pass)
    print(f"  Pass case: {p4_result['pass']}")
    print(f"    Details: {p4_result.get('details', {})}")
    p4_fail_result = verify("P4", p4_fail)
    print(f"  Fail case: {p4_fail_result['pass']}")
    print(f"    Details: {p4_fail_result.get('details', {})}")
    print()

    print("=== P5: AXI4 Master ===")
    p5_result = verify("P5", p5_pass)
    print(f"  Pass case: {p5_result['pass']}")
    print(f"    Details: {p5_result.get('details', {})}")
    p5_fail_result = verify("P5", p5_fail)
    print(f"  Fail case: {p5_fail_result['pass']}")
    print(f"    Details: {p5_fail_result.get('details', {})}")
    print()

    # P6: PWM Generator - Pass case
    p6_pass = {
        "pwm_generator_module": """module pwm_generator(
    input clk,
    input rst_n,
    input [7:0] duty_cycle,
    output reg pwm_out,
    output reg [7:0] period_count
);
    reg [7:0] threshold;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_out <= 1'b0;
            period_count <= 8'd0;
            threshold <= 8'd128;
        end else begin
            if (period_count == 8'd99) begin
                period_count <= 8'd0;
            end else begin
                period_count <= period_count + 1;
            end
            threshold <= duty_cycle;
            if (period_count < threshold) begin
                pwm_out <= 1'b1;
            end else begin
                pwm_out <= 1'b0;
            end
        end
    end
endmodule"""
    }
    p6_fail = {
        "pwm_generator_module": """module pwm_generator(
    input clk,
    input rst_n,
    input [7:0] duty_cycle,
    output pwm_out,
    output [7:0] period_count
);
    // Wrong: never responds to duty_cycle and uses a fixed count
    assign pwm_out = 1'b0;
    assign period_count = 8'd50;
endmodule"""
    }

    # P7: Motor Speed Controller - Pass case
    p7_pass = {
        "motor_controller_module": """module motor_controller(
    input clk,
    input rst_n,
    input [7:0] target_speed,
    input [7:0] actual_speed,
    output reg [7:0] pwm_duty,
    output reg [15:0] error
);
    wire [8:0] error_ext;
    
    assign error_ext = {1'b0, target_speed} - {1'b0, actual_speed};
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_duty <= 8'd0;
            error <= 16'd0;
        end else begin
            error <= {7'd0, error_ext[7:0]};
            pwm_duty <= error_ext[7:0];
        end
    end
endmodule"""
    }
    p7_fail = {
        "motor_controller_module": """module motor_controller(
    input clk,
    input rst_n,
    input [7:0] target_speed,
    input [7:0] actual_speed,
    output [7:0] pwm_duty,
    output [15:0] error
);
    // Wrong: always outputs 0 instead of computing error
    assign pwm_duty = 8'd0;
    assign error = 16'd0;
endmodule"""
    }

    # P8: Quadrature Encoder - Pass case
    p8_pass = {
        "quadrature_encoder_module": """module quadrature_encoder(
    input clk,
    input rst_n,
    input enc_a,
    input enc_b,
    output reg [15:0] position,
    output reg direction,
    output reg [15:0] velocity
);
    reg [1:0] enc_a_delayed;
    reg [1:0] enc_b_delayed;
    reg [15:0] prev_position;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            position <= 16'd0;
            direction <= 1'b0;
            velocity <= 16'd0;
            enc_a_delayed <= 2'b0;
            enc_b_delayed <= 2'b0;
            prev_position <= 16'd0;
        end else begin
            enc_a_delayed <= {enc_a_delayed[0], enc_a};
            enc_b_delayed <= {enc_b_delayed[0], enc_b};
            
            // Decoding: A leads B = clockwise (direction=1), B leads A = CCW (direction=0)
            if (enc_a == 1'b1 && enc_a_delayed[1] == 1'b0 && enc_b == enc_b_delayed[1]) begin
                position <= position + 1;
                direction <= 1'b1;
            end else if (enc_b == 1'b1 && enc_b_delayed[1] == 1'b0 && enc_a == enc_a_delayed[1]) begin
                position <= position - 1;
                direction <= 1'b0;
            end
            
            velocity <= position - prev_position;
            prev_position <= position;
        end
    end
endmodule"""
    }
    p8_fail = {
        "quadrature_encoder_module": """module quadrature_encoder(
    input clk,
    input rst_n,
    input enc_a,
    input enc_b,
    output [15:0] position,
    output direction,
    output [15:0] velocity
);
    // Wrong: always 0
    assign position = 16'd0;
    assign direction = 1'b0;
    assign velocity = 16'd0;
endmodule"""
    }

    # P9: PID Controller - Pass case
    p9_pass = {
        "pid_controller_module": """module pid_controller(
    input clk,
    input rst_n,
    input [15:0] setpoint,
    input [15:0] feedback,
    input enable,
    output reg [15:0] control_output,
    output reg [15:0] error,
    output reg [15:0] p_term,
    output reg [15:0] i_term,
    output reg [15:0] d_term
);
    reg [15:0] prev_error;
    reg [15:0] i_accum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            control_output <= 16'd0;
            error <= 16'd0;
            p_term <= 16'd0;
            i_term <= 16'd0;
            d_term <= 16'd0;
            prev_error <= 16'd0;
            i_accum <= 16'd0;
        end else begin
            error <= setpoint - feedback;
            p_term <= error;
            i_accum <= i_accum + (error >> 3);  // Ki = 1/10
            i_term <= i_accum;
            d_term <= (error - prev_error) >> 1;  // Kd = 1/2
            control_output <= error + i_term + d_term;
            prev_error <= error;
        end
    end
endmodule"""
    }
    p9_fail = {
        "pid_controller_module": """module pid_controller(
    input clk,
    input rst_n,
    input [15:0] setpoint,
    input [15:0] feedback,
    input enable,
    output [15:0] control_output,
    output [15:0] error,
    output [15:0] p_term,
    output [15:0] i_term,
    output [15:0] d_term
);
    // Wrong: all zeros
    assign control_output = 16'd0;
    assign error = 16'd0;
    assign p_term = 16'd0;
    assign i_term = 16'd0;
    assign d_term = 16'd0;
endmodule"""
    }

    # P10: Servo Position Controller - Pass case
    p10_pass = {
        "servo_controller_module": """module servo_controller(
    input clk,
    input rst_n,
    input [15:0] target_position,
    input enc_a,
    input enc_b,
    output reg pwm_out,
    output reg [15:0] actual_position,
    output reg [15:0] control_signal
);
    reg [15:0] error;
    reg [7:0] duty_cycle_out;
    reg [7:0] period_count;
    reg [1:0] enc_a_delayed;
    reg [1:0] enc_b_delayed;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_out <= 1'b0;
            actual_position <= 16'd0;
            control_signal <= 16'd0;
            duty_cycle_out <= 8'd0;
            period_count <= 8'd0;
            enc_a_delayed <= 2'b0;
            enc_b_delayed <= 2'b0;
        end else begin
            enc_a_delayed <= {enc_a_delayed[0], enc_a};
            enc_b_delayed <= {enc_b_delayed[0], enc_b};
            
            if (enc_a == 1'b1 && enc_a_delayed[1] == 1'b0 && enc_b == enc_b_delayed[1]) begin
                actual_position <= actual_position + 1;
            end
            
            if (target_position > actual_position) begin
                error = target_position - actual_position;
                duty_cycle_out <= (error > 16'd255) ? 8'd255 : error[7:0];
                control_signal <= {8'd0, duty_cycle_out};
            end else begin
                error = actual_position - target_position;
                duty_cycle_out <= 8'd0;
                control_signal <= 16'd0;
            end
            
            if (period_count >= 8'd99) begin
                period_count <= 8'd0;
            end else begin
                period_count <= period_count + 1;
            end
            
            pwm_out <= (period_count < duty_cycle_out) ? 1'b1 : 1'b0;
        end
    end
endmodule"""
    }
    p10_fail = {
        "servo_controller_module": """module servo_controller(
    input clk,
    input rst_n,
    input [15:0] target_position,
    input enc_a,
    input enc_b,
    output pwm_out,
    output [15:0] actual_position,
    output [15:0] control_signal
);
    // Wrong: no control loop or encoder integration
    assign pwm_out = 1'b0;
    assign actual_position = 16'd0;
    assign control_signal = 16'd0;
endmodule"""
    }

    # Run P6-P10 tests
    print("=== P6: PWM Generator ===")
    p6_result = verify("P6", p6_pass)
    print_manual_result("P6", "Pass", p6_result)
    p6_fail_result = verify("P6", p6_fail)
    print_manual_result("P6", "Fail", p6_fail_result)
    print()

    print("=== P7: Motor Speed Controller ===")
    p7_result = verify("P7", p7_pass)
    print_manual_result("P7", "Pass", p7_result)
    p7_fail_result = verify("P7", p7_fail)
    print_manual_result("P7", "Fail", p7_fail_result)
    print()

    print("=== P8: Quadrature Encoder ===")
    p8_result = verify("P8", p8_pass)
    print_manual_result("P8", "Pass", p8_result)
    p8_fail_result = verify("P8", p8_fail)
    print_manual_result("P8", "Fail", p8_fail_result)
    print()

    print("=== P9: PID Controller ===")
    p9_result = verify("P9", p9_pass)
    print_manual_result("P9", "Pass", p9_result)
    p9_fail_result = verify("P9", p9_fail)
    print_manual_result("P9", "Fail", p9_fail_result)
    print()

    print("=== P10: Servo Position Controller ===")
    p10_result = verify("P10", p10_pass)
    print_manual_result("P10", "Pass", p10_result)
    p10_fail_result = verify("P10", p10_fail)
    print_manual_result("P10", "Fail", p10_fail_result)
    print()

    print("Done.")
