#
# Chart class
#

from svgtag import *
import re, math

# Default margin
DEFM = 12

class Chart:
    """Chart class"""

    def __init__(self):

        # Dimensions ... if "y_chart_height" is 100, then they end up being expressed
        # a percentage of that height which is intuitive

        # Vertical increments, starting from top.  Mostly non-overlapping, except
        # for X axis and tick lines, as tick lines start at axis line center
        self.y_top_margin = DEFM            # Top margin
        self.y_chart_title_height = 10      # Size of one line of chart title (if exists)
        self.y_chart_title_lines = None     # Nubmer of chart title lines for which to allocate space
        self.y_chart_height = 100           # Chart height, usually this is left at 100.  Data is scaled to this height.
        self.y_x_axis_tick_height = 0       # Height of "ticks" on X axis (if present)
        self.y_x_axis_label_margin = 1      # Vertical margin between X axis (center of line, or bottom of ticks) and labels (if exist)
                                            # This needs to be >= half the thickness of the X axis for labels never to never overlap
        self.y_x_axis_label_lines = None    # Number of lines for X axis labels (0 if no labels)
        self.y_x_axis_title_margin = 5      # Margin between X axis labels and X axis title, only relevant when an X axis title exists
        self.y_bottom_margin = 0            # Bottom margin

        # Horizontal increments, starting from left.  Mostly non-overlapping, except
        # for Y axis and tick lines, as tick lines start at axis line center.
        # These are analagous to the Vertical dimension increments above, in reverse order
        self.x_left_margin = DEFM           # Left margin
        self.x_y_axis_label_width = 10      # Width of text for Y axis labels (if exist)
        self.x_y_axis_label_margin = 2      # Horizontal margin between Y-axis labels (if exist) and center line of Y axis
                                            # This needs to be >= half thickness of the Y axis to never overlap
        self.x_y_axis_tick_width = 2        # Width of ticks on Y axis
        self.x_chart_width = None           # Chart width, will depend on how much X-axis data there is.
        self.x_right_margin = DEFM          # Right margin

        # Titles
        self.chart_title = None                     # Text of chart title
        self.chart_title_font_family = "Arial"      # Font size of chart title
        self.x_axis_title = None
        self.x_axis_title_lines = None
        self.y_axis_title = None
        self.y_axis_title_lines = None

        # Stroke width for axes, bars, border, etc.
        self.stroke_width = 0.75                 # Stroke width

        # Axis ticks and labels.  There should be a label in the array for every tick implied by tick_sep.
        # Unlaballed ticks have empty label in the array
        self.axis_label_height = 5               # Height of one line of label text for Y axis labels and axis titles (if exist)
        self.x_axis_label_height = None          # Height of one line of label text for X axis labels (if exist).  May be scaled based on bar width
        self.axis_tick_thickness = 0.2           # X/Y-axis Thickness of tick lines
        self.axis_label_font_family = "Arial"    # Font size of chart title

        # Colors
        self.chart_color = "black"           # Color of "chart ink" - axes, ticks, labels, etc.
        self.data_color = "#0099ff"          # Color of "data ink" (content that varies)

        # Bar dimensions and spacing
        self.max_chart_aspect = 4            # Maximum width of chart as a multiple of height
        self.preferred_bar_width = 10        # Preferred width of maximum bar in units
        self.bar_width = None                # Actual width of bar, possibly shrunk for max aspect
        self.bar_spacing = .75               # Space between bars, a fraction of bar width
     
        # Draw box around whole chart?
        self.border = -1                     # Border for whole chart.  None for no border, -1 means default to stroke_width

        # Data
        self.data = []			     # Data points
        self.data_max = None                 # Max value of data


    # Size the chart, setting self.x_chart_width and adjusting self.bar_width
    def size_chart(self):
        ndata = len(self.data)

        # See if already done
        if self.x_chart_width is not None and self.bar_width is not None:
            return

        # One of chart_width or preferred_bar_width must be set
        if self.x_chart_width is None and self.preferred_bar_width is None:
            raise Exception("One of chart_width or preferred_bar_width must be set")

        # Set chart width based on preferred bar width, stopping at max aspect
        if self.x_chart_width is None:
            # Determine total chart width, based on number of bars and preferred bar width
            # If number of bars grows large, scale down the bar width to fit a maximum chart width
            # as given by max_chart_aspect
            width_preferred = (self.preferred_bar_width * ndata) + (self.bar_spacing * self.preferred_bar_width) * (ndata + 1)
            width_max = self.y_chart_height * self.max_chart_aspect
            if width_preferred <= width_max:
                self.x_chart_width = width_preferred
            else:
                self.x_chart_width = width_max
                
        # Make actual width so we fit N bars and N+1 spacings into chart width
        # Solve for w: (w * ndata) + (bs * w)*(ndata + 1) = TW
        # -> w = TW / ( ndata + bs * (ndata + 1) )
        self.bar_width = self.x_chart_width / (ndata + self.bar_spacing * (ndata + 1))

        # Based on bard width, adjust X axis label size
        self.x_axis_label_height = self.axis_label_height * self.bar_width / self.preferred_bar_width

    # Drawing locations, calculated from dimensions
    # Y location of chart title
    def y_loc_chart_title(self):
        return self.y_top_margin

    # Y location of Y axis title
    def y_loc_y_axis_title(self):
        result = self.y_loc_chart_title()
        if self.chart_title:
            result += self.y_chart_title_height * self.count_y_chart_title_lines()
        return result

    # Y location of top of chart area
    def y_loc_chart_top(self):
        result = self.y_loc_y_axis_title()
        if self.y_axis_title:
            result += self.axis_label_height * self.count_y_axis_title_lines()
        return result

    # Y location of X axis line (on center).  The is also the Y (vertical)
    # start of vertical X-axis "tick" lines, which start from the X-axis line's vertical
    # center and extend downward for y_x_axis_tick_height units
    def y_loc_x_axis(self):
        return self.y_loc_chart_top() + self.y_chart_height

    # Y location of X axis labels
    def y_loc_x_axis_label(self):
        self.size_chart()
        result = self.y_loc_x_axis() + self.y_x_axis_tick_height
        self.count_x_axis_label_lines()
        if self.y_x_axis_label_lines > 0:
            result += self.y_x_axis_label_margin + self.x_axis_label_height
        return result

    # Location of X axis title
    def y_loc_x_axis_title(self):
        result = self.y_loc_x_axis_label()
        self.count_x_axis_label_lines()
        if self.y_x_axis_label_lines > 0:
            result += self.x_axis_label_height * self.y_x_axis_label_lines
        if self.x_axis_title:
            result += self.y_x_axis_title_margin
        return result

    # Bottom of chart drawn area (excl. bottom margin)
    def y_loc_chart_bottom(self):
        result = self.y_loc_x_axis_title()
        if self.x_axis_title:
            result += self.axis_label_height * self.count_x_axis_title_lines()
        return result

    # Total height, i.e. Y location of bottom of chart incl. margin
    def height(self):
        return self.y_loc_chart_bottom() + self.y_bottom_margin

    # X locations (horizontal)
    # X location of start of Y axis label
    def x_loc_y_axis_label(self):
        return self.x_left_margin

    # X location of start of Y axis tick line
    def x_loc_y_axis_tick(self):
        result = self.x_loc_y_axis_label()
        result += self.x_y_axis_label_width + self.x_y_axis_label_margin
        return result

    # X location of Y axis line.  This is also the center point of the Y axis title
    def x_loc_y_axis(self):
        return self.x_loc_y_axis_tick() + self.x_y_axis_tick_width

    # X location of right end of chart
    def x_loc_chart_right(self):
        self.size_chart()
        return self.x_loc_y_axis() + self.x_chart_width

    # X location of center of chart
    def x_loc_chart_center(self):
        self.size_chart()
        return self.x_loc_y_axis() + self.x_chart_width / 2

    # Total width, i.e. X location of right edge of chart incl margin
    def width(self):
        return self.x_loc_chart_right() + self.x_right_margin

    # Get style content
    def render_style(self):
        self.size_chart()
        axth = str(self.stroke_width)
        tkth = str(self.axis_tick_thickness)
        ctfs = str(self.y_chart_title_height)
        ctff = self.chart_title_font_family
        axlfs = str(self.axis_label_height)
        xaxlfs = str(self.x_axis_label_height)
        axlff = self.axis_label_font_family
        ccolor = self.chart_color
        dcolor = self.data_color
        result = \
            "<style>\n" \
        + ".axis { stroke: " + ccolor + "; stroke-width: " + axth + "; }\n" \
        + ".tick { stroke: " + ccolor + "; stroke-width: " + tkth + "; }\n" \
        + ".ctitle { font-family: \"" + ctff + "\"; font-size: " + ctfs + "; text-anchor: middle; }\n" \
        + ".axlabel { font-family: \"" + axlff + "\"; font-size: " + axlfs + "; text-anchor: middle; fill: " + ccolor + "; }\n" \
        + ".xaxlabel { font-family: \"" + axlff + "\"; font-size: " + xaxlfs + "; text-anchor: middle; fill: " + ccolor + "; }\n" \
        + ".yaxlabel { font-family: \"" + axlff + "\"; font-size: " + axlfs + "; text-anchor: start; fill: " + ccolor + "; }\n" \
        + "</style>"
        return result

    # Render SVG doc
    def render_svg(self, preserveAspectRatio="none", width=None, height=None, scale=None):
        elts = []

        # Border around whole chart
        sw = self.border
        if sw is not None:
            if sw < 0:
                sw = self.stroke_width
            elts.append(st_rect(x=sw/2.0, y=sw/2.0, width=self.width() - sw*2, height=self.height() - sw*2,
                                stroke=self.chart_color, fill="none", stroke_width=sw))

        # Chart title lines
        if self.chart_title:
            y = self.y_loc_chart_title()
            x = self.x_loc_chart_center()
            chart_title_lines = _label_lines(self.chart_title)
            for line in chart_title_lines:
                elts.append(st_text(line, _class="ctitle", x=x, y=y, fill=self.data_color))
                y += self.y_chart_title_height

        # Y axis title lines
        if self.y_axis_title:
            y = self.y_loc_y_axis_title()
            x = self.x_loc_y_axis_label()
            y_axis_title_lines = _label_lines(self.y_axis_title)
            for line in y_axis_title_lines:
                elts.append(st_text(line, _class="yaxlabel", x=x, y=y))
                y += self.axis_label_height

        # X axis title
        if self.x_axis_title:
            y = self.y_loc_x_axis_title()
            x = self.x_loc_chart_center()
            x_axis_title_lines = _label_lines(self.x_axis_title)
            for line in x_axis_title_lines:
                elts.append(st_text(line, _class="axlabel", x=x, y=y))
                y += self.axis_label_height

        # X axis line
        x1 = self.x_loc_y_axis() - self.stroke_width / 2.0
        y1 = y2 = self.y_loc_x_axis()
        x2 = self.x_loc_chart_right()
        elts.append(st_line(_class="axis", x1=x1, y1=y1, x2=x2, y2=y2))
        
        # Y axis line
        x1 = x2 = self.x_loc_y_axis()
        y1 = self.y_loc_chart_top()
        y2 = self.y_loc_x_axis() + self.stroke_width / 2.0
        elts.append(st_line(_class="axis", x1=x1, y1=y1, x2=x2, y2=y2))
        
        # Data bars
        # Get max data (if not already set explicity)
        if self.data_max is None:
            for d in self.data:
                v = _data_value(d)
                if self.data_max is None or v > self.data_max:
                    self.data_max = v
                
        # Draw bars, scaled so that self.data_max extends up to self.y_chart_height
        # Also draw X axis labels
        spacing_width = self.bar_spacing * self.bar_width
        x_y_axis = self.x_loc_y_axis()
        y_x_axis = self.y_loc_x_axis()
        y_x_axis_label = self.y_loc_x_axis_label()
        curx = x_y_axis + spacing_width
        cc = self.chart_color
        bsw = self.stroke_width
        for d in self.data:
            v = _data_value(d)
            fill = _data_color(d)
            if fill is None:
                fill = self.data_color
            if v is not None:
                bar_height = (v / self.data_max) * self.y_chart_height
                y = y_x_axis - bar_height
                elts.append(st_rect(x=curx, y=y, width=self.bar_width, height=bar_height, fill=fill, stroke=cc, stroke_width=bsw))

            # Draw X axis label at rectangle center
            rect_center = curx + self.bar_width / 2.0
            xlabel = _data_label(d)
            xlabel_lines = _label_lines(xlabel)
            label_y = y_x_axis_label
            for label_line in xlabel_lines:
                elts.append(st_text(label_line, _class="xaxlabel", x=rect_center, y=label_y))
                label_y += self.x_axis_label_height

            # Advance X value
            curx += spacing_width + self.bar_width
            
        # Draw Y axis labels and ticks
        (y_incr, y_labels) = _axis_labels_for_max(self.data_max)
        cur_val = y_incr
        x_label = self.x_loc_y_axis_label()
        x_tick = self.x_loc_y_axis_tick()
        i = 0
        for y_label in y_labels:
            if cur_val > self.data_max:
                # Should never get here
                break
            # Get offset above X axis at which to draw label
            y_offset = cur_val * self.y_chart_height / self.data_max
            y_tick = y_x_axis - y_offset
            y_lb = y_tick + (self.axis_label_height / 2.0)
            elts.append(st_text(y_label, _class="yaxlabel", x=x_label, y=y_lb))

            # Draw Y axis tick, but not the last one
            elts.append(st_line(_class="tick", x1=x_tick, y1=y_tick, x2=x_y_axis, y2=y_tick))

            # Advance to next tick value
            cur_val += y_incr


        # Top level SVG
        # Size chart using given dimensions, or implied dimensions, optionally scaled
        chart_width = self.width()
        chart_height = self.height()
        vbox = st_coords(0, 0, chart_width, chart_height)
        if width is None:
            if scale is not None:
                svg_width = scale * chart_width
            else:
                svg_width = chart_width
        else:
            svg_width = width
        if height is None:
            if scale is not None:
                svg_height = chart_height * scale
            else:
                svg_height = chart_height
        else:
            svg_height = height
        
        result = st_svg(elts, viewBox=vbox, preserveAspectRatio=preserveAspectRatio, width=svg_width, height=svg_height)
        return result

    # Count chart title lines
    def count_y_chart_title_lines(self):
        if self.y_chart_title_lines is not None:
            return self.y_chart_title_lines
        self.y_chart_title_lines = string_height(self.chart_title)
        return self.y_chart_title_lines

    # Count Y axis title lines
    def count_y_axis_title_lines(self):
        if self.y_axis_title_lines is not None:
            return self.y_axis_title_lines
        self.y_axis_title_lines = string_height(self.y_axis_title)
        return self.y_axis_title_lines

    # Count X axis title lines
    def count_x_axis_title_lines(self):
        if self.x_axis_title_lines is not None:
            return self.x_axis_title_lines
        self.x_axis_title_lines = string_height(self.x_axis_title)
        return self.x_axis_title_lines

    # Count X axis label lines and set self.y_x_axis_label_lines
    def count_x_axis_label_lines(self):
        if self.y_x_axis_label_lines is not None:
            return self.y_x_axis_label_lines
        max_height = 0
        for d in self.data:
            l = _data_label(d)
            h = string_height(l)
            if h > max_height:
                max_height = h
        self.y_x_axis_label_lines = max_height
        return max_height

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=   Private routines -=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Get numeric value of data pont
def _data_value(d):
    if "value" not in d or d["value"] is None:
        return None
    return float(d["value"])

