# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Description

# %% [markdown]
# This notebook performs cross-vendor QA checks to compare vendors in terms of:
#    - Difference and intersection of vendor universes
#    - Time intervals, i.e. which vendor has the longest data available for each full symbol in intersecting universe
#    - Data quality (bad data [%], missing bars [%], volume=0 [%], NaNs [%]) for intersecting universe and time intervals

# %% [markdown]
# # Imports

# %%
import logging
import os
from typing import List, Optional, Tuple

import pandas as pd

import core.config.config_ as cconconf
import core.config.config_utils as ccocouti
import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hprint as hprint
import helpers.hs3 as hs3
import im_v2.ccxt.data.client as icdcl
import im_v2.crypto_chassis.data.client as iccdc
import research_amp.cc.qa as ramccqa

# %%
hdbg.init_logger(verbosity=logging.INFO)

_LOG = logging.getLogger(__name__)

_LOG.info("%s", henv.get_system_signature()[0])

hprint.config_notebook()


# %% [markdown]
# # Configs

# %%
def get_cmtask1966_config_ccxt() -> cconconf.Config:
    """
    Get task1966-specific config.
    """
    config = cconconf.Config()
    param_dict = {
        "data": {
            "ccxt": {
                "universe_version": "v3",
                "resample_1min": False,
                "root_dir": os.path.join(
                    hs3.get_s3_bucket_path("ck"), "reorg", "historical.manual.pq"
                ),
                "partition_mode": "by_year_month",
                "aws_profile": "ck",
            },
            "crypto_chassis": {
                "universe_version": "v1",
                "resample_1min": False,
                "root_dir": os.path.join(
                    hs3.get_s3_bucket_path("ck"), "reorg", "historical.manual.pq"
                ),
                "partition_mode": "by_year_month",
                "aws_profile": "ck",
            },
            # Parameters for data query.
            "read_data": {
                "start_ts": None,
                "end_ts": None,
                "columns": ["full_symbol", "close", "volume"],
                "filter_data_mode": "assert",
            },
        },
        "column_names": {
            "full_symbol": "full_symbol",
            "close_price": "close",
        },
        "stats": {
            "threshold": 30,
        },
    }
    config = ccocouti.get_config_from_nested_dict(param_dict)
    return config


# %%
config = get_cmtask1966_config_ccxt()
print(config)


# %% [markdown]
# # Functions

# %%
# TODO(Dan): Clean up and move to a lib.
# TODO(Dan): Make functions independent from hard-coded vendor names.
# TODO(Dan): @Nina add more detailed description of functions.
def _compare_vendor_universes(
    crypto_chassis_universe: List[str],
    ccxt_universe: List[str],
) -> Tuple[List[Optional[str]], List[Optional[str]], List[Optional[str]]]:
    """
    Get common and unique vendors universes.
    """
    common_universe = list(
        set(ccxt_universe).intersection(set(crypto_chassis_universe))
    )
    unique_crypto_chassis_universe = list(
        set(crypto_chassis_universe) - set(ccxt_universe)
    )
    unique_ccxt_universe = list(set(ccxt_universe) - set(crypto_chassis_universe))
    return common_universe, unique_crypto_chassis_universe, unique_ccxt_universe


# TODO(Dan): Add filtering by dates.
def _plot_bad_data_by_year_month_stats(
    config: cconconf.Config, bad_data_stats: pd.DataFrame
) -> None:
    """
    Plot bad data stats by year and month per unique full symbol in data.

    Bad data is the sum of NaNs and "volume=0" stats.
    """
    full_symbols = bad_data_stats.index.get_level_values(0).unique()
    for full_symbol in full_symbols:
        bad_data_col_name = "bad data [%]"
        ax = bad_data_stats.loc[full_symbol].plot.bar(
            y=bad_data_col_name, rot=0, title=full_symbol
        )
        #
        ax.hlines(
            y=config["stats"]["threshold"],
            xmin=0,
            xmax=len(bad_data_stats),
            color="r",
        )
        # TODO(Dan): Make ticklabels more readable.
        # Get ticks and labels for x-axis.
        ticks = ax.xaxis.get_ticklocs()
        ticklabels = [
            l.get_text().strip("()").split(", ")
            for l in ax.xaxis.get_ticklabels()
        ]
        ticklabels = [".".join([l[0], l[1]]) for l in ticklabels]
        # Adjust x-axis labels so they do not overlap on plot by
        # picking ticks and labels by specified stride that limits
        # the number of final ticks to 10.
        stride = len(ticks) // 10 + 1
        ax.xaxis.set_ticks(ticks[::stride])
        ax.xaxis.set_ticklabels(ticklabels[::stride])
        ax.figure.show()


# %% [markdown]
# # Compare universes

# %%
crypto_chassis_client = iccdc.CryptoChassisHistoricalPqByTileClient(
    **config["data"]["crypto_chassis"]
)
ccxt_client = icdcl.CcxtHistoricalPqByTileClient(**config["data"]["ccxt"])

