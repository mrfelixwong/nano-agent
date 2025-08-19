#!/usr/bin/env bash
set -euo pipefail

echo "🔎 nano-agent smoke tests (expects Ollama running llama3.1)"
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
grep -q "FINAL: 3287550000000.0" /tmp/nano_agent_last.out || fail "percent math failed"
echo "PASS: percent math test"

# 2) unit convert
run "python -m nano_agent run 'Convert 72 F to C'"
grep -q "FINAL: 22.2" /tmp/nano_agent_last.out || fail "unit convert failed"
echo "PASS: unit conversion test"

# 3) date diff
run "python -m nano_agent run 'days between 2025-01-01 2025-08-18'"
grep -q "FINAL: 229" /tmp/nano_agent_last.out || fail "date calc failed"
echo "PASS: date calculation test"

echo "ALL SMOKE TESTS PASSED"

