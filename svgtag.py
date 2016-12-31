# svgtag.py -- Generate tags for SVG

import pprint
import sys


def _strip_fix(att):
    if att.startswith("_"):
        att = att[1:]
    return att.replace("_", "-")


def _esc_attr(v):
    s = "" if v is None else str(v)
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def _esc_text(v):
    s = "" if v is None else str(v)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Wrap args inside <TAG kw1="val1" ...>...</TAG> or self-close as <TAG ... />.
# `closer=True`  -> always emit open/close pair (args become content)
# `closer=False` -> self-close iff no positional args, else open/close with args as content
# `escape_children=True` -> XML-escape positional args as text (for text-bearing elements).
# Default False so container tags (g/svg/style) can compose pre-rendered SVG fragments.
def svgtag(tag, closer, *args, escape_children=False, **kwargs):
    attrs = []
    for k, v in kwargs.items():
        name = _strip_fix(k)
        if v is None:
            attrs.append(" " + name)
        else:
            attrs.append(' %s="%s"' % (name, _esc_attr(v)))
    head = "<" + tag + "".join(attrs)

    has_content = bool(args)
    if closer or has_content:
        body_parts = []
        for a in flatten(args):
            if a is None:
                continue
            body_parts.append(_esc_text(a) if escape_children else str(a))
        return head + ">" + "".join(body_parts) + "</" + tag + ">\n"
    return head + " />\n"


def st_style(*args, **kwargs):  return svgtag("style", True,  *args, **kwargs)
def st_svg(*args, **kwargs):    return svgtag("svg",   True,  *args, **kwargs)
def st_text(*args, **kwargs):   return svgtag("text",  True,  *args, escape_children=True, **kwargs)
def st_line(*args, **kwargs):   return svgtag("line",  False, *args, **kwargs)
def st_rect(*args, **kwargs):   return svgtag("rect",  False, *args, **kwargs)
def st_polygon(*args, **kwargs): return svgtag("polygon", False, *args, **kwargs)
def st_g(*args, **kwargs):      return svgtag("g",     True,  *args, **kwargs)
def st_title(text):             return "<title>" + _esc_text(text) + "</title>"


# Build a viewBox / coords string from positional args
def st_coords(*args):
    return " ".join(str(c) for c in args)


# Concatenate args as strings
def scat(*args):
    return "".join(xstr(x) for x in flatten(args))


# Flatten a nested list/tuple structure (preserves outer type)
def flatten(seq, ltypes=(list, tuple)):
    ltype = type(seq)
    out = list(seq)
    i = 0
    while i < len(out):
        while isinstance(out[i], ltypes):
            if not out[i]:
                out.pop(i)
                i -= 1
                break
            out[i:i + 1] = out[i]
        i += 1
    return ltype(out)


# xstr() - Like str() only "None" is empty
def xstr(s):
    return "" if s is None else str(s)


# Pretty print arg
def pp(x):
    print(pprint.PrettyPrinter().pformat(x))


# Emit HTML response (CGI-style); used in legacy contexts
def output_html(html):
    sys.stdout.write("Content-type: text/html\n")
    sys.stdout.write("Content-length: %d\n\n" % len(html))
    sys.stdout.flush()
    sys.stdout.write(html)
