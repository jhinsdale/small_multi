#
# small_multi.py
#
# Master entrypoint: render_small_multiples(...)

import copy
import math
from functools import cmp_to_key

from chart import Chart, string_height


# Tiny toposort (Kahn's algorithm). Mirrors the 'toposort' PyPI package API used previously:
# input is {node: set(predecessor_nodes)}; yields successive sets of nodes whose predecessors
# have all been emitted.
def toposort(deps):
    all_nodes = set(deps.keys())
    for ps in deps.values():
        all_nodes.update(ps)
    remaining = {n: set(deps.get(n, ())) for n in all_nodes}
    while remaining:
        ready = {n for n, d in remaining.items() if not d}
        if not ready:
            raise ValueError("cyclic dependency in label ordering")
        yield ready
        for n in ready:
            del remaining[n]
        for n in remaining:
            remaining[n] -= ready


# Master API. Returns an SVG string (single <style> block followed by N <svg> chart elements).
#
# data: list of {"title": <subject>, "data": [{"label": <x>, "value": <y>, "color": <opt>}], "chart_opts": {<opt>}}
# width, height: optional fixed pixel size per chart (None = use intrinsic units)
# preserveAspectRatio: SVG attr forwarded to each <svg>
# scale: optional uniform scale factor (applied when width/height not supplied)
# totals: append "(<total>)" to each chart title
# sort: sort charts by descending total
# top: keep only top N charts, aggregate the rest into one "+ K others" chart
# preserve_order: try to preserve relative input order of X labels via topo sort (vs alphabetical)
# chart_opts: dict of attribute names -> values applied to every Chart (per-chart chart_opts override)
def render_small_multiples(data, width=None, height=None, preserveAspectRatio="none",
                           scale=None, totals=False, sort=False, top=None,
                           preserve_order=False, chart_opts=None):
    if chart_opts is None:
        chart_opts = {}

    # Deep-copy so caller-owned dicts/lists are not mutated by the additions and
    # rewrites below (per-chart 'total' insertion, padded data replacement, sort).
    data = copy.deepcopy(data)

    # Scan data: per-chart totals, overall min/max, X label sequences, max title height
    label_seqs = []
    overall_max = None
    overall_min = None
    max_chart_title_lines = None
    for cinf in data:
        cdata = cinf["data"]
        label_seqs.append([item["label"] for item in cdata])
        cinf["total"] = 0
        for item in cdata:
            v = item.get("value")
            if v is None:
                continue
            v = float(v)
            if overall_max is None or v > overall_max:
                overall_max = v
            if overall_min is None or v < overall_min:
                overall_min = v
            cinf["total"] += v

        h = string_height(cinf.get("title"))
        if max_chart_title_lines is None or h > max_chart_title_lines:
            max_chart_title_lines = h

    if overall_max is None:
        overall_max = 0.0
    if overall_min is None:
        overall_min = 0.0

    all_labels = total_order(label_seqs, preserve_order=preserve_order)

    # Rebuild per-chart data, padding missing labels with value=None.
    # Duplicate labels in one chart are merged (values summed, first color kept)
    # so the rendered bar matches the chart total instead of silently dropping bars.
    for i in range(len(data)):
        cdata_labels = {}
        for item in data[i]["data"]:
            lbl = item["label"]
            existing = cdata_labels.get(lbl)
            if existing is None:
                cdata_labels[lbl] = dict(item)
            else:
                ev = existing.get("value")
                iv = item.get("value")
                if ev is None:
                    existing["value"] = iv
                elif iv is not None:
                    existing["value"] = float(ev) + float(iv)
                if "color" not in existing and "color" in item:
                    existing["color"] = item["color"]
        new_cdata = []
        for label in all_labels:
            if label in cdata_labels:
                new_cdata.append(cdata_labels[label])
            else:
                new_cdata.append({"label": label, "value": None})
        data[i]["data"] = new_cdata

    if sort or top:
        def sort_by_top_total(a, b):
            res = _cmp(b["total"], a["total"])
            if res == 0:
                return _cmp(a.get("title") or "", b.get("title") or "")
            return res
        data.sort(key=cmp_to_key(sort_by_top_total))

    # Aggregate tail into "+ K others"
    if top is not None and 0 < top < len(data):
        to_agg = data[top:]
        data = data[:top]
        agg_cinf = {"title": "+ " + str(len(to_agg)) + " others", "data": []}
        agg_data = agg_cinf["data"]
        agg_total = 0
        # Per-label color tallies, bucketed by sign of the source bar
        pos_colors = [{} for _ in all_labels]
        neg_colors = [{} for _ in all_labels]
        for label in all_labels:
            agg_data.append({"label": label, "value": None})
        for cinf in to_agg:
            for i, item in enumerate(cinf["data"]):
                v = item.get("value")
                if v is None:
                    continue
                if agg_data[i]["value"] is None:
                    agg_data[i]["value"] = 0.0
                agg_data[i]["value"] += float(v)
                agg_total += float(v)
                c = item.get("color")
                if c is not None:
                    bucket = pos_colors[i] if v >= 0 else neg_colors[i]
                    bucket[c] = bucket.get(c, 0) + 1
        # Pick a color for each aggregated bar by matching the sign of its sum
        # to the most common source-bar color of that sign
        for i, item in enumerate(agg_data):
            v = item.get("value")
            if v is None:
                continue
            bucket = pos_colors[i] if v >= 0 else neg_colors[i]
            if bucket:
                item["color"] = max(bucket.items(), key=lambda kv: kv[1])[0]
            # Extend the uniform scale so the aggregated bar fits the chart area
            if v > overall_max:
                overall_max = v
            if v < overall_min:
                overall_min = v
        agg_cinf["total"] = agg_total
        data.append(agg_cinf)

    any_x_label_markers = False
    for cinfo in data:
        chart = Chart(assign_id=False)
        chart.data = cinfo["data"]
        opts = {**chart_opts, **cinfo.get("chart_opts", {})}
        for k, v in opts.items():
            setattr(chart, k, v)
        if chart.needs_x_label_marker_space():
            any_x_label_markers = True
            break

    charts = []
    chart_basis = 0
    for cinfo in data:
        chart = Chart()
        subject = cinfo.get("title")
        chart.subject = subject
        chart.chart_title = subject
        if totals and cinfo.get("total") is not None:
            chart.chart_title = (chart.chart_title or "") + " (" + num_disp(cinfo["total"]) + ")"
        chart.y_chart_title_lines = max_chart_title_lines
        chart.data = cinfo["data"]

        # Merge global chart_opts with per-chart chart_opts (per-chart wins)
        opts = {**chart_opts, **cinfo.get("chart_opts", {})}
        for k, v in opts.items():
            setattr(chart, k, v)
        if any_x_label_markers:
            chart.y_x_axis_marker_height = 3

        # Uniform scale across all charts in the set
        chart.data_max = overall_max
        chart.data_min = overall_min

        chart_width = chart.width()
        displayed_width = width if width is not None else (scale * chart_width if scale is not None else chart_width)
        if displayed_width > chart_basis:
            chart_basis = displayed_width
        charts.append(chart)

    # Build charts. Each chart emits its own <style> block scoped to a unique id
    # so per-chart chart_opts (colors, fonts) cannot leak across charts on the page.
    preferred_cols = max(1, int(math.ceil(math.sqrt(len(charts) * 2)))) if charts else 1
    basis_style = "--small-multiple-basis: %.6gpx; --small-multiple-cols: %d;" % (chart_basis, preferred_cols) if chart_basis else ""
    result = (
        "<style>\n"
        ".small-multiple-chart { width: 100%; max-width: 100%; height: auto; box-sizing: border-box; overflow: visible; }\n"
        ".small-multiple-wrap { display: grid; grid-template-columns: repeat(auto-fit, minmax(max(min(100%, var(--small-multiple-basis)), calc(100% / var(--small-multiple-cols))), 1fr)); align-items: start; }\n"
        "</style>"
        '<div class="small-multiple-wrap" style="' + basis_style + '">'
    )
    for chart in charts:
        result += chart.render_style()
        result += chart.render_svg(width=width, height=height, scale=scale,
                                   preserveAspectRatio=preserveAspectRatio)

    result += "</div>"
    return result


