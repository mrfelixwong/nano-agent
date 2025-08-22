import typer
import json
from typing import Dict, Any, Tuple
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import llm_judge, rule_judge

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")

def _format_trace_step(i: int, step_str: str, observations: list, trace_format: str) -> None:
    """Format and print a single trace step based on the format type."""
    try:
        data = json.loads(step_str)
        action = data.get("action")
        
        if trace_format == "compact":
            if action == "CALL":
                tool = data.get('tool_name')
                arg = data.get('argument')
                result_str = ""
                if i < len(observations):
                    obs = observations[i]
                    if "succeeded" in obs and "result: " in obs:
                        result_str = obs.split("result: ", 1)[1]
                    else:
                        result_str = obs
                print(f"  [{i+1}] {tool}(\"{arg}\") → {result_str}")
            elif action == "FINAL":
                print(f"  [{i+1}] Return: {data.get('answer')}")
                
        elif trace_format == "detailed":
            print(f"\n  Step {i+1}:")
            if action == "CALL":
                tool = data.get('tool_name')
                arg = data.get('argument')
                print(f"    Decision: Use {tool}")
                print(f"    Input:    {arg}")
                if i < len(observations):
                    obs = observations[i]
                    if "succeeded" in obs and "result: " in obs:
                        output = obs.split("result: ", 1)[1]
                    else:
                        output = obs
                    print(f"    Output:   {output}")
            elif action == "FINAL":
                print(f"    Decision: Task complete")
                print(f"    Return:   {data.get('answer')}")
    except (json.JSONDecodeError, TypeError):
        print(f"  [{i+1}] Error: {step_str}")

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


def _display_agent_output(result: dict, passed: bool, reason: str, judge_type: str = "", trace_format: str = "compact", verbose: bool = False):
    """Print agent results in readable format."""
    usage_stats = result["cost"]
    
    # If verbose mode already showed the trace, skip detailed trace
    if verbose:
        trace_format = "none"
    
    # Streamlined output
    print(f"\nAnswer: {result['final']} {'✓' if passed else '✗'}")
    
    # Show steps in compact form if not verbose and trace requested
    if trace_format != "none" and not verbose:
        steps = []
        for i, step_str in enumerate(result["trace"]):
            try:
                data = json.loads(step_str)
                if data.get("action") == "CALL":
                    tool = data.get('tool_name')
                    arg = data.get('argument')
                    if i < len(result.get("observations", [])):
                        obs = result["observations"][i]
                        if "succeeded" in obs and "result:" in obs:
                            res = obs.split("result: ", 1)[1]
                        elif "returned error:" in obs:
                            res = "error: " + obs.split("returned error: ", 1)[1]
                        else:
                            res = obs
                        steps.append(f"{tool}(\"{arg}\") → {res}")
            except:
                pass
        if steps:
            print(f"Steps: {' | '.join(steps)}")
    
    # Show time
    print(f"Time: {usage_stats['s']:.1f}s ({len(result['trace'])} steps)")
    
    # Only show judge details if it failed
    if not passed:
        # Extract just the key part of the reason
        if "FAIL:" in reason:
            reason = reason.split("FAIL:", 1)[1].strip()
        elif "error:" in reason:
            reason = reason.split("error:", 1)[1].strip()
        print(f"Issue: {reason}")


@app.command()
def run(task: str, model: str = "llama3.1", budget_tokens: int = 400, max_steps: int = 4, verbose: bool = False, trace_format: str = "compact"):
    """Run agent on a single task.
    
    Args:
        task: The task for the agent to perform
        model: Ollama model to use (default: llama3.1)
        budget_tokens: Maximum tokens to use (default: 400)
        max_steps: Maximum reasoning steps allowed (default: 4)
        verbose: Show full LLM prompts and responses
        trace_format: How to display trace - 'compact', 'detailed', or 'none'
    """
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps, verbose=verbose)
    
    # Execute
    result = agent.run(task, token_budget=budget_tokens)
    passed, reason = _get_judgment(agent, task, result)
    _display_agent_output(result, passed, reason, trace_format=trace_format, verbose=verbose)


@app.command()
def playground(model: str = "llama3.1", max_steps: int = 4, verbose: bool = False, trace_format: str = "compact"):
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
            
            result = agent.run(task, token_budget=800)            
            passed, reason = _get_judgment(agent, task, result)
            _display_agent_output(result, passed, reason, trace_format=trace_format, verbose=verbose)
            print("-" * 25)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting playground.")
            break


