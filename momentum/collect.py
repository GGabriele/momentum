import click

from datetime import datetime

from .utils import collect_history, get_sp500_symbols


@click.command()
@click.pass_context
@click.option("--start", default="2020-6-1", help="Start date in Y-M-D format.")
@click.option(
    "--end",
    default=datetime.today().date(),
    help="End date in Y-M-D format.",
)
def collect(ctx, start, end, **kwargs):
    """Collect and store historical SP500 data."""
    config = ctx.obj["config"]
    exclude = config["exclude_symbols"]
    include = config["include_symbols"]
    symbols = get_sp500_symbols(exclude, include=include)
    # Add SPY ticker to the symbols to include it into history.
    symbols.append("SPY")
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(str(end), "%Y-%m-%d")
    collect_history(start, end, symbols)


def add_commands(cli):
    cli.add_command(collect)
