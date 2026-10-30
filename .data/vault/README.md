# Password vault

`detox.kdbx` in this folder is an encrypted KeePass database. It stores the passwords the crawler
uses to log in (for example Reddit), grouped by site, one entry per account.

- It is protected by a master password. By default `add-password` remembers it in the macOS login
  keychain (not in this folder) so it isn't asked every run. Skip remembering
  with `NO_REMEMBER=1`. If it stops working, the next command prompts for it and updates it.
- It is gitignored. Only this README is tracked. Never commit the database.
- Add or update a password with `make add-password SERVER=<site> ACCOUNT=<username>`. The database is created on first use.
- List what's saved (no passwords shown) with `make list-passwords`.
- Remove one with `make remove-password SERVER=<site> ACCOUNT=<username>`.
- It is a standard KeePass file, so KeePassXC can open and edit it too.
