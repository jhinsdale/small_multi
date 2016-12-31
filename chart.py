#
# Chart class
#

import re
import math

from svgtag import st_text, st_rect, st_line, st_svg, st_coords, st_g, st_title, st_polygon

DEFM = 12

_CHART_ID_SEQ = 0


def _next_chart_id():
    global _CHART_ID_SEQ
    _CHART_ID_SEQ += 1
    return _CHART_ID_SEQ

# Whitelist values that get interpolated into the <style> block (CSS context).
# Rejects anything containing ;, {, }, <, >, ", \, parens, or newlines.
_SAFE_CSS_COLOR_RE = re.compile(r'^(#[0-9a-fA-F]{3,8}|[a-zA-Z]{1,32})$')
_SAFE_CSS_FONT_RE  = re.compile(r'^[a-zA-Z0-9 ,_.\-]{1,64}$')


def _check_css_color(v, attr):
    if not _SAFE_CSS_COLOR_RE.match(str(v)):
        raise ValueError("unsafe CSS color for %s: %r" % (attr, v))
    return str(v)


def _check_css_font(v, attr):
    if not _SAFE_CSS_FONT_RE.match(str(v)):
        raise ValueError("unsafe CSS font for %s: %r" % (attr, v))
    return str(v)


class Chart:
    """Single SVG bar chart. Supports negative values and per-bar hover titles."""

    def __init__(self, assign_id=True):
        # Vertical increments, top -> bottom
        self.y_top_margin = DEFM
        self.y_chart_title_height = 10
        self.y_chart_title_lines = None
        self.y_chart_height = 100
        self.max_auto_chart_height = 150
        self.y_x_axis_tick_height = 0
        self.y_x_axis_marker_height = 0
        self.y_x_axis_label_margin = 1
        self.y_x_axis_label_lines = None
        self.y_x_axis_title_margin = 5
        self.y_bottom_margin = 0

        # Horizontal increments, left -> right
        self.x_left_margin = DEFM
        self.x_y_axis_label_width = 10
        self.x_y_axis_label_margin = 2
        self.x_y_axis_tick_width = 2
        self.x_chart_width = None
        self.x_right_margin = DEFM

        # Titles
        self.chart_title = None
        self.chart_title_font_family = "Arial"
        self.x_axis_title = None
        self.x_axis_title_lines = None
        self.y_axis_title = None
        self.y_axis_title_lines = None

        # Strokes
        self.stroke_width = 0.75
        self.bar_stroke_width = None

        # Labels and ticks
        self.axis_label_height = 5
        self.x_axis_label_height = None
        self.min_x_axis_label_height = 4
        self.x_axis_label_gap = 6
        self.axis_tick_thickness = 0.2
        self.axis_label_font_family = "Arial"

        # Colors
        self.chart_color = "black"
        self.data_color = "#0099ff"
        self.hover_color = "goldenrod"
        self.tooltip_bg_color = "white"
        self.tooltip_text_color = None

        # Bars
        self.max_chart_aspect = 4
        self.preferred_bar_width = 10
        self.bar_width = None
        self.bar_spacing = .75

        # Border
        self.border = -1

        # Data
        self.data = []
        self.data_max = None        # caller may set externally to fix scale across multiples
        self.data_min = None        # caller may set externally to fix scale across multiples
        self.subject = None         # used for hover tooltip; usually equals chart_title without totals

        # Unique DOM id so per-chart CSS does not leak across charts on one page
        self.chart_id = "sm-%d" % _next_chart_id() if assign_id else None

    # Effective scaling range: always includes zero so positive/negative bars share a baseline
    def _effective_range(self):
        dmax = self.data_max if self.data_max is not None else 0.0
        dmin = self.data_min if self.data_min is not None else 0.0
        eff_max = max(0.0, float(dmax))
        eff_min = min(0.0, float(dmin))
        span = eff_max - eff_min
        return eff_min, eff_max, span

    def size_chart(self):
        ndata = len(self.data)
        if self.x_chart_width is not None and self.bar_width is not None:
            return
        if self.x_chart_width is None and self.preferred_bar_width is None:
            raise Exception("One of chart_width or preferred_bar_width must be set")

        if self.x_chart_width is None:
            width_preferred = (self.preferred_bar_width * ndata) + (self.bar_spacing * self.preferred_bar_width) * (ndata + 1)
            if self.max_auto_chart_height is not None:
                height_for_preferred = width_preferred / self.max_chart_aspect
                self.y_chart_height = min(self.max_auto_chart_height,
                                          max(self.y_chart_height, height_for_preferred))
            width_max = self.y_chart_height * self.max_chart_aspect
            self.x_chart_width = min(width_preferred, width_max)

        # Solve (w * ndata) + (bs * w) * (ndata + 1) = TW
        self.bar_width = self.x_chart_width / (ndata + self.bar_spacing * (ndata + 1))
        scaled_label_height = self.axis_label_height * self.bar_width / self.preferred_bar_width
        fit_label_height = self._x_label_height_to_fit_all()
        if fit_label_height is not None:
            scaled_label_height = min(scaled_label_height, fit_label_height)
        self.x_axis_label_height = max(self.min_x_axis_label_height, scaled_label_height)

    def _x_label_height_to_fit_all(self):
        ndata = len(self.data)
        if ndata == 0:
            return None
        max_chars = 0
        for d in self.data:
            max_chars = max(max_chars, _max_wrapped_label_chars(_data_label(d)))
        if max_chars == 0:
            return None
        available = (self.x_chart_width / ndata) - self.x_axis_label_gap
        if available <= 0:
            return None
        return available / (max_chars * 0.6)

    # --- Vertical drawing locations (cumulative from top) ---

    def y_loc_chart_title(self):
        return self.y_top_margin

    def y_loc_y_axis_title(self):
        result = self.y_loc_chart_title()
        if self.chart_title:
            result += self.y_chart_title_height * self.count_y_chart_title_lines()
        return result

    def y_loc_chart_top(self):
        result = self.y_loc_y_axis_title()
        if self.y_axis_title:
            result += self.axis_label_height * self.count_y_axis_title_lines()
        return result

    # Y coord of the chart-area bottom (lowest possible bar extent)
    def y_loc_chart_area_bottom(self):
        return self.y_loc_chart_top() + self.y_chart_height

    # Y coord of zero on the data axis -- this is where the X-axis line is drawn
    def y_loc_x_axis(self):
        eff_min, eff_max, span = self._effective_range()
        top = self.y_loc_chart_top()
        if span <= 0:
            return top + self.y_chart_height
        # zero is at top + (eff_max / span) * height
        return top + (eff_max / span) * self.y_chart_height

    def y_loc_x_axis_label(self):
        self.size_chart()
        # X axis labels go below the entire chart area, regardless of where the zero line is
        result = self.y_loc_chart_area_bottom() + self.y_x_axis_tick_height + self.y_x_axis_marker_height
        self.count_x_axis_label_lines()
        if self.y_x_axis_label_lines > 0:
            margin = 0 if self.y_x_axis_marker_height > 0 else self.y_x_axis_label_margin
            result += margin + self.x_axis_label_height
        return result

    def y_loc_x_axis_title(self):
        result = self.y_loc_x_axis_label()
        self.count_x_axis_label_lines()
        if self.y_x_axis_label_lines > 0:
            result += self.x_axis_label_height * self.y_x_axis_label_lines
        if self.x_axis_title:
            result += self.y_x_axis_title_margin
        return result

    def y_loc_chart_bottom(self):
        result = self.y_loc_x_axis_title()
        if self.x_axis_title:
            result += self.axis_label_height * self.count_x_axis_title_lines()
        return result

    def height(self):
        return self.y_loc_chart_bottom() + self.y_bottom_margin

    # --- Horizontal drawing locations ---

    def x_loc_y_axis_label(self):
        return self.x_left_margin

    def x_loc_y_axis_tick(self):
        return self.x_loc_y_axis_label() + self.x_y_axis_label_width + self.x_y_axis_label_margin

    def x_loc_y_axis(self):
        return self.x_loc_y_axis_tick() + self.x_y_axis_tick_width

    def x_loc_chart_right(self):
        self.size_chart()
        return self.x_loc_y_axis() + self.x_chart_width

    def x_loc_chart_center(self):
        self.size_chart()
        return self.x_loc_y_axis() + self.x_chart_width / 2

    def width(self):
        return self.x_loc_chart_right() + self.x_right_margin

    def render_style(self):
        self.size_chart()
        axth  = str(self.stroke_width)
        tkth  = str(self.axis_tick_thickness)
        ctfs  = str(self.y_chart_title_height)
        ctff  = _check_css_font(self.chart_title_font_family, "chart_title_font_family")
        axlfs = str(self.axis_label_height)
        xaxlfs = str(self.x_axis_label_height)
        axlff = _check_css_font(self.axis_label_font_family, "axis_label_font_family")
        ccolor = _check_css_color(self.chart_color, "chart_color")
        hcolor = _check_css_color(self.hover_color, "hover_color")
        ttbg = _check_css_color(self.tooltip_bg_color, "tooltip_bg_color")
        tttxt = _check_css_color(
            self.tooltip_text_color if self.tooltip_text_color is not None else self.hover_color,
            "tooltip_text_color")

        sel = "#" + self.chart_id
        return (
            "<style>\n"
            + sel + " .axis { stroke: " + ccolor + "; stroke-width: " + axth + "; }\n"
            + sel + " .tick { stroke: " + ccolor + "; stroke-width: " + tkth + "; }\n"
            + sel + " .bar { cursor: pointer; }\n"
            + sel + " .bar:hover { fill: " + hcolor + "; }\n"
            + sel + " .bar-wrap:hover .bar { fill: " + hcolor + "; }\n"
            + sel + " .bar-tooltip { display: none; pointer-events: none; }\n"
            + sel + " .bar-wrap:hover .bar-tooltip { display: inline; }\n"
            + sel + " .bar-tooltip-bg { fill: " + ttbg + "; stroke: " + ccolor + "; stroke-width: " + tkth + "; }\n"
            + sel + ' .bar-tooltip-text { font-family: "' + axlff + '"; font-size: ' + axlfs + "; text-anchor: middle; fill: " + tttxt + "; }\n"
            + sel + " .xlabel-marker { fill: black; }\n"
            + sel + ' .ctitle { font-family: "' + ctff + '"; font-size: ' + ctfs + "; text-anchor: middle; }\n"
            + sel + ' .axlabel { font-family: "' + axlff + '"; font-size: ' + axlfs + "; text-anchor: middle; fill: " + ccolor + "; }\n"
            + sel + ' .xaxlabel { font-family: "' + axlff + '"; font-size: ' + xaxlfs + "; text-anchor: middle; fill: " + ccolor + "; }\n"
            + sel + ' .yaxlabel { font-family: "' + axlff + '"; font-size: ' + axlfs + "; text-anchor: start; fill: " + ccolor + "; }\n"
            + "</style>"
        )

    def render_svg(self, preserveAspectRatio="none", width=None, height=None, scale=None):
        elts = []

        # Border around whole chart
        sw = self.border
        if sw is not None:
            if sw < 0:
                sw = self.stroke_width
            elts.append(st_rect(x=sw / 2.0, y=sw / 2.0,
                                width=self.width() - sw * 2,
                                height=self.height() - sw * 2,
                                stroke=self.chart_color, fill="none", stroke_width=sw))

        # Chart title lines
        if self.chart_title:
            y = self.y_loc_chart_title()
            x = self.x_loc_chart_center()
            for line in _label_lines(self.chart_title):
                elts.append(st_text(line, _class="ctitle", x=x, y=y, fill=self.data_color))
                y += self.y_chart_title_height

        # Y axis title lines
        if self.y_axis_title:
            y = self.y_loc_y_axis_title()
            x = self.x_loc_y_axis_label()
            for line in _label_lines(self.y_axis_title):
                elts.append(st_text(line, _class="yaxlabel", x=x, y=y))
                y += self.axis_label_height

        # X axis title
        if self.x_axis_title:
            y = self.y_loc_x_axis_title()
            x = self.x_loc_chart_center()
            for line in _label_lines(self.x_axis_title):
                elts.append(st_text(line, _class="axlabel", x=x, y=y))
                y += self.axis_label_height

        # Compute scale (auto-derive min/max from data if not set externally)
        if self.data_max is None or self.data_min is None:
            derived_max = None
            derived_min = None
            for d in self.data:
                v = _data_value(d)
                if v is None:
                    continue
                if derived_max is None or v > derived_max:
                    derived_max = v
                if derived_min is None or v < derived_min:
                    derived_min = v
            if self.data_max is None:
                self.data_max = derived_max if derived_max is not None else 0.0
            if self.data_min is None:
                self.data_min = derived_min if derived_min is not None else 0.0

        eff_min, eff_max, span = self._effective_range()
        y_zero = self.y_loc_x_axis()

        # X axis line (drawn at zero crossing)
        x1 = self.x_loc_y_axis() - self.stroke_width / 2.0
        x2 = self.x_loc_chart_right()
        elts.append(st_line(_class="axis", x1=x1, y1=y_zero, x2=x2, y2=y_zero))

        # Y axis line spans the full chart area (top of chart to bottom of chart)
        x1 = x2 = self.x_loc_y_axis()
        y1 = self.y_loc_chart_top()
        y2 = self.y_loc_chart_area_bottom() + self.stroke_width / 2.0
        elts.append(st_line(_class="axis", x1=x1, y1=y1, x2=x2, y2=y2))

        # Bars
        spacing_width = self.bar_spacing * self.bar_width
        x_y_axis = self.x_loc_y_axis()
        y_x_axis_label = self.y_loc_x_axis_label()
        curx = x_y_axis + spacing_width
        cc = self.chart_color
        bsw = self.effective_bar_stroke_width()

        label_indexes = self.visible_x_label_indexes()
        show_x_label_markers = len(label_indexes) < len(self.data) and self.values_are_nonnegative()
        tooltip_elts = []
        for i, d in enumerate(self.data):
            v = _data_value(d)
            fill = _data_color(d)
            if fill is None:
                fill = self.data_color

            if v is not None and span > 0:
                pixels = (abs(v) / span) * self.y_chart_height
                if v >= 0:
                    bar_y = y_zero - pixels
                else:
                    bar_y = y_zero
                bar = st_rect(x=curx, y=bar_y, width=self.bar_width, height=pixels,
                              fill=fill, stroke=cc, stroke_width=bsw, _class="bar")
                hover_lines = _build_hover_lines(self.subject or self.chart_title, _data_label(d), v)
                tooltip_id = self.chart_id + "-tooltip-" + str(i)
                tooltip_elts.append(_build_tooltip(tooltip_id, hover_lines,
                                                   curx + self.bar_width / 2.0, bar_y, pixels, v < 0,
                                                   self.axis_label_height))
                elts.append(st_g(st_title("\n".join(hover_lines)), bar,
                                 onmouseover=_show_tooltip_js(tooltip_id),
                                 onmouseout=_hide_tooltip_js(tooltip_id),
                                 _class="bar-wrap"))

            # X-axis label centered under bar
            rect_center = curx + self.bar_width / 2.0
            if i in label_indexes:
                if show_x_label_markers and _data_value(d) is not None:
                    elts.append(st_polygon(points=_up_triangle_points(rect_center, self.y_loc_chart_area_bottom(), 2),
                                           _class="xlabel-marker"))
                xlabel = _data_label(d)
                label_y = y_x_axis_label
                for label_line in self.x_label_lines(xlabel):
                    elts.append(st_text(label_line, _class="xaxlabel", x=rect_center, y=label_y))
                    label_y += self.x_axis_label_height

            curx += spacing_width + self.bar_width

        elts.extend(tooltip_elts)

        # Y axis labels and ticks
        x_label = self.x_loc_y_axis_label()
        x_tick = self.x_loc_y_axis_tick()
        for tick_val, tick_label in _axis_ticks(eff_min, eff_max):
            if span <= 0:
                break
            y_offset = (tick_val / span) * self.y_chart_height
            y_tick = y_zero - y_offset
            y_lb = y_tick + (self.axis_label_height / 2.0)
            elts.append(st_text(tick_label, _class="yaxlabel", x=x_label, y=y_lb))
            elts.append(st_line(_class="tick", x1=x_tick, y1=y_tick, x2=x_y_axis, y2=y_tick))

        chart_width = self.width()
        chart_height = self.height()
        vbox = st_coords(0, 0, chart_width, chart_height)
        svg_width = width if width is not None else (scale * chart_width if scale is not None else chart_width)
        svg_height = height if height is not None else (chart_height * scale if scale is not None else chart_height)
        return st_svg(elts, viewBox=vbox, preserveAspectRatio=preserveAspectRatio,
                      width=svg_width, height=svg_height, id=self.chart_id,
                      _class="small-multiple-chart")

    def count_y_chart_title_lines(self):
        if self.y_chart_title_lines is not None:
            return self.y_chart_title_lines
        self.y_chart_title_lines = string_height(self.chart_title)
        return self.y_chart_title_lines

    def count_y_axis_title_lines(self):
        if self.y_axis_title_lines is not None:
            return self.y_axis_title_lines
        self.y_axis_title_lines = string_height(self.y_axis_title)
        return self.y_axis_title_lines

    def count_x_axis_title_lines(self):
        if self.x_axis_title_lines is not None:
            return self.x_axis_title_lines
        self.x_axis_title_lines = string_height(self.x_axis_title)
        return self.x_axis_title_lines

    def count_x_axis_label_lines(self):
        if self.y_x_axis_label_lines is not None:
            return self.y_x_axis_label_lines
        max_height = 0
        for d in self.data:
            h = len(self.x_label_lines(_data_label(d)))
            if h > max_height:
                max_height = h
        self.y_x_axis_label_lines = max_height
        return max_height

    def visible_x_label_indexes(self):
        self.size_chart()
        ndata = len(self.data)
        if ndata == 0:
            return set()

        max_label_width = 0
        for d in self.data:
            for line in self.x_label_lines(_data_label(d)):
                max_label_width = max(max_label_width, _estimate_text_width(line, self.x_axis_label_height))
        if max_label_width <= 0:
            return set(range(ndata))

        min_center_gap = max_label_width + self.x_axis_label_gap
        max_labels = max(1, int(self.x_chart_width / min_center_gap))
        if ndata <= max_labels:
            return set(range(ndata))

        stride = int(math.ceil(float(ndata) / max_labels))
        indexes = list(range(0, ndata, stride))
        if indexes[-1] != ndata - 1:
            if ndata - 1 - indexes[-1] < stride:
                indexes[-1] = ndata - 1
            else:
                indexes.append(ndata - 1)
        return set(indexes)

    def values_are_nonnegative(self):
        saw_value = False
        for d in self.data:
            v = _data_value(d)
            if v is None:
                continue
            saw_value = True
            if v < 0:
                return False
        return saw_value

    def needs_x_label_marker_space(self):
        label_indexes = self.visible_x_label_indexes()
        return len(label_indexes) < len(self.data) and self.values_are_nonnegative()

    def effective_bar_stroke_width(self):
        self.size_chart()
        if self.bar_stroke_width is not None:
            return self.bar_stroke_width
        return min(self.stroke_width, self.bar_width * 0.12)

    def x_label_lines(self, label):
        self.size_chart()
        max_width = self.bar_width + (self.bar_spacing * self.bar_width)
        return _x_label_lines(label, max_width, self.x_axis_label_height)


