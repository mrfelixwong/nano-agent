import typer
import json
from .agent import Agent
from .model_ollama import OllamaModel
from .tools import ToolRegistry, register_default_tools
from .judge import llm_judge, rule_judge

app = typer.Typer(help="nano-agent")

def build_agent(model_name: str = "llama3.1", max_steps: int = 4):
    tools = ToolRegistry()
    register_default_tools(tools)
    model = OllamaModel(model_name)
    return Agent(model=model, tools=tools, max_steps=max_steps)

@app.command()
def run(task: str, model: str = "llama3.1", budget_tokens: int = 400, max_steps: int = 4):
    agent = build_agent(model_name=model, max_steps=max_steps)
    out = agent.run(task, token_budget=budget_tokens)
    
    ok, reason = llm_judge(agent.model, task, out)
    
    c = out["cost"]
    print(f"Response: {out['final']}")
    print(f"Steps: {len(out['trace'])} | Tokens_In: {c['ti']} | Tokens_Out: {c['to']} | Duration: {c['s']:.3f}s")
    print(f"Status: {'PASS' if ok else 'FAIL'} | Explanation: {reason}")
    
    print("Call trace:")
    for t in out["trace"]:
        try:
            data = json.loads(t)
            action = data.get("action")
            if action == "CALL":
                print(f'  -> CALL: {data.get("tool_name")} | {data.get("argument")}')
            elif action == "FINAL":
                 print(f'  -> FINAL: {data.get("answer")}')
            else:
                # Fallback for other JSON structures
                print(f"  -> {t}")
        except json.JSONDecodeError:
            # If it's not JSON, print it as-is (for old logs or errors)
            print(f"  -> {t}")

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