# Get label for data point
def _data_label(d):
    return d["label"]

# Get color for data point
def _data_color(d):
    if "color" in d:
        return d["color"]
    return None

# Normalize newlines, mapping multiple \r\n's into a single \n
def _normalize_newlines(s):
    if s is None:
        return s
    return re.sub("[\\r\\n]+", "\n", s)

# Get lines for multi-line label
def _label_lines(s):
    s = _normalize_newlines(s)
    return s.split("\n")

# Get height of string
def string_height(s):
    if s is None or s == "":
        return 0
    s = _normalize_newlines(s)
    return s.count("\n") + 1

# Axis labels for max value
def _axis_labels_for_max(n):
    n = float(n)
    (base, exp) = _base_exp(n)
    if base < 2.0:
        incr = 5 * pow(10, exp - 1)
    else:
        incr = pow(10, exp)
    cur = incr
    labels = []
    while cur <= n:
        if cur >= 1000000000:
            cur_disp = ("%.2g" % (cur/1000000000.0)) + "G"
        elif cur >= 1000000:
            cur_disp = ("%.2g" % (cur/1000000.0)) + "M"
        elif cur >= 1000:
            cur_disp = ("%.2g" % (cur/1000.0)) + "k"
        else:
            cur_disp = str(cur)
        labels.append(str(cur_disp))
        cur += incr
    return (incr, labels)

# Get base and exponent of a number
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
