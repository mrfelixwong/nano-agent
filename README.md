# nano-agent: Learn AI Agents in One Sitting
**Build an AI Agent *and* an AI Judge from scratch with no frameworks.**

**Zero frameworks. Pure Python. Built for learning.**

A minimalist AI agent implementation that teaches core agentic patterns without LangChain, CrewAI, or any agent framework. Just 300 lines of readable Python you can understand in one setting.

## 100% Local, Zero API Keys Required, Data never leaves your computer

**Everything runs on your machine:**
- No OpenAI API keys needed
- No cloud services or accounts
- No network calls (except downloading Ollama)
- Your data never leaves your computer
- Perfect for learning without costs or privacy concerns

## Why nano-agent?

**No Framework Magic** - While LangChain and others are powerful, their abstractions hide how agents actually work. This codebase shows you the raw mechanics.

**Optimized for Learning** - Every line is written to be understood.

**Complete Implementation** - Despite being tiny, this is a fully functional agent with:
- The observe → think → act loop
- Tool calling with JSON structured output  
- Token budget and safety limits
- LLM-as-Judge: Using one AI to judge another's performance

## A Key Concept: The AI Judge

Beyond just making an agent, nano-agent teaches you how to evaluate it. It includes a powerful pattern called LLM-as-Judge, where you use a second AI to act as an impartial evaluator.

## Quick Start

```bash
# 1. Install Ollama (local LLM runtime - one-time setup)
brew install ollama        # macOS (or see ollama.ai for Linux/Windows)
ollama run llama3.1        # Downloads ~5GB model, runs locally forever

# 2. Install nano-agent
git clone https://github.com/yourusername/nano-agent.git
cd nano-agent
pip install -e .

# 3. Run your first agent task
python -m nano_agent run "Add 8.5% to 3.03e12 exactly"

# 4. Compare how different judges evaluate the same task
python -m nano_agent compare "Calculate 15% of 200"
# Shows both rule-based (math verification) and LLM (semantic) evaluation

# 5. Start the interactive playground
python -m nano_agent playground
```

**Note:** After initial setup, everything runs offline. No internet needed!

## Learning from the Compare Command

The `compare` command reveals how different evaluation strategies work:

```bash
$ python -m nano_agent compare "Calculate 2 * 50"

Final Answer: 100
Rule Judge: ✅ PASS - Final answer 100.0 matches re-calculated value.
LLM Judge:  ✅ PASS - Agent correctly calculated the multiplication.

# This might fail sometimes (LLMs are non-deterministic!)
$ python -m nano_agent compare "What is 25% of 80?"

Final Answer: 20.0  # Or sometimes: error: max steps reached
Rule Judge: ✅ PASS  # Or: ❌ FAIL if agent struggled
LLM Judge:  ✅ PASS  # Or: ❌ FAIL if agent struggled
```

**What This Teaches:**
- **LLMs are non-deterministic** - Same prompt might succeed or fail
- **Phrasing matters** - "Calculate X" more reliable than "What is X?"
- **Both judges agree** - When agent succeeds/fails, both judges detect it
- **Different perspectives** - Rule judge verifies math, LLM judge verifies intent

## Using the Playground

The playground is an interactive REPL for experimenting with the agent:

```bash
$ python -m nano_agent playground

Starting Nano-Agent Playground...
Type your task and press Enter. Type "quit" or "exit" to leave.

>> Convert 100 fahrenheit to celsius

--- Agent Run Complete ---
Final Response: 37.8 °C
Stats: Steps=1 | Tokens In=89 | Tokens Out=15 | Duration=1.234s
Judgment: PASS | Agent correctly converted temperature

--- Agent Trace ---
Step 1:
  Thought: The next step is to use the 'unit_convert' tool.
  Action: CALL: unit_convert | 100 f to c
-------------------------

>> What's 15% of 2500?

--- Agent Run Complete ---
Final Response: 375.0
Stats: Steps=1 | Tokens In=92 | Tokens Out=18 | Duration=0.987s
Judgment: PASS | Agent calculated percentage correctly

>> quit
Exiting playground.
```

**Playground Features:**
- **Interactive exploration**: Try any task instantly
- **Live traces**: See the agent's thinking process
- **Immediate feedback**: Judge evaluates each response

