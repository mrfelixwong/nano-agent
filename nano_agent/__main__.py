"""CLI for the educational agent."""

import typer
from .agent import Agent
from .model_ollama import OllamaModel
from .judge import rule_judge

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")


@app.command()
def run(task: str, model: str = "llama3.1", max_steps: int = 6, verbose: bool = False):
    """Run agent on a single task."""
    agent = Agent(OllamaModel(model), max_steps, verbose)
    result = agent.run(task)
    
    # Display result
    passed, reason = rule_judge(task, result["final"])
    status = "✓" if passed else "✗"
    print(f"\nAnswer: {result['final']} {status}")
    if not passed and "error:" in reason:
        print(f"Issue: {reason.split(':', 1)[-1].strip()}")


@app.command()  
def playground(model: str = "llama3.1", max_steps: int = 6, verbose: bool = False):
    """Interactive session to experiment with the agent."""
    print("nano-agent playground")
    print("Type task and press Enter. Type 'quit' to exit.\n")
    
    agent = Agent(OllamaModel(model), max_steps, verbose)
    
    while True:
        try:
            task = input(">> ")
            if task.lower() in ["quit", "exit"]:
                break
            
            result = agent.run(task)
            passed, reason = rule_judge(task, result["final"])
            
            status = "✓" if passed else "✗"
            print(f"\nAnswer: {result['final']} {status}")
            if not passed:
                print(f"Issue: {reason}")
            print("-" * 40)
            
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break


if __name__ == "__main__":
    app()