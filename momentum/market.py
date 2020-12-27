import click

from datetime import datetime, timedelta

from .utils import calculate_averages, retrieve_upstream


@click.command()
@click.pass_context
def market_status(ctx, **kwargs):
    """Get market status information."""
    today = datetime.today().date()
    start = today - timedelta(days=200)
    sp500 = retrieve_upstream(start, today, "SPY").loc[:, "Close"]
    calculate_averages(sp500)


def add_commands(cli):
    cli.add_command(market_status)
