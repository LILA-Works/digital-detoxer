from dataclasses import dataclass
from pathlib import Path

from pykeepass import PyKeePass, create_database
from pykeepass.exceptions import CredentialsError

VAULT_PATH = Path(".data/vault/detox.kdbx")


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


class VaultError(Exception):
    pass


def vault_exists() -> bool:
    return VAULT_PATH.exists()


def fetch_credentials(server: str, account: str, master_password: str) -> Credentials:
    """Look up the password for `account` on `server` (e.g. `reddit.com`) in the KeePass vault."""
    db = _open(master_password)
    group = db.find_groups(name=server, first=True)
    entry = next((e for e in group.entries if e.username == account), None) if group else None
    if entry is None or entry.password is None:
        raise VaultError(f"No password for account {account!r} on {server!r} in {VAULT_PATH}.")
    return Credentials(username=account, password=entry.password)


def store_password(server: str, account: str, password: str, master_password: str) -> bool:
    """Add or update the password for `account` on `server`. Creates the vault if missing.

    Returns True if an existing entry was updated, False if a new one was added.
    """
    if vault_exists():
        db = _open(master_password)
    else:
        VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = create_database(str(VAULT_PATH), password=master_password)

    group = db.find_groups(name=server, first=True) or db.add_group(db.root_group, server)
    entry = next((e for e in group.entries if e.username == account), None)
    if entry:
        entry.password = password
    else:
        db.add_entry(group, account, account, password, url=f"https://{server}")
    db.save()
    return entry is not None


def _open(master_password: str) -> PyKeePass:
    if not vault_exists():
        raise VaultError(f"No vault at {VAULT_PATH}. Run `make add-password` to create it.")
    try:
        return PyKeePass(str(VAULT_PATH), password=master_password)
    except CredentialsError as e:
        raise VaultError("Wrong master password.") from e
