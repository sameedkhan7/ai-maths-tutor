import os
import sys
import glob
import re
import html.parser
import py_compile
import subprocess

PROJECT_DIR = r"C:\Users\SK\OneDrive\Desktop\maths project"
os.chdir(PROJECT_DIR)

print("=" * 60)
print("1. CHECKING PYTHON FILES (SYNTAX & COMPILATION)")
print("=" * 60)

python_files = [
    "backend/main.py",
    "backend/database.py",
    "backend/email_service.py",
    "backend/ncert_mcp_server.py",
    "backend/ai/groq_client.py",
    "backend/ai/math_engine.py",
    "backend/rag/sample_data.py",
]

py_errors = 0
for py_f in python_files:
    if os.path.exists(py_f):
        try:
            py_compile.compile(py_f, doraise=True)
            with open(py_f, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
            print(f"  [OK] {py_f} ({lines} lines) compiled cleanly.")
        except Exception as e:
            print(f"  [FAIL] {py_f}: {e}")
            py_errors += 1
    else:
        print(f"  [MISSING] {py_f}")
        py_errors += 1

print(f"Python check completed with {py_errors} errors.\n")

print("=" * 60)
print("2. CHECKING JAVASCRIPT FILES (SYNTAX VIA NODE)")
print("=" * 60)

js_files = ["script.js"]
js_errors = 0
for js_f in js_files:
    if os.path.exists(js_f):
        res = subprocess.run(["node", "-c", js_f], capture_output=True, text=True)
        if res.returncode == 0:
            with open(js_f, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
            print(f"  [OK] {js_f} ({lines} lines) syntax is valid.")
        else:
            print(f"  [FAIL] {js_f}:\n{res.stderr}")
            js_errors += 1
    else:
        print(f"  [MISSING] {js_f}")
        js_errors += 1

print(f"JS check completed with {js_errors} errors.\n")

print("=" * 60)
print("3. CHECKING CSS FILES (BRACE BALANCE)")
print("=" * 60)

css_files = ["style.css"]
css_errors = 0
for css_f in css_files:
    if os.path.exists(css_f):
        with open(css_f, "r", encoding="utf-8", errors="ignore") as f:
            css = f.read()
        
        in_comment = False
        in_string = False
        str_char = ""
        brace_depth = 0
        errs = []
        lines = css.split("\n")
        for line_idx, line in enumerate(lines, 1):
            i = 0
            while i < len(line):
                ch = line[i]
                if not in_comment and not in_string:
                    if ch == "/" and i + 1 < len(line) and line[i+1] == "*":
                        in_comment = True
                        i += 1
                    elif ch in ('"', "'"):
                        in_string = True
                        str_char = ch
                    elif ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                        if brace_depth < 0:
                            errs.append(f"Line {line_idx}: Unexpected '}}'")
                            brace_depth = 0
                elif in_comment:
                    if ch == "*" and i + 1 < len(line) and line[i+1] == "/":
                        in_comment = False
                        i += 1
                elif in_string:
                    if ch == "\\":
                        i += 1
                    elif ch == str_char:
                        in_string = False
                i += 1
        if brace_depth != 0:
            errs.append(f"Unclosed braces remaining: {brace_depth}")
        if errs:
            print(f"  [FAIL] {css_f} errors:\n    " + "\n    ".join(errs[:5]))
            css_errors += len(errs)
        else:
            print(f"  [OK] {css_f} ({len(lines)} lines) braces are 100% balanced.")
    else:
        print(f"  [MISSING] {css_f}")
        css_errors += 1

print(f"CSS check completed with {css_errors} errors.\n")

print("=" * 60)
print("4. CHECKING HTML FILES & INTERNAL ASSET REFERENCES")
print("=" * 60)

html_files = glob.glob("*.html")
html_errors = 0

class LinkChecker(html.parser.HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.assets = []
        self.stack = []
        self.self_closing = {'br', 'hr', 'img', 'input', 'link', 'meta', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'}
        self.tag_errors = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag.lower() not in self.self_closing:
            self.stack.append((tag.lower(), self.getpos()))
        if tag.lower() == 'script' and 'src' in attr_dict:
            self.assets.append(('script', attr_dict['src'], self.getpos()))
        elif tag.lower() == 'link' and attr_dict.get('rel') == 'stylesheet' and 'href' in attr_dict:
            self.assets.append(('stylesheet', attr_dict['href'], self.getpos()))
        elif tag.lower() == 'img' and 'src' in attr_dict:
            self.assets.append(('image', attr_dict['src'], self.getpos()))

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in self.self_closing:
            return
        if not self.stack:
            self.tag_errors.append(f"Unexpected closing tag </{tag_l}> at line {self.getpos()}")
            return
        last_tag, pos = self.stack.pop()
        if last_tag != tag_l:
            self.tag_errors.append(f"Mismatched </{tag_l}> at {self.getpos()} (opened <{last_tag}> at {pos})")

for hf in html_files:
    with open(hf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    lc = LinkChecker(hf)
    lc.feed(content)
    
    missing_assets = []
    for kind, ref, pos in lc.assets:
        # Ignore external cdn urls
        if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("//"):
            continue
        # Strip query params like ?v=164
        clean_ref = ref.split("?")[0].split("#")[0]
        if clean_ref and not os.path.exists(clean_ref):
            missing_assets.append(f"{kind} '{ref}' at {pos}")
            
    if lc.tag_errors or missing_assets:
        print(f"  [WARN] {hf}:")
        for te in lc.tag_errors[:3]:
            print(f"    - Tag issue: {te}")
        for ma in missing_assets[:5]:
            print(f"    - Missing local asset: {ma}")
            html_errors += 1
    else:
        print(f"  [OK] {hf} ({len(content.splitlines())} lines) tags and local assets verified.")

print(f"HTML check completed with {html_errors} errors.\n")
