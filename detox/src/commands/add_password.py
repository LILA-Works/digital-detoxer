import click

from detox.src.vault import VaultError, remember_master_password, store_password, vault_exists


@click.command("add-password")
@click.option("--server", required=True, help="Site the login is for, e.g. reddit.com.")
@click.option("--account", required=True, help="Username on that site.")
@click.option(
    "--remember/--no-remember",
    default=True,
    help="Remember the master password in the macOS login keychain so it isn't asked every run.",
)
def add_password(server: str, account: str, remember: bool) -> None:
    """Save (or update) a login in the password vault, creating the vault on first use."""
    creating = not vault_exists()
    if creating:
        click.echo("No vault yet. Choose a master password for the new one.")
    master = click.prompt("Master password", hide_input=True, confirmation_prompt=creating)
    password = click.prompt(f"Password for {account} on {server}", hide_input=True)
    try:
        updated = store_password(server, account, password, master)
        if remember:
            remember_master_password(master)
    except VaultError as e:
        raise click.ClickException(str(e)) from e
    click.echo(f"{'Updated' if updated else 'Saved'} {account} on {server}.")
    if remember:
        click.echo("Master password remembered in the macOS login keychain.")
