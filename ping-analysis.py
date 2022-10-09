#!/usr/bin/python

import argparse
from os.path import basename
from itertools import dropwhile
import re
import datetime
from matplotlib import pyplot as plt
from matplotlib import ticker
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type = argparse.FileType("r"), nargs = "+", help = "one or more files to be read")
    args = parser.parse_args()

    latencies = read_files(args.file)
    print(describe(latencies))
    print(latencies.head(2), "\n", latencies.tail(2))
    
    plots = []
    plots.append(plot_mult(latencies))
    plots.append(single = plot_single(latencies))

    for plot in plots:
        plot.show()

def read_files(files) -> pd.DataFrame:
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

def extract_pings(pings):
    # remove head until "Reply from" is matched
    pings = list(dropwhile(lambda ln: "Reply from" not in ln, pings))
    # remove tail until "Reply from" is matched
    n = len(pings)
    i = n - 1
    while "Reply from" not in pings[i]:
        pings.pop(i)
        i -=  1
    lines_to_delete = len(pings) - 1 - i
    pings[-lines_to_delete:lines_to_delete and None] = []
    return pings

def get_datetime(ping) -> int:
    return datetime.datetime.strptime(ping[0:19], "%d.%m.%Y %H:%M:%S")

def get_latency(ping) -> int:
    return int(re.search("time=(\d*)", ping).group(1))

def describe(df: pd.DataFrame, include = 'all') -> pd.DataFrame:
    if include == 'all':
        cols = list(df.columns.values)
    else: 
        cols = include
    desc = {}
    for col in cols: 
        desc[col] = {
            "count": df[col].count(),
            "mean": df[col].mean(skipna = True).round(2),
            "median": df[col].median(skipna=True),
            "std": df[col].std(skipna=True).round(2),
            "min": df[col].min(skipna=True),
            "max": df[col].max(skipna=True),
            "05%": df[col].quantile(.05),
            "01%": df[col].quantile(.1),
            "75%": df[col].quantile(.75),
            "90%": df[col].quantile(.9),
            "95%": df[col].quantile(.95),
        }
    return pd.DataFrame.from_dict(desc)

def plot_mult(latencies: pd.DataFrame, ewm_window: int = 20) -> plt:
    n = latencies.shape[1]
    cols = list(latencies.columns.values)
    desc = describe(latencies)    
    
    plt.title(label = f"ping statistics - moving average = {ewm_window} s")
    
    fig, axes = plt.subplots(
        nrows = n, ncols = 2, 
        sharey = True,
        figsize = (16, 10), 
        constrained_layout=True, 
        gridspec_kw={"width_ratios": [8, 1]}
    )

    fig.suptitle(f"ping statistics: moving average = {ewm_window} s", fontsize = 16)

    for i, col in enumerate(cols):
        # latencies[col].plot(
        #     ax = axes[i, 0], 
        #     alpha = 0.5, 
        #     label = "latency in ms", 
        #     linewidth = 0.75
        # )
        latencies[col].ewm(span = 5).mean().plot(
            ax = axes[i, 0], 
            alpha = 0.7, 
            label = "10s average",
            linewidth = 0.75
        )
        
        axes[i, 0].xaxis.set_major_formatter(ticker.FuncFormatter(timeTicks))
        axes[i, 0].set(xlabel = "time", ylabel = "latency in ms", title = col)
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

def plot_single(latencies: pd.DataFrame, ewm_window: int = 20):
    cols = list(latencies.columns.values)
    desc = describe(latencies)

    fig, axes = plt.subplots(
        nrows = 1, ncols = 2, 
        figsize = (16, 10 / 2), 
        constrained_layout=True, 
        gridspec_kw={"width_ratios": [8, 1]}
    )
    latencies.ewm(span = ewm_window).mean().plot(
        ax = axes[0], 
        alpha = 0.7,
        linewidth = 0.75
    )
    fig.suptitle(f"ping statistics: moving average = {ewm_window} s", fontsize = 16)
    axes[0].xaxis.set_major_formatter(ticker.FuncFormatter(timeTicks))

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
    
    return plt

def timeTicks(x, pos):
    return str(datetime.timedelta(seconds=x))

if __name__ ==  "__main__":
    main()