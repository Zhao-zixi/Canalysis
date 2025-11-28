import os
import json
import asyncio
import argparse
import re
from pathlib import Path
from openai import OpenAI, AsyncOpenAI
try:
    import platform
    if platform.system().lower().startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass

BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
API_KEY = os.getenv("API_KEY")

SCHEMA_KEYS = [
    "file_path",
    "function_name",
    "line_number",
    "content",
    "origin",
    "summary",
    "calls",
    "confidence",
    "notes",
]

def read_functions(root: Path):
    p = root / "scripts" / "c_functions.json"
    return json.loads(p.read_text(encoding="utf-8"))

def classify_origin(file_path: str):
    fp = file_path.replace("\\", "/")
    if "/kernel/" in fp:
        return "kernel"
    if "/user/" in fp:
        return "user"
    return "unknown"

def build_prompt(item):
    origin_hint = classify_origin(item["file"])
    content = item["content"]
    file_path = item["file"].replace("\\", "/")
    name = item["function"]
    line = item["line"]
    schema = {
        "file_path": file_path,
        "function_name": name,
        "line_number": line,
        "content": content,
        "origin": "kernel|user",
        "summary": "",
        "calls": [{"callee": "", "condition": ""}],
        "confidence": 0.0,
        "notes": ""
    }
    sys = (
        "You are a strict JSON generator. Return only a single JSON object with keys: "
        + ",".join(SCHEMA_KEYS)
        + ". Do not include any markdown or explanations outside JSON."
    )
    usr = (
        "Analyze the following C function and produce strictly valid JSON. Requirements: "
        "1) Only list direct, reachable calls within the function body; exclude self-calls. "
        "2) For each call, provide its entry condition as the expression INSIDE the if parentheses (no 'if' and no outer parentheses). Use 'unconditional' if always executed. "
        "3) When an early-return guard like 'if (len == 0) return 0;' precedes a call, the call's condition is the logical negation expression (e.g., 'len != 0'). "
        "4) Prefer concise expressions; avoid redundant text. "
        f"Origin hint: {origin_hint}. File: {file_path}. Name: {name}. Line: {line}. "
        "Function content begins:\n" + content + "\nFunction content ends."
    )
    return sys, usr, schema

def merge_result(item, model_json):
    out = {
        "file_path": item["file"].replace("\\", "/"),
        "function_name": item["function"],
        "line_number": item["line"],
        "content": item["content"],
        "origin": model_json.get("origin", classify_origin(item["file"])),
        "summary": model_json.get("summary", ""),
        "calls": model_json.get("calls", []),
        "confidence": model_json.get("confidence", 0.0),
        "notes": model_json.get("notes", ""),
    }
    return out

