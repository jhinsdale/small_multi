#!/usr/bin/env python3
#
# Assertion-based regression tests for issues previously reported in ISSUES.md.
# Run: python3 test_small_multi.py
#

import copy
import os
import re
import subprocess
import sys
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from small_multi import render_small_multiples, total_order  # noqa: E402
from chart import Chart  # noqa: E402


def _bar_count(svg):
    return len(re.findall(r'<rect[^>]*class="bar"', svg))


def _xlabels(svg):
    return re.findall(r'class="xaxlabel"[^>]*>([^<]+)<', svg)


def _xmarkers(svg):
    return re.findall(r'<polygon[^>]*class="xlabel-marker"', svg)


class StyleScopingTests(unittest.TestCase):
    def test_charts_are_responsive_to_viewport(self):
        data = [{"title": "A", "data": [{"label": "x", "value": 1}]}]
        svg = render_small_multiples(data, scale=8)
        self.assertIn(".small-multiple-chart { width: 100%; max-width: 100%; height: auto;", svg)
        self.assertIn(".small-multiple-wrap { display: grid; grid-template-columns:", svg)
        self.assertIn("--small-multiple-basis:", svg)
        self.assertIn("--small-multiple-cols:", svg)
        self.assertIn("overflow: visible;", svg)
        self.assertIn('<div class="small-multiple-wrap" style="--small-multiple-basis:', svg)
        self.assertIn('class="small-multiple-chart"', svg)

    def test_dense_x_labels_are_thinned_and_readable(self):
        data = [{"title": "A", "data": [
            {"label": "2024-Q%02d" % i, "value": i} for i in range(80)
        ]}]
        svg = render_small_multiples(data, preserve_order=True)
        labels = _xlabels(svg)
        self.assertLess(len(labels), 80)
        self.assertIn('font-size: 4;', svg)

    def test_twenty_quarter_x_labels_fit_without_markers(self):
        labels = [
            "2021-Q4", "2022-Q1", "2022-Q2", "2022-Q3", "2022-Q4",
            "2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4",
            "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4",
            "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4",
            "2026-Q1", "2026-Q2", "2026-Q3",
        ]
        data = [{"title": "A", "data": [
            {"label": label, "value": i} for i, label in enumerate(labels)
        ]}]
        svg = render_small_multiples(data, preserve_order=True)
        self.assertEqual(len(_xmarkers(svg)), 0)
        self.assertIn("2021", _xlabels(svg))
        self.assertIn("-Q4", _xlabels(svg))

    def test_wrapped_x_label_width_controls_marker_decision(self):
        labels = ["Quarter_%04d-Q%d" % (2021 + (i // 4), (i % 4) + 1) for i in range(20)]
        data = [{"title": "A", "data": [
            {"label": label, "value": i} for i, label in enumerate(labels)
        ]}]
        svg = render_small_multiples(data, preserve_order=True)
        labels = _xlabels(svg)
        self.assertIn("Quarter", labels)
        self.assertIn("_2021", labels)
        self.assertIn("-Q1", labels)
        self.assertGreater(len(_xmarkers(svg)), 0)

    def test_thinned_nonnegative_x_labels_get_markers(self):
        data = [{"title": "A", "data": [
            {"label": "2024-Q%02d" % i, "value": i} for i in range(80)
        ]}]
        svg = render_small_multiples(data, preserve_order=True)
        self.assertGreater(len(_xmarkers(svg)), 0)
        self.assertLess(len(_xmarkers(svg)), len(_xlabels(svg)))

    def test_blank_displayed_labels_do_not_get_markers(self):
        chart = Chart()
        chart.y_x_axis_marker_height = 3
        chart.data = [
            {"label": "2024-Q%02d" % i, "value": i if i in (20, 40, 60) else None}
            for i in range(80)
        ]
        svg = chart.render_style() + chart.render_svg()
        self.assertLess(len(_xmarkers(svg)), len(_xlabels(svg)))

    def test_dense_bars_get_thinner_strokes(self):
        chart = Chart()
        chart.data = [{"label": str(i), "value": i} for i in range(153)]
        svg = chart.render_style() + chart.render_svg()
        bar = re.search(r'<rect(?=[^>]*class="bar")[^>]*/>', svg).group(0)
        stroke_width = float(re.search(r' stroke-width="([^"]+)"', bar).group(1))
        self.assertLess(stroke_width, chart.stroke_width)
        self.assertLessEqual(stroke_width, chart.bar_width * 0.12)

    def test_dense_charts_auto_expand_height_before_aspect_cap(self):
        chart = Chart()
        chart.data = [{"label": str(i), "value": i} for i in range(153)]
        chart.size_chart()
        self.assertEqual(chart.y_chart_height, chart.max_auto_chart_height)

    def test_marker_space_is_reserved_across_all_charts(self):
        labels = ["2024-Q%02d" % i for i in range(80)]
        data = [
            {"title": "A", "data": [
                {"label": label, "value": i} for i, label in enumerate(labels)
            ]},
            {"title": "B", "data": [
                {"label": label, "value": -1 if i == 3 else i} for i, label in enumerate(labels)
            ]},
        ]
        svg = render_small_multiples(data, preserve_order=True)
        heights = re.findall(r'<svg[^>]*height="([^"]+)"', svg)
        self.assertEqual(len(heights), 2)
        self.assertEqual(heights[0], heights[1])

    def test_thinned_labels_with_negative_values_do_not_get_markers(self):
        data = [{"title": "A", "data": [
            {"label": "2024-Q%02d" % i, "value": -1 if i == 3 else i} for i in range(80)
        ]}]
        svg = render_small_multiples(data, preserve_order=True)
        self.assertEqual(len(_xmarkers(svg)), 0)

    def test_per_chart_chart_color_reaches_later_charts(self):
        data = [
            {"title": "A", "data": [{"label": "x", "value": 1}],
             "chart_opts": {"chart_color": "red"}},
            {"title": "B", "data": [{"label": "x", "value": 2}],
             "chart_opts": {"chart_color": "blue"}},
        ]
        svg = render_small_multiples(data)
        self.assertIn("stroke: red", svg)
        self.assertIn("stroke: blue", svg)

    def test_unique_chart_ids(self):
        data = [
            {"title": "A", "data": [{"label": "x", "value": 1}]},
            {"title": "B", "data": [{"label": "x", "value": 2}]},
        ]
        svg = render_small_multiples(data)
        ids = re.findall(r'id="(sm-\d+)"', svg)
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)
        for cid in ids:
            self.assertIn("#" + cid + " .axis", svg)

    def test_bar_hover_style_and_title(self):
        data = [{"title": "Subject", "data": [{"label": "Q1", "value": 12}]}]
        svg = render_small_multiples(data)
        self.assertIn(".bar { cursor: pointer; }", svg)
        self.assertIn(".bar:hover { fill: goldenrod; }", svg)
        self.assertIn(".bar-tooltip-text", svg)
        self.assertIn("fill: goldenrod", svg)
        self.assertIn("onmouseover=", svg)
        self.assertIn("<title>12\nQ1\nSubject</title>", svg)
        self.assertIn('class="bar-tooltip"', svg)

    def test_custom_hover_color(self):
        data = [{"title": "Subject", "data": [{"label": "Q1", "value": 12}]}]
        svg = render_small_multiples(data, chart_opts={"hover_color": "red"})
        self.assertIn(".bar:hover { fill: red; }", svg)

    def test_negative_bar_tooltip_is_below_bar(self):
        chart = Chart()
        chart.data = [{"label": "Q1", "value": -10}]
        svg = chart.render_style() + chart.render_svg()
        bar = re.search(r'<rect(?=[^>]*class="bar")[^>]*/>', svg).group(0)
        tooltip = re.search(r'<rect(?=[^>]*class="bar-tooltip-bg")[^>]*/>', svg).group(0)
        bar_y = float(re.search(r' y="([^"]+)"', bar).group(1))
        bar_height = float(re.search(r' height="([^"]+)"', bar).group(1))
        tooltip_y = float(re.search(r' y="([^"]+)"', tooltip).group(1))
        self.assertGreater(tooltip_y, bar_y + bar_height)


class InputImmutabilityTests(unittest.TestCase):
    def test_caller_data_not_mutated(self):
        data = [
            {"title": "A", "data": [{"label": "x", "value": 1}]},
            {"title": "B", "data": [{"label": "y", "value": 2}]},
        ]
        snapshot = copy.deepcopy(data)
        render_small_multiples(data, sort=True, totals=True, top=1)
        self.assertEqual(data, snapshot)
        self.assertNotIn("total", data[0])
        self.assertNotIn("total", data[1])


class DuplicateLabelTests(unittest.TestCase):
    def test_duplicates_merged_alphabetical(self):
        data = [{"title": "A", "data": [
            {"label": "q1", "value": 10},
            {"label": "q1", "value": 5},
            {"label": "q2", "value": 3},
        ]}]
        svg = render_small_multiples(data, totals=True)
        self.assertIn("(18)", svg)
        self.assertEqual(_bar_count(svg), 2)

    def test_duplicates_merged_preserve_order(self):
        data = [{"title": "A", "data": [
            {"label": "q1", "value": 10},
            {"label": "q1", "value": 5},
            {"label": "q2", "value": 3},
        ]}]
        svg = render_small_multiples(data, totals=True, preserve_order=True)
        self.assertIn("(18)", svg)
        self.assertEqual(_bar_count(svg), 2)

    def test_consecutive_duplicate_only(self):
        data = [{"title": "A", "data": [
            {"label": "x", "value": 1},
            {"label": "x", "value": 2},
        ]}]
        svg = render_small_multiples(data, totals=True, preserve_order=True)
        self.assertIn("(3)", svg)
        self.assertEqual(_bar_count(svg), 1)


class PreserveOrderTests(unittest.TestCase):
    def test_topo_merge_across_charts(self):
        seqs = [
            ["q1", "q2", "q3"],
            ["q2", "q4"],
        ]
        result = total_order(seqs, preserve_order=True)
        self.assertEqual(result.index("q1") < result.index("q2"), True)
        self.assertEqual(result.index("q2") < result.index("q3"), True)
        self.assertEqual(result.index("q2") < result.index("q4"), True)

    def test_alphabetical_default(self):
        seqs = [["b", "a"], ["c"]]
        self.assertEqual(total_order(seqs, preserve_order=False), ["a", "b", "c"])

    def test_render_uses_preserve_order(self):
        data = [
            {"title": "A", "data": [
                {"label": "q1", "value": 1},
                {"label": "q2", "value": 2},
            ]},
            {"title": "B", "data": [
                {"label": "q2", "value": 4},
                {"label": "q3", "value": 5},
            ]},
        ]
        svg = render_small_multiples(data, preserve_order=True)
        labels = _xlabels(svg)
        self.assertEqual(labels[:3], ["q1", "q2", "q3"])


class ZeroTotalTests(unittest.TestCase):
    def test_zero_total_annotation(self):
        data = [{"title": "Z", "data": [
            {"label": "a", "value": 5},
            {"label": "b", "value": -5},
        ]}]
        svg = render_small_multiples(data, totals=True)
        self.assertIn("Z (0)", svg)

    def test_nonzero_total_annotation(self):
        data = [{"title": "P", "data": [
            {"label": "a", "value": 3},
        ]}]
        svg = render_small_multiples(data, totals=True)
        self.assertIn("P (3)", svg)


class HtmltagImportTests(unittest.TestCase):
    def test_local_module_renamed(self):
        self.assertTrue(os.path.exists(os.path.join(HERE, "htmltag.py")))
        self.assertFalse(os.path.exists(os.path.join(HERE, "html.py")))

    def test_stdlib_html_not_shadowed(self):
        # Run a subprocess from this directory and confirm `import html`
        # resolves to the standard library, not a local module.
        code = (
            "import html, sys;"
            "sys.exit(0 if 'python' in html.__file__ and hasattr(html,'escape') else 1)"
        )
        rc = subprocess.call([sys.executable, "-c", code], cwd=HERE)
        self.assertEqual(rc, 0)

    def test_htmltag_module_imports(self):
        import htmltag
        self.assertTrue(callable(htmltag.h_h2))
        self.assertEqual(htmltag.h_h2("hi"), "<h2>hi</h2>")


class CliSummaryTests(unittest.TestCase):
    def test_summary_line_reports_chart_count_and_ranges(self):
        data = "B\t2024-Q2\t-5\nA\t2024-Q1\t10\nA\t2024-Q3\t20\n"
        out = subprocess.check_output(
            [
                sys.executable, os.path.join(HERE, "sm_chart.py"),
                "--summary",
                "--x-axis-title", "Quarter",
                "--y-axis-title", "Commits",
            ],
            input=data.encode("utf-8"),
            cwd=HERE,
        ).decode("utf-8")
        self.assertIn(
            '<p style="font-family: Arial"><span style="color: #0099ff">2</span> charts '
            '&bull; Quarter: <span style="color: #0099ff">2024-Q1</span> - '
            '<span style="color: #0099ff">2024-Q3</span> &bull; Commits: '
            '<span style="color: #0099ff">-5 (B, 2024-Q2)</span> - '
            '<span style="color: #0099ff">20 (A, 2024-Q3)</span></p>',
            out,
        )

    def test_summary_count_matches_top_aggregation(self):
        data = "A\tq1\t3\nB\tq1\t2\nC\tq1\t1\n"
        out = subprocess.check_output(
            [
                sys.executable, os.path.join(HERE, "sm_chart.py"),
                "--summary", "--top", "1",
            ],
            input=data.encode("utf-8"),
            cwd=HERE,
        ).decode("utf-8")
        self.assertIn('<span style="color: #0099ff">2</span> charts &bull; X: '
                      '<span style="color: #0099ff">q1</span> - '
                      '<span style="color: #0099ff">q1</span> &bull; Y: '
                      '<span style="color: #0099ff">1 (C, q1)</span> - '
                      '<span style="color: #0099ff">3 (A, q1)</span>', out)

    def test_summary_omits_subject_for_ambiguous_extreme(self):
        data = "A\tq1\t0\nB\tq1\t0\nC\tq1\t3\n"
        out = subprocess.check_output(
            [
                sys.executable, os.path.join(HERE, "sm_chart.py"),
                "--summary",
            ],
            input=data.encode("utf-8"),
            cwd=HERE,
        ).decode("utf-8")
        self.assertIn('Y: <span style="color: #0099ff">0</span> - '
                      '<span style="color: #0099ff">3 (C, q1)</span>', out)

    def test_summary_uses_earliest_x_for_repeated_extreme_in_one_subject(self):
        data = "A\tq2\t5\nA\tq1\t5\nB\tq1\t1\n"
        out = subprocess.check_output(
            [
                sys.executable, os.path.join(HERE, "sm_chart.py"),
                "--summary",
            ],
            input=data.encode("utf-8"),
            cwd=HERE,
        ).decode("utf-8")
        self.assertIn('<span style="color: #0099ff">5 (A, q1)</span>', out)

    def test_header_grand_total_is_colored(self):
        data = "A\tq1\t3\nB\tq1\t2\n"
        out = subprocess.check_output(
            [
                sys.executable, os.path.join(HERE, "sm_chart.py"),
                "--sm-title", "Commits",
                "--totals",
            ],
            input=data.encode("utf-8"),
            cwd=HERE,
        ).decode("utf-8")
        self.assertIn('Commits <span style="color: #0099ff">(5)</span>', out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
