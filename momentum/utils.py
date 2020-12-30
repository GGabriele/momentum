import numpy as np
from scipy import stats
import pandas_datareader.data as web
import pandas as pd

from pathlib import Path

import click

HOME_DIR = str(Path.home())
MOMENTUM_DIR = f"{HOME_DIR}/.momentum"


def slope(ts):
    """
    Input: Price time series.
    Output: Annualized exponential regression slope, weighted on positive returns percentile
    """
    x = np.arange(len(ts))
    log_ts = np.log(ts)
    slope, _, r_value, _, _ = stats.linregress(x, log_ts)
    annualized_slope = (np.power(np.exp(slope), 252) - 1) * 100
    score = annualized_slope * (r_value ** 2)
    daily_returns = ts / ts.shift(1) - 1
    positive_returns = ((daily_returns > 0).sum() / len(daily_returns)) * 100
    return score * positive_returns


def volatility(ts, window):
    """
    Input: Price time series.
    Output: Inverse exponential moving average standard deviation.
    """
    return ts.pct_change().rolling(window).std().iloc[-1]


def inv_vola_calc(ts, window):
    """
    Input: Price time series.
    Output: Inverse exponential moving average standard deviation.
    Purpose: Provides inverse vola for use in vola parity position sizing.
    """
    returns = np.log(ts).diff()
    stddev = (
        returns.ewm(halflife=20, ignore_na=True, min_periods=0, adjust=True)
        .std(bias=False)
        .dropna()
    )
    return 1 / stddev.iloc[-1]


def get_sp500_symbols():
    """Get SP500 components from wikipedia."""
    sp500_table = pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", header=0
    )[0]
    return list(sp500_table.loc[:, "Symbol"])


def retrieve_upstream(start, end, symbols):
    return web.DataReader(symbols, "yahoo", start, end)


def collect_history(start, end, symbols):
    """Collect and store historical data."""
    data = retrieve_upstream(start, end, symbols)
    data = data.loc[:, "Close"]
    Path(MOMENTUM_DIR).mkdir(parents=True, exist_ok=True)
    start = start.strftime("%Y%m%d")
    end = end.strftime("%Y%m%d")
    filename = f"{MOMENTUM_DIR}/sp500-{start}-{end}.data"
    data.to_pickle(filename)


def get_historical_data_from_file(filename):
    """Get historical data from file."""
    try:
        return pd.read_pickle(filename)
    except IOError:
        msg = f"File {filename} not found, you may need to re-collect some data"
        click.echo(click.style(f"{msg}", fg="red"))


def get_ranking_table(data, config):
    momentum_hist1 = data[(-1 * config["momentum_window_near"]) :]
    momentum_hist2 = data[(-1 * config["momentum_window_far"]) :]
    # Calculate momentum scores for all stocks.
    momentum_list = momentum_hist1.apply(slope)
    momentum_list2 = momentum_hist2.apply(slope)

    # Combine the lists and make average
    momentum_concat = pd.concat((momentum_list, momentum_list2))
    mom_by_row = momentum_concat.groupby(momentum_concat.index)
    mom_means = mom_by_row.mean()

    # Sort the momentum list, and we've got ourselves a ranking table.
    return mom_means.sort_values(ascending=False)


def get_weighted_table(data, buy_list, config):
    vola_table = data[buy_list.index].apply(
        volatility, args=(config["volatility_window"],)
    )
    inv_vola_table = 1 / vola_table
    sum_inv_vola = np.sum(inv_vola_table)
    vola_target_weights = inv_vola_table / sum_inv_vola
    return vola_target_weights.clip(upper=0.25)


def can_we_trade(config, index_history):
    ind_hist1 = index_history.iloc[(-1 * config["trend_filter_window_far"]) :]
    index_sma = ind_hist1.mean()
    current_index = index_history[-1]
    # declare bull if index is over average
    bull_market = current_index > index_sma

    ind_hist2 = index_history.iloc[(-1 * config["trend_filter_window_near"]) :]
    if not bull_market:
        # Check wheather this is due to distant dips
        bull_market = (
            ind_hist2.mean() > index_history.mean() and current_index > ind_hist2.mean()
        )
    return bull_market