def extract_calls_with_conditions(content: str, function_name: str = None):
    lines = content.splitlines()
    call_re = re.compile(r"([A-Za-z_]\w*)\s*\(")
    keywords = {"if", "for", "while", "switch", "return", "sizeof"}

    def invert_condition(expr: str) -> str:
        s = expr.strip()
        pairs = [("==", "!="), ("!=", "=="), ("<=", ">") , (">=", "<"), ("<", ">="), (">", "<=")]
        for a, b in pairs:
            if a in s:
                return s.replace(a, b)
        if s.startswith("!"):
            return s[1:].strip()
        return "!(" + s + ")"

    def extract_if_condition(start_line: int):
        for j in range(start_line, -1, -1):
            s = lines[j]
            m = re.search(r"\bif\s*\(", s)
            if not m:
                continue
            found_close = False
            depth = 1
            buf = []
            rest = s[m.end():]
            for ch in rest:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        found_close = True
                        break
                buf.append(ch)
            end_line = j
            if not found_close:
                for k in range(j + 1, min(len(lines), start_line + 1)):
                    for ch in lines[k]:
                        if ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                            if depth == 0:
                                end_line = k
                                found_close = True
                                break
                        buf.append(ch)
                    if found_close:
                        break
            if not found_close:
                continue
            cond_inner = ''.join(buf).strip()
            if not found_close:
                continue
            brace_depth = 0
            inside_if = False
            for t in range(j, start_line + 1):
                brace_depth += lines[t].count("{")
                brace_depth -= lines[t].count("}")
                if t == start_line:
                    inside_if = brace_depth > 0
            block_has_brace = any("{" in lines[t] for t in range(j, min(len(lines), end_line + 1)))
            early_return = False
            if not block_has_brace:
                tail = lines[j][m.end():]
                if re.search(r"\b(return|goto|break|continue)\b", tail):
                    early_return = True
                else:
                    if j + 1 <= start_line:
                        nxt = lines[j + 1]
                        if re.search(r"\b(return|goto|break|continue)\b", nxt):
                            early_return = True
            return cond_inner, inside_if, early_return
        return None, False, False

    calls = []
    for idx, line in enumerate(lines):
        for m in call_re.finditer(line):
            callee = m.group(1)
            if callee in keywords:
                continue
            if callee.isupper():
                continue
            if function_name and callee == function_name:
                continue
            cond = "unconditional"
            cond_inner, inside_if, early_return = extract_if_condition(idx)
            if cond_inner is not None:
                if inside_if:
                    cond = cond_inner
                elif early_return:
                    inv = invert_condition(cond_inner)
                    cond = inv
                else:
                    cond = "unconditional"
            calls.append({"callee": callee, "condition": cond})
    unique = []
    seen = set()
    for c in calls:
        if function_name and c["callee"] == function_name:
            continue
        key = (c["callee"], c["condition"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique

def static_analyze(item):
    content = item["content"]
    name = item["function"]
    origin = classify_origin(item["file"])
    calls = extract_calls_with_conditions(content, name)
    has_write = "write(" in content
    has_read = "read(" in content
    has_ctu = "copy_to_user(" in content
    has_cfu = "copy_from_user(" in content
    has_in = "kfifo_in(" in content
    has_out = "kfifo_out(" in content
    has_ioctl = "ioctl(" in content or "unlocked_ioctl" in content or name.startswith("my_ioctl")
    has_init = ("alloc_chrdev_region(" in content) or ("cdev_add(" in content) or ("class_create(" in content) or ("device_create(" in content)
    has_exit = ("unregister_chrdev_region(" in content) or ("device_destroy(" in content) or ("class_destroy(" in content) or ("cdev_del(" in content)
    has_open = "open(" in content
    has_close = "close(" in content
    desc = []
    if has_read or has_ctu or has_out:
        desc.append("reads data")
    if has_write or has_cfu or has_in:
        desc.append("writes data")
    if has_ioctl:
        desc.append("handles ioctl")
    if has_init:
        desc.append("initializes device")
    if has_exit:
        desc.append("tears down device")
    if has_open and origin == "user":
        desc.append("opens file descriptor")
    if has_close and origin == "user":
        desc.append("closes file descriptor")
    if not desc:
        desc.append("helper function")
    summary = ", ".join(desc)
    base_conf = 0.4
    enrich = sum([has_read, has_write, has_ioctl, has_init, has_exit])
    conf = min(0.9, base_conf + 0.1 * enrich + 0.1 * (1 if calls else 0))
    return {"origin": origin, "summary": summary, "calls": calls, "confidence": conf, "notes": "fallback_static_analysis"}

def analyze_sync(client: OpenAI, item):
    sys, usr, schema = build_prompt(item)
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        txt = resp.choices[0].message.content.strip()
        model_json = json.loads(txt)
    except Exception as e:
        sa = static_analyze(item)
        sa["notes"] = f"llm_call_failed: {type(e).__name__}: {str(e)}; " + sa["notes"]
        model_json = sa
    return merge_result(item, model_json)

async def analyze_async(client: AsyncOpenAI, item, sem: asyncio.Semaphore):
    sys, usr, schema = build_prompt(item)
    async with sem:
        try:
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": usr}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            txt = resp.choices[0].message.content.strip()
            model_json = json.loads(txt)
        except Exception as e:
            sa = static_analyze(item)
            sa["notes"] = f"llm_call_failed: {type(e).__name__}: {str(e)}; " + sa["notes"]
            model_json = sa
        return merge_result(item, model_json)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--async", dest="use_async", action="store_true")
    parser.add_argument("--max-concurrency", type=int, default=5)
    parser.add_argument("--output", type=str, default=str(Path("llm") / "function_analysis.json"))
    parser.add_argument("--force-fallback", dest="force_fallback", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    items = read_functions(root)
    if args.force_fallback:
        results = [merge_result(it, static_analyze(it)) for it in items]
    elif args.use_async:
        async def run():
            aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
            sem = asyncio.Semaphore(max(1, args.max_concurrency))
            tasks = [analyze_async(aclient, it, sem) for it in items]
            return await asyncio.gather(*tasks)
        results = asyncio.run(run())
    else:
        client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
        results = [analyze_sync(client, it) for it in items]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
