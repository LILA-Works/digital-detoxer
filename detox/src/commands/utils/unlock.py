from collections.abc import Callable

import click

from detox.src.vault import (
    VaultError,
    WrongMasterPassword,
    recall_master_password,
    remember_master_password,
)


def with_vault[T](action: Callable[[str], T]) -> T:
    """Run `action(master_password)`, using the remembered master password or prompting for it.

    If the remembered one no longer works, prompts instead and updates what is remembered.
    """
    remembered = recall_master_password()
    try:
        if remembered is not None:
            try:
                return action(remembered)
            except WrongMasterPassword:
                click.echo("The remembered master password no longer works.")
        master = click.prompt("Master password", hide_input=True)
        result = action(master)
        if remembered is not None:
            remember_master_password(master)
        return result
    except VaultError as e:
        raise click.ClickException(str(e)) from e
