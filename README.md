# small_multi
Python library for rendering Tufte-style "small multiples" charts in SVG

Author:
	John Hinsdale
	38 Quaker Road,
	Princeton Junction, NJ 08550 USA
	Email: hin@alma.com

This Python code allows to render a series of SVG charts, which may
then be embedded in HTML, that display data in a set of equally-sized
"small multiples" for comparison.  This is a great way, for example,
to compare time series against each other.

The only chart style is the column chart, but coloration of the entire
little chart, or bars within the chart, is supported.

A data file manipulation program, "tdf" (tab-delimited-file) is also
included for processing input data, extracting fields, etc.
