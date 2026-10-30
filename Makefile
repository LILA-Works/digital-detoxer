.PHONY: setup add-password update upgrade cli test-browser crawl-reddit

########################################
# Setup
########################################

# For setting up the development environment. Installs the dependencies without upgrading them.
setup:
	uv sync --all-packages --group dev --frozen
	mkdir -p .data/vault

# For when updating a new dependency. Updates the lock file to the latest versions.
update:
	uv sync --all-packages --group dev

# For upgrading all dependencies to their latest versions. Bumps all versions to latest.
upgrade:
	uv sync --all-packages --group dev --upgrade

# Saves a login into the encrypted password vault (created on first use). Requires ACCOUNT and SERVER. e.g. make add-password SERVER=reddit.com ACCOUNT=alice
# Password is managed by https://keepassxc.org/
# First time running this command will lead a prompt for providing a master password.
#   $ uv run detox add-password --account alice --server reddit.com
#   No vault yet. Choose a master password for the new one.
#   Master password: 
#   Repeat for confirmation: 
#   Password for alice on reddit.com: 
add-password:
	uv run detox add-password --account $(ACCOUNT) $(if $(SERVER),--server $(SERVER))

########################################
# App via CLI
########################################

cli:
	uv run detox --help

# Opens a page and keeps the browser open until a key is pressed. Optional: make test-browser URL=https://example.com
test-browser:
	uv run detox test-browser --keep-open $(if $(URL),--url $(URL))

# Logs into Reddit if needed. Requires ACCOUNT, whose password must be in the vault (see add-password). e.g. make crawl-reddit ACCOUNT=alice
crawl-reddit:
	uv run detox crawl-reddit --keep-open --account $(ACCOUNT)

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