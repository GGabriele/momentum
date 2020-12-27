## Momentum

This repository is based on a momentum strategy described into the books [Stock on the move](https://www.amazon.com/gp/product/B00YPHZO3W/ref=dbs_a_def_rwt_bibl_vppi_i1) and [Trading evolved](https://www.amazon.com/gp/product/B07VDLX55H/ref=dbs_a_def_rwt_bibl_vppi_i0) from Andreas Clenow. The strategy looks as follows:

- From your stock universe, rank the tickers based on a momentum score
- Allocate the positions based on volatility to have a risk-balanced portfolio
- Rebalance the portfolio every weeks
- Rebalance the positions every 2 week
- Sell a stock if:
1. it's not part of the universe anymore
2. it's not in the top X% of the universe
3. it's trading below its X SMA
4. it's a gap over X%
- Trade only if the index (SP500) is above the X SMA

This repo tries to implement this strategy, with few modifications.

### Install

Create a virtual environment using `conda`

```
$ conda create --name momentum python=3.6
$ conda activate momentum
```

Install the package

```
$ python setup.py install
```

Verify installation

```
$ momentum --help
Usage: momentum [OPTIONS] COMMAND [ARGS]...

  CLI entry point.

Options:
  --config TEXT  Config file path.  [required]
  --help         Show this message and exit.

Commands:
  market-status  Get market status information.
  portfolio      Generate a new portfolio or rebalance an existing one.
```

### market-status

Get overall market status information (`SPY` index)

```
$ momentum market-status

******* SP500 SMAs *******
|       |   value |
|:------|--------:|
| 30    | 364.632 |
| 60    | 353.599 |
| 90    | 348.561 |
| 120   | 343.106 |
| 200   | 338.357 |
| TODAY | 369     |

```

### collect

Before creating a portfolio, we need historical data to do some calculation.

```
$ momentum collect --help
Usage: momentum collect [OPTIONS]

  Collect and store historical SP500 data.

Options:
  --start TEXT  Start date in Y-M-D format.
  --end TEXT    End date in Y-M-D format.
  --help        Show this message and exit.

$
$ momentum collect --start 2020-12-1
...
...
$ ls ~/.momentum
sp500-20201201-20201227.data
```


### portfolio

The configuration file (passed via `--config`, default to `./config.json`) holds the parameters used by the engine to build the best portfolio.

Parameters:
- `minimum_momentum`: the minimum momentum score for a stock to be considered into our calculation
- `portfolio_size`: the number of individual stocks the portfolio can be composed by
- `portfolio`: the size of the initial portfolio
- `trend_filter_window_far`: a long window for market's momentum calculation
- `trend_filter_window_near`: a short window for market's momentum calculation
- `momentum_window_near`: a short window for stocks' momentum calculation
- `momentum_window_far`: a long window for stocks' momentum calculation
- `exclude_days`: day to skip from windwows calculation
- `volatility_window`: volatility range allowed

If no `--data-file` is provided, the script will pull historical data for the `SPY` index and its components and then it will store it into the `$HOME/.momentum` directory.

```
$ momentum portfolio --help
Usage: momentum portfolio [OPTIONS]

  Generate a new portfolio or rebalance an existing one.

Options:
  --execution-time TEXT         Time of portfolio calculation.
  --data-file TEXT              Pickle data file with historical records.
  --rebalance / --no-rebalance  Whether or not this is a rebalance from last
                                portfolio.

  --help                        Show this message and exit.
```

```
$ momentum portfolio --data-file ~/.momentum/sp500-20190101-20201226.data

******* NEW PORTFOLIO *******
|           |   price |    value |   amount |   proposed weight |   real weight |   weight delta |   add-on increase |
|:----------|--------:|---------:|---------:|------------------:|--------------:|---------------:|------------------:|
| OXY       |   17.67 |   318.06 |       18 |           3.21269 |        3.1806 |       0.99883  |            0.1767 |
| TPR       |   30.85 |  1048.9  |       34 |          10.5306  |       10.489  |       0.394574 |            0.3085 |
| DVN       |   15.33 |   413.91 |       27 |           4.29499 |        4.1391 |       3.62959  |            0.1533 |
| GE        |   10.65 |   894.6  |       84 |           9.0005  |        8.946  |       0.605519 |            0.1065 |
| BKR       |   21.01 |   630.3  |       30 |           6.39993 |        6.303  |       1.5146   |            0.2101 |
| MRO       |    6.63 |   397.8  |       60 |           4.00478 |        3.978  |       0.668766 |            0.0663 |
| HAL       |   19.21 |   518.67 |       27 |           5.20949 |        5.1867 |       0.437407 |            0.1921 |
| APA       |   14.43 |   346.32 |       24 |           3.51332 |        3.4632 |       1.42645  |            0.1443 |
| NOV       |   13.5  |   486    |       36 |           4.88902 |        4.86   |       0.593629 |            0.135  |
| FANG      |   48.25 |   337.75 |        7 |           3.60842 |        3.3775 |       6.39954  |            0.4825 |
| ALB       |  149.64 |   748.2  |        5 |           7.86754 |        7.482  |       4.90041  |            1.4964 |
| FCX       |   24.79 |  1065.97 |       43 |          10.6741  |       10.6597 |       0.134902 |            0.2479 |
| WYNN      |  114.39 |   686.34 |        6 |           7.36193 |        6.8634 |       6.77177  |            1.1439 |
| PVH       |   93.82 |   656.74 |        7 |           6.86186 |        6.5674 |       4.29121  |            0.9382 |
| ALGN      |  528.03 |  1056.06 |        2 |          12.5709  |       10.5606 |      15.9915   |            5.2803 |
| TOTAL     |  nan    |  9605.62 |      nan |         100       |       96.0562 |       3.9438   |          nan      |
| CASH      |  nan    |   394.38 |      nan |         nan       |      nan      |     nan        |          nan      |
| PORTFOLIO |  nan    | 10000    |      nan |         nan       |      nan      |     nan        |          nan      |
```

This will create a `$HOME/.momentum/portfolio.last` file.

If the `--execution-time` parameter is provided, the portfolio will be built based on that date's market status.

```
$ momentum portfolio --data-file ~/.momentum/sp500-20190101-20201226.data --execution-time 2020-7-1

******* NEW PORTFOLIO *******
|           |   price |     value |   amount |   proposed weight |   real weight |   weight delta |   add-on increase |
|:----------|--------:|----------:|---------:|------------------:|--------------:|---------------:|------------------:|
| CARR      |  22.61  |   859.18  |       38 |           8.71703 |       8.5918  |       1.43661  |           0.2261  |
| ETSY      | 111.21  |   889.68  |        8 |           8.92851 |       8.8968  |       0.35521  |           1.1121  |
| DISH      |  34.63  |   796.49  |       23 |           7.98523 |       7.9649  |       0.254546 |           0.3463  |
| HAL       |  12.47  |   436.45  |       35 |           4.45039 |       4.3645  |       1.92997  |           0.1247  |
| ABMD      | 255.22  |   765.66  |        3 |          10.052   |       7.6566  |      23.8302   |           2.5522  |
| PYPL      | 177.43  |  1242.01  |        7 |          13.3412  |      12.4201  |       6.90433  |           1.7743  |
| VIAC      |  23.6   |   519.2   |       22 |           5.24631 |       5.192   |       1.03527  |           0.236   |
| APA       |  13     |   351     |       27 |           3.59873 |       3.51    |       2.46556  |           0.13    |
| TSLA      | 223.926 |   671.778 |        3 |           7.13409 |       6.71778 |       5.83547  |           2.23926 |
| MPC       |  35.68  |   642.24  |       18 |           6.44995 |       6.4224  |       0.427101 |           0.3568  |
| NCLH      |  16.42  |   262.72  |       16 |           2.77136 |       2.6272  |       5.20168  |           0.1642  |
| RCL       |  50.83  |   304.98  |        6 |           3.42609 |       3.0498  |      10.9832   |           0.5083  |
| PAYC      | 320.26  |   640.52  |        2 |           7.44927 |       6.4052  |      14.0158   |           3.2026  |
| DFS       |  48.22  |   626.86  |       13 |           6.55177 |       6.2686  |       4.32205  |           0.4822  |
| GPS       |  12.47  |   386.57  |       31 |           3.89802 |       3.8657  |       0.829234 |           0.1247  |
| TOTAL     | nan     |  9395.34  |      nan |         100       |      93.9534  |       6.04662  |         nan       |
| CASH      | nan     |   604.662 |      nan |         nan       |     nan       |     nan        |         nan       |
| PORTFOLIO | nan     | 10000     |      nan |         nan       |     nan       |     nan        |         nan       |
```

If the `--rebalance` parameter is provided, the existing portfolio will be restored (stored in the `$HOME/.momentum` directory) and it will be adjusted based on the new market status.

```
$ momentum portfolio --data-file ~/.momentum/sp500-20190101-20201226.data --execution-time 2020-8-3 --rebalance

******* SELL *******
|       |   price |   value |   amount |
|:------|--------:|--------:|---------:|
| DISH  |   33.96 |  781.08 |       23 |
| HAL   |   14.53 |  508.55 |       35 |
| VIAC  |   25.71 |  565.62 |       22 |
| APA   |   15.72 |  424.44 |       27 |
| MPC   |   38.57 |  694.26 |       18 |
| NCLH  |   13.06 |  208.96 |       16 |
| RCL   |   47.39 |  284.34 |        6 |
| PAYC  |  288.08 |  576.16 |        2 |
| DFS   |   49.5  |  643.5  |       13 |
| TOTAL |  nan    | 4686.91 |      nan |

******* REMAINING *******
|           |   price |    value |   amount |
|:----------|--------:|---------:|---------:|
| CARR      |   27.62 |  1049.56 |       38 |
| ETSY      |  126.62 |  1012.96 |        8 |
| ABMD      |  308.35 |   925.05 |        3 |
| PYPL      |  197.07 |  1379.49 |        7 |
| TSLA      |  297    |   891    |        3 |
| GPS       |   13.11 |   406.41 |       31 |
| TOTAL     |  nan    |  5664.47 |      nan |
| CASH      |  nan    |  5291.57 |      nan |
| PORTFOLIO |  nan    | 10956    |      nan |


******* NEW PORTFOLIO *******
|           |   price |    value |   amount |   proposed weight |   real weight |   weight delta |   add-on increase |
|:----------|--------:|---------:|---------:|------------------:|--------------:|---------------:|------------------:|
| FCX       |   13.1  |   956.3  |       73 |           8.85129 |       8.72852 |       1.38707  |          0.119569 |
| TER       |   90.26 |   722.08 |        8 |           6.88284 |       6.5907  |       4.24442  |          0.823838 |
| EBAY      |   56.57 |   848.55 |       15 |           7.9957  |       7.74504 |       3.13486  |          0.516336 |
| TSCO      |  147.42 |   884.52 |        6 |           9.27055 |       8.07335 |      12.914    |          1.34556  |
| FDX       |  169.22 |   846.1  |        5 |           8.93509 |       7.72268 |      13.5691   |          1.54454  |
| AMZN      | 3111.89 |     0    |        0 |           5.41366 |       0       |     100        |         28.4034   |
| CINF      |   78.4  |   705.6  |        9 |           6.78645 |       6.44028 |       5.10083  |          0.715587 |
| LRCX      |  381.41 |   762.82 |        2 |           7.09911 |       6.96255 |       1.92359  |          3.48128  |
| NVDA      |  440.41 |   440.41 |        1 |           6.58459 |       4.01979 |      38.9515   |          4.01979  |
| TSLA      |  297    |   297    |        1 |           3.07839 |       2.71083 |      11.9399   |          2.71083  |
| ETSY      |  126.62 |   379.86 |        3 |           4.3248  |       3.46713 |      19.8316   |          1.15571  |
| ABMD      |  308.35 |   925.05 |        3 |           8.46373 |       8.44329 |       0.241507 |          2.81443  |
| CARR      |   27.62 |   718.12 |       26 |           6.64715 |       6.55456 |       1.39293  |          0.252098 |
| GPS       |   13.11 |   353.97 |       27 |           3.35591 |       3.23082 |       3.72759  |          0.11966  |
| PYPL      |  197.07 |   591.21 |        3 |           6.31075 |       5.3962  |      14.4919   |          1.79873  |
| TOTAL     |  nan    |  9431.59 |      nan |         100       |      86.0857  |      13.9143   |        nan        |
| CASH      |  nan    |  1524.45 |      nan |         nan       |     nan       |     nan        |        nan        |
| PORTFOLIO |  nan    | 10956    |      nan |         nan       |     nan       |     nan        |        nan        |

```