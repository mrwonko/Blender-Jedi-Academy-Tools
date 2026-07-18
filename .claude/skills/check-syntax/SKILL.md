---
name: check-syntax
description: Validate Python syntax for one or more files via ast.parse, without executing them. Use after editing any .py file in this repo.
---

# Check Python syntax

A fixed, directly-executable script instead of an ad-hoc `python3 -c "import ast; ...`
invocation, so it can be whitelisted in permission settings by exact path rather than needing a
broader rule for arbitrary `python3 -c`/`-m` execution.

```
.claude/skills/check-syntax/check_syntax.py <file> [<file> ...]
```

Exit 0 if all files parse; exit 1 and prints `SYNTAX ERROR in <file>: ...` to stderr for any that
don't. Takes explicit file path arguments and does no shell substitution of its own — that's what
makes it safe to whitelist by exact path, unlike the ad-hoc `python3 -c` invocation it replaces,
which would need a much broader rule to allow arbitrary code.