def _cmp(a, b):
    return (a > b) - (a < b)


# Merge partial orderings into a total ordering. If preserve_order is False, just sort distinct values.
def total_order(seqs, preserve_order=False):
    if not preserve_order:
        distinct = set()
        for seq in seqs:
            distinct.update(seq)
        return sorted(distinct)

    ordering = {}
    for seq in seqs:
        for item in seq:
            ordering.setdefault(item, set())
        # Skip self-edges: consecutive duplicates in one chart's labels are merged
        # downstream, so x -> x would create a false cycle without changing order.
        for i in range(len(seq) - 1):
            if seq[i] == seq[i + 1]:
                continue
            ordering.setdefault(seq[i + 1], set()).add(seq[i])
    result = []
    for ties in toposort(ordering):
        for item in sorted(ties):
            result.append(item)
    return result


def num_disp(n):
    av = abs(n)
    if av < 1000:
        if n == int(n):
            return str(int(n))
        return "%.3g" % n
    if av < 1_000_000:
        return "%.3gk" % (n / 1000)
    if av < 1_000_000_000:
        return "%.3gm" % (n / 1_000_000)
    if av < 1_000_000_000_000:
        return "%.3gG" % (n / 1_000_000_000)
    if av < 1_000_000_000_000_000:
        return "%.3gT" % (n / 1_000_000_000_000)
    return str(n)
