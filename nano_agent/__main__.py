import typer
import json
from typing import Dict, Any, Tuple
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import llm_judge, rule_judge

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")

def _get_judgment(agent: Agent, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Gets a judgment, using rule_judge first and falling back to llm_judge if
    the rule-based check is inconclusive.
    """
    passed, reason = rule_judge(task, result["final"], result["trace"])
    
    # If the deterministic check failed specifically because it couldn't verify
    # the tool, then we escalate to the LLM judge for a second opinion.
    if not passed and "UNVERIFIED" in reason:
        llm_passed, llm_reason = llm_judge(agent.model, task, result)
        return llm_passed, f"[LLM Judge] {llm_reason}"
    else:
        # Otherwise, we trust the deterministic result (whether it's a PASS or a FAIL).
        return passed, f"[Rule Judge] {reason}"


def _display_agent_output(result: dict, passed: bool, reason: str, judge_type: str = ""):
    """Print agent results in readable format."""
    usage_stats = result["cost"]
    
    print("\n--- Agent Run Complete ---")
    print(f"Final Response: {result['final']}")
    print(f"Stats: Steps={len(result['trace'])} | Tokens In={usage_stats['ti']} | Tokens Out={usage_stats['to']} | Duration={usage_stats['s']:.3f}s")
    print(f"Judgment: {'PASS' if passed else 'FAIL'} | {reason}")
    print("\n--- Agent Trace ---")
    
    for i, step_str in enumerate(result["trace"]):
        print(f"Step {i+1}:")
        try:
            data = json.loads(step_str)
            action = data.get("action")
            if action == "CALL":
                print(f"  Thought: Use '{data.get('tool_name')}' tool")
                print(f"  Action: CALL: {data.get('tool_name')} | {data.get('argument')}")
            elif action == "FINAL":
                print(f"  Thought: Have final answer")
                print(f"  Action: FINAL: {data.get('answer')}")
        except (json.JSONDecodeError, TypeError):
            print(f"  Raw: {step_str}")


@app.command()
def run(task: str, model: str = "llama3.1", budget_tokens: int = 400, max_steps: int = 4):
    """Run agent on a single task."""
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps)
    
    # Execute
    result = agent.run(task, token_budget=budget_tokens)
    passed, reason = _get_judgment(agent, task, result)
    _display_agent_output(result, passed, reason)


@app.command()
def playground(model: str = "llama3.1", max_steps: int = 4):
    """Interactive session to experiment with the agent."""
    print("Starting Nano-Agent Playground...")
    print("Using hybrid judge (rule-based with LLM fallback)")
    print('Type your task and press Enter. Type "quit" or "exit" to leave.')
    
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps)
    
    while True:
        try:
            task = input(">> ")
            if task.lower() in ["quit", "exit"]:
                print("Exiting playground.")
                break
            
            result = agent.run(task, token_budget=800)            
            passed, reason = _get_judgment(agent, task, result)
            _display_agent_output(result, passed, reason)
            print("-" * 25)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting playground.")
            break


@app.command()
def compare(task: str, model: str = "llama3.1", max_steps: int = 4):
    """
    Compare rule-based and LLM judges on the same task.
    
    Educational tool that runs a task once and evaluates it with both judge types,
    highlighting their different approaches and trade-offs.
    
    Args:
        task: The task for the agent to perform
        model: Ollama model to use (default: llama3.1)
        max_steps: Maximum reasoning steps allowed (default: 4)
    
    Example:
        python -m nano_agent compare "What's 15% of 2500?"
        
    This will show:
        - Rule Judge: Deterministic verification by re-computing the math
        - LLM Judge: Semantic evaluation of the task completion
        - Whether the judges agree (they usually do for math, may differ for complex tasks)
    """
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps)
    
    # Execute once
    print(f"\nTask: {task}")
    print("=" * 50)
    result = agent.run(task, token_budget=400)
    
    # Judge with both methods
    rule_passed, rule_reason = rule_judge(task, result["final"], result["trace"])
    llm_passed, llm_reason = llm_judge(agent.model, task, result)
    
    # Display comparison
    print(f"\nFinal Answer: {result['final']}")
    print(f"Steps Taken: {len(result['trace'])}")
    print("\n--- Judge Comparison ---")
    print(f"Rule Judge: {'[PASS]' if rule_passed else '[FAIL]'}")
    print(f"  Reason: {rule_reason}")
    print(f"\nLLM Judge:  {'[PASS]' if llm_passed else '[FAIL]'}")
    print(f"  Reason: {llm_reason}")
    
    if rule_passed != llm_passed:
        print("\n[WARNING] Judges disagree! This highlights their different approaches.")


if __name__ == "__main__":
    app()
