# Convention

- Do not pin versions in `pyproject.toml` dependencies (e.g. `"playwright"`, not `"playwright>=1.64.1"`). `uv.lock` is the source of truth for versions.
- Run `make ci` after making changes to ensure the repo is in a clean state (format, lint and type checks all pass).
