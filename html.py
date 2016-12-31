# html.py
# Copyright 2014-2016 John K. Hinsdale

from util import *
import cu

# Skirt Windows CRLF nonsense
import os
if os.name == "nt":
    import msvcrt

# These tags do not have a matching closer:
# area, base, basefont, br, hr, input, img, link, meta

# Wrap args inside <TAG kw1=val1 kw2=val2>...</TAG>
def html(tag, autoclose, *args, **kwargs):
    # Strip off leading "_" which may be used to avoid reserved word clashes
    def strip(att):
        if att[0] == "_":
            att = att[1:]
        return att
    def kval(k):
        result = " " + strip(k)
        if kwargs[k] is not None:
            result += "=\"" + xstr(kwargs[k]) + "\""
        return result;
    return "<" + tag \
               + scat(map(kval, kwargs.keys())) \
               + ">" + scat(args) \
               + ( ("</" + tag + ">") if autoclose else "" )

def h_html(*args, **kwargs):		return html("html", True, *args, **kwargs)
def h_head(*args, **kwargs):		return html("head", True, *args, **kwargs)
def h_title(*args, **kwargs):		return html("title", True, *args, **kwargs)
def h_link(*args, **kwargs):            return html("link", False, *args, **kwargs)
def h_body(*args, **kwargs):		return html("body", True, *args, **kwargs)

def h_table(*args, **kwargs):		return html("table", True, *args, **kwargs)
def h_tr(*args, **kwargs):		return html("tr", True, *args, **kwargs)
def h_td(*args, **kwargs):		return html("td", True, *args, **kwargs)
def h_th(*args, **kwargs):		return html("th", True, *args, **kwargs)

def h_h1(*args, **kwargs):		return html("h1", True, *args, **kwargs)
def h_h2(*args, **kwargs):		return html("h2", True, *args, **kwargs)
def h_h3(*args, **kwargs):		return html("h3", True, *args, **kwargs)

def h_p(*args, **kwargs):		return html("p", True, *args, **kwargs)
def h_b(*args, **kwargs):		return html("b", True, *args, **kwargs)
def h_i(*args, **kwargs):		return html("i", True, *args, **kwargs)
def h_pre(*args, **kwargs):		return html("pre", True, *args, **kwargs)
def h_br(*args, **kwargs):		return html("br", False, *args, **kwargs)
def h_hr(*args, **kwargs):		return html("hr", False, *args, **kwargs)
def h_font(*args, **kwargs):		return html("font", True, *args, **kwargs)
def h_center(*args, **kwargs):		return html("center", True, *args, **kwargs)
def h_ul(*args, **kwargs):		return html("ul", True, *args, **kwargs)
def h_ol(*args, **kwargs):		return html("ol", True, *args, **kwargs)
def h_li(*args, **kwargs):		return html("li", True, *args, **kwargs)

def h_a(*args, **kwargs):		return html("a", True, *args, **kwargs)
def h_form(*args, **kwargs):		return html("form", True, *args, **kwargs)
def h_input(*args, **kwargs):		return html("input", False, *args, **kwargs)
def h_select(*args, **kwargs):		return html("select", True, *args, **kwargs)
def h_option(*args, **kwargs):		return html("option", True, *args, **kwargs)
def h_textarea(*args, **kwargs):	return html("textarea", True, *args, **kwargs)

# Form elements, optionally defaulted with current input

# <HIDDEN> - works with any arbitrary expression
def v_hidden(name, value=None, encode=True):
    if value is None:
        value = cu.param(name)
    if value is None:
        return ""
    if encode:
        value = cu.encode_expr(value)
    return h_input(_type="hidden", name=name, value=value)

# <INPUT type="text"> - defaulted text input
def v_input_text(name, value=None, size=20):
    if value is None:
        value = cu.param(name)
    return h_input(_type="text", name=name, value=value, size=size)

# <TEXTAREA> input element
def v_textarea(name, value=None, rows=3, cols=60):
    if value is None:
        value = cu.param(name)
    return h_textarea(value, name=name, rows=rows, cols=cols)

# <SELECT> list, with array of options.  Each option is either
# a value which is the display value and option value, or a pair
# [ internal_value, display_value ]
def v_select(name, options, value=None, id=None):
    if value is None:
        value = cu.param(name)
    opts = ""
    for opt in options:
        if isinstance(opt, list):
            if value is not None and opt[0] == value:
                opts += h_option(opt[1], value=opt[0], selected=None)
            else:
                opts += h_option(opt[1], value=opt[0])
        else:
            if value is not None and opt == value:
                opts += h_option(opt, selected=None)
            else:
                opts += h_option(opt)
    return h_select(opts, name=name, id=id)

#
# output_html
#
def output_html(html):
    l = len(html)
    p("Content-type: text/html\n")
    p("Content-length: ", l, "\n")
    p("\n")

    # Flush so browser knows response is on the way
    sys.stdout.flush
    
    # Skirt Windows CRLF issues so content agrees with length above
    if os.name == "nt":
        msvcrt.setmode(1, os.O_BINARY)
    p(html)

# style_link
def style_link():
    return h_link(rel="stylesheet", href="style.css", _type="text/css")


# Testing
# print html("table", "<tr><td>foo</td></tr>")
# print h_table("the rows", ["a", ["b", " "]], 2*8, "and more", foo="bar")
