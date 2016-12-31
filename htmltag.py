# html.py
#
# Lightweight HTML tag builders. CGI form helpers that depended on external util/cu
# modules have been removed; what remained was unused by the chart code.

import os
import sys

if os.name == "nt":
    import msvcrt


def _strip(att):
    return att[1:] if att.startswith("_") else att


def _xstr(s):
    return "" if s is None else str(s)


def html(tag, autoclose, *args, **kwargs):
    attrs = []
    for k, v in kwargs.items():
        name = _strip(k)
        if v is None:
            attrs.append(" " + name)
        else:
            attrs.append(' %s="%s"' % (name, _xstr(v)))
    head = "<" + tag + "".join(attrs) + ">"
    body = "".join(_xstr(a) for a in args)
    tail = ("</" + tag + ">") if autoclose else ""
    return head + body + tail


def h_html(*args, **kwargs):     return html("html",     True,  *args, **kwargs)
def h_head(*args, **kwargs):     return html("head",     True,  *args, **kwargs)
def h_title(*args, **kwargs):    return html("title",    True,  *args, **kwargs)
def h_link(*args, **kwargs):     return html("link",     False, *args, **kwargs)
def h_body(*args, **kwargs):     return html("body",     True,  *args, **kwargs)

def h_table(*args, **kwargs):    return html("table",    True,  *args, **kwargs)
def h_tr(*args, **kwargs):       return html("tr",       True,  *args, **kwargs)
def h_td(*args, **kwargs):       return html("td",       True,  *args, **kwargs)
def h_th(*args, **kwargs):       return html("th",       True,  *args, **kwargs)

def h_h1(*args, **kwargs):       return html("h1",       True,  *args, **kwargs)
def h_h2(*args, **kwargs):       return html("h2",       True,  *args, **kwargs)
def h_h3(*args, **kwargs):       return html("h3",       True,  *args, **kwargs)

def h_p(*args, **kwargs):        return html("p",        True,  *args, **kwargs)
def h_b(*args, **kwargs):        return html("b",        True,  *args, **kwargs)
def h_i(*args, **kwargs):        return html("i",        True,  *args, **kwargs)
def h_pre(*args, **kwargs):      return html("pre",      True,  *args, **kwargs)
def h_br(*args, **kwargs):       return html("br",       False, *args, **kwargs)
def h_hr(*args, **kwargs):       return html("hr",       False, *args, **kwargs)
def h_font(*args, **kwargs):     return html("font",     True,  *args, **kwargs)
def h_center(*args, **kwargs):   return html("center",   True,  *args, **kwargs)
def h_ul(*args, **kwargs):       return html("ul",       True,  *args, **kwargs)
def h_ol(*args, **kwargs):       return html("ol",       True,  *args, **kwargs)
def h_li(*args, **kwargs):       return html("li",       True,  *args, **kwargs)

def h_a(*args, **kwargs):        return html("a",        True,  *args, **kwargs)
def h_form(*args, **kwargs):     return html("form",     True,  *args, **kwargs)
def h_input(*args, **kwargs):    return html("input",    False, *args, **kwargs)
def h_select(*args, **kwargs):   return html("select",   True,  *args, **kwargs)
def h_option(*args, **kwargs):   return html("option",   True,  *args, **kwargs)
def h_textarea(*args, **kwargs): return html("textarea", True,  *args, **kwargs)


def output_html(body):
    sys.stdout.write("Content-type: text/html\n")
    sys.stdout.write("Content-length: %d\n\n" % len(body))
    sys.stdout.flush()
    if os.name == "nt":
        msvcrt.setmode(1, os.O_BINARY)
    sys.stdout.write(body)


def style_link():
    return h_link(rel="stylesheet", href="style.css", _type="text/css")
