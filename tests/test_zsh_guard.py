#!/usr/bin/env python3
"""Runs the guard on commands it must allow or deny; exits non-zero on any mismatch."""
import json
import os
import subprocess
import sys

GUARD = os.path.join(os.path.dirname(__file__), "..", "hooks", "zsh_guard.py")

CASES = [
    ("allow", "D=/opt/app; V=$D/../venv/bin/python; cd $D && $V -m pytest -q"),
    ("allow", "X=echo; $X hi"),
    ("allow", "G=/usr/local/bin/tool.sh; $G fetch"),
    ("allow", "A=/opt/bin; B=${A}/tool; $B --version"),
    ("allow", "ssh host 'P=\"psql -h db\"; $P -c select'"),
    ("allow", "echo \"for x in $list\""),
    ("allow", "arr=(a b c); for x in $arr; do echo $x; done"),
    ("deny", "K=\"kubectl --context c -n ns\"; $K get pods"),
    ("deny", "L=\"python3 tool.py\"; $L run \"x\""),
    ("deny", "F=$(git ls-files); for f in $F; do echo $f; done"),
    ("deny", "for r in \"repo-a 1\" \"repo-b 2\"; do set -- $r; echo $2; done"),
    ("deny", "X=\"a b\"; V=$X/bin; $V run"),
    ("deny", "V=$(which python3); $V -V"),
    ("deny", "A=$B; B=$A; $A x"),
]


def run(cmd):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    out = subprocess.run([sys.executable, GUARD], input=payload, capture_output=True, text=True).stdout
    return "deny" if '"deny"' in out else "allow"


failures = 0
for want, cmd in CASES:
    got = run(cmd)
    failures += got != want
    print(f"{'PASS' if got == want else 'FAIL'} {want:5} | {cmd}")
print(f"{len(CASES) - failures}/{len(CASES)} passed")
sys.exit(1 if failures else 0)
