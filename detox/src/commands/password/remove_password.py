import click

from detox.src.commands.utils.unlock import with_vault
from detox.src.vault import remove_password


@click.command("remove-password")
@click.option("--server", required=True, help="Site the login is for, e.g. reddit.com.")
@click.option("--account", required=True, help="Username on that site.")
@click.confirmation_option(prompt="Remove this password from the vault?")
def remove_password_command(server: str, account: str) -> None:
    """Delete a saved login from the password vault."""
    with_vault(lambda master: remove_password(server, account, master))
    click.echo(f"Removed {account} on {server}.")
