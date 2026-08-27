#!/usr/bin/env python3
"""
Regenerate docs/<package>/ from the sources each package actually names.

The site links a package card only when docs/<short>/ has pages, so a package with
no docs is a card that does nothing -- which is what std/system, std/process,
std/terminal, std/time and std/encoding were. This closes the gap the README
described as "regenerated when sources change" without saying with what.

    python3 tools/gen-docs.py                 # every package, std/* included
    python3 tools/gen-docs.py std/time        # just these
    MINIA2=/path/to/minia2  OB=/path/to/ob    # where the tree and the driver are

std/* and attic/* name modules that live in minia2 source/; a community package
vendors its own .Mod files beside the manifest. Platform twins (Unix.X.Mod and
Windows.X.Mod both declare MODULE X) are resolved to the Unix one: the docs are
one page per module, not per file.
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINIA2 = os.environ.get("MINIA2", os.path.join(os.path.dirname(HERE), "minia2"))
OB = os.environ.get("OB", os.path.join(MINIA2, "target", "bundle", "ob"))
want = set(sys.argv[1:])


def module(path):
    b = open(path, "rb").read()
    if len(b) > 4 and b[0] == 0xF0 and b[1] == 0x01:
        b = b[b[2] + b[3] * 256:]
    for line in b.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n"):
        head = line.lstrip(b" \t")
        if head[:7] in (b"MODULE ", b"module "):
            m = re.match(rb"\w+", head[7:].lstrip(b" \t"))
            if m:
                return m.group(0).decode()
    return None


source = {}
for p in sorted(glob.glob(os.path.join(MINIA2, "source", "*.Mod"))):
    n = module(p)
    if n and (n not in source or os.path.basename(p).startswith("Unix.")):
        source[n] = p

manifests = sorted(glob.glob(os.path.join(MINIA2, "packages", "*", "*", "a2pkg.json"))
                   + glob.glob(os.path.join(HERE, "packages", "*", "a2pkg.json")))
written, skipped, alive = [], [], set()
for man in manifests:
    pkg = json.load(open(man))
    name = pkg["name"]
    if want and name not in want:
        continue
    if name.startswith("lib/"):
        continue        # lib/* is minia2's own classification; this catalogue never carries it
    short = name.split("/")[-1]
    vendored = os.path.dirname(man) if name.startswith("community/") else None
    here_by_module = {}
    if vendored:
        # by the MODULE header, not the file name: community/v4l2 ships Unix.V4L2.Mod
        for f in sorted(glob.glob(os.path.join(vendored, "*.Mod"))):
            n = module(f)
            if n:
                here_by_module.setdefault(n, f)
    files = []
    for m in pkg.get("provides", []):
        p = here_by_module.get(m) if vendored else source.get(m)
        if p and os.path.exists(p):
            files.append((m, p))
    alive.add(short)
    if not files:
        skipped.append(f"{name} (no sources found)")
        continue
    with tempfile.TemporaryDirectory() as work:
        for m, p in files:
            shutil.copy(p, os.path.join(work, m + ".Mod"))
        out = os.path.join(work, "out")
        r = subprocess.run([OB, "doc", "-o", out], cwd=work, capture_output=True, text=True)
        pages = glob.glob(os.path.join(out, "*.html")) if os.path.isdir(out) else []
        if len(pages) < 2:      # index.html alone means ob doc produced nothing -- keep what is there
            skipped.append(f"{name} (no pages; left the existing docs alone)")
            continue
        if not pages:
            skipped.append(f"{name} ({(r.stderr or r.stdout).strip().splitlines()[-1:] or ['no pages']}")
            continue
        dst = os.path.join(HERE, "docs", short)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(out, dst)
        written.append(f"{name}: {len(pages)-1} module(s)")

for line in written:
    print("  " + line)
for line in skipped:
    print("  SKIP " + line)
if not want:
    stale = [d for d in sorted(os.listdir(os.path.join(HERE, "docs")))
             if os.path.isdir(os.path.join(HERE, "docs", d)) and d not in alive]
    if stale:
        print("  stale (no package names them any more): " + ", ".join(stale))
print(f"{len(written)} package(s) documented, {len(skipped)} skipped")
