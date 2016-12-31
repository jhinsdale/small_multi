# small_multi

Render Tufte-style **small multiples** of column charts as SVG, ready to drop into
an HTML page. Each chart in a series shares a uniform Y scale so that subjects can
be compared at a glance. Charts in the same rendered set use the same size and
the same data scale, so visual comparisons stay honest across subjects.

- One small function call produces the whole grid of charts as an SVG string.
- Charts in one output keep equal size and equal scale, even as the browser wraps
  them into more or fewer columns.
- Bars highlight on hover and show a tooltip with **subject, x-label, and y-value**.
- Negative values are supported: bars extend below a zero baseline.
- Per-bar and per-chart colors can be supplied.
- No third-party runtime dependencies. Pure Python 3.

## System requirements

- Python 3.
- No third-party Python packages.
- A browser or SVG-capable HTML renderer to view the generated output.

## Installation

Install from this source tree with `pip`:

```bash
pip install .
python3 -c "from small_multi import render_small_multiples; print('ok')"
```

Or just drop the directory on your `PYTHONPATH`. The library has no external
dependencies; `toposort` is included inline.

```bash
git clone <repo>
cd small_multi
python3 -c "from small_multi import render_small_multiples; print('ok')"
```

## Quick start (library)

```python
from small_multi import render_small_multiples

data = [
    {"title": "AlphaCo", "data": [
        {"label": "2024 Q1", "value":  100},
        {"label": "2024 Q2", "value":  -30},
        {"label": "2024 Q3", "value":   60},
    ]},
    {"title": "BetaCo", "data": [
        {"label": "2024 Q1", "value":  -10},
        {"label": "2024 Q2", "value":   50},
        {"label": "2024 Q3", "value":  -20},
    ]},
]

svg = render_small_multiples(
    data,
    chart_opts={
        "x_axis_title": "Quarter",
        "y_axis_title": "Profit ($k)",
        "preferred_bar_width": 25,
        "bar_spacing": 0.4,
    },
    totals=True,
)

with open("out.html", "w") as f:
    f.write("<html><body>" + svg + "</body></html>")
```

Open `out.html` in a browser. Hovering over any bar shows e.g.
`-30`, `2024 Q2`, and `AlphaCo` in a three-line tooltip.

## The data format

`data` is a list of one dict per chart:

```python
{
    "title": "Subject name",        # shown above the chart, also used as hover subject
    "data":  [ ... bar dicts ... ], # one entry per X position
    "chart_opts": { ... },          # OPTIONAL: per-chart overrides for chart_opts below
}
```

Each bar dict looks like:

```python
{
    "label": "X-axis label",   # required; may contain "\n" for multi-line labels
    "value": 42.0,             # required; numeric; may be negative; None to skip the bar
    "color": "#cc3333",        # optional; overrides the chart's data_color
}
```

Charts in a series do **not** need to have the same set of X labels. The library
takes the union of labels across all charts; charts missing a label render a gap
at that X position. See `preserve_order` below for how the merged order is chosen.

## The master API

```python
render_small_multiples(
    data,
    width=None,                 # px width per chart (None = use intrinsic SVG units)
    height=None,                # px height per chart
    preserveAspectRatio="none", # forwarded to each <svg>
    scale=None,                 # uniform scale factor when width/height not given
    totals=False,               # append "(<total>)" to each chart title
    sort=False,                 # sort charts by descending total
    top=None,                   # keep top N charts; aggregate the rest into "+ K others"
    preserve_order=False,       # see below
    chart_opts=None,            # dict of Chart attribute overrides applied to every chart
) -> str
```

Returns one HTML string, suitable for direct insertion into a page.

### Useful `chart_opts` keys

These tune the look of every chart in the set. Per-chart `chart_opts` (inside a
`data` entry) override the global ones.

| key                   | meaning                                              | default |
|-----------------------|------------------------------------------------------|---------|
| `x_axis_title`        | text under the X axis                                | `None`  |
| `y_axis_title`        | text left of the Y axis (may include `\n`)           | `None`  |
| `preferred_bar_width` | preferred bar width in chart units                   | `10`    |
| `bar_spacing`         | gap between bars, as a fraction of bar width         | `0.75`  |
| `bar_stroke_width`    | bar border width; `None` picks a readable default    | `None`  |
| `max_chart_aspect`    | max chart width as a multiple of height              | `4`     |
| `max_auto_chart_height` | max plot height for charts with many X values      | `150`   |
| `data_color`          | default bar fill when a bar has no explicit color    | `#0099ff` |
| `hover_color`         | bar fill while hovering                              | `goldenrod` |
| `tooltip_text_color`  | tooltip text fill; `None` uses `hover_color`         | `None` |
| `chart_color`         | color of axes, ticks, and labels                     | `black` |
| `stroke_width`        | line thickness for axes, bars, border                | `0.75`  |
| `border`              | border around each chart; `None` for no border       | `-1` (= `stroke_width`) |

### Hover tooltips

Every bar is wrapped in an SVG `<g>` element with a child `<title>` containing
`"<y-value>\n<x-label>\n<subject>"`. Browsers show this as a native tooltip on
hover. The SVG also renders a small tooltip above the hovered bar with the same
three lines; negative-value bars show the SVG tooltip under the bar. Newlines in
the subject or X-label are flattened to spaces inside the tooltip lines.

