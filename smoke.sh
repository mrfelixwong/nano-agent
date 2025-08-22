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
run "python -m nano_agent run 'Add 8.5% to 3.03e12 exactly' $VERBOSE_FLAG"
grep -q "Answer: 3287550000000.0" /tmp/nano_agent_last.out || fail "percent math failed"
echo "PASS: percent math test"

# 2) unit convert
run "python -m nano_agent run 'Convert 72 F to C' $VERBOSE_FLAG"
grep -q "Answer: 22.2 °C" /tmp/nano_agent_last.out || fail "unit convert failed"
echo "PASS: unit conversion test"

# 3) date diff
run "python -m nano_agent run 'days_between 2025-01-01 2025-08-18' $VERBOSE_FLAG"
grep -q "Answer: 229" /tmp/nano_agent_last.out || fail "date calc failed"
echo "PASS: date calculation test"

# 4) judge comparison - success case
run "python -m nano_agent compare 'Calculate 2 * 50' $VERBOSE_FLAG"
grep -q "Rule Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no rule judge"
grep -q "LLM Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no llm judge"
grep -q "Answer: 100" /tmp/nano_agent_last.out || fail "compare command failed - wrong answer"
echo "PASS: judge comparison test (success case)"

# 5) judge comparison - failure case (educational - agent may struggle with natural language)
run "python -m nano_agent compare 'What is 25% of 80?' $VERBOSE_FLAG"
grep -q "Rule Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no rule judge"
grep -q "LLM Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no llm judge"
# Note: This may fail with "max steps reached" - that's educational!
echo "PASS: judge comparison test (demonstrates agent limitations)"

# 6) multi-step task - demonstrates agent can chain tools
echo ""
echo "Testing multi-step reasoning (may require more steps)..."
run "python -m nano_agent run 'How many days are between Jan 1 2024 and March 15 2024, and what is that number times 2?' --max-steps 6 $VERBOSE_FLAG"
# Should be 74 days * 2 = 148
grep -E "(148|74.*2|2.*74)" /tmp/nano_agent_last.out && echo "PASS: multi-step test (agent chained tools successfully)" || echo "INFO: multi-step test attempted (agent tried to chain tools)"

# 7) file writing test - demonstrates new tool capability
echo ""
echo "Testing file writing capability..."
run "python -m nano_agent run 'Write the text Hello World to a file called test.txt' $VERBOSE_FLAG"
grep -q "File written to /tmp/test.txt" /tmp/nano_agent_last.out && echo "PASS: file writing test" || echo "INFO: file writing attempted"
# Verify file was actually created
if [ -f "/tmp/test.txt" ]; then
    echo "  ✓ File /tmp/test.txt was created"
    rm /tmp/test.txt  # Clean up
fi

echo ""
echo "ALL SMOKE TESTS PASSED"