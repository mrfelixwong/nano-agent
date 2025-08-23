import typer
import json
from typing import Dict, Any, Tuple
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import rule_judge

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")

def _display_agent_output(result: dict, passed: bool, reason: str, verbose: bool = False):
    # Streamlined output
    print(f"\nAnswer: {result['final']} {'✓' if passed else '✗'}")
    
    # Only show judge details if it failed
    if not passed:
        # Extract just the key part of the reason
        if "FAIL:" in reason:
            reason = reason.split("FAIL:", 1)[1].strip()
        elif "error:" in reason:
            reason = reason.split("error:", 1)[1].strip()
        print(f"Issue: {reason}")


@app.command()
def run(task: str, model: str = "llama3.1", max_steps: int = 6, verbose: bool = False):
    """Run agent on a single task.
    
    Args:
        task: The task for the agent to perform
        model: Ollama model to use (default: llama3.1)
        max_steps: Maximum reasoning steps allowed (default: 4)
        verbose: Show full LLM prompts and responses
    """
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps, verbose=verbose)
    
    # Execute
    result = agent.run(task)
    _display_agent_output(result, passed, reason, verbose=verbose)

@app.command()
def playground(model: str = "llama3.1", max_steps: int = 6, verbose: bool = False, trace_format: str = "compact"):
    """Interactive session to experiment with the agent.
    
    Args:
        model: Ollama model to use (default: llama3.1)
        max_steps: Maximum reasoning steps allowed (default: 4)
        verbose: Show full LLM prompts and responses
        trace_format: How to display trace - 'compact', 'detailed', or 'none'
    """
    print("Starting Nano-Agent Playground...")
    print("Using hybrid judge (rule-based with LLM fallback)")
    if verbose:
        print("[VERBOSE MODE: Showing full LLM prompts and responses]")
    print(f"Trace format: {trace_format}")
    print('Type your task and press Enter. Type "quit" or "exit" to leave.')
    
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps, verbose=verbose)
    
    while True:
        try:
            task = input(">> ")
            if task.lower() in ["quit", "exit"]:
                print("Exiting playground.")
                break
            
            result = agent.run(task)            
            passed, reason = rule_judge(task, result["final"])
            _display_agent_output(result, passed, reason, trace_format=trace_format, verbose=verbose)
            print("-" * 25)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting playground.")
            break

if __name__ == "__main__":
    app()
