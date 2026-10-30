# Convention

- Do not pin versions in `pyproject.toml` dependencies (e.g. `"playwright"`, not `"playwright>=1.64.1"`). `uv.lock` is the source of truth for versions.
