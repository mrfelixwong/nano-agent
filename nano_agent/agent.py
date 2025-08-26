"""Simple agent implementation for educational purposes."""

import json
import os
from typing import Dict, List



class Agent:
    """Minimal agent showing observe-think-act loop."""
    
    def __init__(self, model, tools, max_steps: int = 6, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true')
    
    def run(self, task: str, token_budget: int) -> Dict:
        """Execute task using observe-think-act loop."""
        tools_spec = json.dumps(self.tools.get_tools_spec())
        observations = []
        trace = []
        
        for step in range(self.max_steps):
            if self.verbose:
                print(f"\n[Step {step + 1}]")
            
            context = "\n".join(observations[-3:]) if observations else "Starting"
            if observations and "error" not in observations[-1]:
                prompt = f"""Task: {task}
Last result: {observations[-1]}

Task complete. Return the answer:
{{"action": "FINAL", "answer": "..."}}"""
            else:
                prompt = f"""Task: {task}
Tools: {tools_spec}
Context: {context}

Respond with JSON only:
{{"action": "CALL", "tool_name": "...", "argument": "..."}}
{{"action": "FINAL", "answer": "..."}}"""
            
            if self.verbose:
                print(f"PROMPT:\n{prompt}\n")
            
            response = self.model.generate(prompt, format='json')
            try:
                action = json.loads(response)
            except json.JSONDecodeError:
                if self.verbose:
                    print(f"Invalid JSON: {response}")
                return {"final": "error: invalid response", "trace": trace, "observations": observations}
            
            trace.append(json.dumps(action))
            
            if self.verbose:
                print(f"ACTION: {action}")
            
            if action.get("action") == "FINAL":
                return {"final": action.get("answer", ""), "trace": trace, "observations": observations}
            
            if action.get("action") == "CALL":
                tool_name = action.get("tool_name", "")
                argument = action.get("argument", "")
                
                if self.verbose:
                    print(f"Calling {tool_name}('{argument}')")
                
                result = self.tools.execute_tool(tool_name, argument)
                observation = f"Tool '{tool_name}' returned: {result}"
                observations.append(observation)
                
                if self.verbose:
                    print(f"Result: {result}")
                
            else:
                observations.append(f"Unknown action: {action}")
        
        return {"final": "error: max steps reached", "trace": trace, "observations": observations}
