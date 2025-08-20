# 🤖 nano-agent: Learn AI Agents in One Sitting

**Zero frameworks. Pure Python. Built for learning.**

A minimalist AI agent implementation that teaches core agentic patterns without LangChain, CrewAI, or any agent framework. Just 300 lines of readable Python you can understand in 30 minutes.

## 100% Local, Zero API Keys Required

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
- Execution tracing and evaluation
- Interactive playground for experimentation

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

# 4. Start the interactive playground
python -m nano_agent playground
```

**Note:** After initial setup, everything runs offline. No internet needed!

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
- **No setup**: Just type and experiment
- **Safe environment**: All computation is sandboxed

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

## Key Questions This Code Answers

1. **Q: How do agents really work?**
   A: They're loops that repeatedly ask an LLM "what next?" until done.

2. **Q: Why do agents need tools?**
   A: LLMs can't do math, access data, or take actions - tools can.

3. **Q: How do you prevent agent failures?**
   A: Structured output (JSON), retry logic, safety limits, validation.

4. **Q: What makes a good agent?**
   A: Correct results + efficient process + reliable execution.

5. **Q: Why use local LLMs instead of GPT-4?**
   A: Free, private, no rate limits, and perfect for learning. The patterns you learn here work with any LLM.

## Contributing

Found a bug? Have an idea? We welcome contributions that maintain simplicity while teaching important concepts.

---

*"The best way to understand agents is to build one from scratch."*

**Ready to dive deeper?** Start with `agent.py` and follow the execution flow. In 30 minutes, you'll understand how AI agents really work.
