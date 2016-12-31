# svgtag.py -- Generate tags for SVG

import pprint

# Wrap args inside <TAG kw1=val1 kw2=val2>...</TAG> or <TAG kw1=val1 kw2=val2 />
def svgtag(tag, closer, *args, **kwargs):
    # Strip off leading "_" which may be used to avoid reserved word clashes
    def strip_fix(att):
        if att[0] == "_":
            att = att[1:]
        # Replace "_" with "-" so we can use in Python syntax
        att = att.replace("_", "-")
        return att
    def kval(k):
        result = " " + strip_fix(k)
        if kwargs[k] is not None:
            result += "=\"" + xstr(kwargs[k]) + "\""
        return result;
    # result = "<" + tag + scat(map(kval, kwargs.keys()))
    result = "<" + tag + scat([kval(k) for k in kwargs.keys()])
    if closer:
        result += ">" + scat(args) + "</" + tag + ">"
    else:
        result += " />"
    return result + "\n"

def st_style(*args, **kwargs):		return svgtag("style", True, *args, **kwargs)
def st_svg(*args, **kwargs):		return svgtag("svg", True, *args, **kwargs)
def st_text(*args, **kwargs):		return svgtag("text", True, *args, **kwargs)
def st_line(*args, **kwargs):		return svgtag("line", False, *args, **kwargs)
def st_rect(*args, **kwargs):		return svgtag("rect", False, *args, **kwargs)

# Get coords string
def st_coords(*args, **kwargs):
    arr = []
    for c in args:
        arr.append(str(c))
    return " ".join(arr)

# Concat args as strings                                                                                                                                        
def scat(*args):
    return "".join(map(xstr, flatten(args)))

# Flatten a nested structure                                                                                                                                    
# From Mike C. Fletcher's "BasicTypes"                                                                                                                          
def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

# xstr() - Like str() only "None" is empty                                                                                                                      
def xstr(s):
    return '' if s is None else str(s)

# Pretty print arg
def pp(x):
    print pprint.PrettyPrinter().pformat(x)

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
    
    p(html)

# Testing
# print html("table", "<tr><td>foo</td></tr>")
# print h_table("the rows", ["a", ["b", " "]], 2*8, "and more", foo="bar")
