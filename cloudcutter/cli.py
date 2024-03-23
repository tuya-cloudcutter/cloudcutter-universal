#  Copyright (c) Kuba Szczodrzyński 2023-9-2.

from logging import DEBUG

import click
from ltchiptool.util.logging import LoggingHandler

from .core import Cloudcutter


@click.command()
def cli():
    logger = LoggingHandler.get()
    logger.level = DEBUG
    cloudcutter = Cloudcutter()
    cloudcutter.entrypoint()


if __name__ == "__main__":
    cli()
