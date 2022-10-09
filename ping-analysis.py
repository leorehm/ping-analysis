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
# TODO: type functions

def main():
    args = parse_args()
    latencies = read_files(args.file)

    plots = []
    if args.plot in ["single", "both"]:
        # plots.append(plot_single(latencies, args.ma_window))
        plots.append(create_plot(latencies, args.ma_window, "single"))
    if args.plot in ["multi", "both"]:
        # plots.append(plot_multi(latencies, args.ma_window))
        plots.append(create_plot(latencies, args.ma_window, "multi"))

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
        type = int,
        help = "moving-average window in seconds; default = 20"
    )
    return parser.parse_args()

def read_files(files: list[argparse.FileType]) -> pd.DataFrame:
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
            "△ t": str(df[col].last_valid_index()).split( )[-1],
            "count": df[col].count(),
            "mean": df[col].mean(skipna = True).round(2),
            "median": df[col].median(skipna=True),
            "std": df[col].std(skipna=True).round(2),
            "min": df[col].min(skipna=True),
            "max": df[col].max(skipna=True),
            "25%": df[col].quantile(.25),
            "75%": df[col].quantile(.75),
            "90%": df[col].quantile(.9),
            "95%": df[col].quantile(.95),
        }
    return pd.DataFrame.from_dict(desc)

def create_plot(latencies: pd.DataFrame, ewm_window: int = 20, plots: str = "single") -> plt:
    desc = describe(latencies)
    cols = list(latencies.columns.values)

    if plots == "multi":
        n = latencies.shape[1]
    elif plots == "single":
        n = 1
    
    fig, axes = plt.subplots(
        nrows = n, ncols = 2,
        figsize = (16, 5 * n), 
        constrained_layout=True, 
        gridspec_kw={"width_ratios": [8, 1]}
    )

    fig.suptitle(f"ping statistics: moving average = {ewm_window} s", fontsize = 16)
    xformatter = ticker.FuncFormatter(timeTicks)

    # single chart
    if n == 1: 
        latencies.ewm(span = ewm_window).mean().plot(
            ax = axes[0], 
            alpha = 0.7,
            linewidth = 0.75
        )
        axes[0].set(xlabel = "△ t", ylabel = "latency in ms")
        axes[0].xaxis.set_major_formatter(xformatter)

        # TODO: table creation as seperate function
        tab = axes[1].table( 
            cellText = desc.values, 
            rowLabels = desc.index, 
            colLabels = desc.columns,
            loc = "center", 
            cellLoc = "center",
            edges = "open"
        )
        tab.scale(1.4, 1.4)
        axes[1].axis("off")
    # multiple charts
    else: 
        for i, col in enumerate(cols):
            latencies[col].ewm(span = 5).mean().plot(
                ax = axes[i, 0], 
                alpha = 0.7, 
                linewidth = 0.75
            )
            axes[i, 0].xaxis.set_major_formatter(xformatter)
            axes[i, 0].set(xlabel = "△ t", ylabel = "latency in ms", title = col)
            axes[i, 0].legend()
            
            colinfo = pd.DataFrame(desc[col])
            # TODO: table creation as seperate function
            tab = axes[i, 1].table( 
                cellText = colinfo.values, 
                rowLabels = colinfo.index, 
                loc = "center", 
                cellLoc = "center",
                edges = "open"
            )
            tab.scale(1.4, 1.4)
            axes[i, 1].axis("off")
    
    return plt

def timeTicks(x, pos):
    return str(datetime.timedelta(seconds=x))

if __name__ ==  "__main__":
    main()