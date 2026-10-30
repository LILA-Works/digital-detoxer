import click

from detox.src.vault import VaultError, store_password, vault_exists


@click.command("add-password")
@click.option("--server", show_default=True, help="Site the login is for.")
@click.option("--account", required=True, help="Username on that site.")
def add_password(server: str, account: str) -> None:
    """Save (or update) a login in the password vault, creating the vault on first use."""
    creating = not vault_exists()
    if creating:
        click.echo("No vault yet. Choose a master password for the new one.")
    master = click.prompt("Master password", hide_input=True, confirmation_prompt=creating)
    password = click.prompt(f"Password for {account} on {server}", hide_input=True)
    try:
        updated = store_password(server, account, password, master)
    except VaultError as e:
        raise click.ClickException(str(e)) from e
    click.echo(f"{'Updated' if updated else 'Saved'} {account} on {server}.")
