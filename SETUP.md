# ECE 498 BH - Assignment 3: LLM Reasoning for Engineering

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
| `verifier.py` | Verification functions for all 5 problems |
| `baseline.py` | Baseline evaluation (no tools) - 5 trials × 5 problems |
| `tool_pipeline.py` | Tool-augmented pipeline (Option A: pre-defined tool) |
| `tool_eval.py` | Tool-augmented evaluation |
| `refinement.py` | Self-refinement + tools on P5 |

## Usage

### 1. Baseline Evaluation (No Tools)
```bash
python baseline.py
```

### 2. Tool-Augmented Evaluation
```bash
python tool_eval.py
```

### 3. Self-Refinement + Tools
```bash
python refinement.py
```

## Problems

| Problem | Name | Difficulty |
|---------|------|------------|
| P1 | 4-bit Carry-Lookahead Adder | Easy |
| P2 | VGA Controller | Easy |
| P3 | I2C Master Controller | Hard |
| P4 | AXI Stream FIFO | Hard |
| P5 | AXI4 Full Master | Hard |

