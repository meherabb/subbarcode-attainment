"""Prepare an executed copy of the experiment notebook for double-blind sharing.

Removes notebook and cell metadata (platform provenance, authorship tags, data-source names, execution timestamps) and redacts e-mail
addresses and home-directory paths in every output. Extra strings (names, affiliations, user names) can be redacted with --forbid.

Usage: python3 scrub_notebook.py EXECUTED.ipynb CLEAN.ipynb [--forbid "string one,string two"] [--drop-outputs]
"""
import json, re, sys

PATTERNS = [re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
            re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\\\?Users\\\\?)[^/\\\r\n\"',;:)]+"),
            re.compile(r"/content/drive/[^\s\"',;]*")]


def main(argv):
    src, dst = argv[1], argv[2]; extra = []; drop = "--drop-outputs" in argv
    if "--forbid" in argv:
        extra = [s.strip() for s in argv[argv.index("--forbid") + 1].split(",") if s.strip()]
    pats = PATTERNS + [re.compile(re.escape(s), re.I) for s in extra]
    hits = 0

    def clean(x):
        nonlocal hits
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, str):
            for p in pats:
                x, n = p.subn("<redacted>", x); hits += n
        return x

    with open(src, encoding="utf-8") as fh:
        nb = json.load(fh)
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                      "language_info": {"name": "python"}}
    for cell in nb["cells"]:
        cell["metadata"] = {}
        cell["source"] = clean(cell.get("source", ""))
        if cell["cell_type"] != "code":
            continue
        if drop:
            cell["outputs"] = []; cell["execution_count"] = None; continue
        for out in cell.get("outputs", []):
            if "metadata" in out:
                out["metadata"] = {}
            for key in ("text", "traceback", "evalue"):
                if key in out:
                    out[key] = clean(out[key])
            for mime in ("text/plain", "text/html", "text/markdown", "text/latex", "application/json"):
                if mime in out.get("data", {}):
                    out["data"][mime] = clean(out["data"][mime])
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)
    print(f"wrote {dst}: metadata removed, {hits} identifying strings redacted")


if __name__ == "__main__":
    main(sys.argv)
