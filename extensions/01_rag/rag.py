"""Simple RAG implementation for educational purposes."""

class SimpleRAG:
    def __init__(self, knowledge_file="knowledge.txt"):
        """Load facts from file."""
        try:
            with open(knowledge_file, 'r') as f:
                self.facts = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            # Try with full path for extension
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_path = os.path.join(current_dir, "knowledge.txt")
            with open(knowledge_path, 'r') as f:
                self.facts = [line.strip() for line in f if line.strip()]
    
    def search(self, query: str, top_k: int = 3) -> list:
        """Find relevant facts using keyword matching."""
        query_words = query.lower().split()
        scored_facts = []
        
        for fact in self.facts:
            fact_lower = fact.lower()
            # Score = how many query words appear in fact
            score = sum(1 for word in query_words if word in fact_lower)
            if score > 0:
                scored_facts.append((score, fact))
        
        # Return top matches
        scored_facts.sort(reverse=True, key=lambda x: x[0])
        return [fact for score, fact in scored_facts[:top_k]]


def rag_tool(query: str) -> str:
    """Search knowledge base and answer questions."""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    knowledge_path = os.path.join(current_dir, "knowledge.txt")
    
    rag = SimpleRAG(knowledge_path)
    
    # 1. RETRIEVE relevant facts
    facts = rag.search(query)
    
    if not facts:
        return "No information found in knowledge base"
    
    # 2. Create context
    context = "\n".join(facts)
    
    # 3. AUGMENT prompt with context
    prompt = f"""Based on these facts:
{context}

Question: {query}
Answer using ONLY the facts above (or say "not found"):"""
    
    # 4. GENERATE answer from context
    import sys
    import os
    # Add parent dirs to path to import nano_agent
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from nano_agent.model_ollama import OllamaModel
    model = OllamaModel()
    answer = model.generate(prompt, format='text')
    
    return answer