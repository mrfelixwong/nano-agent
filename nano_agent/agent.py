"""AI Agent with key components clearly demonstrated."""

import json
import re
import os
from typing import Dict, List
from .tools import get_tools_spec, execute_tool


class Agent:
    """AI Agent demonstrating key components:
    - Reasoning Engine: self.model for decision-making
    - Memory: self.memory for conversation history  
    - Observer: observe() processes environment
    - Thinker: think() decides actions
    - Actor: act() executes decisions
    - Judge: judge() evaluates outputs
    - Controller: run() orchestrates everything
    """
    
    def __init__(self, model, max_steps: int = 6, verbose: bool = False):
        self.model, self.memory, self.max_steps = model, [], max_steps
        self.verbose = verbose
    
    def observe(self, task: str = None, tool_result: str = None) -> str:
        """Process input from user or environment."""
        if task: return f"User requested: {task}"
        elif tool_result: return f"Tool returned: {tool_result}"
        return "Ready for input"
    
    def think(self, task: str, observation: str) -> Dict:
        """Decide next action using reasoning engine."""
        # Build context from memory (last 3 entries)
        context = "\n".join(self.memory[-3:]) if self.memory else "Starting"
        
        # Check if last observation was successful tool result
        if "Tool returned:" in observation and "error" not in observation:
            prompt = f"""Task: {task}
{observation}

Task complete. Return the answer:
{{"action": "FINAL", "answer": "..."}}"""
        else:
            prompt = f"""Task: {task}
Current observation: {observation}
Memory: {context}
Tools: {json.dumps(get_tools_spec())}

Decide action (JSON):
{{"action": "CALL", "tool_name": "...", "argument": "..."}}
{{"action": "FINAL", "answer": "..."}}"""
        
        if self.verbose: 
            print(f"THINKING with prompt:\n{prompt}\n")
        
        response = self.model.generate(prompt, format='json')
        try: 
            return json.loads(response)
        except: 
            return {
                "action": "FINAL", 
                "answer": "error: invalid response"
            }
    
    def act(self, decision: Dict) -> str:
        """Execute the decided action."""
        if decision.get("action") != "CALL": 
            return None
        tool_name = decision.get("tool_name", "")
        argument = decision.get("argument", "")
        if self.verbose: 
            print(f"ACTING: Calling {tool_name}('{argument}')")
        return execute_tool(tool_name, argument)
    
    def judge(self, task: str, answer: str) -> tuple[bool, str]:
        """Evaluate if task is complete and correct."""
        answer = str(answer).strip()
        task_lower = task.lower()
        
        if answer.startswith("error:"): return False, answer
        has_number = re.search(r'[+-]?\d+(?:\.\d+)?', answer)
        if any(word in task_lower for word in ['calculate', 'add', 'subtract', 'multiply', 'divide', '%', 'percent']):
            return (True, "Calculation completed") if has_number else (False, "No numeric result")
        if 'convert' in task_lower or any(unit in task_lower for unit in ['celsius', 'fahrenheit', 'miles', 'kilometers']):
            return (True, "Conversion completed") if has_number else (False, "No numeric result")
        if any(word in task_lower for word in ['days', 'date', 'between']):
            return (True, "Date completed") if (has_number or re.search(r'\d{4}-\d{2}-\d{2}', answer)) else (False, "No result")
        return True, "Task completed"
    
    def run(self, task: str) -> Dict:
        """Execute the complete agent loop."""
        observation = self.observe(task=task)
        self.memory.append(observation)
        
        for step in range(self.max_steps):
            if self.verbose: 
                print(f"\n[Step {step + 1}]\nOBSERVING: {observation}")
            decision = self.think(task, observation)
            self.memory.append(f"Decided: {json.dumps(decision)}")
            if self.verbose: 
                print(f"DECISION: {decision}")
            if decision.get("action") == "FINAL":
                answer = decision.get("answer", "")
                passed, reason = self.judge(task, answer)
                return {
                    "final": answer,
                    "success": passed,
                    "reason": reason,
                    "steps": step + 1,
                    "memory": self.memory}
            
            # ACT: Execute tool
            result = self.act(decision)
            # OBSERVE: Process tool result
            observation = self.observe(tool_result=result)
            self.memory.append(observation)
        return {
                "final": "error: max steps reached", 
                "success": False, 
                "reason": "Max steps reached", 
                "steps": self.max_steps, 
                "memory": self.memory}