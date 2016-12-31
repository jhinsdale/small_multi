#
# small_multi.py
#
# Copyright 2014-2016 John K. Hinsdale

from toposort import toposort
from svgtag import st_style, st_svg, st_text, st_rect, st_line, st_coords, pp
from chart import Chart, string_height

# Given data, process and render small multiple charts
def render_small_multiples(data, width, height, preserveAspectRatio, scale=None, totals=False, sort=False, top=None, preserve_order=False, chart_opts={}):

    # print data

    # Scan data and get overall max, totals, and lists of labels for merging, max title height
    label_seqs = []
    overall_max = None
    max_chart_title_lines = None
    for cinf in data:
        cdata = cinf["data"]
        label_seqs.append([item["label"] for item in cdata])
        cinf["total"] = 0
        for item in cdata:
            if item["value"] is not None:
                if overall_max is None or item["value"] > overall_max:
                    overall_max = item["value"]
                cinf["total"] += item["value"]

        h = string_height(cinf["title"])
        if max_chart_title_lines is None or h > max_chart_title_lines:
            max_chart_title_lines = h

    # print overall_max
    # print label_seqs
    all_labels = total_order(label_seqs, preserve_order=preserve_order)
    # print all_labels
    
    # Rebuild input sequences of data
    for i in range(0, len(data)):
        cdata_labels = {}
        cdata = data[i]["data"]
        for item in cdata:
            cdata_labels[item["label"]] = item
        new_cdata = []
        for label in all_labels:
            if label in cdata_labels:
                new_cdata.append(cdata_labels[label])
            else:
                new_cdata.append({"label": label, "value": None})
        data[i]["data"] = new_cdata

    # Sort charts reverse by total, then title
    def sort_by_top_total(a, b):
        res = cmp(b["total"], a["total"])
        if res == 0:
            return cmp(a["title"], b["title"])
        return res
    if sort or top:
        data.sort(cmp=sort_by_top_total)

    # If doing "top", clip off top elements and append "others" chart data
    # Only aggregate smaller data if two or more would be consolidated
    if top is not None and top < len(data) - 1:
        # Clip off top charts
        to_agg = data[top:]
        data = data[0:top]
        agg_cinf = {"title": "+ " + str(len(to_agg)) + " others", "data": []}
        agg_data = agg_cinf["data"]
        agg_total = 0
        for label in all_labels:
            agg_data.append({"label":label, "value": None})
        for cinf in to_agg:
            i = 0
            for item in cinf["data"]:
                if item["value"] is not None:
                    if agg_data[i]["value"] is None:
                        agg_data[i]["value"] = 0
                    agg_data[i]["value"] += item["value"]
                    agg_total += item["value"]
                i += 1
        agg_cinf["total"] = agg_total
        data.append(agg_cinf)

    # Create charts
    first = True
    result = ""
    for cinfo in data:
        chart = Chart()

        # Set chart title and height in lines
        chart.chart_title = cinfo["title"]
        if totals and cinfo["total"]:
            chart.chart_title += " (" + num_disp(cinfo["total"]) + ")"
        chart.y_chart_title_lines = max_chart_title_lines

        # Set chart data
        chart.data = cinfo["data"]

        # Set chart options from global input, plus per-data chart options (e.g., chart data color) which override
        opts = cinfo.get("chart_opts", {})
        opts = dict(chart_opts.items() + opts.items())
        for k, v in opts.iteritems():
            setattr(chart, k, opts[k])

        # print chart.data
        chart.data_max = overall_max
        if first:
            result += chart.render_style()
            first = False
        result += chart.render_svg(width=width, height=height, scale=scale, preserveAspectRatio=preserveAspectRatio)

    return result

    # o = total_order(seqs)
    # print o


# Merge partial orderings into a total ordering by constructing order graph and doing a topo sort
# Alternatively, just do a straight sort
def total_order(seqs, preserve_order=False):
    # Straight sort
    if not preserve_order:
        distinct = {}
        for seq in seqs:
            for item in seq:
                distinct[item] = True
        result = distinct.keys()
        result.sort()
        return result

    # Use topo sort to preserve order on merging.  This is not always 100% reliable
    # but will work if enough partial ordering occurs in the individual sequences
    ordering = {}
    for seq in seqs:
        if len(seq) <= 1:
            continue
        for i in range(0, len(seq)-1):
            if seq[i+1] not in ordering:
                ordering[seq[i+1]] = set()
            ordering[seq[i+1]].add(seq[i])
    result = []
    for ties in toposort(ordering):
        sorted = list(ties)
        sorted.sort()
        for item in sorted:
            result.append(item)
    return result

# Display number abbreviated
def num_disp(n):
    if n < 1000:
        if n == int(n):
            return str(int(n))
        return ("%.3g" % n)
    if n >= 1000 and n < 1000000:
        return "%.3gk" % (n / 1000)
    if n >= 1000000 and n < 1000000000:
        return "%.3gm" % (n / 1000000)
    if n >= 1000000000 and n < 1000000000000:
        return "%.3gG" % (n / 1000000000)
    if n >= 1000000000000 and n < 1000000000000000:
        return "%.3gT" % (n / 1000000000000)
    return str(n)
