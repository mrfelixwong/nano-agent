import json
import os
from typing import Dict, List, Any
from .tools import ToolRegistry


class Agent:
    """Agent that uses LLM reasoning and tools to solve tasks."""
    
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true', 'yes')
    
    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Execute tool and return observation string."""
        try:
            result = self.tools.get(tool_name)(arg)
            # Check if the result is an error from the tool itself
            if isinstance(result, str) and result.startswith("error:"):
                return f"Tool '{tool_name}' returned error: {result[6:].strip()}"
            return f"Tool '{tool_name}' succeeded with result: {result}"
        except Exception as e:
            return f"Tool '{tool_name}' failed with exception: {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        """Execute observe-think-act loop until task completes or limits reached."""
        
        # --- Setup ---
        tool_specs = [f"{name}: {desc}" for name, desc in self.tools.spec()]
        context = f"""Task: {task}
Tools: {' | '.join(tool_specs)}

If task needs multiple steps: First use action: "PLAN" once. Then use "CALL" for each step.
Respond with ONLY a JSON object:
{{
  "action": "PLAN" or "CALL" or "FINAL",
  "steps": ["step 1", "step 2", ...] or null,  // only for PLAN
  "tool_name": "name_of_tool" or null,         // only for CALL
  "argument": "tool_argument" or null,         // only for CALL
  "answer": "final_answer" or null             // only for FINAL
}}"""
        
        observation = "No observation yet. You must decide on the first action."
        trace_log: List[str] = []
        observations: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0
        
        # Planning state
        plan_steps: List[str] = []
        current_plan_step = 0
        plan_results: List[str] = []
        
        # --- Main Loop ---
        for step in range(self.max_steps):
            
            # OBSERVE + THINK: Prepare context for LLM's next decision
            
            # If we're executing a plan step, use isolated context
            if plan_steps and current_plan_step < len(plan_steps) and "execute step" in observation.lower():
                # Get the current step task
                current_task = plan_steps[current_plan_step]
                
                # Replace vague references with actual values
                if plan_results:
                    last_result = plan_results[-1].split(": ")[-1] if plan_results else None
                    if last_result:
                        current_task = current_task.replace("that number", last_result)
                        current_task = current_task.replace("the result", last_result)
                        current_task = current_task.replace("result", last_result)
                
                # Create minimal, isolated prompt for step execution
                input_value = last_result if plan_results else None
                
                # Help the LLM understand how to format the argument
                if "multiply" in current_task.lower() and input_value:
                    example = f" (e.g., '{input_value}*2')"
                elif "add" in current_task.lower() and input_value:
                    example = f" (e.g., '{input_value}+10')"
                else:
                    example = ""
                
                prompt = f"""Tools: {' | '.join(tool_specs)}

Task: {current_task}
Input: {input_value if input_value else 'none'}

