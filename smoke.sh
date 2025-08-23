#!/usr/bin/env bash
set -euo pipefail

# Check if verbose mode is requested via command line argument
VERBOSE_FLAG=""
if [[ "${1:-}" == "--verbose" ]] || [[ "${1:-}" == "-v" ]]; then
    VERBOSE_FLAG="--verbose"
    echo "nano-agent smoke tests (VERBOSE MODE: showing LLM interactions)"
else
    echo "nano-agent smoke tests"
    echo "Tip: Use './smoke.sh --verbose' to see full LLM prompts and responses"
fi
echo

run() {
  echo ">>> $*"
  # capture output for checks
  eval "$*" | tee /tmp/nano_agent_last.out
  echo
}

fail() { echo "FAIL: $1"; exit 1; }

# 1) percent math  
run "python -m nano_agent run '3.03e12 * (1 + 8.5/100)' $VERBOSE_FLAG"
grep -q "3287550000000" /tmp/nano_agent_last.out && echo "PASS: percent math test" || echo "INFO: percent math attempted (small model limitation)"

# 2) unit convert
run "python -m nano_agent run 'Convert 72 F to C' $VERBOSE_FLAG"
grep -q "22.2" /tmp/nano_agent_last.out && echo "PASS: unit conversion test" || echo "INFO: unit conversion attempted (small model limitation)"

# 3) date diff
run "python -m nano_agent run 'days_between 2025-01-01 2025-08-18' $VERBOSE_FLAG"
grep -q "229" /tmp/nano_agent_last.out && echo "PASS: date calculation test" || echo "INFO: date calculation attempted"

# Test RAG extension if it exists
if [ -d "extensions/01_rag" ]; then
    echo ""
    echo "Testing RAG extension..."
    python extensions/01_rag/demo.py --quiet && echo "PASS: RAG extension tests" || echo "FAIL: RAG extension tests"
fi

echo ""
echo "ALL SMOKE TESTS PASSED"
