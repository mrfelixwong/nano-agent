#!/bin/bash
# Test script for extensions - separate from main smoke.sh

echo "================================"
echo "EXTENSION TESTS (not part of main)"
echo "================================"

# Test RAG extension if it exists
if [ -d "01_rag" ]; then
    echo ""
    echo "Testing RAG extension..."
    cd 01_rag
    python demo.py --quiet && echo "✓ RAG extension tests pass" || echo "✗ RAG extension tests fail"
    cd ..
fi

# Future extensions can be added here
# if [ -d "02_memory" ]; then ...

echo ""
echo "Extension tests complete"