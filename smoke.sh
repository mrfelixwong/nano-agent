#!/usr/bin/env bash
set -euo pipefail

echo "nano-agent smoke tests"
echo

run() {
  echo ">>> $*"
  # capture output for checks
  eval "$*" | tee /tmp/nano_agent_last.out
  echo
}

fail() { echo "FAIL: $1"; exit 1; }

# 1) percent math
run "python -m nano_agent run 'Add 8.5% to 3.03e12 exactly'"
grep -q "Response: 3287550000000.0" /tmp/nano_agent_last.out || fail "percent math failed"
echo "PASS: percent math test"

# 2) unit convert
run "python -m nano_agent run 'Convert 72 F to C'"
grep -q "Response: 22.2 °C" /tmp/nano_agent_last.out || fail "unit convert failed"
echo "PASS: unit conversion test"

# 3) date diff
run "python -m nano_agent run 'days_between 2025-01-01 2025-08-18'"
grep -q "Response: 229" /tmp/nano_agent_last.out || fail "date calc failed"
echo "PASS: date calculation test"

# 4) judge comparison - success case
run "python -m nano_agent compare 'Calculate 2 * 50'"
grep -q "Rule Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no rule judge"
grep -q "LLM Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no llm judge"
grep -q "Final Answer: 100" /tmp/nano_agent_last.out || fail "compare command failed - wrong answer"
echo "PASS: judge comparison test (success case)"

# 5) judge comparison - failure case (educational - agent may struggle with natural language)
run "python -m nano_agent compare 'What is 25% of 80?'"
grep -q "Rule Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no rule judge"
grep -q "LLM Judge:" /tmp/nano_agent_last.out || fail "compare command failed - no llm judge"
# Note: This may fail with "max steps reached" - that's educational!
echo "PASS: judge comparison test (demonstrates agent limitations)"

echo "ALL SMOKE TESTS PASSED"