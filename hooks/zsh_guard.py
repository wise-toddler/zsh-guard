#!/usr/bin/env python3
"""Deny Bash commands with zsh word-split traps: $VAR as a command word, for x in $list, set -- $s."""
import json, os, re, sys
d = json.load(sys.stdin)
cmd = (d.get("tool_input") or {}).get("command") or ""
if cmd.lstrip().startswith("bash -c") or cmd.lstrip().startswith("bash <<") or "\nbash -c" in cmd:
    sys.exit(0)


def strip_inert(text):
    """Drop heredoc bodies and single-quoted strings: other programs read them, not zsh."""
    out, delim = [], None
    for line in text.split("\n"):
        if delim is not None:
            if line.strip() == delim:
                delim = None
            continue
        m = re.search(r"(?<!<)<<-?(?!<)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
        if m:
            delim = m.group(2)
        out.append(line)
    return re.sub(r"'[^']*'", "''", "\n".join(out))


code = strip_inert(cmd)
# Rules scan without double-quoted text: nothing inside quotes sits in command or word-list position.
scan = re.sub(r'"(?:[^"\\]|\\.)*"', '""', code)


def kind(name, depth=0):
    """How NAME was last assigned in this command: array, word (one literal word), or unknown."""
    hits = re.findall(r"(?:^|[\s;&|(])" + re.escape(name) + r"=(\([^)]*\)|\"[^\"]*\"|\S*)", code)
    if not hits:
        env = os.environ.get(name)
        return "word" if env and not re.search(r"\s", env) else "unknown"
    v = hits[-1]
    if v.startswith("("):
        return "array"
    v = v.strip('"')
    if not v or depth > 3 or re.search(r"\s|`|\$\(", v):
        return "unknown"
    # A value built only from single-word variables and literal text is still one word.
    refs = re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", v)
    return "word" if all(r != name and kind(r, depth + 1) == "word" for r in refs) else "unknown"


VAR = r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?"
rules = [
    (r"(?:^|[;&|(]\s*|\bthen\s+|\bdo\s+)" + VAR + r"(?=\s|$)",
     "variable used as a command word ($M ...). zsh does not word-split: define a function m(){ ...; } or use ${=M}."),
    (r"\bfor\s+\w+\s+in\s+((?:" + VAR + r"\s*)+)(?=;|$|\bdo\b)",
     "for x in $list: zsh gives one iteration. Use ${=list}, an array, or $(...) output."),
    (r"\bset\s+--\s+" + VAR, "set -- $s: not split in zsh. Use read -r a b <<< \"$s\" or ${=s}."),
]
for pat, why in rules:
    for m in re.finditer(pat, scan, re.M):
        names = re.findall(VAR, m.group(0))
        if names and all(kind(n) in ("array", "word") for n in names):
            continue
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
              "permissionDecisionReason": f"zsh-guard: {why}"}}))
        sys.exit(0)
sys.exit(0)
