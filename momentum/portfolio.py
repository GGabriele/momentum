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
    check_volatility,
)


@click.command()
@click.pass_context
@click.argument("name")
@click.option(
    "--execution-time",
    default=str(datetime.today().date()),
    help="Time of portfolio calculation.",
)
@click.option("--data-file", help="Pickle data file with historical records.")
@click.option(
    "--rebalance/--no-rebalance",
    default=False,
    help="Whether or not this is a rebalance from last portfolio.",
)
@click.option(
    "--check/--no-check",
    default=False,
    help="If set, the calculated portfolio will not be stored.",
)
def portfolio(ctx, name, data_file, execution_time, rebalance, check, **kwargs):
    """Generate a new portfolio or rebalance an existing one."""
    config = ctx.obj["config"]
    exclude = config["exclude_symbols"]
    include = config["include_symbols"]
    symbols = get_sp500_symbols(exclude, include=include)
    # Add SPY ticker to the symbols to include it into history.
    symbols.append("SPY")

    # History window filter.
    hist_window = (
        max(config["momentum_window_near"], config["momentum_window_far"])
        + config["exclude_days"]
    )
    execution_time = datetime.strptime(execution_time, "%Y-%m-%d")
    data = get_historical_data_from_file(data_file)
    data = data.truncate(after=execution_time.date())[-hist_window:]
    ranking_table = get_ranking_table(data, config)

    # Check volatility
    is_too_volatile = data.apply(check_volatility)
    too_volatile = is_too_volatile[is_too_volatile == True]
    ranking_table = ranking_table[is_too_volatile[is_too_volatile == False].index]
    ranking_table = ranking_table.sort_values(ascending=False)

    # Remove unwanted stocks.
    for ex in exclude:
        if ex in ranking_table:
            ranking_table = ranking_table.drop(ex)

    buy_list = ranking_table[: config["portfolio_size"]]
    final_buy_list = buy_list[buy_list > config["minimum_momentum"]]
    vola_target_weights = get_weighted_table(data, buy_list, config)
    if rebalance:
        rebalance_portfolio(name, symbols, exclude, ranking_table, config, data, check, too_volatile)
    else:
        compute_portfolio(
            name, final_buy_list, vola_target_weights, config, config["portfolio"], data, check
        )


def add_commands(cli):
    cli.add_command(portfolio)
