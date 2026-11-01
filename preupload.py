# -*- coding: utf-8 -*-
from __future__ import print_function
import os, re, sys

# Scan this folder for *.html (except index.html) and rewrite the list
# between <!-- AUTO:START --> and <!-- AUTO:END --> in index.html.
#
# Everything is processed as BYTES on purpose: index.html contains
# UTF-8 Chinese, and mixing bytes/unicode in re.subn crashes Python 2.
# Byte mode never decodes the page, so Chinese passes through untouched.
# Works with Python 2.7 and Python 3:  python preupload.py

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")

def to_bytes(s):
    if isinstance(s, bytes):
        return s
    return s.encode("utf-8")

def to_text(b):
    if isinstance(b, bytes):
        return b.decode("utf-8", "replace")
    return b

def natural_key(name):
    parts = re.split(r"(\d+)", name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

def main():
    names = [to_text(n) for n in os.listdir(ROOT)]
    files = sorted(
        (n for n in names
         if n.lower().endswith(".html") and n.lower() != "index.html"
         and os.path.isfile(os.path.join(ROOT, n))),
        key=natural_key,
    )
    items = b"\n".join(
        b'    <li><a href="' + to_bytes(n) + b'">' +
        to_bytes(os.path.splitext(n)[0]) + b"</a></li>"
        for n in files
    )
    with open(INDEX, "rb") as f:
        data = f.read()
    new_data, count = re.subn(
        br"(<!-- AUTO:START -->).*?(<!-- AUTO:END -->)",
        lambda m: m.group(1) + b"\n" + items + b"\n    " + m.group(2),
        data, flags=re.S,
    )
    if count == 0:
        sys.exit("AUTO markers not found in index.html, nothing changed")
    with open(INDEX, "wb") as f:
        f.write(new_data)
    # Print as raw bytes: a filename may contain Chinese, and Python 2
    # print() of unicode to an ascii pipe (e.g. VS Code runner) crashes.
    msg = (b"Updated " + to_bytes(str(len(files))) + b" links: " +
           b", ".join(to_bytes(n) for n in files) + b"\n")
    stream = getattr(sys.stdout, "buffer", sys.stdout)
    stream.write(msg)

if __name__ == "__main__":
    main()