**Example Tasks to Try:**
```
- "Calculate 18% tip on $47.50"
- "How many days between Christmas and New Year's?"
- "Convert 5 kilometers to miles"
- "What's 2^10?"
- "72 degrees fahrenheit in celsius"
```

## Core Concepts

### 1. The Agent Loop (agent.py)

The heart of any agent is its decision loop:

```python
for step in range(max_steps):
    # 1. OBSERVE: What's the current situation?
    prompt = f"{context}\nObservation: {observation}"
    
    # 2. THINK: What should I do next?
    llm_output = model.generate(prompt, format='json')
    
    # 3. ACT: Execute the chosen action
    if action == "CALL":
        observation = execute_tool(tool_name, argument)
    elif action == "FINAL":
        return final_answer
```

**Key Lesson**: Agents are just loops that repeatedly ask "what next?" until they find an answer.

### 2. Tool Use Pattern

Tools give agents abilities beyond text generation:

```python
# Tools are just functions with descriptions
def calculator(expr: str) -> str:
    return str(eval(expr))  # Simplified for teaching

registry.register("calculator", 
                 "Evaluate arithmetic expressions", 
                 calculator)
```

**Key Lesson**: Tools bridge the gap between language and computation.

### 3. Structured Communication

We use JSON to ensure reliable LLM-to-code communication:

```json
{"action": "CALL", "tool_name": "calculator", "argument": "3.03e12 * 1.085"}
{"action": "FINAL", "answer": "3287550000000.0"}
```

**Key Lesson**: Structure prevents parsing ambiguity and improves reliability.

### 4. Safety Mechanisms

Real agents need guardrails:

```python
# Token budget prevents runaway costs
if tokens_used > budget * 1.1:
    return "error: token budget exceeded"

# Step limit prevents infinite loops  
if step >= max_steps:
    return "error: max steps reached"
```

**Key Lesson**: Always implement safety limits in production agents.

## Architecture Deep Dive

### File Structure
```
nano_agent/
├── agent.py          # Core agent loop with JSON parsing
├── model_ollama.py   # LLM interface with retry logic
├── tools.py          # Tool registry and implementations
├── judge.py          # Two evaluation systems (rule & LLM)
└── __main__.py       # CLI interface with judge comparison
```

### Two Judge Types: Learning Evaluation Strategies

nano-agent includes **two different judge implementations** to teach evaluation approaches:

#### 1. Rule-Based Judge (Default)
A deterministic judge that verifies answers by re-computing results:

```bash
python -m nano_agent run "Add 8.5% to 3.03e12" --judge rule
```

**How it works:**
- Parses the agent's tool calls from the trace
- Re-executes the computation locally
- Compares expected vs actual mathematically

**Pros:**
- ✅ Fast and deterministic (no LLM calls)
- ✅ Mathematically precise verification
- ✅ Zero additional tokens/cost
- ✅ Consistent results every time

**Cons:**
- ❌ Can only verify computational tasks
- ❌ No semantic understanding
- ❌ Limited to tools it knows how to verify

#### 2. LLM Judge
An AI judge that evaluates semantic correctness:

```bash
python -m nano_agent run "Convert 72F to celsius" --judge llm
```

**How it works:**
- Sends the task, trace, and answer to an LLM
- LLM evaluates if the agent solved the task correctly
- Returns success/failure with reasoning

**Pros:**
- ✅ Understands context and intent
- ✅ Works with any task type
- ✅ Can evaluate partial success
- ✅ Flexible reasoning

**Cons:**
- ❌ Slower (requires LLM call)
- ❌ Uses additional tokens
- ❌ May be inconsistent
- ❌ Can be fooled by plausible-sounding errors

#### Compare Both Judges

Use the `compare` command to see how both judges evaluate the same task:

```bash
python -m nano_agent compare "What's 15% of 2500?"

# Output shows both judgments:
Rule Judge: ✅ PASS
  Reason: PASS: Final answer 375.0 matches re-calculated value.

LLM Judge:  ✅ PASS  
  Reason: The agent correctly calculated 15% of 2500 as 375.

# They might disagree on complex tasks!
```

This teaches an important lesson: **evaluation strategy matters** in production agents.

