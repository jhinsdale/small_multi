#!/usr/bin/env python3

import argparse
import csv
import os
import sys
from functools import cmp_to_key
from random import uniform, seed, choice

from small_multi import render_small_multiples
from htmltag import h_h2, h_p
from sm_chart import build_summary


DEMOS = {}
DEFAULT_SEED = 42
DEMO_SCALE = 2
HERE = os.path.dirname(os.path.abspath(__file__))


def demo(name):
    def deco(fn):
        DEMOS[name] = fn
        return fn
    return deco


def load_mlb_yearly(filename):
    by_player = {}
    order = []
    with open(os.path.join(HERE, "data", filename), newline="") as f:
        for player, year, value in csv.reader(f, delimiter="\t"):
            if player not in by_player:
                by_player[player] = {"title": player, "data": []}
                order.append(player)
            by_player[player]["data"].append({"label": year, "value": int(value)})
    return [by_player[player] for player in order]


# ----------------------- Demo: README quick start -----------------------
@demo("quickstart")
def demo_quickstart():
    opts = {"x_axis_title": "Quarter", "y_axis_title": "Profit ($k)",
            "preferred_bar_width": 25, "bar_spacing": .4}
    data = [
        {"title": "AlphaCo", "data": [
            {"label": "2024 Q1", "value": 100},
            {"label": "2024 Q2", "value": -30},
            {"label": "2024 Q3", "value": 60},
        ]},
        {"title": "BetaCo", "data": [
            {"label": "2024 Q1", "value": -10},
            {"label": "2024 Q2", "value": 50},
            {"label": "2024 Q3", "value": -20},
        ]},
    ]
    return ("README quick start: quarterly P&L", data, opts, {"totals": True})


# ----------------------- Demo: real-world MLB hits by year -----------------------
@demo("mlb-hits")
def demo_mlb_hits():
    opts = {"x_axis_title": "Season", "y_axis_title": "Hits",
            "preferred_bar_width": 14, "bar_spacing": .35,
            "max_chart_aspect": 4}
    data = load_mlb_yearly("mlb_3000_hit_club_hits_by_year.tsv")
    return ("MLB 3,000-hit Club: Hits by Season",
            data, opts, {"totals": True,
                         "summary": True, "scale": 1})


# ----------------------- Demo: real-world MLB strikeouts by year -----------------------
@demo("mlb-strikeouts")
def demo_mlb_strikeouts():
    opts = {"x_axis_title": "Season", "y_axis_title": "Strikeouts",
            "preferred_bar_width": 14, "bar_spacing": .35,
            "max_chart_aspect": 4}
    data = load_mlb_yearly("mlb_3000_strikeout_club_strikeouts_by_year.tsv")
    return ("MLB 3,000-strikeout Club: Strikeouts by Season",
            data, opts, {"totals": True,
                         "summary": True, "scale": 1})


# ----------------------- Demo: real-world MLB home runs by year -----------------------
@demo("mlb-home-runs")
def demo_mlb_home_runs():
    opts = {"x_axis_title": "Season", "y_axis_title": "Home runs",
            "preferred_bar_width": 14, "bar_spacing": .35,
            "max_chart_aspect": 4}
    data = load_mlb_yearly("mlb_500_home_run_club_home_runs_by_year.tsv")
    return ("MLB 500-home-run Club: Home Runs by Season",
            data, opts, {"totals": True,
                         "summary": True, "scale": 1})


# ----------------------- Demo: time series, all-positive -----------------------
@demo("time")
def demo_time():
    nchart, nx = 20, 3
    opts = {"x_axis_title": "Assessment period", "y_axis_title": "Correct answers",
            "preferred_bar_width": 18, "bar_spacing": .45}
    data = []
    for i in range(nchart):
        cdata = []
        cmax = uniform(1, 5000)
        for x in range(nx):
            if uniform(0, 1) >= 0.2:
                color = "red" if uniform(0, 1) <= 0.5 else None
                cdata.append({"value": int(uniform(0, cmax)),
                              "label": "X" + str(x) + "\nFoo", "color": color})
        data.append({"title": "Chart #" + str(i), "data": cdata})
    return ("Comparison of student performance trends, 2010 - 2015",
            data, opts, {"totals": True})


