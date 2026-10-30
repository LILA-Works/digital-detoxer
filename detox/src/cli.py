import click

from detox.src.commands.add_password import add_password
from detox.src.commands.crawl_reddit import crawl_reddit
from detox.src.commands.test_browser import test_browser


@click.group()
def main() -> None:
    """Digital detoxer."""


main.add_command(test_browser)
main.add_command(crawl_reddit)
main.add_command(add_password)


if __name__ == "__main__":
    main()
