import typer
import json
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import llm_judge

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")


def _display_agent_output(result: dict, passed: bool, reason: str):
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
    passed, reason = llm_judge(agent.model, task, result)
    _display_agent_output(result, passed, reason)


@app.command()
def playground(model: str = "llama3.1", max_steps: int = 4):
    """Interactive session to experiment with the agent."""
    print("Starting Nano-Agent Playground...")
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
            passed, reason = llm_judge(agent.model, task, result)
            _display_agent_output(result, passed, reason)
            print("-" * 25)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting playground.")
            break


if __name__ == "__main__":
    app()