Respond with ONLY a JSON object:
{{
  "action": "CALL",
  "tool_name": "name_of_tool",
  "argument": "tool_argument{example}"
}}"""
            else:
                # For planning or single-step tasks, use full context
                prompt = f"{context}\nObservation: {observation}"
            
            # Verbose logging: show what we're sending to LLM
            if self.verbose:
                print(f"\n[Step {step + 1}]")
                if step == 0:
                    print(f"  THINK: Analyzing task: {task}")
                elif plan_steps and current_plan_step < len(plan_steps) and "execute step" in observation.lower():
                    # Show isolated context for plan step
                    print(f"  THINK: Executing step {current_plan_step + 1}: {plan_steps[current_plan_step]}")
                    if plan_results:
                        print(f"  INPUT: {plan_results[-1].split(': ')[-1]}")
                else:
                    # Extract cleaner observation message
                    if "succeeded with result:" in observation:
                        print(f"  THINK: Previous tool returned: {observation.split('result: ', 1)[1]}")
                    elif "failed" in observation or "error" in observation.lower():
                        print(f"  THINK: Previous tool failed: {observation.split('failed with exception: ', 1)[-1]}")
                    else:
                        print(f"  THINK: {observation}")
            
            plan_json = self.model.generate(prompt, format='json').strip()
            
            # Parse LLM's decision once
            try:
                plan = json.loads(plan_json)
            except json.JSONDecodeError:
                plan = {"action": "ERROR", "error": "Invalid JSON from LLM"}
            
            # Verbose logging: show what LLM decided
            if self.verbose:
                action = plan.get("action", "?")
                if action == "PLAN":
                    print(f"  DECIDE: Create plan with {len(plan.get('steps', []))} steps")
                elif action == "CALL":
                    print(f"  DECIDE: Use {plan.get('tool_name')} tool")
                elif action == "FINAL":
                    print(f"  DECIDE: Return the result")
                elif action == "ERROR":
                    print(f"  ERROR: {plan.get('error', 'Unknown error')}")
                else:
                    print(f"  DECIDE: {action}")
            
            # Track costs
            trace_log.append(plan_json)
            tokens_input += len(prompt.split())
            tokens_output += len(plan_json.split())
            time_elapsed += self.model.last_duration if hasattr(self.model, 'last_duration') else 0
            
            # ACT: Execute the chosen action
            if plan.get("action") == "PLAN":
                # Only create plan if we don't have one
                if not plan_steps:
                    raw_steps = plan.get("steps", [])
                    # Clean up plan steps to be task-focused, not implementation-focused
                    plan_steps = []
                    for step in raw_steps:
                        # Remove implementation details like "CALL", "use", tool names
                        cleaned = step
                        cleaned = cleaned.replace("CALL ", "")
                        cleaned = cleaned.replace("call ", "")
                        cleaned = cleaned.replace(" tool", "")
                        cleaned = cleaned.replace("date_calc", "calculate days")
                        cleaned = cleaned.replace("calculator", "calculate")
                        cleaned = cleaned.replace(" with argument", ":")
                        plan_steps.append(cleaned)
                    
                    current_plan_step = 0
                    plan_results = []
                    observation = f"Plan created. Now use CALL to execute step 1: {plan_steps[0] if plan_steps else 'No steps'}"
                    if self.verbose:
                        print(f"  → PLAN: {plan_steps}")
                else:
                    # Already have a plan, don't re-plan
                    observation = f"Already have a plan. Continue with step {current_plan_step + 1}: {plan_steps[current_plan_step] if current_plan_step < len(plan_steps) else 'Complete'}"
                    if self.verbose:
                        print(f"  → SKIP: Already have plan")
                observations.append(observation)
            elif plan.get("action") == "FINAL":
                final_answer = plan.get("answer")
                observations.append("")  # No observation for final answer
                if self.verbose:
                    print(f"  → RETURN: {final_answer}")
                break
            elif plan.get("action") == "CALL":
                tool_name = plan.get("tool_name")
                arg = plan.get("argument")
                if self.verbose:
                    print(f"  → TOOL: {tool_name}(\"{arg}\")")
                observation = self._execute_tool(tool_name, arg)
                observations.append(observation)
                
                # If executing a plan, track progress
                if plan_steps and current_plan_step < len(plan_steps):
                    # Extract result for plan tracking
                    tool_result = None
                    if "succeeded with result:" in observation:
                        tool_result = observation.split("result: ", 1)[1]
                        plan_results.append(f"Step {current_plan_step + 1}: {tool_result}")
                    elif "returned error:" in observation:
                        # Don't increment step on error, let it retry
                        tool_result = "error"
                        # Keep isolated context for retry
                        error_msg = observation.split("returned error: ", 1)[1]
                        observation = f"Tool failed: {error_msg}"
                        observation += f"\nRetry execute step {current_plan_step + 1}: {plan_steps[current_plan_step]}"
                        if plan_results:
                            observation += f"\nInput available: {plan_results[-1].split(': ')[-1]}"
                    else:
                        current_plan_step += 1
                    
                    if tool_result != "error":
                        current_plan_step += 1
                        
                        # Update observation with next step info
                        if current_plan_step < len(plan_steps):
                            # Clear observation and provide clean context for next step
                            next_step = plan_steps[current_plan_step]
                            
                            observation = f"Step {current_plan_step} completed successfully with result: {tool_result}"
                            observation += f"\nNow execute step {current_plan_step + 1}: {next_step}"
                            observation += f"\nInput for next step: {tool_result}"
                        else:
                            # All plan steps completed
                            if tool_result:
                                observation = f"All plan steps completed. Final result: {tool_result}. Use FINAL action to return {tool_result} as the answer."
                            else:
                                observation = f"All plan steps completed. Use FINAL action to return the answer."
                # Show execution result in verbose mode
                if self.verbose:
                    if "returned error:" in observation:
                        error_msg = observation.split("returned error: ", 1)[1]
                        print(f"  ← ERROR: {error_msg}")
                    elif "succeeded" in observation and "result:" in observation:
                        result = observation.split("result: ", 1)[1]
                        print(f"  ← RESULT: {result}")
                    elif "failed" in observation:
                        error_msg = observation.split("failed with exception: ", 1)[-1]
                        print(f"  ← ERROR: {error_msg}")
                    else:
                        print(f"  ← RESULT: {observation}")
            else:
                observation = f"error: {plan.get('error', 'Unknown error')}"
                observations.append(observation)
                if self.verbose:
                    print(f"  ← ERROR: {observation}")
            
            # Safety check: token budget
            if (tokens_input + tokens_output) > int(token_budget * 1.1):
                final_answer = "error: token budget exceeded"
                break
        
        if not final_answer:
            final_answer = "error: max steps reached"
        
        return {
            "final": final_answer,
            "trace": trace_log,
            "observations": observations,
            "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}
        }