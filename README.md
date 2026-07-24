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

Currently validated & installable: `matrix` (74), `fftw`, `usb`, `freeimage`, `generics`.

## Build the docs site

The site is **Python-only** to build (no Docker) — it consumes `index.json` + `docs/`:

```sh
python3 tools/build_site.py      # -> site/ (open site/index.html)
```

Regenerating the raw docs after changing a package's sources needs the SDK image:

```sh
docker run --rm -v "$PWD/packages/<name>:/work" minia2-sdk doc -o /work/_doc
mv packages/<name>/_doc/*.html docs/<name>/
```

## Publishing (GitHub Pages)

`.github/workflows/pages.yml` builds `site/` and deploys it to Pages on every push to
`main` (Settings → Pages → Source: GitHub Actions). Served at
`https://<org>.github.io/a2-registry/`.

## Notes

- Canonical source of the libraries: `github.com/sergundo/A2Community`.
- `a2oberon/ocp` adds ~33 modules not in A2Community (union candidates).
- OCTK / Reanimator / sr are stored in A2 **binary Text format** — `ob compile`/`ob doc`
  read it fine; only text-based analysis / manifest auto-generation is blocked (needs
  interface extraction from `.SymUu`). Their real blockers are 32-bit, GPU FFI, legacy
  `Aos*` names + `std/compiler`, and `std/gui` respectively (see `index.json`).
- `a2oberon/ARM` (Enet/Zynq bare-metal) is an embedded track, not a library — excluded.