@app.command()
def compare(task: str, model: str = "llama3.1", max_steps: int = 4, verbose: bool = False, trace_format: str = "compact"):
    """
    Compare rule-based and LLM judges on the same task.
    
    Educational tool that runs a task once and evaluates it with both judge types,
    highlighting their different approaches and trade-offs.
    
    Args:
        task: The task for the agent to perform
        model: Ollama model to use (default: llama3.1)
        max_steps: Maximum reasoning steps allowed (default: 4)
    
    Args:
        task: The task for the agent to perform
        model: Ollama model to use (default: llama3.1)
        max_steps: Maximum reasoning steps allowed (default: 4)
        verbose: Show full LLM prompts and responses
        trace_format: How to display trace - 'compact', 'detailed', or 'none'
    
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
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps, verbose=verbose)
    
    # Execute once
    print(f"\nTask: {task}")
    print("=" * 50)
    result = agent.run(task, token_budget=400)
    
    # Show execution trace if requested
    if trace_format != "none":
        print("\n📋 Execution Trace:")
        for i, step_str in enumerate(result["trace"]):
            _format_trace_step(i, step_str, result.get("observations", []), trace_format)
    
    # Judge with both methods
    rule_passed, rule_reason = rule_judge(task, result["final"], result["trace"])
    llm_passed, llm_reason = llm_judge(agent.model, task, result)
    
    # Display comparison
    print(f"\nAnswer: {result['final']}")
    print(f"Steps: {len(result['trace'])}")
    print("\n--- Judge Comparison ---")
    print(f"Rule Judge: {'[PASS]' if rule_passed else '[FAIL]'}")
    print(f"  Reason: {rule_reason}")
    print(f"\nLLM Judge:  {'[PASS]' if llm_passed else '[FAIL]'}")
    print(f"  Reason: {llm_reason}")
    
    if rule_passed != llm_passed:
        print("\n[WARNING] Judges disagree! This highlights their different approaches.")


@app.command()
def eval(model: str = "llama3.1", max_steps: int = 4):
    """
    Run systematic evaluation on a set of test cases.
    
    Tests the agent on various task types and reports success rate.
    Educational tool to understand agent capabilities and limitations.
    """
    test_cases = [
        ("Add 8.5% to 3.03e12", "3287550000000.0"),
        ("Calculate 2 * 50", "100"),
        ("Convert 72 F to C", "22.2"),
        ("days_between 2025-01-01 2025-08-18", "229"),
        ("What is 15% of 200?", "30"),  # Might fail - tests natural language
    ]
    
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps)
    
    print("=" * 60)
    print("NANO-AGENT EVALUATION SUITE")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for task, expected in test_cases:
        print(f"\nTest: {task}")
        print(f"Expected: {expected}")
        
        result = agent.run(task, token_budget=400)
        actual = result["final"]
        
        # Check if answer contains expected value (flexible matching)
        success = False
        if expected.lower() in str(actual).lower():
            success = True
        elif expected.replace(".", "") in str(actual).replace(".", ""):
            success = True
        
        if success:
            print(f"Result: ✅ PASS (got: {actual})")
            passed += 1
        else:
            print(f"Result: ❌ FAIL (got: {actual})")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    print("=" * 60)


@app.command()
def probe(prompt_template: str = "Calculate {}", value: str = "15% of 200", model: str = "llama3.1", max_steps: int = 4):
    """
    Test how different prompt phrasings affect agent success.
    
    Educational tool to understand prompt engineering impact.
    
    Examples:
        python -m nano_agent probe "Calculate {}" "15% of 200"
        python -m nano_agent probe "What is {}?" "15% of 200"
        python -m nano_agent probe "Please compute {}" "2 * 50"
    """
    # Different prompt variations to test
    if "{}" not in prompt_template:
        prompt_template = prompt_template + " {}"
    
    prompts = [
        prompt_template.format(value),
        prompt_template.format(value).lower(),
        prompt_template.format(value).upper(),
        prompt_template.format(value).capitalize(),
    ]
    
    # Setup
    tools = ToolRegistry()
    register_default_tools(tools)
    agent = Agent(model=OllamaModel(model), tools=tools, max_steps=max_steps)
    
    print("=" * 60)
    print("PROMPT VARIATION PROBE")
    print(f"Testing: {value}")
    print("=" * 60)
    
    results = []
    for prompt in prompts:
        print(f"\nPrompt: '{prompt}'")
        result = agent.run(prompt, token_budget=400)
        answer = result["final"]
        steps = len(result["trace"])
        
        if "error" in answer.lower():
            print(f"Result: ❌ {answer} (steps: {steps})")
            results.append(False)
        else:
            print(f"Result: ✅ {answer} (steps: {steps})")
            results.append(True)
    
    success_rate = sum(results) / len(results) * 100
    print("\n" + "=" * 60)
    print(f"Success Rate: {success_rate:.0f}% ({sum(results)}/{len(results)} succeeded)")
    print("Key Insight: Prompt phrasing significantly affects agent success!")
    print("=" * 60)


if __name__ == "__main__":
    app()
