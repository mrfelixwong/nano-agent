# Extension 1: RAG (Retrieval-Augmented Generation)

Learn how to prevent LLM hallucination by grounding answers with facts from a file.

## What You'll Learn

1. **The Problem**: LLMs make things up when they don't know
2. **The Solution**: RAG = Search + Context + Generate
3. **Implementation**: Simple keyword search is often enough
4. **Integration**: How to add RAG as a tool to the agent

## Files

- `knowledge.txt` - Facts database (8 facts about various topics)
- `rag.py` - Simple RAG implementation (40 lines)
- `demo.py` - Combined test suite and learning tool

## Quick Start

```bash
# Run the interactive demo (teaches while testing)
python extensions/01_rag/demo.py

# Run quietly for CI/testing
python extensions/01_rag/demo.py --quiet
```

## How It Works

1. **Load facts** from `knowledge.txt`
2. **Search** for relevant facts using keyword matching
3. **Inject context** into the LLM prompt
4. **Generate answer** based only on provided facts

## Example

Without RAG:
```
Q: "How tall is the Eiffel Tower?"
A: "Around 300 meters" (might be wrong!)
```

With RAG:
```
Q: "How tall is the Eiffel Tower?"
Context: "The Eiffel Tower is 330 meters tall..."
A: "330 meters" (correct from file!)
```

## Adding Your Own Facts

Edit `knowledge.txt` to add any facts you want:
```
Your university was founded in 1850.
The local population is 50,000 people.
```

Then test:
```python
from rag import SimpleRAG
rag = SimpleRAG()
print(rag.search("university"))
```

## Integration with Agent

The demo shows how to add RAG as a tool:
```python
from nano_agent.tools import TOOLS
TOOLS["search"] = ("Search knowledge", rag_tool)
```

Now the agent can search for facts when needed!

## Key Insight

RAG is just "search + prompt engineering" - no magic, just smart context injection.