#!/usr/bin/env python3
"""
Every module of a community package's upstream directory is either shipped or excluded on purpose.

A community package here vendors its own sources, so `provides` must name exactly the .Mod files
beside the manifest -- that half is checked everywhere. The half that can rot is the other one:
the upstream directory in a2oberon/ocp, entered once and never looked at again, where a module
can be lost without anybody noticing. A package therefore says where it came from (`upstream`)
and why each module of that directory did not travel (`excludes`), and this fails when the two
lists together do not account for the directory. Same discipline as `graphical` in std/*: an
annotation that cannot go stale in silence.

    python3 tools/check-ocp.py            # report; exit 1 if anything is unaccounted for
    A2OBERON=/path/to/a2oberon            # where the upstream tree is (default: ../a2oberon)

A package with no `upstream` is checked for `provides` only -- it has no upstream to compare with.
A missing upstream tree is a skip, not a failure: it is a second clone, not a dependency.
"""
import json, glob, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("A2OBERON", os.path.join(os.path.dirname(HERE), "a2oberon"))

def module(path):
    """The module a file declares -- read from the file, the way ob reads it (sdk/Ob.Mod
    ModuleName), because the file name is not the module name often enough to matter:
    ocp/Matrix/LinearFIRConvolve.Mod declares MODULE TestLFC, and MatrixKrylovCGS.Mod declares
    KrylovCGS. An A2 binary Text starts with F0X 01X and the offset of the text after the font
    table; the header is the first line that opens with MODULE, in either case."""
    b = open(path, "rb").read()
    if len(b) > 4 and b[0] == 0xF0 and b[1] == 0x01:
        b = b[b[2] + b[3] * 256:]
    for line in b.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n"):
        head = line.lstrip(b" \t")
        if head[:7] in (b"MODULE ", b"module "):
            name = head[7:].lstrip(b" \t")
            m = re.match(rb"\w+", name)
            if m: return m.group(0).decode()
    return None

problems, checked, skipped = [], 0, []
for manifest in sorted(glob.glob(os.path.join(HERE, "packages", "*", "a2pkg.json"))):
    pkg = json.load(open(manifest))
    name = pkg.get("name", os.path.basename(os.path.dirname(manifest)))
    here = os.path.dirname(manifest)
    provides = set(pkg.get("provides", []))
    vendored = {module(f) for f in glob.glob(os.path.join(here, "*.[Mm]od"))}
    if provides != vendored:
        for m in sorted(provides - vendored): problems.append(f"{name}: {m} is in provides, no source beside the manifest")
        for m in sorted(vendored - provides): problems.append(f"{name}: {m}.Mod ships, no package names it")

    upstream = pkg.get("upstream")
    if not upstream:
        skipped.append(f"{name} (no upstream)"); continue
    d = os.path.join(TREE, upstream)
    if not os.path.isdir(d):
        skipped.append(f"{name} (no {upstream} under {TREE})"); continue
    excludes = pkg.get("excludes", {})
    theirs = {module(f) for f in glob.glob(os.path.join(d, "**", "*.[Mm]od"), recursive=True)}
    for m in sorted(theirs - provides - set(excludes)):
        problems.append(f"{name}: {m} is in {upstream}, named neither in provides nor in excludes")
    for m in sorted(set(excludes) - theirs):
        problems.append(f"{name}: excludes names {m}, which is not in {upstream} any more")
    for m, why in sorted(excludes.items()):
        if not str(why).strip(): problems.append(f"{name}: {m} is excluded without a reason")
    checked += 1

for line in problems: print(line)
print(f"{checked} package(s) checked against the upstream tree, {len(problems)} problem(s)"
      + (f"; not compared: {', '.join(skipped)}" if skipped else ""))
sys.exit(1 if problems else 0)
