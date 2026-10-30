import click

APP_NAME = "Digital Detoxer"


def notify(message: str) -> None:
    """Deliver a notification. For now this just prints to the console."""
    click.echo(f"[{APP_NAME}] {message}")
