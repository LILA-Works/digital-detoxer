import click

from detox.src.commands.add_password import add_password
from detox.src.commands.crawl_reddit import crawl_reddit
from detox.src.commands.list_passwords import list_passwords
from detox.src.commands.remove_password import remove_password_command
from detox.src.commands.test_browser import test_browser


@click.group()
def main() -> None:
    """Digital detoxer."""


main.add_command(test_browser)
main.add_command(crawl_reddit)
main.add_command(add_password)
main.add_command(list_passwords)
main.add_command(remove_password_command)


if __name__ == "__main__":
    main()