def compute_portfolio(final_buy_list, vola_target_weights, config, liquidity, data):
    if not can_we_trade(config, data["SPY"]):
        click.echo(
            click.style(
                "******* SPY IS UNDERPERFORMING - CANNOT TRADE *******", fg="red"
            )
        )
        return
    equity_weight = 0.0
    portfolio = pd.DataFrame(
        columns=[
            "price",
            "value",
            "amount",
            "proposed weight",
            "real weight",
            "weight delta",
            "add-on increase",
        ]
    )
    for security in final_buy_list.keys():
        weight = vola_target_weights[security]
        security_amount = int(weight * liquidity)
        number_of_shares = int(security_amount / data[security][-1])
        real_weight = (number_of_shares * data[security][-1]) / liquidity
        portfolio.loc[security, "price"] = data[security][-1]
        portfolio.loc[security, "value"] = data[security][-1] * number_of_shares
        portfolio.loc[security, "amount"] = number_of_shares
        portfolio.loc[security, "proposed weight"] = weight * 100
        portfolio.loc[security, "real weight"] = real_weight * 100
        portfolio.loc[security, "weight delta"] = (1 - real_weight / weight) * 100
        portfolio.loc[security, "add-on increase"] = (
            data[security][-1] / liquidity
        ) * 100
        equity_weight += weight
    # Add summary info
    portfolio.loc["TOTAL", "proposed weight"] = portfolio["proposed weight"].sum()
    portfolio.loc["TOTAL", "real weight"] = portfolio["real weight"].sum()
    portfolio.loc["TOTAL", "weight delta"] = (
        1 - portfolio["real weight"].sum() / portfolio["proposed weight"].sum()
    ) * 100
    portfolio.loc["TOTAL", "value"] = portfolio["value"].sum()
    portfolio.loc["CASH", "value"] = liquidity - portfolio.loc["TOTAL"].value
    portfolio.loc["PORTFOLIO", "value"] = (
        portfolio.loc["TOTAL"].value + portfolio.loc["CASH"].value
    )
    # Store portfolio
    portfolio.to_pickle(f"{MOMENTUM_DIR}/portfolio.last", protocol=4)
    print()
    click.echo(click.style("******* NEW PORTFOLIO *******", fg="green"))
    print(portfolio.to_dense())
    print()


def calculate_averages(data):
    df = pd.DataFrame(columns=["value"])
    for win in (30, 60, 90, 120, 200):
        df.loc[str(win), "value"] = data.iloc[-win:].mean()
    df.loc["TODAY", "value"] = data[-1]
    print()
    click.echo(click.style("******* SP500 SMAs *******", fg="green"))
    print(df.to_dense())
    print()


def sell_report(sell, data, portfolio):
    # Sell section
    to_sell = pd.DataFrame(columns=["price", "value", "amount"])
    for security in sell:
        to_sell.loc[security, "price"] = data[security][-1]
        to_sell.loc[security, "value"] = (
            data[security][-1] * portfolio.loc[security].amount
        )
        to_sell.loc[security, "amount"] = portfolio.loc[security].amount
    to_sell.loc["TOTAL", "value"] = to_sell["value"].sum()

    print()
    click.echo(click.style("******* SELL *******", fg="red"))
    print(to_sell.to_dense())
    print()


def remaining_report(portfolio, cash, liquidity):
    new_portfolio = portfolio.drop(
        ["proposed weight", "real weight", "weight delta", "add-on increase"], axis=1
    )
    new_portfolio.loc["TOTAL", "value"] = new_portfolio["value"].sum()
    new_portfolio.loc["CASH", "value"] = liquidity + cash
    portfolio_value = new_portfolio.loc["TOTAL"].value + liquidity + cash
    new_portfolio.loc["PORTFOLIO", "value"] = portfolio_value
    click.echo(click.style("******* REMAINING *******", fg="yellow"))
    print(new_portfolio.to_dense())
    print()


def rebalance_portfolio(universe, ranking_table, config, data):
    existing_portfolio = pd.read_pickle(f"{MOMENTUM_DIR}/portfolio.last")
    ignore_cols = ["TOTAL", "CASH", "PORTFOLIO"]
    sell = []
    zeros = []
    liquidity_from_sells = 0

    def sell_security(security, amount):
        nonlocal liquidity_from_sells
        if amount != 0:
            sell.append(security)
            kept_positions.remove(security)
            liquidity_from_sells += values.amount * data[security][-1]
        else:
            zeros.append(security)

    kept_positions = [k for k in existing_portfolio.index if k not in ignore_cols]
    """
    Sell Logic

    First we check if any existing position should be sold.
    * Sell if stock is no longer part of index.
    * Sell if stock has too low momentum value.
    * Sell if stock is lower 100MA
    * Sell if stock not in top 100 stocks
    """
    for security, values in existing_portfolio.iterrows():
        if security in ignore_cols:
            continue
        sec_history = data[security][:100]
        if security not in universe:
            sell_security(security, values.amount)
        elif ranking_table[security] < config["minimum_momentum"]:
            sell_security(security, values.amount)
        elif sec_history[-1] < sec_history.mean():
            sell_security(security, values.amount)
        elif security not in ranking_table[:50]:
            sell_security(security, values.amount)
        else:
            # Hold it. Update portfolio with current price of the stock.
            existing_portfolio.loc[security]["price"] = data[security][-1]
            existing_portfolio.loc[security]["value"] = (
                values.amount * data[security][-1]
            )

    sell_report(sell, data, existing_portfolio)
    cash = existing_portfolio.loc["CASH"].value
    new_portfolio = existing_portfolio.drop(sell).drop(zeros).drop(ignore_cols)
    portfolio_value = cash + liquidity_from_sells + new_portfolio["value"].sum()
    remaining_report(new_portfolio, cash, liquidity_from_sells)

    replacement_stocks = config["portfolio_size"] - len(kept_positions)
    buy_list = ranking_table.loc[~ranking_table.index.isin(kept_positions)][
        :replacement_stocks
    ]

    final_buy_list = pd.concat(
        (buy_list, ranking_table.loc[ranking_table.index.isin(kept_positions)])
    )
    vola_target_weights = get_weighted_table(data, final_buy_list, config)
    compute_portfolio(
        final_buy_list, vola_target_weights, config, portfolio_value, data
    )
