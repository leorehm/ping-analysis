#!/usr/bin/env python3

import sys
from os.path import basename
import argparse
from itertools import dropwhile
import re
import datetime
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import ticker

# TODO: UNIX/Linux support
# TODO: input validation, error checking

def main():
    args = parse_args()
    latencies = files_to_dataframe(args.file)

    plots = []
    if args.plot in ["single", "both"]:
        # plots.append(plot_single(latencies, args.ma_window))
        plots.append(plot_latencies(latencies, args.ma_window, "single"))
    if args.plot in ["multi", "both"]:
        # plots.append(plot_multi(latencies, args.ma_window))
        plots.append(plot_latencies(latencies, args.ma_window, "multi"))

    if args.out and len(args.out) != len(plots):
        sys.exit("error: number of plots doesnt match number of out-files specified")

    for plot in plots:
        if args.out:
            plot.savefig(args.out.pop().name)
            plot.close()
            continue
        plot.show()
        plot.close()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", 
        type = argparse.FileType("r"), 
        nargs = "+", 
        help = "one or more files to be read"
    )
    parser.add_argument(
        "-p", "--plot", 
        default = "single", 
        choices = ["single", "multi", "both"],
        help = "plot type: (single|multi|both); default = single"
    )
    parser.add_argument(
        "-o", "--out", 
        type = argparse.FileType("w"),
        nargs = "+",
        help = 'save plot to file; enter two paths when using "-p both"'
    )
    parser.add_argument(
        "--ma-window", 
        default = 20, 
        type = float,
        help = "moving-average window in seconds; default = 20"
        # = ewm_window internally
    )
    return parser.parse_args()

def files_to_dataframe(files: list[argparse.FileType]) -> pd.DataFrame:
    data = {}
    index = []
    
    for file in files:
        pings = open(file.name, file.mode,encoding = file.encoding).read().split("\n")
        pings = extract_pings(pings)
        t0 = get_datetime(pings[0])
        data[basename(file.name)] = [get_latency(ln) for ln in pings]
        times = [get_datetime(ln) - t0 for ln in pings]
        if len(times) > len(index): 
            index = times

    # create data frame
    data["index"] = index
    latencies = pd.DataFrame.from_dict(data, orient = "index")
    latencies = latencies.transpose()
    latencies = latencies.set_index("index", drop=True)
    return latencies

def extract_pings(pings: list[str]) -> list[str]:
    # remove head until "Reply from" is matched
    pings = list(dropwhile(lambda ln: "Reply from" not in ln, pings))
    # TODO: make readable
    # remove tail until "Reply from" is matched
    n = len(pings)
    i = n - 1
    while "Reply from" not in pings[i]:
        pings.pop(i)
        i -=  1
    lines_to_delete = len(pings) - 1 - i
    pings[-lines_to_delete:lines_to_delete and None] = []
    return pings

def get_datetime(ping: str) -> datetime:
    return datetime.datetime.strptime(ping[0:19], "%d.%m.%Y %H:%M:%S")

def get_latency(ping: str) -> int:
    return int(re.search("time=(\d*)", ping).group(1))

def describe(df: pd.DataFrame, include = 'all') -> pd.DataFrame:
    if include == 'all':
        cols = list(df.columns.values)
    else: 
        cols = include
    desc = {}
    for col in cols: 
        desc[col] = {
            "count": str(df[col].count()),
            "△ t": str(df[col].last_valid_index()).split( )[-1],
            "mean": f"{df[col].mean(skipna = True).round(2)} ms",
            "median": f"{df[col].median(skipna=True)} ms",
            "std": f"{df[col].std(skipna=True).round(2)} ms",
            "min": f"{df[col].min(skipna=True)} ms",
            "max": f"{df[col].max(skipna=True)} ms",
            "25%": f"{df[col].quantile(.25)} ms",
            "75%": f"{df[col].quantile(.75)} ms",
            "90%": f"{df[col].quantile(.9)} ms",
            "95%": f"{df[col].quantile(.95)} ms",
        }
    return pd.DataFrame.from_dict(desc)

def plot_latencies(latencies: pd.DataFrame, ewm_window: float = 20, plots: str = "single") -> plt:
    # TODO: dont plot NaN values as 0
    desc = describe(latencies)

    if plots == "multi":
        n = latencies.shape[1]
    elif plots == "single":
        n = 1
    
    fig, axes = plt.subplots(
        nrows = n, ncols = 2,
        figsize = (16, 5 * n), # width = 16 inches, height = 5 inches per row
        constrained_layout = True, 
        sharey = True,
        gridspec_kw={"width_ratios": [9, 1]}
    )
    
    fig.suptitle(f"ping statistics: moving average = {ewm_window} s", fontsize = 16)

    linewidth = 0.75

    # single chart
    if n == 1: 
        create_plot(axes[0], latencies, ewm_window, linewidth)
        create_table(axes[1], desc)

    # multiple charts
    else: 
        cols = list(latencies.columns.values)
        for i, col in enumerate(cols):
            create_plot(axes[i, 0], latencies[col], ewm_window, linewidth)
            create_table(axes[i, 1], pd.DataFrame(desc[col]))

    return plt

def create_plot(axis: plt.axis, df: pd.DataFrame, ewm_window: float = 20, linewidth: int = 0.75) -> plt.plot:
    plot = df.ewm(span = ewm_window, ignore_na = True).mean().plot(
        ax = axis, 
        alpha = 0.7, 
        linewidth = linewidth
    )
    axis.set(xlabel = "△ t", ylabel = "latency in ms")
    axis.xaxis.set_major_formatter(ticker.FuncFormatter(time_ticks))
    axis.legend()

    return plot

def create_table(axis: plt.axis, df: pd.DataFrame) -> plt.table:
    tab = axis.table( 
        cellText = df.values, 
        rowLabels = df.index, 
        colLabels = df.columns,
        loc = "center", 
        cellLoc = "right",
        colLoc = "right",
        edges = "open",
        fontsize = 12
    )
    tab.scale(1.4, 1.4)
    axis.axis("off")
    
    return tab

def time_ticks(x, pos):
    return str(datetime.timedelta(seconds=x))

if __name__ ==  "__main__":
    main()