# %%
crypto_chassis_universe = crypto_chassis_client.get_universe()
ccxt_universe = ccxt_client.get_universe()

# %%
(
    common_universe,
    unique_crypto_chassis_universe,
    unique_ccxt_universe,
) = _compare_vendor_universes(crypto_chassis_universe, ccxt_universe)

# %%
print(len(common_universe))
common_universe

# %%
print(len(unique_crypto_chassis_universe))
unique_crypto_chassis_universe

# %%
print(len(unique_ccxt_universe))
unique_ccxt_universe

# %% [markdown]
# # Compare Binance QA stats

# %%
binance_universe = [
    full_symbol
    for full_symbol in common_universe
    if full_symbol.startswith("binance")
]
binance_universe

# %%
ccxt_binance_data = ccxt_client.read_data(
    binance_universe, **config["data"]["read_data"]
)
ccxt_binance_data.head(3)

# %%
crypto_chassis_binance_data = crypto_chassis_client.read_data(
    binance_universe, **config["data"]["read_data"]
)
crypto_chassis_binance_data.head(3)

# %%
crypto_chassis_vendor = "Crypto Chassis"
crypto_chassis_timestamp_binance_stats = ramccqa.get_timestamp_stats(
    crypto_chassis_binance_data, crypto_chassis_vendor
)
ccxt_vendor = "CCXT"
ccxt_timestamp_binance_stats = ramccqa.get_timestamp_stats(
    ccxt_binance_data, ccxt_vendor
)
#
binance_timestamp_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_timestamp_binance_stats,
    ccxt_timestamp_binance_stats,
)
binance_timestamp_stats_qa

# %%
agg_level_full_symbol = ["full_symbol"]
crypto_chassis_bad_data_binance_stats = ramccqa.get_bad_data_stats(
    crypto_chassis_binance_data, agg_level_full_symbol, crypto_chassis_vendor
)
ccxt_bad_data_binance_stats = ramccqa.get_bad_data_stats(
    ccxt_binance_data, agg_level_full_symbol, ccxt_vendor
)
#
binance_bad_data_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_binance_stats,
    ccxt_bad_data_binance_stats,
)
binance_bad_data_stats_qa

# %%
agg_level_full_symbol_year_month = ["full_symbol", "year", "month"]
crypto_chassis_bad_data_binance_stats_by_year_month = ramccqa.get_bad_data_stats(
    crypto_chassis_binance_data,
    agg_level_full_symbol_year_month,
    crypto_chassis_vendor,
)
ccxt_bad_data_binance_stats_by_year_month = ramccqa.get_bad_data_stats(
    ccxt_binance_data, agg_level_full_symbol_year_month, ccxt_vendor
)
#
binance_bad_data_stats_by_year_month_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_binance_stats_by_year_month,
    ccxt_bad_data_binance_stats_by_year_month,
)
binance_bad_data_stats_by_year_month_qa

# %%
_plot_bad_data_by_year_month_stats(
    config, binance_bad_data_stats_by_year_month_qa
)

# %% [markdown]
# # Compare FTX QA stats

# %%
ftx_universe = [
    full_symbol
    for full_symbol in common_universe
    if full_symbol.startswith("ftx")
]
ftx_universe

# %%
ccxt_ftx_data = ccxt_client.read_data(ftx_universe, **config["data"]["read_data"])
ccxt_ftx_data.head(3)

# %%
crypto_chassis_ftx_data = crypto_chassis_client.read_data(
    ftx_universe, **config["data"]["read_data"]
)
crypto_chassis_ftx_data.head(3)

# %%
crypto_chassis_timestamp_ftx_stats = ramccqa.get_timestamp_stats(
    crypto_chassis_ftx_data, crypto_chassis_vendor
)
ccxt_timestamp_ftx_stats = ramccqa.get_timestamp_stats(ccxt_ftx_data, ccxt_vendor)
#
ftx_timestamp_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_timestamp_ftx_stats,
    ccxt_timestamp_ftx_stats,
)
ftx_timestamp_stats_qa

# %%
crypto_chassis_bad_data_ftx_stats = ramccqa.get_bad_data_stats(
    crypto_chassis_ftx_data, agg_level_full_symbol, crypto_chassis_vendor
)
ccxt_bad_data_ftx_stats = ramccqa.get_bad_data_stats(
    ccxt_ftx_data, agg_level_full_symbol, ccxt_vendor
)
#
ftx_bad_data_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_ftx_stats,
    ccxt_bad_data_ftx_stats,
)
ftx_bad_data_stats_qa

# %%
crypto_chassis_bad_data_ftx_stats_by_year_month = ramccqa.get_bad_data_stats(
    crypto_chassis_ftx_data,
    agg_level_full_symbol_year_month,
    crypto_chassis_vendor,
)
ccxt_bad_data_ftx_stats_by_year_month = ramccqa.get_bad_data_stats(
    ccxt_ftx_data, agg_level_full_symbol_year_month, ccxt_vendor
)
#
ftx_bad_data_stats_by_year_month_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_ftx_stats_by_year_month,
    ccxt_bad_data_ftx_stats_by_year_month,
)
ftx_bad_data_stats_by_year_month_qa