# ============================== Private helpers ==============================

def _data_value(d):
    v = d.get("value")
    return None if v is None else float(v)


def _data_label(d):
    return d["label"]


def _data_color(d):
    return d.get("color")


def _up_triangle_points(x_center, y_tip, size):
    half = size / 2.0
    return st_coords(x_center, y_tip, x_center - half, y_tip + size, x_center + half, y_tip + size)


def _normalize_newlines(s):
    return None if s is None else re.sub(r"[\r\n]+", "\n", s)


def _label_lines(s):
    s = _normalize_newlines(s)
    return s.split("\n")


def _x_label_lines(s, max_width, font_size):
    result = []
    for line in _label_lines(s):
        result.extend(_wrap_label_line(line, max_width, font_size))
    return result


def _wrap_label_line(line, max_width, font_size):
    parts = _split_label_for_wrap(line)
    if not parts:
        return [line]
    result = []
    cur = ""
    for part in parts:
        candidate = cur + part
        if cur and _estimate_text_width(candidate, font_size) > max_width:
            result.append(cur.rstrip())
            cur = part.lstrip()
        else:
            cur = candidate
    if cur:
        result.append(cur.rstrip())
    return result or [line]


def _split_label_for_wrap(line):
    parts = []
    start = 0
    s = str(line)
    for i, ch in enumerate(s):
        if ch == " ":
            parts.append(s[start:i + 1])
            start = i + 1
        elif ch in "-_":
            if start < i:
                parts.append(s[start:i])
            start = i
            j = i + 1
            while j < len(s) and s[j] not in " -_":
                j += 1
            parts.append(s[start:j])
            start = j
    if start < len(s):
        parts.append(s[start:])
    return parts


