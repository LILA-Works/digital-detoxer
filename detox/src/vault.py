from dataclasses import dataclass
from pathlib import Path
from typing import cast

import keyring
from keyring.errors import KeyringError
from pykeepass import PyKeePass, create_database
from pykeepass.entry import Entry
from pykeepass.exceptions import CredentialsError
from pykeepass.group import Group

VAULT_PATH = Path(".data/vault/detox.kdbx")
KEYRING_SERVICE = "detox-vault"
KEYRING_USER = "master-password"


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


class VaultError(Exception):
    pass


class WrongMasterPassword(VaultError):
    pass


def recall_master_password() -> str | None:
    """The master password remembered in the macOS login keychain, if any."""
    try:
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    except KeyringError:
        return None


def remember_master_password(master_password: str) -> None:
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, master_password)
    except KeyringError as e:
        raise VaultError(f"Could not save the master password to the keychain: {e}") from e


def vault_exists() -> bool:
    return VAULT_PATH.exists()


def fetch_credentials(server: str, account: str, master_password: str) -> Credentials:
    """Look up the password for `account` on `server` (e.g. `reddit.com`) in the KeePass vault."""
    db = _open(master_password)
    entry = _find_entry(db, server, account)
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

    group = _find_group(db, server) or db.add_group(_root(db), server)
    entry = _find_entry(db, server, account)
    if entry:
        entry.password = password
    else:
        db.add_entry(group, account, account, password, url=f"https://{server}")
    db.save()
    return entry is not None


def list_accounts(master_password: str) -> list[tuple[str, str]]:
    """All saved (server, account) pairs, sorted. Never includes passwords."""
    db = _open(master_password)
    pairs = [(g.name, e.username) for g in _root(db).subgroups for e in g.entries if g.name]
    return sorted((server, account) for server, account in pairs if account)


def remove_password(server: str, account: str, master_password: str) -> None:
    """Delete the entry for `account` on `server`, and its group if that leaves it empty."""
    db = _open(master_password)
    group = _find_group(db, server)
    entry = _find_entry(db, server, account)
    if group is None or entry is None:
        raise VaultError(f"No password for account {account!r} on {server!r} in {VAULT_PATH}.")
    db.delete_entry(entry)
    if not cast(list[Entry], group.entries):
        db.delete_group(group)
    db.save()


def _root(db: PyKeePass) -> Group:
    return cast(Group, db.root_group)


def _find_group(db: PyKeePass, server: str) -> Group | None:
    return cast(Group | None, db.find_groups(name=server, first=True))


def _find_entry(db: PyKeePass, server: str, account: str) -> Entry | None:
    group = _find_group(db, server)
    entries = cast(list[Entry], group.entries) if group else []
    return next((e for e in entries if e.username == account), None)


def _open(master_password: str) -> PyKeePass:
    if not vault_exists():
        raise VaultError(f"No vault at {VAULT_PATH}. Run `make add-password` to create it.")
    try:
        return PyKeePass(str(VAULT_PATH), password=master_password)
    except CredentialsError as e:
        raise WrongMasterPassword("Wrong master password.") from e
