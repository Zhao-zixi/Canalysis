import argparse
import json
import asyncio
import hashlib
from pathlib import Path

from scripts.scan_c_functions import extract_functions_from_text
from llm import analyze_functions as af
from visualization.generate_report import generate_report


def scan_functions(root: Path, target: Path):
    items = []
    for p in target.rglob('*.c'):
        try:
            t = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for name, line, func_text in extract_functions_from_text(t):
            items.append({
                "file": str(p.relative_to(root)),
                "function": name,
                "line": line,
                "content": func_text
            })
    return items


def analyze_items(items, mode: str, max_concurrency: int):
    if mode == 'fallback':
        return [af.merge_result(it, af.static_analyze(it)) for it in items]
    elif mode == 'sync':
        client = af.OpenAI(base_url=af.BASE_URL, api_key=af.API_KEY)
        return [af.analyze_sync(client, it) for it in items]
    elif mode == 'async':
        async def run():
            aclient = af.AsyncOpenAI(base_url=af.BASE_URL, api_key=af.API_KEY)
            sem = asyncio.Semaphore(max(1, max_concurrency))
            tasks = [af.analyze_async(aclient, it, sem) for it in items]
            return await asyncio.gather(*tasks)
        return asyncio.run(run())
    else:
        raise ValueError(f"Unknown mode: {mode}")


def make_key(item):
    fp = item["file"].replace("\\", "/")
    return f"{fp}:{item['function']}:{item['line']}"


def compute_hash(content: str) -> str:
    return hashlib.sha1(content.encode('utf-8')).hexdigest()[:16]


def load_store(root: Path):
    store_path = root / 'llm' / 'function_analysis_store.json'
    if store_path.exists():
        try:
            return json.loads(store_path.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_store(root: Path, store: dict):
    store_path = root / 'llm' / 'function_analysis_store.json'
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=str, default=str(Path('examples') / 'linux_serial_demo'))
    parser.add_argument('--mode', type=str, choices=['fallback', 'sync', 'async'], default='fallback')
    parser.add_argument('--max-concurrency', type=int, default=5)
    parser.add_argument('--output', type=str, default=str(Path('visualization') / 'report.html'))
    parser.add_argument('--keep-json', action='store_true')
    parser.add_argument('--clean', action='store_true')
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    target = (root / args.target).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Target directory not found: {target}")

    if args.clean:
        # Remove previous outputs if present
        for p in [root / 'llm' / 'function_analysis.json',
                  root / 'llm' / 'function_analysis_serial.json',
                  root / 'llm' / 'function_analysis_async.json',
                  root / 'visualization' / 'report.html']:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

    items = scan_functions(root, target)

    store = load_store(root)
    results = []
    to_analyze = []
    pending_hashes = {}
    for it in items:
        key = make_key(it)
        h = compute_hash(it["content"])
        cached = store.get(key)
        if cached and cached.get("content_hash") == h:
            results.append(cached)
        else:
            to_analyze.append(it)
            pending_hashes[key] = h

    new_results = analyze_items(to_analyze, args.mode, args.max_concurrency) if to_analyze else []

    store_updated = False
    for nr in new_results:
        # Build key from analysis result for consistency
        fp = nr["file_path"].replace("\\", "/")
        key = f"{fp}:{nr['function_name']}:{nr['line_number']}"
        h = pending_hashes.get(key)
        if h:
            nr["content_hash"] = h
        results.append(nr)
        if args.mode in ("sync", "async"):
            note = nr.get("notes", "")
            if "fallback_static_analysis" not in note:
                store[key] = nr
                store_updated = True

    if store_updated:
        save_store(root, store)

    # Write temp JSON for report generation
    tmp_json = root / 'llm' / 'function_analysis.json'
    tmp_json.parent.mkdir(parents=True, exist_ok=True)
    tmp_json.write_text(json.dumps(results, ensure_ascii=False), encoding='utf-8')

    # Generate HTML report
    output_path = (root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report(str(tmp_json), str(output_path))

    if not args.keep_json:
        try:
            tmp_json.unlink()
        except Exception:
            pass


if __name__ == '__main__':
    main()