### Understanding Agent Failures (Educational!)

Not all tasks succeed, and **that's by design**. Failures teach important lessons:

```bash
# This might succeed
$ python -m nano_agent run "Calculate 15% of 200"
Final Response: 30.0
Judgment: PASS | [Rule Judge] PASS: Final answer 30.0 matches re-calculated value.

# This might fail (depending on how the LLM interprets it)
$ python -m nano_agent run "What is 25% of 80?"
Final Response: error: max steps reached
Judgment: FAIL | [Rule Judge] FAIL: Could not compare final answer...
```

**Why the difference?**
- "Calculate X" → LLM likely outputs `0.15 * 200` 
- "What is X?" → LLM might try `25% of 80` which isn't valid Python

**Key Lessons:**
1. **Prompt engineering matters** - How you phrase tasks affects success
2. **Agents aren't magic** - They can fail on seemingly simple tasks
3. **Step limits prevent infinite loops** - Better to fail fast than run forever
4. **Different judges catch different failures** - Rule judge catches math errors, LLM judge catches semantic issues

### Key Design Decisions

1. **JSON Over Text Parsing**: We chose JSON for reliability over simplicity
   - Pro: No ambiguous parsing, structured data
   - Con: More tokens, slightly harder to debug
   - Learning: Production systems need reliability

2. **Numerical Shortcuts**: Auto-return numbers from math tools
   - Why: Saves an LLM call for simple numeric results
   - Learning: Pragmatic optimizations improve efficiency

3. **Tool Registry Pattern**: Extensible tool system
   - Why: Easy to add new capabilities
   - Learning: Good abstractions enable growth

4. **Trace-Based Evaluation**: Judge examines the full execution
   - Why: Correctness isn't just about the final answer
   - Learning: Process matters as much as outcome

##  Understanding Agent Behavior

### Reading Traces

Agent traces show the thinking process:

```
Step 1:
  Thought: I need to calculate 8.5% of 3.03e12
  Action: CALL: calculator | 3.03e12 * (1 + 8.5/100)
  
Step 2:  
  Thought: I have the final answer
  Action: FINAL: 3287550000000.0
```

### Cost Analysis

Every agent run tracks resource usage:
- **Tokens In**: Prompt tokens sent to LLM
- **Tokens Out**: Response tokens from LLM  
- **Duration**: Total execution time
- **Steps**: Number of reasoning iterations
- **Cost**: $0.00 (everything runs locally!)

## Debugging Agent Failures

When an agent fails, the trace tells you exactly what went wrong:

```bash
$ python -m nano_agent run "What is 25% of 80?" --max-steps 6

--- Agent Trace ---
Step 1:
  Action: CALL: calculator | 25% of 80     # ❌ Invalid Python expression
Step 2:
  Action: CALL: calculator | 0.25 * 80     # ✅ Retry with valid expression  
Step 3:
  Action: FINAL: 20.0                      # ✅ Success!
```

**Common Failure Patterns:**
1. **Invalid tool arguments** - Agent passes natural language instead of code
2. **Max steps reached** - Agent keeps retrying without success
3. **Wrong tool selection** - Agent uses calculator for date problems
4. **Token budget exceeded** - Task too complex for budget

**How to Debug:**
- Check the trace to see what tools were called
- Look at tool arguments - are they valid?
- Count steps - did it hit the limit?
- Compare judges - do they agree on the failure?

## Code Walkthrough: Follow a Task End-to-End

Let's trace `"Calculate 2 * 50"` through the entire system:

### 1. CLI Entry (`__main__.py:54`)
```python
def run(task: str, ...):
    agent = Agent(model=OllamaModel(), tools=tools)
    result = agent.run(task)
```

### 2. Agent Loop (`agent.py:44-77`)
```python
# Step 1: Build context with task and available tools
context = "Task: Calculate 2 * 50\nTools: calculator | unit_convert | date_calc"

# Step 2: LLM decides first action
plan = {"action": "CALL", "tool_name": "calculator", "argument": "2 * 50"}

# Step 3: Execute tool
observation = "Tool 'calculator' succeeded with result: 100"

# Step 4: LLM sees result and decides to finish
plan = {"action": "FINAL", "answer": "100"}
```

