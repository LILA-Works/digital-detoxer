# Password vault

`detox.kdbx` in this folder is an encrypted KeePass database. It stores the passwords the crawler
uses to log in (for example Reddit), grouped by site, one entry per account.

- It is protected by a master password, which is prompted for at run time and never stored.
- It is gitignored. Only this README is tracked. Never commit the database.
- Add or update a password with `make add-password ACCOUNT=<username>` (optional `SERVER=<site>`,
  default `reddit.com`). The database is created on first use.
- It is a standard KeePass file, so KeePassXC can open and edit it too.
