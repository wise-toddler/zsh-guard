# zsh-guard

A Claude Code plugin for people whose shell is zsh.

Claude writes Bash commands as if the shell were bash. zsh does not split an unquoted `$var` into words, so some of those commands break, often silently. This plugin adds a `PreToolUse` hook on the Bash tool that blocks them and tells Claude how to rewrite them.

## What it blocks

| Pattern | What zsh does | Fix it suggests |
|---|---|---|
| `K="kubectl -n ns"; $K get pods` | runs a command literally named `kubectl -n ns` | a function, or `${=K}` |
| `for f in $files` | one iteration over the whole string | `${=files}`, an array, or `$(...)` |
| `set -- $pair` | `$1` is the whole string | `read -r a b <<< "$pair"` or `${=pair}` |

## What it lets through

- Variables that hold one word, including ones built from other one-word variables (`V=$DIR/bin/python; $V -V`).
- Arrays (`arr=(a b); for x in $arr`).
- Text zsh never runs itself: heredoc bodies, single-quoted strings (for example a script sent over `ssh '...'`), double-quoted text, and `bash -c` commands.

## Install

```
/plugin marketplace add wise-toddler/zsh-guard
/plugin install zsh-guard@zsh-guard
```

Needs `python3` on the PATH.

## Test

```
python3 tests/test_zsh_guard.py
```

## Related tip

zsh also fails on an unmatched glob (`grep --include=*.py` gives `no matches found`). This plugin does not check for that. To make Claude's shells behave like bash there, while keeping your own terminal unchanged, add this to `~/.zshrc`:

```
[[ -n $CLAUDECODE ]] && setopt no_nomatch
```