def _max_wrapped_label_chars(label):
    max_chars = 0
    for line in _label_lines(label):
        parts = _split_label_for_wrap(line)
        if parts:
            for part in parts:
                max_chars = max(max_chars, len(part.strip()))
        else:
            max_chars = max(max_chars, len(str(line)))
    return max_chars


def _estimate_text_width(s, font_size):
    return len(str(s)) * float(font_size) * 0.6


def string_height(s):
    if not s:
        return 0
    return _normalize_newlines(s).count("\n") + 1


def _build_hover_lines(subject, xlabel, yvalue):
    subject = _single_line_text(subject) if subject else ""
    xlabel = _single_line_text(xlabel) if xlabel is not None else ""
    lines = [_format_value(yvalue), xlabel]
    if subject:
        lines.append(subject)
    return lines


def _build_tooltip(tooltip_id, lines, x_center, bar_top_y, bar_height, place_below, font_size):
    pad_x = 2
    pad_y = 1
    line_height = float(font_size) * 1.2
    width = max(18, max(_estimate_text_width(line, font_size) for line in lines) + pad_x * 2)
    height = line_height * len(lines) + pad_y * 2
    gap = 2
    x = x_center - width / 2.0
    if place_below:
        y = bar_top_y + bar_height + gap
    else:
        y = max(0, bar_top_y - height - gap)
    text_y = y + pad_y + float(font_size)
    elts = [st_rect(x=x, y=y, width=width, height=height, rx=1, ry=1,
                    _class="bar-tooltip-bg")]
    for line in lines:
        elts.append(st_text(line, x=x_center, y=text_y, _class="bar-tooltip-text"))
        text_y += line_height
    return st_g(elts, id=tooltip_id, _class="bar-tooltip")


