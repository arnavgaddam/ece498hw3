# ECE 498 BH - LLM Reasoning for Engineering

## Environment Setup

### Python Version
- Python 3.10 or higher

### Required Packages
```bash
pip install openai pydantic python-dotenv instructor
```

### API Keys
Create a `.env` file in the project root with your OpenAI API key:
```bash
# .env file
OPENAI_API_KEY=your-api-key-here
```

### External Tools
- **Icarus Verilog** (iverilog): For compiling and simulating Verilog code
  - Ubuntu/Debian: `sudo apt-get install iverilog`
  - macOS: `brew install iverilog`
  - Windows: Download from http://iverilog.icarus.com/

### API Keys
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Files

| File | Description |
|------|-------------|
| `common.py` | Shared: problem definitions, API config, prompt builder |
| `verifier.py` | Verification functions for all 10 problems |
| `baseline_eval.py` | Baseline evaluation (no tools) - 5 trials × 10 problems |
| `memory.py` | Memory schema and JSON-backed store |
| `extraction.py` | Lesson extraction prompt and helper |
| `memory_pipeline.py` | Memory-augmented solve pipeline with retrieval |
| `sequential_eval.py` | Sequential memory evaluation (5 trials) |

## Usage

### 1. Baseline Evaluation (No Tools)
```bash
python baseline_eval.py
```

### 2. Memory-Augmented Solve (Single Run)
```bash
python memory_pipeline.py
```

### 3. Sequential Memory Evaluation (5 Trials)
```bash
python sequential_eval.py
```

## Problems

| Problem | Name | Difficulty |
|---------|------|------------|
| P1 | 4-bit Carry-Lookahead Adder | Easy |
| P2 | VGA Controller | Easy |
| P3 | I2C Master Controller | Hard |
| P4 | AXI Stream FIFO | Hard |
| P5 | AXI4 Full Master | Hard |
| P6 | PWM Generator | Easy |
| P7 | Motor Speed Controller | Easy |
| P8 | Quadrature Encoder Interface | Medium |
| P9 | PID Controller | Hard |
| P10 | Servo Position Controller | Hard |
