# a2-registry — A2 / Active Oberon package registry

A central, CPAN/Maven-style catalogue of community libraries for A2 / Active Oberon,
installable with the minia2 SDK's `ob get`. Each package under `packages/<name>/` is a
self-contained set of `.Mod` sources plus an `a2pkg.json` manifest (see the minia2
`packages/README.md` for the manifest format and the tier model).

`index.json` is the machine-readable catalogue (name → status, module count, requires,
summary). `docs/` holds generated pkg.go.dev-style HTML API docs (produced by `ob doc`).

## Status legend
- **validated** — manifest written, sources compile headless against the SDK stdlib, docs generated.
- **pending-manifest** — ASCII sources present; manifest + headless/GUI split still to generate.
- **pending-binary** — sources in A2 binary Text format; `ob`/`ob doc` read them, but text-based
  manifest auto-generation needs interface extraction first.

## Install (once published as git repos or via a registry-aware `ob get`)
```
ob get <host>/<user>/a2-registry//packages/matrix     # (subdir form — planned)
```
Today `ob get` clones one git repo per package; registry-name resolution (`ob get community/matrix`)
is the next wiring step.
