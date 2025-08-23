# nano-agent

Learn AI agents from scratch. Under 200 lines of code. No frameworks.

## Quick Start

```bash
# 1. Install Ollama (local LLM runtime - one-time setup)
brew install ollama        # macOS (or see ollama.ai for Linux/Windows)
ollama run llama3.1      # Or download the previous version

# Run agent
pip install -e .
python -m nano_agent run "Calculate 15% of 200"
```

## How It Works

```python
# The agent loop (simplified)
for step in range(max_steps):
    # 1. PERCEIVE: Current state
    prompt = f"Task: {task}\nTools: {available_tools}\nContext: {observations}"
    
    # 2. THINK: LLM decides action (returns JSON)
    action = model.generate(prompt)  # → {"action": "CALL", "tool_name": "calculator", "argument": "2+2"}
    
    # 3. ACT: Execute tool or return answer
    if action == "CALL":
        result = execute_tool(tool_name, argument)  # Actually runs the Python function
        observations.append(result)
    elif action == "FINAL":
        return answer
```

## Core Files (190 lines of code)

- `tools.py` (63 lines): Calculator, converter, date math
- `agent.py` (52 lines): Perceive-think-act loop  
- `__main__.py` (36 lines): CLI interface
- `model_ollama.py` (25 lines): Local LLM wrapper
- `judge.py` (14 lines): Output validation

## Examples

```bash
python -m nano_agent run "Add 8.5% to 3.03e12"        # → 3287550000000.0
python -m nano_agent run "Convert 72 F to C"          # → 22.2 °C
python -m nano_agent run "days_between 2025-01-01 2025-08-18"  # → 229

# See the agent thinking and calling tools
python -m nano_agent run "Convert 72 F to C" --verbose

[Step 1]
ACTION: {'action': 'CALL', 'tool_name': 'unit_convert', 'argument': '72 f to c'}
Calling unit_convert('72 f to c')
Result: 22.2 °C
```

## Under the Hood

The agent doesn't just print answers - it calls tools:

| You Ask | Agent Does | Tool Returns |
|---------|------------|--------------|
| "Calculate 15% of 200" | `calculator("0.15 * 200")` | "30.0" |
| "Convert 72 F to C" | `unit_convert("72 f to c")` | "22.2 °C" |
| "Days between dates" | `date_calc("days_between...")` | "229" |

Try `--verbose` to watch how it reasons and call tools.

## Key Concepts

**Agent Loop**: Repeatedly asks LLM "what next?" until done  
**Tools**: Functions the LLM can call (math, convert, dates)  
**JSON Format**: Structured LLM↔code communication  
**Safety**: Max steps prevent infinite loops  

## Test

```bash
./smoke.sh  # Run all tests
```

That's it. Read the code in 30 minutes, understand agents.