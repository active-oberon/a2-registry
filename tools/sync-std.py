#!/usr/bin/env python3
"""
Bring the std/* and attic/* manifests here into line with minia2, and rebuild the index entries
for them.

There is one source of truth for what a standard package contains, and it is minia2's
packages/ — because that is the only copy anything checks. `task registry` there fails if a
manifest disagrees with the import graph, if a module in the shipped payload is claimed by no
package, if the runtime is not closed, or if two packages import each other without saying so.
Nothing here checks anything, so nothing here may be edited by hand: this repository publishes.

Community packages are ours to keep and are never touched.

    python3 tools/sync-std.py            # copy and rewrite index.json
    python3 tools/sync-std.py --check    # say what differs, change nothing, exit 1 if anything does

MINIA2 says where the tree is; the default is ../minia2, matching how ob-check finds this
repository from there.
"""
import json, os, shutil, sys, glob

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREE = os.environ.get("MINIA2", os.path.join(os.path.dirname(HERE), "minia2"))
CHECK = "--check" in sys.argv

def die(msg):
    print(msg, file=sys.stderr); sys.exit(2)

src = os.path.join(TREE, "packages")
os.path.isdir(src) or die(f"no tree at {TREE} (set MINIA2)")

# What travels: every manifest of minia2's, under the same relative path. Community packages here
# have no counterpart there and are left exactly as they are.
# std/, attic/ and apps/ travel; lib/ does not. A lib/* package is library that is not standard,
# and its sources are still in minia2 source/ -- it becomes community/<name> here only when they
# move, and then it is a package of this repository, not a copy of that one.
CARRIED = ("std", "attic", "apps")
manifests = sorted(m for c in CARRIED
                   for m in glob.glob(os.path.join(src, c, "*", "a2pkg.json")))
manifests or die(f"no manifests under {src}")

changes, index_entries = [], {}
for m in manifests:
    rel = os.path.relpath(m, src)                      # std/runtime/a2pkg.json
    dst = os.path.join(HERE, "packages", rel)
    body = open(m, encoding="utf-8").read()
    was = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
    if was != body:
        changes.append(("new" if was is None else "changed", rel))
        if not CHECK:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "w", encoding="utf-8").write(body)
    d = json.loads(body)
    # The index says what the front page says: how big, how deep, what it needs, one sentence, and
    # whether it travels in the SDK. `graphical` and `cycle` are the manifest's business, not the
    # catalogue's -- a reader who wants them opens the package.
    entry = {
        "status": "bundled" if d.get("headless") else "in-tree",
        "modules": len(d.get("provides", [])),
        "path": "packages/" + os.path.dirname(rel),
        "tier": d.get("tier"),
        "install": "bundled with the SDK" if d.get("headless")
                   else "in the tree, not in the SDK payload",
        "summary": d.get("description", ""),
    }
    if d.get("requires"):
        entry["requires"] = sorted(d["requires"])
    index_entries[d["name"]] = entry

# Whatever this repository had for std/* or attic/* and minia2 no longer has is gone: the tree
# decides membership, so a stale entry is a stale entry.
idx_path = os.path.join(HERE, "index.json")
idx = json.load(open(idx_path, encoding="utf-8"))
pkgs = idx["packages"]
carried = tuple(c + "/" for c in CARRIED)
ours = {k for k in pkgs if k.startswith(carried)}
new = {k: v for k, v in pkgs.items() if not k.startswith(carried)}
for name, entry in index_entries.items():
    old = pkgs.get(name, {})
    for keep in ("doc_pages",):          # written by the documentation step, not by us
        if keep in old:
            entry[keep] = old[keep]
    new[name] = entry
for gone in sorted(ours - set(index_entries)):
    changes.append(("dropped from the index", gone))
for name in sorted(index_entries):
    if pkgs.get(name) != new[name]:
        changes.append(("index", name))

if not CHECK:
    idx["packages"] = dict(sorted(new.items()))
    open(idx_path, "w", encoding="utf-8").write(json.dumps(idx, indent=2, ensure_ascii=False) + "\n")

if not changes:
    print(f"std/* and attic/* already say what {os.path.relpath(TREE, os.path.dirname(HERE))} says")
    sys.exit(0)
verb = "differs" if CHECK else "synced"
print(f"{verb}: {len(changes)} item(s)")
for kind, what in changes:
    print(f"  {kind:22} {what}")
if CHECK:
    print("\nrun `python3 tools/sync-std.py` and rebuild the site", file=sys.stderr)
    sys.exit(1)
print("\nnow: python3 tools/build_site.py")
