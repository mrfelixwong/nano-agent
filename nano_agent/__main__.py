import typer
import json
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import llm_judge

app = typer.Typer(help="nano-agent")

def build_agent(model_name: str = "llama3.1", max_steps: int = 4):
    tools = ToolRegistry()
    register_default_tools(tools)
    model = OllamaModel(model_name)
    return Agent(model=model, tools=tools, max_steps=max_steps)

@app.command()
def run(task: str, model: str = "llama3.1", budget_tokens: int = 400, max_steps: int = 4):
    ag = build_agent(model_name=model, max_steps=max_steps)
    out = ag.run(task, token_budget=budget_tokens)
    
    ok, reason = llm_judge(ag.model, task, out)
    c = out["cost"]

    print("\n--- Agent Run Complete ---")
    print(f"Final Response: {out['final']}")
    print(f"Stats: Steps={len(out['trace'])} | Tokens In={c['ti']} | Tokens Out={c['to']} | Duration={c['s']:.3f}s")
    print(f"Judgment: {'PASS' if ok else 'FAIL'} | {reason}")
    
    print("\n--- Agent Trace ---")
    ## REFACTOR: Create a more visual step-by-step trace.
    for i, step_str in enumerate(out["trace"]):
        print(f"Step {i+1}:")
        try:
            data = json.loads(step_str)
            action = data.get("action")

            if action == "CALL":
                tool = data.get('tool_name')
                arg = data.get('argument')
                print(f"  Thought: The next step is to use the '{tool}' tool.")
                print(f"  Action: CALL: {tool} | {arg}")
            elif action == "FINAL":
                answer = data.get('answer')
                print(f"  Thought: I have the final answer.")
                print(f"  Action: FINAL: {answer}")
        except (json.JSONDecodeError, TypeError):
            print(f"  - Raw Output: {step_str}") # Fallback for non-json steps

@app.command()
def playground(model: str = "llama3.1", max_steps: int = 4):
    """Start an interactive session to experiment with the agent."""
    print("🚀 Starting Nano-Agent Playground...")
    print('Type your task and press Enter. Type "quit" or "exit" to leave.')
    
    ag = build_agent(model_name=model, max_steps=max_steps)

    while True:
        try:
            task = input(">> ")
            if task.lower() in ["quit", "exit"]:
                print("Exiting playground.")
                break

            # Re-use the same logic as the 'run' command
            out = ag.run(task, token_budget=800)
            ok, reason = llm_judge(ag.model, task, out)
            c = out["cost"]

            print("\n--- Agent Run Complete ---")
            print(f"Final Response: {out['final']}")
            print(f"Stats: Steps={len(out['trace'])} | Tokens In={c['ti']} | Tokens Out={c['to']} | Duration={c['s']:.3f}s")
            print(f"Judgment: {'PASS' if ok else 'FAIL'} | {reason}")
            print("\n--- Agent Trace ---")
            # (This uses the new visualization from proposal #2)
            for i, step_str in enumerate(out["trace"]):
                print(f"Step {i+1}:")
                try:
                    data = json.loads(step_str)
                    action = data.get("action")
                    if action == "CALL":
                        print(f"  Thought: The next step is to use the '{data.get('tool_name')}' tool.")
                        print(f"  Action: CALL: {data.get('tool_name')} | {data.get('argument')}")
                    elif action == "FINAL":
                        print(f"  Thought: I have the final answer.")
                        print(f"  Action: FINAL: {data.get('answer')}")
                except (json.JSONDecodeError, TypeError):
                    print(f"  - Raw Output: {step_str}")
            print("-" * 25)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting playground.")
            break

if __name__ == "__main__":
    app()

