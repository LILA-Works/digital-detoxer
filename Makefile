.PHONY: setup add-password list-passwords remove-password update upgrade cli test-browser crawl-reddit summarize-reddit db migrate backward migration

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

# Applies all database migrations to the SQLite db at .data/reddit/reddit.db.
migrate:
	uv run alembic upgrade head

# Rolls back the most recent database migration. Optional: make backward STEPS=2 (default 1)
backward:
	uv run alembic downgrade -$(or $(STEPS),1)

# Generates a migration from model changes. Requires MSG. e.g. make migration MSG="add posts table"
migration:
	uv run alembic revision --autogenerate -m "$(MSG)"

# Saves a login into the encrypted password vault (created on first use). Requires ACCOUNT and SERVER. e.g. make add-password SERVER=reddit.com ACCOUNT=alice
# Password is managed by https://keepassxc.org/
# First time running this command will lead a prompt for providing a master password.
#   $ uv run detox add-password --account alice --server reddit.com
#   No vault yet. Choose a master password for the new one.
#   Master password: 
#   Repeat for confirmation: 
#   Password for alice on reddit.com: 
# The master password is remembered in the macOS login keychain; pass NO_REMEMBER=1 to skip that.
add-password:
	uv run detox add-password --account $(ACCOUNT) --server $(SERVER) $(if $(NO_REMEMBER),--no-remember)

# Deletes a saved login from the vault (asks to confirm). Requires ACCOUNT and SERVER. e.g. make remove-password SERVER=reddit.com ACCOUNT=alice
remove-password:
	uv run detox remove-password --account $(ACCOUNT) --server $(SERVER)

# Lists saved logins (site and username only, never the passwords).
list-passwords:
	uv run detox list-passwords

########################################
# App via CLI
########################################

# Opens the sqlite3 shell on the Reddit db, with column headers and aligned output.
db:
	sqlite3 -header -column .data/reddit/reddit.db

cli:
	uv run detox --help

# Opens a page and keeps the browser open until a key is pressed. Optional: make test-browser URL=https://example.com
test-browser:
	uv run detox test-browser --keep-open $(if $(URL),--url $(URL))

# Logs into Reddit if needed. Requires ACCOUNT, whose password must be in the vault (see add-password). e.g. make crawl-reddit ACCOUNT=alice. Optional: POSTS_PER_SUBREDDIT=5 (default 3)
crawl-reddit:
	uv run detox crawl-reddit --account $(ACCOUNT) $(if $(POSTS_PER_SUBREDDIT),--posts-per-subreddit $(POSTS_PER_SUBREDDIT))

# Summarizes the latest unsummarized posts, then prints a notification with an update on the interesting ones. Requires a running Ollama with the model set in llm.py. Optional: NO_NOTIFY=1, and RESUMMARIZE=1 to overwrite the latest posts' existing summaries (e.g. after a prompt change). e.g. make summarize-reddit RESUMMARIZE=1
summarize-reddit:
	uv run detox summarize-reddit $(if $(NO_NOTIFY),--no-notify) $(if $(RESUMMARIZE),--resummarize)

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