# ----------------------- Demo: stacked-mix proficiency composition -----------------------
@demo("mix")
def demo_mix():
    titles = ["Mrs.\nCooke", "Mr. Reynolds", "Ms. Chang", "Mrs. Russell", "Mr. Norman",
              "Ms. Janet", "Mrs. Williams", "Ms. O'Donnell", "Mrs. Melnick", "Ms. Boren",
              "Ms. Angela", "Mrs. Zeist", "Mr. Manning", "Ms. Ottavio", "Ms. Yu",
              "Mrs. Somnowitcz", "Ms. Yurkisian", "Mr. Fischer", "Ms. Ramanathan", "Mrs. Pulian"]
    opts = {"x_axis_title": "Assessment Outcome",
            "y_axis_title": "% Students",
            "preferred_bar_width": 30, "bar_spacing": .3}
    mix = "e0"
    red, yellow, green = "#" + mix + "0000", "#" + mix + mix + "00", "#00" + mix + "00"
    data = []
    for title in titles:
        pct_ok = uniform(30, 95)
        pct_border = uniform(20, 100 - pct_ok)
        pct_fail = 100 - pct_ok - pct_border
        data.append({"title": title, "data": [
            {"value": pct_fail,   "label": "Not\nProficient",      "color": red},
            {"value": pct_border, "label": "Somewhat\nProficient", "color": yellow},
            {"value": pct_ok,     "label": "Proficient",           "color": green},
        ]})

    def sortit(a, b):
        av = [c["value"] for c in a["data"]]
        bv = [c["value"] for c in b["data"]]
        ka, kb = av[2] * 1.5 + av[1], bv[2] * 1.5 + bv[1]
        return (kb > ka) - (kb < ka)
    data.sort(key=cmp_to_key(sortit))
    return ("Student Proficiency Composition by Class", data, opts, {"totals": False})


# ----------------------- Demo: mixed-sign quarterly P&L -----------------------
@demo("negative")
def demo_negative():
    opts = {"x_axis_title": "Quarter", "y_axis_title": "Profit ($k)",
            "preferred_bar_width": 25, "bar_spacing": .4}
    regions = ["North", "South", "East", "West", "Central",
               "Midwest", "Pacific", "Atlantic", "Mountain", "Plains"]
    quarters = ["2024 Q1", "2024 Q2", "2024 Q3", "2024 Q4",
                "2025 Q1", "2025 Q2", "2025 Q3", "2025 Q4"]
    data = []
    for region in regions:
        cdata = []
        for q in quarters:
            v = round(uniform(-50, 80), 1)
            cdata.append({"value": v, "label": q,
                          "color": "#cc3333" if v < 0 else "#3399cc"})
        data.append({"title": region, "data": cdata})
    return ("Quarterly P&L by Region (mixed sign)",
            data, opts, {"totals": True})


# ----------------------- Demo: all-negative (drawdowns) -----------------------
@demo("allneg")
def demo_allneg():
    opts = {"x_axis_title": "Quarter", "y_axis_title": "Drawdown ($k)",
            "preferred_bar_width": 25, "bar_spacing": .4}
    funds = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
    quarters = ["2024 Q1", "2024 Q2", "2024 Q3", "2024 Q4"]
    data = []
    for f in funds:
        cdata = [{"value": -round(uniform(5, 200), 1), "label": q, "color": "#cc3333"}
                 for q in quarters]
        data.append({"title": f + " Fund", "data": cdata})
    return ("Fund Drawdowns by Quarter (all negative)",
            data, opts, {"totals": True})


# ----------------------- Demo: monthly returns, color-by-sign -----------------------
@demo("returns")
def demo_returns():
    opts = {"x_axis_title": "Month", "y_axis_title": "Return (%)",
            "preferred_bar_width": 18, "bar_spacing": .35}
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "NVDA",
               "TSLA", "JPM", "XOM", "WMT", "PG", "HD"]
    data = []
    for t in tickers:
        cdata = []
        for m in months:
            v = round(uniform(-12, 14), 2)
            cdata.append({"value": v, "label": m,
                          "color": "#cc3333" if v < 0 else "#3399cc"})
        data.append({"title": t, "data": cdata})
    return ("Monthly returns by ticker (color by sign)",
            data, opts, {"totals": False, "preserve_order": True})


