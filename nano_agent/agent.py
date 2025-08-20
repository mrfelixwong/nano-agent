import time
import re
import json
from typing import Dict, List, Any
from .tools import ToolRegistry


class Agent:
    """
    An autonomous agent that uses an LLM to reason and tools to act.

    This agent follows a pure agentic pattern where the central LLM (the "Planner")
    is responsible for all strategic decisions, and the Python code (the "Executor")
    is responsible for carrying out those decisions.
    """
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4):
        """
        Initializes the Agent.

        Args:
            model: The language model interface (the "brain" or "Planner").
            tools: A registry of available tools (the "hands" of the Executor).
            max_steps: The maximum number of steps the agent can take.
        """
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def _build_context(self, task: str) -> str:
        """
        Creates the initial mission briefing for the LLM.

        This combines the user's task with the list of available tools and
        instructions for the expected JSON output format.

        Args:
            task: The user's specific task.

        Returns:
            A formatted string containing the full context for the LLM.
        """
        tool_specs = [f"{name}: {desc}" for name, desc in self.tools.spec()]
        tools_string = " | ".join(tool_specs)
        
        json_instructions = """
Respond with ONLY a JSON object with the following schema:
{
  "action": "CALL" or "FINAL",
  "tool_name": "name_of_tool_to_call" or null,
  "argument": "argument_for_the_tool" or null,
  "answer": "final_answer_to_the_user" or null
}"""
        
        context = f"Task: {task}\nTools: {tools_string}\n{json_instructions}"
        return context

    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """
        Executes a tool call and returns the result as an observation string.

        This is the "hands" of the agent, performing actions and producing results.

        Args:
            tool_name: The name of the tool to execute.
            arg: The argument to pass to the tool.

        Returns:
            A string describing the outcome of the tool execution.
        """
        try:
            res = self.tools.get(tool_name)(arg)
            return f"Tool '{tool_name}' succeeded with result: {res}"
        except Exception as e:
            return f"Tool '{tool_name}' failed with exception: {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        """
        Executes the agent's main Reason-Act loop to solve a task.

        This method orchestrates the entire process: reasoning with the LLM,
        acting with tools, and observing the results until the task is complete
        or a limit is reached.

        Args:
            task: The user's task to be solved.
            token_budget: The maximum number of tokens to use.

        Returns:
            A dictionary containing the final answer, the execution trace, and costs.
        """
        prompt_context = self._build_context(task)
        observation = "No observation yet. You must decide on the first action."
        trace_log: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0

        for step in range(self.max_steps):
            
            # --- 1. REASON ---
            # In this phase, the Planner (LLM) synthesizes the mission, its
            # history, and the last observation to decide on the next step.
            prompt = f"{prompt_context}\nObservation: {observation}"
            plan_json = self.model.generate(prompt, format='json').strip()
            
            # Log the Planner's decision and track costs.
            trace_log.append(plan_json)
            tokens_input += len(prompt.split())
            tokens_output += len(plan_json.split())
            time_elapsed += self.model.last_duration if hasattr(self.model, 'last_duration') else 0
            
            # The Executor's first job is to parse the Planner's JSON into a usable plan.
            try:
                plan = json.loads(plan_json)
            except json.JSONDecodeError:
                plan = {"action": "ERROR", "error": "Invalid JSON output from LLM."}

            # --- 2. ACT ---
            # In this phase, the Executor (code) carries out the Planner's
            # instructions. The outcome of the action becomes the next observation.
            if plan.get("action") == "FINAL":
                final_answer = plan.get("answer")
                break # Mission complete
            elif plan.get("action") == "CALL":
                tool_name = plan.get("tool_name")
                arg = plan.get("argument")
                observation = self._execute_tool(tool_name, arg)
            else: # Handle ERROR from the Planner
                observation = plan.get("error", "Unknown error from Planner.")

            # --- Safety Break ---
            if (tokens_input + tokens_output) > int(token_budget * 1.1):
                final_answer = "error: token budget exceeded"
                break
        
        if not final_answer:
            final_answer = "error: max steps reached"
            
        return {
            "final": final_answer, 
            "trace": trace_log, 
            "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}
        }