import re
import json
from pathlib import Path

def find_matching_brace(s, start):
    i = start + 1
    level = 1
    in_str = False
    in_char = False
    in_block_comment = False
    in_line_comment = False
    while i < len(s):
        c = s[i]
        if in_block_comment:
            if c == '*' and i + 1 < len(s) and s[i + 1] == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
            i += 1
            continue
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if in_char:
            if c == '\\':
                i += 2
                continue
            if c == '\'':
                in_char = False
            i += 1
            continue
        if c == '/' and i + 1 < len(s):
            d = s[i + 1]
            if d == '*':
                in_block_comment = True
                i += 2
                continue
            if d == '/':
                in_line_comment = True
                i += 2
                continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == '\'':
            in_char = True
            i += 1
            continue
        if c == '{':
            level += 1
        elif c == '}':
            level -= 1
            if level == 0:
                return i
        i += 1
    return len(s) - 1

def extract_functions_from_text(text):
    pattern = re.compile(r"^[ \t]*(?:[A-Za-z_][\w\s\*\(\),]*?[ \t\*])?([A-Za-z_]\w*)\s*\([^;]*\)[ \t\r\n]*\{", re.MULTILINE | re.DOTALL)
    results = []
    for m in pattern.finditer(text):
        name = m.group(1)
        if name in {"if", "for", "while", "switch", "do"}:
            continue
        start_pos = m.start()
        line = text.count('\n', 0, start_pos) + 1
        brace_index = m.end() - 1
        end_pos = find_matching_brace(text, brace_index)
        func_text = text[start_pos:end_pos + 1]
        results.append((name, line, func_text))
    return results

def main():
    root = Path(__file__).resolve().parent.parent
    target = root / "examples" / "linux_serial_demo"
    out_file = root / "scripts" / "c_functions.json"
    items = []
    for p in target.rglob('*.c'):
        t = p.read_text(encoding='utf-8', errors='ignore')
        for name, line, func_text in extract_functions_from_text(t):
            items.append({
                "file": str(p.relative_to(root)),
                "function": name,
                "line": line,
                "content": func_text
            })
    out_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == "__main__":
    main()
