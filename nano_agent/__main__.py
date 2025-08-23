"""CLI for the educational agent."""

import typer
from .agent import Agent
from .model_ollama import OllamaModel

app = typer.Typer(help="nano-agent: learn AI agents in one sitting")


@app.command()
def run(task: str, model: str = "llama3.1", max_steps: int = 6, verbose: bool = False):
    """Run agent on a single task."""
    # Initialize agent with reasoning engine
    agent = Agent(OllamaModel(model), max_steps, verbose)
    
    # Run the agent controller
    result = agent.run(task)
    
    # Display result (judge already evaluated internally)
    status = "✓" if result["success"] else "✗"
    print(f"\nAnswer: {result['final']} {status}")
    
    if not result["success"]:
        print(f"Issue: {result['reason']}")
    
    if verbose:
        print(f"Steps: {result['steps']}")
        print(f"Memory entries: {len(result['memory'])}")


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
            
            status = "✓" if result["success"] else "✗"
            print(f"\nAnswer: {result['final']} {status}")
            if not result["success"]:
                print(f"Issue: {result['reason']}")
            print("-" * 40)
            
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break


if __name__ == "__main__":
    app()