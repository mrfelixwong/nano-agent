# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nano-agent is a minimalist AI agent implementation for educational purposes. It demonstrates core agent concepts (tool use, execution tracing, cost tracking) using local Ollama models with no cloud dependencies.

## Commands

### Development & Testing
```bash
# Run single task
python -m nano_agent run "Add 8.5% to 3.03e12 exactly"

# Run smoke tests (requires Ollama with llama3.1)
./smoke.sh
```

### Installation
```bash
# Install Ollama first
brew install ollama
ollama run llama3.1

# Install package in development mode
pip install -e .
```

## Architecture

The agent follows an observe-plan-act loop with these core components:

1. **Agent** (`nano_agent/agent.py`): Orchestrates execution with token budget enforcement (default: 400) and max steps (default: 4). Automatically returns numerical results from numerical tools.

2. **Model Interface** (`nano_agent/model_ollama.py`): Ollama wrapper enforcing structured responses (`CALL: tool | arg` or `FINAL: answer`). Includes retry logic for malformed responses.

3. **Tools** (`nano_agent/tools.py`): Extensible registry with 3 built-in tools:
   - `calculator`: Safe arithmetic evaluation
   - `unit_convert`: Temperature/distance/weight conversions
   - `date_calc`: Date arithmetic operations

4. **Judge** (`nano_agent/judge.py`): Rule-based validation for task completion, particularly for percentage, calculation, and conversion tasks.

5. **CLI** (`nano_agent/__main__.py`): Typer-based interface with `run`, `playground`, and `compare` commands.

## Testing Strategy

- **Smoke Tests**: Three core scenarios testing percentage math (expected: 3287550000000.0), unit conversion (expected: 22.2), and date calculation (expected: 229)
- **No traditional unit tests**: Focus on end-to-end integration testing
- **Requires Ollama running with llama3.1 model**

## Key Development Notes

- **Local-first**: All processing happens locally via Ollama
- **Security**: Calculator tool restricts input characters to prevent injection
- **Token tracking**: Built-in cost metrics for token usage and execution time
- **Educational design**: Code intentionally kept simple and readable
- **Minimal dependencies**: Only typer and requests required