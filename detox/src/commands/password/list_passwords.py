import click

from detox.src.commands.utils.unlock import with_vault
from detox.src.vault import list_accounts


@click.command("list-passwords")
def list_passwords() -> None:
    """List the saved logins (site and username only, never the passwords)."""
    accounts = with_vault(list_accounts)
    if not accounts:
        click.echo("No passwords saved.")
    for server, account in accounts:
        click.echo(f"{server}\t{account}")
