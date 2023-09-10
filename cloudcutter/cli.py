#  Copyright (c) Kuba Szczodrzyński 2023-9-2.

import click

from .core import Cloudcutter


@click.command()
def cli():
    cloudcutter = Cloudcutter()
    cloudcutter.entrypoint()


if __name__ == "__main__":
    cli()
