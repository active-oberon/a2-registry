# a2-registry — A2 / Active Oberon package registry

A central, CPAN/Maven-style catalogue of community libraries for A2 / Active Oberon,
installable with the minia2 SDK's `ob get`, with a generated documentation site.

- **`index.json`** — the machine-readable catalogue (name → status, module count, `requires`, summary).
- **`packages/<name>/`** — a package: `.Mod` sources + an `a2pkg.json` manifest (see minia2 `packages/README.md` for the manifest/tier model).
- **`docs/<name>/`** — raw per-module HTML from `ob doc` (regenerated when sources change).
- **`site/`** — the styled static site served by GitHub Pages (generated; git-ignored).
- **`tools/build_site.py`** — the site generator.

## Install a package

```sh
export A2_REGISTRY=https://github.com/<org>/a2-registry.git   # or a local checkout path
ob get community/matrix          # resolves via index.json, vendors into .a2pkg/, pins a2pkg.lock
ob build MyApp.Mod -o myapp      # a consumer that IMPORTs MatrixBase, etc.
```

`ob get` also takes a git repo directly (`ob get gitlab.com/user/repo`); a bare
`community/<name>` is resolved against `$A2_REGISTRY`.

## Status legend

- **validated** — manifest written, sources compile headless against the SDK stdlib, docs generated.
- **pending-manifest** — ASCII sources present; manifest + headless/GUI split still to generate.
- **pending-deps** — needs std packages or capabilities beyond the headless 64-bit SDK (e.g. std/net, 32-bit, GPU FFI).
- **pending-gui** — needs `std/gui` (window manager + raster).

Currently validated & installable: `matrix` (83 modules), `ar`, `fftw`, `usb`, `freeimage`,
`generics`. The six that are not — `octk`, `opendocument`, `ph`, `reanimator`, `sr`, `work` —
carry the reason they are not, measured rather than guessed; remeasured 2026-08-24.

## Updating this registry

**One rule above all: `std/*`, `attic/*` and `apps/*` are edited in minia2, never here.** minia2's
`packages/` is the only copy anything checks (`task registry` there fails on a manifest that
disagrees with the import graph, on a payload module no package claims, on a stale `graphical`
annotation, and on this repository having drifted from that one). What lives here and nowhere else
are the **community packages** — their manifests and their vendored `.Mod` sources.

```sh
# 1. std/attic/apps: edit minia2/packages/…/a2pkg.json, then regenerate what ships
cd ../minia2 && bash docker/gen-headless-core.sh

# 2. carry it here (copies the manifests, rewrites the index entries for them)
cd ../a2-registry && python3 tools/sync-std.py          # --check to only report

# 3. both gates, run from minia2
cd ../minia2 && task registry

# 4. commit and push -- Pages rebuilds site/ itself
```

For a **community** package the sources are here, so the edit is here too, and
`tools/check-ocp.py` is what keeps it honest: every module of the package's `upstream` directory
in `a2oberon/ocp` has to be either in `provides` or in `excludes` with a reason. It reads the
module name **from the file**, because the file name is not it often enough to matter
(`ocp/Matrix/LinearFIRConvolve.Mod` declares `MODULE TestLFC`). It is part of `task registry`, and
skips itself where the `a2oberon` clone is absent.

```sh
A2OBERON=/path/to/a2oberon python3 tools/check-ocp.py
```

## Build the docs site

Python only — it consumes `index.json` + `docs/`:

```sh
python3 tools/build_site.py      # -> site/ (open site/index.html)
```

Regenerating the raw docs after changing a package's sources needs the SDK, which is a tarball
(or `curl | sh`) and not a container:

```sh
ob doc -o packages/<name>/_doc packages/<name>/*.Mod
mv packages/<name>/_doc/*.html docs/<name>/
```

## Publishing (GitHub Pages)

`.github/workflows/pages.yml` builds `site/` and deploys it to Pages on every push to
`main` (Settings → Pages → Source: GitHub Actions). Served at
`https://<org>.github.io/a2-registry/`.

## Notes

- Canonical source of the libraries: `github.com/sergundo/A2Community`.
- `a2oberon/ocp` adds ~33 modules not in A2Community (union candidates).
- OCTK / Reanimator / sr are stored in A2 **binary Text format** — `ob` reads it since
  2026-08-24 (before that it read the module header as plain text and refused the file, while
  the compiler underneath compiled it); text-based analysis still needs care. Their real blockers are 32-bit, GPU FFI, legacy
  `Aos*` names + `std/compiler`, and `std/gui` respectively (see `index.json`).
- `a2oberon/ARM` (Enet/Zynq bare-metal) is an embedded track, not a library — excluded.

## License

Registry tooling, catalogue and site: **BSD 3-Clause**, © 2026 Andrii Puhachenko (see `LICENSE`).
Vendored package sources under `packages/` remain the work of their original authors, gathered
here for consolidation with attribution preserved — see `NOTICE`.
