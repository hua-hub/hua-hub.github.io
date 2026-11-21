# -*- coding: utf-8 -*-
from __future__ import print_function
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")

# 忽略的文件夹名称
IGNORE_DIRS = {".git", ".vscode", ".idea", "__pycache__", "node_modules", "assets", "images", "css", "js"}

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

def html_escape(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

def scan_html_groups():
    groups = []  # 格式: [(分组显示名, [(显示标题, 相对路径), ...]), ...]
    
    # 1. 扫描根目录下的 HTML
    root_files = []
    for n in os.listdir(ROOT):
        name = to_text(n)
        full_path = os.path.join(ROOT, name)
        if os.path.isfile(full_path) and name.lower().endswith(".html") and name.lower() != "index.html":
            title = os.path.splitext(name)[0]
            root_files.append((title, name))
            
    if root_files:
        root_files.sort(key=lambda x: natural_key(x[0]))
        groups.append(("常用 / 根目录", root_files))

    # 2. 扫描子文件夹（支持嵌套子文件夹，按路径归类）
    sub_groups = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # 过滤隐藏目录和忽略目录（修改 dirnames 原地生效，阻止 os.walk 深入）
        dirnames[:] = sorted(
            [d for d in dirnames if not to_text(d).startswith(".") and to_text(d) not in IGNORE_DIRS],
            key=lambda d: natural_key(to_text(d))
        )
        
        if dirpath == ROOT:
            continue
            
        rel_dir = to_text(os.path.relpath(dirpath, ROOT)).replace("\\", "/")
        html_list = []
        for f in filenames:
            fname = to_text(f)
            if fname.lower().endswith(".html"):
                title = os.path.splitext(fname)[0]
                href = rel_dir + "/" + fname
                html_list.append((title, href))
                
        if html_list:
            html_list.sort(key=lambda x: natural_key(x[0]))
            sub_groups[rel_dir] = html_list

    # 按文件夹名称自然排序后加入总列表
    for folder_name in sorted(sub_groups.keys(), key=natural_key):
        # 如果是多级目录如 "音乐/钢琴"，显示为 "音乐 / 钢琴" 更美观
        display_name = folder_name.replace("/", " / ")
        groups.append((display_name, sub_groups[folder_name]))

    return groups

def render_html(groups):
    blocks = []
    for group_title, items in groups:
        li_lines = []
        for title, href in items:
            safe_href = to_bytes(html_escape(href))
            safe_title = to_bytes(html_escape(title))
            li_lines.append(b'        <li><a href="' + safe_href + b'" title="' + safe_title + b'">' + safe_title + b'</a></li>')
            
        block = (
            b'    <section class="group">\n'
            b'      <h2 class="group-title">' + to_bytes(html_escape(group_title)) + b'</h2>\n'
            b'      <ul>\n' +
            b'\n'.join(li_lines) + b'\n'
            b'      </ul>\n'
            b'    </section>'
        )
        blocks.append(block)
    return b"\n".join(blocks)

def main():
    groups = scan_html_groups()
    total_files = sum(len(items) for _, items in groups)
    rendered_html = render_html(groups)

    with open(INDEX, "rb") as f:
        data = f.read()

    new_data, count = re.subn(
        br"(<!-- AUTO:START -->).*?(<!-- AUTO:END -->)",
        lambda m: m.group(1) + b"\n" + rendered_html + b"\n    " + m.group(2),
        data, flags=re.S,
    )
    if count == 0:
        sys.exit("AUTO markers not found in index.html, nothing changed")

    with open(INDEX, "wb") as f:
        f.write(new_data)

    msg = (b"Updated " + to_bytes(str(total_files)) + b" links across " +
           to_bytes(str(len(groups))) + b" groups.\n")
    stream = getattr(sys.stdout, "buffer", sys.stdout)
    stream.write(msg)

if __name__ == "__main__":
    main()