def _show_tooltip_js(tooltip_id):
    return "document.getElementById('" + tooltip_id + "').style.display='inline'"


def _hide_tooltip_js(tooltip_id):
    return "document.getElementById('" + tooltip_id + "').style.display='none'"


def _single_line_text(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def _format_value(v):
    if v is None:
        return ""
    f = float(v)
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    return ("%.6g" % f)


# Yield (value, label) pairs for tick marks across [eff_min, eff_max], symmetric around zero.
def _axis_ticks(eff_min, eff_max):
    span = eff_max - eff_min
    if span <= 0:
        return []
    incr = _nice_increment(max(abs(eff_max), abs(eff_min)))
    ticks = []
    # Positive ticks above zero
    v = incr
    while v <= eff_max + 1e-9:
        ticks.append((v, _disp(v)))
        v += incr
    # Negative ticks below zero
    v = -incr
    while v >= eff_min - 1e-9:
        ticks.append((v, _disp(v)))
        v -= incr
    return ticks


def _nice_increment(n):
    n = float(n)
    if n <= 0:
        return 1.0
    base, exp = _base_exp(n)
    if base < 2.0:
        return 5 * pow(10, exp - 1)
    return pow(10, exp)


def _disp(v):
    av = abs(v)
    if av >= 1e9:
        s = ("%.2g" % (v / 1e9)) + "G"
    elif av >= 1e6:
        s = ("%.2g" % (v / 1e6)) + "M"
    elif av >= 1e3:
        s = ("%.3g" % (v / 1e3)) + "k"
    else:
        if v == int(v):
            s = str(int(v))
        else:
            s = ("%.3g" % v)
    return s


def _base_exp(n):
    n = float(n)
    if n <= 0:
        return (0, 0)
    exp = int(math.log10(n))
    base = n / pow(10, exp)
    if base < 1.0:
        base *= 10
        exp -= 1
    return (base, exp)


# Backwards-compat wrapper: used to be the only label generator
def _axis_labels_for_max(n):
    incr = _nice_increment(n)
    labels = []
    cur = incr
    while cur <= n:
        labels.append(_disp(cur))
        cur += incr
    return (incr, labels)