# %%
_plot_bad_data_by_year_month_stats(config, ftx_bad_data_stats_by_year_month_qa)

# %% [markdown]
# # Compare Gateio QA stats

# %%
gateio_universe = [
    full_symbol
    for full_symbol in common_universe
    if full_symbol.startswith("gateio")
]
gateio_universe

# %%
ccxt_gateio_data = ccxt_client.read_data(
    gateio_universe, **config["data"]["read_data"]
)
ccxt_gateio_data.head(3)

# %%
crypto_chassis_gateio_data = crypto_chassis_client.read_data(
    gateio_universe, **config["data"]["read_data"]
)
crypto_chassis_gateio_data.head(3)

# %%
crypto_chassis_timestamp_gateio_stats = ramccqa.get_timestamp_stats(
    crypto_chassis_gateio_data, crypto_chassis_vendor
)
ccxt_timestamp_gateio_stats = ramccqa.get_timestamp_stats(
    ccxt_gateio_data, ccxt_vendor
)
#
gateio_timestamp_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_timestamp_gateio_stats,
    ccxt_timestamp_gateio_stats,
)
gateio_timestamp_stats_qa

# %%
crypto_chassis_bad_data_gateio_stats = ramccqa.get_bad_data_stats(
    crypto_chassis_gateio_data, agg_level_full_symbol, crypto_chassis_vendor
)
ccxt_bad_data_gateio_stats = ramccqa.get_bad_data_stats(
    ccxt_gateio_data, agg_level_full_symbol, ccxt_vendor
)
#
gateio_bad_data_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_gateio_stats,
    ccxt_bad_data_gateio_stats,
)
gateio_bad_data_stats_qa

# %%
crypto_chassis_bad_data_gateio_stats_by_year_month = ramccqa.get_bad_data_stats(
    crypto_chassis_gateio_data,
    agg_level_full_symbol_year_month,
    crypto_chassis_vendor,
)
ccxt_bad_data_gateio_stats_by_year_month = ramccqa.get_bad_data_stats(
    ccxt_gateio_data, agg_level_full_symbol_year_month, ccxt_vendor
)
#
gateio_bad_data_stats_by_year_month_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_gateio_stats_by_year_month,
    ccxt_bad_data_gateio_stats_by_year_month,
)
gateio_bad_data_stats_by_year_month_qa

# %%
_plot_bad_data_by_year_month_stats(config, gateio_bad_data_stats_by_year_month_qa)

# %% [markdown]
# # Compare Kucoin QA stats

# %%
kucoin_universe = [
    full_symbol
    for full_symbol in common_universe
    if full_symbol.startswith("kucoin")
]
kucoin_universe

# %%
ccxt_kucoin_data = ccxt_client.read_data(
    kucoin_universe, **config["data"]["read_data"]
)
ccxt_kucoin_data.head(3)

# %%
crypto_chassis_kucoin_data = crypto_chassis_client.read_data(
    kucoin_universe, **config["data"]["read_data"]
)
crypto_chassis_kucoin_data.head(3)

# %%
crypto_chassis_timestamp_kucoin_stats = ramccqa.get_timestamp_stats(
    crypto_chassis_kucoin_data, crypto_chassis_vendor
)
ccxt_timestamp_kucoin_stats = ramccqa.get_timestamp_stats(
    ccxt_kucoin_data, ccxt_vendor
)
#
kucoin_timestamp_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_timestamp_kucoin_stats,
    ccxt_timestamp_kucoin_stats,
)
kucoin_timestamp_stats_qa

# %%
crypto_chassis_bad_data_kucoin_stats = ramccqa.get_bad_data_stats(
    crypto_chassis_kucoin_data, agg_level_full_symbol, crypto_chassis_vendor
)
ccxt_bad_data_kucoin_stats = ramccqa.get_bad_data_stats(
    ccxt_kucoin_data, agg_level_full_symbol, ccxt_vendor
)
#
kucoin_bad_data_stats_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_kucoin_stats,
    ccxt_bad_data_kucoin_stats,
)
kucoin_bad_data_stats_qa

# %%
crypto_chassis_bad_data_kucoin_stats_by_year_month = ramccqa.get_bad_data_stats(
    crypto_chassis_kucoin_data,
    agg_level_full_symbol_year_month,
    crypto_chassis_vendor,
)
ccxt_bad_data_kucoin_stats_by_year_month = ramccqa.get_bad_data_stats(
    ccxt_kucoin_data, agg_level_full_symbol_year_month, ccxt_vendor
)
#
kucoin_bad_data_stats_by_year_month_qa = ramccqa.compare_data_stats(
    crypto_chassis_bad_data_kucoin_stats_by_year_month,
    ccxt_bad_data_kucoin_stats_by_year_month,
)
kucoin_bad_data_stats_by_year_month_qa

# %%
_plot_bad_data_by_year_month_stats(config, kucoin_bad_data_stats_by_year_month_qa)