### Negative values

The Y-axis scale always includes zero. Bars with positive values extend up from
the zero line; bars with negative values extend down. The X-axis line is drawn
at the zero crossing, X-axis labels stay anchored to the bottom of the chart
area regardless of where zero falls, and Y-axis tick labels are emitted both
above and below zero.

The scale is uniform across the whole series: `data_min` and `data_max` are
computed over all values in all charts, so bar heights are directly comparable.
Charts in the same rendered output also keep the same displayed size. If the
browser window changes, the chart grid may reflow, but the charts remain
visually comparable.

### Sorting and top-N

- `sort=True`: charts are ordered by descending sum-of-values; ties broken by
  title.
- `top=N`: keep the top N charts and consolidate the rest into a single chart
  titled `+ K others` whose bars sum the discarded values per X label. Useful
  for keeping a grid readable when N is large.

### Label ordering (`preserve_order`)

By default, the union of X labels is sorted alphabetically. With
`preserve_order=True`, the library treats each chart's label list as a partial
ordering, then topo-sorts all of them into a consistent total order. Use this
when the X axis has natural sequence (timeline, milestone progression) that is
not alphabetical.

## CLI

`sm_chart.py` reads tab-delimited `(subject, x, y)` triples on stdin and writes
HTML to stdout. After `pip install .`, the same CLI is available as `sm-chart`.

```bash
printf 'AlphaCo\t2024Q1\t100\n'\
'AlphaCo\t2024Q2\t-30\n'\
'AlphaCo\t2024Q3\t60\n'\
'BetaCo\t2024Q1\t-10\n'\
'BetaCo\t2024Q2\t50\n'\
'BetaCo\t2024Q3\t-20\n' \
  | python3 sm_chart.py \
      --sm-title "Quarterly P&L" \
      --color-by-sign \
      --totals \
      > pnl.html
```

Installed CLI equivalent:

```bash
sm-chart --help
```

Key flags:

| flag                              | effect                                                       |
|-----------------------------------|--------------------------------------------------------------|
| `--sm-title TEXT`                 | overall heading above the chart grid                         |
| `-S`, `--summary`                 | print chart count plus X/Y ranges below the heading; unique Y extremes include the chart title |
| `--totals`                        | annotate each chart and the grid title with sums             |
| `--sort`                          | sort charts by descending total                              |
| `--top N`                         | keep top N charts, aggregate the rest into `+ K others`      |
| `--preserve-order`                | merge X-label sequences via topo sort instead of alphabetic  |
| `--color-by-sign`                 | color positive bars `--pos-color`, negatives `--neg-color`   |
| `--pos-color COLOR`               | default `#3399cc`                                            |
| `--neg-color COLOR`               | default `#cc3333`                                            |
| `--subject-file FILE`             | TSV mapping subject → color [→ display label]                |
| `--label-file FILE`               | TSV mapping X value → color [→ display label]                |
| `--x-axis-title`, `--y-axis-title`| axis titles                                                  |
| `--preferred-bar-width FRAC`      | bar-width preference                                         |
| `--bar-spacing FRAC`              | bar-spacing fraction                                         |
| `--width W`, `--height H`         | fixed pixel size per chart                                   |
| `--scale FACTOR`                  | uniform scale factor                                         |

A label-file color set explicitly always wins over `--color-by-sign`.

When `--summary` is used, the Y-range endpoints include the source chart title
and earliest matching X value only when that low or high value appears in
exactly one chart, for example `248 (Ty Cobb, 1911)`. Ambiguous endpoints are
left unannotated.

## Demo suite

`sm_test.py` ships a set of self-contained demos. Each writes HTML to stdout.

```bash
python3 sm_test.py --demo negative --seed 42 --scale 2 > demo.html
```

Available `--demo` values:

| name       | content                                                          |
|------------|------------------------------------------------------------------|
| `quickstart` | README quick-start quarterly P&L example                      |
| `mlb-hits` | real-world MLB 3,000-hit club, hits by season                  |
| `mlb-strikeouts` | real-world MLB 3,000-strikeout club, strikeouts by season |
| `mlb-home-runs` | real-world MLB 500-home-run club, home runs by season     |
| `time`     | per-chart random time series (all-positive)                      |
| `mix`      | stacked proficiency mix per teacher                              |
| `negative` | quarterly P&L per region (mixed sign, color-by-sign)             |
| `allneg`   | quarterly drawdowns (all negative)                               |
| `returns`  | monthly returns per ticker (mixed sign, color-by-sign)           |
| `sparse`   | per-team milestones with different label subsets (topo merge)    |
| `top`      | 20 accounts sorted by net flow, top 5 + aggregated rest          |

The MLB demo data comes from SABR's Lahman Baseball Database CSV files, filtered
to milestone clubs and grouped by player season. See `data/README.md` for source
and transform notes.

## Related utilities

- `tdf` — small `awk`-ish helper for extracting/transforming tab-delimited
  fields (column projection, sort, top-counts, author/quarter/file-type
  extraction, include/exclude/map filters). Independent of the chart code,
  bundled because it pairs well with the CLI pipeline.

## License

GPL v3.0 — see `LICENSE`.
