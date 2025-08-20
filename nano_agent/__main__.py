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
def eval(model: str = "llama3.1"):
    tasks = [
        ("percent", "Add 8.5% to 3.03e12 exactly"),
        ("convert", "Convert 72 F to C"),
        ("dates",   "days_between 2025-01-01 2025-08-18"),
    ]
    ag = build_agent(model_name=model)
    for name, prompt in tasks:
        out = ag.run(prompt, token_budget=400)
        print(f"{name}\t{out['final']}")

@app.command()
def probe(model: str = "llama3.1"):
    variants = [
        "add 8.5% to 3.03e12",
        "Add 8.5% to 3.03e12 exactly",
        "Please add 8.5% to 3.03e12",
        "Compute exactly: add 8.5% to 3.03e12."
    ]
    ag = build_agent(model_name=model)
    for p in variants:
        out = ag.run(p, token_budget=400)
        print(f"{p}\t->\t{out['final']}")

if __name__ == "__main__":
    app()

