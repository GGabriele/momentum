import click
import json

from . import portfolio, market, collect


@click.group()
@click.option(
    "--config", required=True, default="./config.json", help="Config file path."
)
@click.pass_context
def cli(ctx, **kwargs):
    """CLI entry point."""
    with open(kwargs["config"], "r") as f:
        ctx.obj["config"] = json.loads(f.read())


def run():
    cli(obj={})


portfolio.add_commands(cli)
market.add_commands(cli)
collect.add_commands(cli)

if __name__ == "__main__":
    run()