### 3. Hybrid Judge Evaluation (`__main__.py:11-25`)
```python
# First try rule-based judge
rule_judge: "2 * 50" = 100 ✓  # Math verified!

# Since rule judge passed, no need for LLM judge
return (True, "[Rule Judge] PASS: Final answer 100 matches...")
```

**Total lines to understand: ~270** - Truly readable in one sitting!

## Try These Experiments

### 1. Watch Non-Determinism in Action
```bash
# Run the same task multiple times
for i in {1..5}; do 
    python -m nano_agent run "What is 15% of 200?"
done
# Notice: Sometimes it succeeds, sometimes it fails!
```

### 2. Test the Safety Limits
```bash
# Hit the step limit
python -m nano_agent run "Count to 100" --max-steps 2
# Result: error: max steps reached

# Hit the token budget  
python -m nano_agent run "Explain quantum physics" --budget-tokens 50
# Result: error: token budget exceeded
```

### 3. Compare Judge Disagreements
```bash
# Find tasks where judges might disagree
python -m nano_agent compare "What day is tomorrow?"
# Rule judge: Can't verify without knowing today's date
# LLM judge: Might evaluate based on attempt quality
```

### 4. Debug a Failure
```bash
# Watch the agent struggle and learn why
python -m nano_agent run "What's 25% of 80?" --max-steps 6
# Check the trace - does it try invalid expressions?
```

## Key Questions This Code Answers

1. **Q: How do agents really work?**
   A: They're loops that repeatedly ask an LLM "what next?" until done.

2. **Q: Why do agents need tools?**
   A: LLMs can't do math, access data, or take actions - tools can.

3. **Q: How should we evaluate agents?**
   A: Use hybrid approach - deterministic checks when possible, AI evaluation when needed.

4. **Q: Why do agents fail on simple tasks?**
   A: LLMs are probabilistic - phrasing, context, and randomness all affect outcomes.

5. **Q: How do you prevent runaway agents?**
   A: Step limits (prevent infinite loops) + token budgets (control costs).

6. **Q: What's LLM-as-Judge?**
   A: Using one AI to evaluate another - powerful but imperfect pattern.

7. **Q: Why not use LangChain/CrewAI/etc?**
   A: Frameworks hide the mechanics. Here you see exactly how agents work - no magic.

## What You'll Learn by Reading This Code

After studying nano-agent, you'll understand:

### Core Agent Concepts
- **The agent loop**: How observe → think → act actually works in code
- **Tool calling**: How LLMs invoke external functions safely
- **Structured output**: Why JSON beats free-text for LLM-to-code communication
- **Context management**: How agents maintain state across steps

### Production Patterns
- **Hybrid evaluation**: Combining fast deterministic checks with flexible AI judgment
- **Safety limits**: Token budgets and step limits to prevent runaway agents
- **Error handling**: Graceful degradation when tools fail or LLMs misbehave
- **Tracing**: Building interpretable logs for debugging

### Real-World Insights
- **LLMs are non-deterministic**: Same prompt, different results
- **Prompt sensitivity**: "Calculate X" vs "What is X?" can determine success
- **Evaluation is hard**: No single judge is perfect
- **Failures are educational**: They reveal system boundaries

### Engineering Lessons
- **Simplicity wins**: 270 lines does what frameworks do in thousands
- **Local-first development**: No API keys, no costs, full control
- **Clear abstractions**: Agent, Model, Tools, Judge - each with one job
- **Educational code**: Optimized for understanding, not production

## Advanced Topics to Explore

Once you understand the basics, try extending nano-agent:

1. **Add new tools**: Weather API, web search, file operations
2. **Implement memory**: Store conversation history between runs
3. **Create custom judges**: Fact-checking, safety validation, output formatting
4. **Add streaming**: Show agent thinking in real-time
5. **Build agent chains**: Multiple agents working together
6. **Add vision support**: Process images with multimodal models

The clean architecture makes these extensions straightforward!

## Contributing

Found a bug? Have an idea? We welcome contributions that maintain simplicity while teaching important concepts.

---

*"The best way to understand agents is to build one from scratch."*

**Ready to dive deeper?** Start with `agent.py` and follow the execution flow. In 30 minutes, you'll understand how AI agents really work.
