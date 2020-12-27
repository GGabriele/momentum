import click

from datetime import datetime

from .utils import (
    get_sp500_symbols,
    get_historical_data_from_file,
    get_ranking_table,
    get_weighted_table,
    can_we_trade,
    compute_portfolio,
    rebalance_portfolio,
)


@click.command()
@click.pass_context
@click.option("--start", default="2020-6-1", help="Start date in Y-M-D format.")
@click.option(
    "--end",
    default=datetime.today().date(),
    help="End date in Y-M-D format.",
)
@click.option(
    "--execution-time",
    default=datetime.today().date(),
    help="Time of portfolio calculation.",
)
@click.option("--data-file", help="Pickle data file with historical records.")
@click.option(
    "--rebalance/--no-rebalance",
    default=False,
    help="Whether or not this is a rebalance from last portfolio.",
)
def portfolio(ctx, start, end, data_file, execution_time, rebalance, **kwargs):
    """Generate a new portfolio or rebalance an existing one."""
    config = ctx.obj["config"]
    symbols = get_sp500_symbols()
    # Add SPY ticker to the symbols to include it into history.
    symbols.append("SPY")

    # History window filter.
    hist_window = (
        max(config["momentum_window_near"], config["momentum_window_far"])
        + config["exclude_days"]
    )

    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(str(end), "%Y-%m-%d")
    execution_time = datetime.strptime(str(execution_time), "%Y-%m-%d")
    data = get_historical_data_from_file(data_file)
    data = data.truncate(after=execution_time.date())[-hist_window:]
    ranking_table = get_ranking_table(data, config)
    buy_list = ranking_table[: config["portfolio_size"]]
    final_buy_list = buy_list[buy_list > config["minimum_momentum"]]
    vola_target_weights = get_weighted_table(data, buy_list, config)

    if rebalance:
        rebalance_portfolio(symbols, ranking_table, config, data)
    else:
        compute_portfolio(
            final_buy_list, vola_target_weights, config, config["portfolio"], data
        )


def add_commands(cli):
    cli.add_command(portfolio)