# ----------------------- Demo: sparse + topo-preserved order -----------------------
@demo("sparse")
def demo_sparse():
    # Charts share an overall ordering of X labels but each subject only reports a subset.
    # preserve_order=True will reconstruct the union ordering via topo sort.
    opts = {"x_axis_title": "Milestone", "y_axis_title": "Count",
            "preferred_bar_width": 22, "bar_spacing": .5}
    full_order = ["Spec", "Design", "Build", "Test", "Beta", "GA", "v1.1", "v1.2", "v2.0"]
    subjects = ["Team Hawk", "Team Lynx", "Team Otter", "Team Wren",
                "Team Bison", "Team Eagle"]
    data = []
    for s in subjects:
        # Pick a random contiguous slice of the milestone timeline
        start = int(uniform(0, len(full_order) - 3))
        end = int(uniform(start + 2, len(full_order)))
        cdata = []
        for label in full_order[start:end]:
            v = round(uniform(-30, 90), 1)
            cdata.append({"value": v, "label": label,
                          "color": "#cc3333" if v < 0 else "#3399cc"})
        data.append({"title": s, "data": cdata})
    return ("Per-team milestone outcomes (sparse, topo-preserved order)",
            data, opts, {"totals": False, "preserve_order": True})


# ----------------------- Demo: top-N aggregation -----------------------
@demo("top")
def demo_top():
    opts = {"x_axis_title": "Channel", "y_axis_title": "Net flow ($k)",
            "preferred_bar_width": 36, "bar_spacing": .35,
            "hover_color": "goldenrod"}
    channels = ["Direct", "Email", "Search", "Social", "Affiliate"]
    accounts = [f"Account #{i:02d}" for i in range(1, 21)]
    data = []
    for acct in accounts:
        cdata = []
        for c in channels:
            v = round(uniform(-40, 100), 1)
            cdata.append({"value": v, "label": c,
                          "color": "#cc3333" if v < 0 else "#3399cc"})
        data.append({"title": acct, "data": cdata})
    return ("Top 5 accounts by total net flow (rest aggregated)",
            data, opts, {"totals": True, "sort": True, "top": 5})


def main(argv):
    ap = argparse.ArgumentParser(description="small_multi demo suite")
    ap.add_argument("--demo", choices=sorted(DEMOS.keys()), default="negative",
                    help="which demo to render (default: %(default)s)")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help="seed RNG for reproducible output (default: %(default)s)")
    ap.add_argument("--scale", type=float, default=DEMO_SCALE,
                    help="display scale for generated SVG charts (default: %(default)s)")
    args = ap.parse_args(argv[1:])

    if args.seed is not None:
        seed(args.seed)

    title, data, chart_opts, render_kwargs = DEMOS[args.demo]()
    summary = render_kwargs.pop("summary", False)
    scale = render_kwargs.pop("scale", args.scale)
    render_kwargs.setdefault("preserve_order", False)
    code = render_small_multiples(data, None, None, "xMinYMin",
                                  scale=scale,
                                  chart_opts=chart_opts, **render_kwargs)
    print(h_h2(title, style="font-family: Arial"))
    if summary:
        print(h_p(demo_summary(data, chart_opts, render_kwargs),
                  style="font-family: Arial"))
    print(code)


def demo_summary(data, chart_opts, render_kwargs):
    class Args:
        pass
    args = Args()
    args.preserve_order = render_kwargs.get("preserve_order", False)
    args.top = render_kwargs.get("top")
    args.x_axis_title = chart_opts.get("x_axis_title")
    args.y_axis_title = chart_opts.get("y_axis_title")

    label_seqs = []
    y_min = None
    y_max = None
    for chart in data:
        seq = []
        for item in chart["data"]:
            seq.append(item["label"])
            v = item.get("value")
            if v is None:
                continue
            v = float(v)
            if y_min is None or v < y_min:
                y_min = v
            if y_max is None or v > y_max:
                y_max = v
        label_seqs.append(seq)
    return build_summary(args, data, label_seqs, y_min, y_max)


if __name__ == "__main__":
    main(sys.argv)
