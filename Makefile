.PHONY: setup update upgrade

########################################
# Setup
########################################

# For setting up the development environment. Installs the dependencies without upgrading them.
setup:
	uv sync --all-packages --group dev --frozen

# For when updating a new dependency. Updates the lock file to the latest versions.
update:
	uv sync --all-packages --group dev

# For upgrading all dependencies to their latest versions. Bumps all versions to latest.
upgrade:
	uv sync --all-packages --group dev --upgrade

########################################
# App via CLI
########################################

cli:
	uv run detox

########################################
# CI
########################################

# For running in CI
ci: format-check lint-check typecheck

# For running in CI to block without making changes.
format-check:
	@printf '\n==================== 🔍 format-check ====================\n'
	uv run black --check .

# For running in CI to block without making changes.
lint-check:
	@printf '\n==================== 🔍 lint-check ====================\n'
	uv run ruff check .

# Run before commit. For making sure there are no type errors.
typecheck:
	@printf '\n==================== 🧐 typecheck ====================\n'
	uv run --no-sync basedpyright


# Run before commit. For formatting the code according to style guidelines.
format:
	@printf '\n==================== ✨ format ====================\n'
	uv run black .

# Run before commit. For fixing lint issues.
lint:
	@printf '\n==================== 🧹 lint ====================\n'
	uv run ruff check --fix .

# Run before commit. Formats and lints.
fix: format lint