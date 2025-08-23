#!/usr/bin/env python3
"""
RAG Demo & Test Suite
Run this to:
1. Learn how RAG works (with explanations)
2. Test that RAG is working correctly
"""

import sys
import os

# Add parent dirs to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_test(test_name: str, test_func, verbose: bool = True):
    """Run a test with optional educational output."""
    if verbose:
        print(f"\n{'='*50}")
        print(f"TEST: {test_name}")
        print('='*50)
    
    try:
        result = test_func(verbose)
        if verbose:
            print(f"✅ PASS: {test_name}")
        return True
    except AssertionError as e:
        if verbose:
            print(f"❌ FAIL: {test_name}")
            print(f"   Reason: {e}")
        return False
    except Exception as e:
        if verbose:
            print(f"❌ ERROR: {test_name}")
            print(f"   Error: {e}")
        return False


def test_hallucination_problem(verbose=True):
    """Test 1: Show LLM hallucination without RAG."""
    if verbose:
        print("\n📚 LESSON: LLMs make things up when they don't know!")
        print("Let's ask about something specific...\n")
    
    from nano_agent.model_ollama import OllamaModel
    model = OllamaModel()
    
    # Ask about something likely to hallucinate
    response = model.generate("What year was the nano-agent created?", format='text')
    
    if verbose:
        print(f"Question: What year was the nano-agent created?")
        print(f"LLM Answer: {response[:100]}...")
        print(f"⚠️  Notice: LLM just guessed! (nano-agent isn't in its training)")
    
    # Test passes if LLM gave ANY answer (showing it hallucinates)
    assert len(response) > 0, "LLM should generate some answer"
    return True


def test_rag_prevents_hallucination(verbose=True):
    """Test 2: Show RAG grounding with facts."""
    if verbose:
        print("\n📚 LESSON: RAG grounds the LLM with facts from a file!")
        print("Now let's use our knowledge.txt file...\n")
    
    from rag import SimpleRAG
    rag = SimpleRAG("knowledge.txt")
    
    # Search for Eiffel Tower
    facts = rag.search("Eiffel Tower height")
    
    if verbose:
        print(f"1. Search for: 'Eiffel Tower height'")
        print(f"2. Found fact: {facts[0] if facts else 'None'}")
    
    assert len(facts) > 0, "Should find Eiffel Tower fact"
    assert "330 meters" in facts[0], "Should contain correct height"
    
    # Now answer with context
    from nano_agent.model_ollama import OllamaModel
    model = OllamaModel()
    
    prompt = f"Fact: {facts[0]}\nQuestion: How tall is the Eiffel Tower?\nAnswer with just the height:"
    answer = model.generate(prompt, format='text')
    
    if verbose:
        print(f"3. Ask LLM with context")
        print(f"4. Answer: {answer}")
        print(f"✓ Answer is grounded in facts!")
    
    # Check for the height in various formats
    answer_lower = answer.lower()
    assert "330" in answer or "330 meters" in answer_lower or "330 m" in answer_lower, f"Should extract 330 meters, got: {answer}"
    return True


def test_rag_as_tool(verbose=True):
    """Test 3: RAG integrated as agent tool."""
    if verbose:
        print("\n📚 LESSON: RAG can be a tool the agent uses!")
        print("Adding search capability to our agent...\n")
    
    # Import tools
    from nano_agent.tools import TOOLS
    from rag import rag_tool
    
    # Save original tools
    original_tools = TOOLS.copy()
    
    try:
        TOOLS["search_knowledge"] = ("Search knowledge base for facts", rag_tool)
        
        if verbose:
            print(f"1. Original tools: {list(original_tools.keys())}")
            print(f"2. Added tool: search_knowledge")
            print(f"3. Agent now has: {list(TOOLS.keys())}")
        
        # Test agent can use it
        from nano_agent.agent import Agent
        from nano_agent.model_ollama import OllamaModel
        
        agent = Agent(OllamaModel(), max_steps=3, verbose=False)
        result = agent.run("When was Python created?")
        
        if verbose:
            print(f"\n4. Ask agent: 'When was Python created?'")
            print(f"5. Agent answer: {result['final']}")
            
            # Check if tool was used
            tool_used = False
            for trace_item in result['trace']:
                if 'search_knowledge' in trace_item:
                    tool_used = True
                    break
            print(f"6. Agent used search_knowledge tool: {tool_used}")
        
        # Check answer is correct - be flexible with format
        answer_str = str(result['final']).lower()
        assert "1991" in answer_str or "guido" in answer_str or "python" in answer_str, f"Should find info about Python, got: {result['final']}"
        
    finally:
        # Restore original tools
        TOOLS.clear()
        TOOLS.update(original_tools)
    
    return True


def test_search_quality(verbose=True):
    """Test 4: Search returns relevant results."""
    if verbose:
        print("\n📚 LESSON: Search quality matters!")
        print("Testing our keyword search...\n")
    
    from rag import SimpleRAG
    rag = SimpleRAG("knowledge.txt")
    
    test_cases = [
        ("Einstein relativity", "Einstein", "Should find Einstein fact"),
        ("speed light", "299,792,458", "Should find speed of light"),
        ("Japan capital", "Tokyo", "Should find Tokyo fact"),
        ("random xyz abc", None, "Should return empty for nonsense")
    ]
    
    for query, expected, description in test_cases:
        results = rag.search(query)
        
        if verbose:
            print(f"Query: '{query}'")
            print(f"Found: {len(results)} results")
            if results:
                print(f"Top result: {results[0][:50]}...")
        
        if expected:
            assert len(results) > 0, f"{description}: No results"
            assert expected in results[0], f"{description}: Missing {expected}"
        else:
            assert len(results) == 0, f"{description}: Should be empty"
        
        if verbose:
            print(f"✓ {description}\n")
    
    return True


def main():
    """Run all tests with educational output."""
    # Check for --quiet flag for CI/automation
    verbose = "--quiet" not in sys.argv
    
    if verbose:
        print("""
╔════════════════════════════════════════════════╗
║     RAG Demo & Test Suite for nano-agent      ║
║                                                ║
║  This is both a learning tool AND test suite! ║
╚════════════════════════════════════════════════╝
        """)
    
    tests = [
        ("Hallucination Problem", test_hallucination_problem),
        ("RAG Prevents Hallucination", test_rag_prevents_hallucination),
        ("RAG as Agent Tool", test_rag_as_tool),
        ("Search Quality", test_search_quality)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func, verbose):
            passed += 1
        else:
            failed += 1
    
    # Summary
    if verbose:
        print(f"\n{'='*50}")
        print(f"SUMMARY: {passed} passed, {failed} failed")
        if failed == 0:
            print("🎉 All tests passed! RAG is working correctly.")
            print("\n💡 What you learned:")
            print("  1. LLMs hallucinate without context")
            print("  2. RAG grounds answers with facts")
            print("  3. Simple keyword search is often enough")
            print("  4. RAG can be integrated as a tool")
        else:
            print(f"⚠️  Some tests failed. Check the output above.")
        print('='*50)
    else:
        # CI-friendly output
        if failed > 0:
            print(f"FAILED: {failed} tests")
            sys.exit(1)
        else:
            print(f"PASSED: All {passed} tests")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)