#!/usr/bin/env python3
"""
Build the styled static site for a2-registry (moon theme) into ./site/.

Inputs:  index.json  +  docs/<pkg>/<Module>.html  (raw `ob doc` output)
Output:  site/index.html, site/assets/{style.css,app.js}, site/<pkg>/<Module>.html

The front page is generated fully (hero + client-side search over an embedded
index). Module pages wrap the raw Fox documentation body in the themed shell and
restyle its elements via CSS. Python-only — no Docker needed to build the site
(regenerating docs/ with `ob doc` is a separate step).
"""
import json, os, re, html, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DOCS = os.path.join(ROOT, "docs")

# ---------------------------------------------------------------- shared CSS
STYLE = r"""
:root{
  --bg:#0a0e1c; --bg-2:#070a15; --surface:#111631; --surface-2:#171d3d; --border:#252c50;
  --ink:#e9ebf6; --muted:#8b93b6; --faint:#5f668c; --accent:#aebde9; --accent-strong:#cdd8f7;
  --accent-glow:rgba(174,189,233,.18); --ok:#74d3ac; --ok-bg:rgba(116,211,172,.12);
  --warn:#e2b56d; --warn-bg:rgba(226,181,109,.12);
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --maxw:1080px; --r:10px; color-scheme:dark;
}
@media (prefers-color-scheme:light){:root{
  --bg:#eceef7; --bg-2:#e3e6f3; --surface:#fff; --surface-2:#f4f6fd; --border:#d7dcef;
  --ink:#141830; --muted:#54608a; --faint:#8b93b6; --accent:#3f4fa0; --accent-strong:#2b3a86;
  --accent-glow:rgba(63,79,160,.14); --ok:#1f9d72; --ok-bg:rgba(31,157,114,.12);
  --warn:#a9761f; --warn-bg:rgba(169,118,31,.12); color-scheme:light;}}
:root[data-theme="dark"]{
  --bg:#0a0e1c; --bg-2:#070a15; --surface:#111631; --surface-2:#171d3d; --border:#252c50;
  --ink:#e9ebf6; --muted:#8b93b6; --faint:#5f668c; --accent:#aebde9; --accent-strong:#cdd8f7;
  --accent-glow:rgba(174,189,233,.18); --ok:#74d3ac; --ok-bg:rgba(116,211,172,.12);
  --warn:#e2b56d; --warn-bg:rgba(226,181,109,.12); color-scheme:dark;}
:root[data-theme="light"]{
  --bg:#eceef7; --bg-2:#e3e6f3; --surface:#fff; --surface-2:#f4f6fd; --border:#d7dcef;
  --ink:#141830; --muted:#54608a; --faint:#8b93b6; --accent:#3f4fa0; --accent-strong:#2b3a86;
  --accent-glow:rgba(63,79,160,.14); --ok:#1f9d72; --ok-bg:rgba(31,157,114,.12);
  --warn:#a9761f; --warn-bg:rgba(169,118,31,.12); color-scheme:light;}
*{box-sizing:border-box} html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:.6;background:
  radial-gradient(1px 1px at 12% 22%,var(--accent-glow),transparent),
  radial-gradient(1px 1px at 78% 14%,var(--accent-glow),transparent),
  radial-gradient(1.5px 1.5px at 44% 68%,var(--accent-glow),transparent),
  radial-gradient(1px 1px at 88% 76%,var(--accent-glow),transparent),
  radial-gradient(1200px 600px at 82% -10%,var(--accent-glow),transparent 60%)}
a{color:var(--accent-strong);text-decoration:none} a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}
header.top{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 82%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
.top .wrap{display:flex;align-items:center;gap:20px;height:60px}
.brand{display:flex;align-items:center;gap:11px}
.brand .mark{width:30px;height:30px;flex:none}
.brand .wm{font-family:var(--mono);font-weight:600;font-size:19px;letter-spacing:-.01em;color:var(--ink)}
.brand .wm sup{color:var(--accent);font-size:.62em;top:-.5em}
.brand .sub{color:var(--faint);font-size:12.5px;margin-left:2px}
.top nav{margin-left:auto;display:flex;align-items:center;gap:22px}
.top nav a{color:var(--muted);font-size:14px} .top nav a:hover{color:var(--ink);text-decoration:none}
.toggle{background:var(--surface-2);border:1px solid var(--border);color:var(--muted);width:34px;height:34px;border-radius:8px;cursor:pointer;font-size:15px;display:grid;place-items:center}
.toggle:hover{color:var(--ink);border-color:var(--accent)}
.hero{position:relative;padding:64px 0 40px;overflow:hidden}
.hero .moon{position:absolute;right:28px;top:28px;width:270px;height:270px;z-index:0;opacity:.85;pointer-events:none;filter:drop-shadow(0 0 60px var(--accent-glow))}
@media(max-width:900px){.hero .moon{width:200px;height:200px;right:8px;top:14px;opacity:.4}}
@media(max-width:600px){.hero .moon{display:none}}
.hero .inner{position:relative;z-index:1;max-width:640px}
.eyebrow{font-family:var(--mono);font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:0 0 14px}
h1.title{font-size:clamp(30px,5vw,46px);line-height:1.08;letter-spacing:-.02em;margin:0 0 16px;font-weight:640;text-wrap:balance}
h1.title .m{font-family:var(--mono);color:var(--accent-strong);font-weight:600}
.lede{font-size:17.5px;color:var(--muted);margin:0 0 28px;max-width:56ch}
.lede code,.hint code{font-family:var(--mono);color:var(--accent-strong)}
.search{position:relative;max-width:560px}
.search svg{position:absolute;left:15px;top:50%;transform:translateY(-50%);color:var(--faint)}
#q{width:100%;padding:14px 16px 14px 44px;font-size:15.5px;font-family:var(--sans);color:var(--ink);background:var(--surface);border:1px solid var(--border);border-radius:12px}
#q::placeholder{color:var(--faint)}
#q:focus{border-color:var(--accent);outline:none;box-shadow:0 0 0 4px var(--accent-glow)}
.hint{margin-top:10px;font-size:13px;color:var(--faint)}
.hint code{background:var(--surface-2);padding:1px 6px;border-radius:5px;color:var(--muted)}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;margin:48px 0 18px}
.sec-head h2{font-size:14px;font-family:var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0;font-weight:600}
.sec-head .count{font-size:13px;color:var(--faint);font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:18px 18px 16px;transition:border-color .15s,transform .15s,background .15s;display:flex;flex-direction:column;min-height:132px;color:inherit}
.card:hover{border-color:var(--accent);transform:translateY(-2px);background:var(--surface-2);text-decoration:none}
.card .row1{display:flex;align-items:center;gap:9px;margin-bottom:7px}
.card .name{font-family:var(--mono);font-size:15.5px;color:var(--ink);font-weight:600}
.card .name .ns{color:var(--faint);font-weight:400}
.card .desc{color:var(--muted);font-size:14px;line-height:1.5;flex:1}
.card .meta{display:flex;align-items:center;gap:10px;margin-top:14px;font-size:12.5px;color:var(--faint);font-family:var(--mono)}
.card .meta .dot{width:3px;height:3px;border-radius:50%;background:var(--faint)}
.chip{font-family:var(--mono);font-size:11px;letter-spacing:.03em;padding:3px 8px;border-radius:20px;white-space:nowrap}
.chip.ok{color:var(--ok);background:var(--ok-bg)} .chip.pending{color:var(--warn);background:var(--warn-bg)}
.chip.bundled{color:var(--accent);background:var(--accent-glow)}
.modindex{list-style:none;padding:0;margin:14px 0 0;columns:2;column-gap:32px}
@media(max-width:640px){.modindex{columns:1}}
.modindex li{margin:0 0 7px;break-inside:avoid}
.modindex a{font-family:var(--mono);font-size:14px;color:var(--accent-strong)}
.foxdoc a[href*=".html#"]{border-bottom:1px dotted var(--faint)}
.badge{font-family:var(--mono);font-size:11px;color:var(--accent);border:1px solid var(--border);padding:2px 7px;border-radius:6px}
.card .sym-hit{margin-top:12px;font-family:var(--mono);font-size:12px;color:var(--accent);background:var(--accent-glow);padding:6px 9px;border-radius:7px;display:none}
.card .sym-hit.show{display:block} .card .sym-hit b{color:var(--accent-strong)}
.empty{color:var(--faint);padding:30px 0;font-size:15px}
/* module page */
.crumb{font-family:var(--mono);font-size:13px;color:var(--faint);padding:26px 0 0} .crumb a{color:var(--muted)}
.modlayout{display:grid;grid-template-columns:230px 1fr;gap:40px;padding:22px 0 80px;align-items:start}
@media(max-width:820px){.modlayout{grid-template-columns:1fr}.rail{display:none}}
.rail{position:sticky;top:80px;font-size:13.5px}
.rail .rlabel{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);margin:0 0 10px}
.rail ul{list-style:none;margin:0 0 20px;padding:0;display:flex;flex-direction:column;gap:3px}
.rail a{color:var(--muted);font-family:var(--mono);font-size:13px;display:block;padding:2px 0} .rail a:hover{color:var(--accent);text-decoration:none}
.doc-purpose{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:var(--r);padding:15px 18px;margin:0 0 22px;color:var(--muted);font-size:14.5px}
/* restyle raw Fox documentation body */
.foxdoc{font-size:15px}
.foxdoc h1{font-family:var(--mono);font-size:28px;font-weight:640;margin:0 0 8px;letter-spacing:-.01em}
.foxdoc h1 a{color:var(--ink)}
.foxdoc h2,.foxdoc h3{font-family:var(--mono);font-size:13px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent);margin:30px 0 4px;padding-bottom:8px;border-bottom:1px solid var(--border);font-weight:600}
.foxdoc hr{border:0;border-top:1px solid var(--border);margin:22px 0}
.foxdoc p{color:var(--muted)}
.foxdoc table{width:100%;border-collapse:collapse;margin:8px 0 4px;display:block;overflow-x:auto}
.foxdoc td,.foxdoc th{text-align:left;vertical-align:top;padding:9px 12px 9px 0;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:13.5px;color:var(--ink)}
.foxdoc th{color:var(--accent);font-size:11px;letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;font-weight:600}
.foxdoc strong{color:var(--accent);font-weight:600}
.foxdoc a{color:var(--accent-strong)}
footer{border-top:1px solid var(--border);padding:26px 0 40px;color:var(--faint);font-size:13px}
footer .wrap{display:flex;gap:16px;flex-wrap:wrap;align-items:center;justify-content:space-between}
footer .mono{font-family:var(--mono)}
.install{font-family:var(--mono);font-size:13px;background:var(--bg-2);border:1px solid var(--border);border-radius:8px;padding:9px 13px;color:var(--muted);overflow-x:auto;white-space:pre}
.install .p{color:var(--accent)}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

APP_JS = r"""
(function(){
  var root=document.documentElement, tt=document.getElementById('tt');
  function sysDark(){return matchMedia('(prefers-color-scheme:dark)').matches}
  function setTheme(t){root.setAttribute('data-theme',t); if(tt) tt.textContent=(t==='dark')?'◑':'◐';}
  setTheme(sysDark()?'dark':'light');
  if(tt) tt.onclick=function(){setTheme(root.getAttribute('data-theme')==='dark'?'light':'dark');};
  var q=document.getElementById('q');
  if(!q||!window.__PKGS__) return;
  var PKGS=window.__PKGS__, grid=document.getElementById('grid'),
      cnt=document.getElementById('cnt'), empty=document.getElementById('empty');
  function nameHTML(n){var i=n.indexOf('/');return '<span class="ns">'+n.slice(0,i+1)+'</span>'+n.slice(i+1);}
  function render(list,query){
    grid.innerHTML='';
    list.forEach(function(p){
      var chip=p.status==='bundled'?'<span class="chip bundled">bundled</span>':
               p.status==='validated'?'<span class="chip ok">validated</span>':
               '<span class="chip pending">pending</span>';
      var hit='';
      if(query){var m=(p.syms||[]).filter(function(s){return s.toLowerCase().indexOf(query)>=0});
        if(m.length&&p.n.indexOf(query)<0) hit='<div class="sym-hit show">↳ symbol · <b>'+m.slice(0,3).join('</b>, <b>')+'</b>'+(m.length>3?' …':'')+'</div>';}
      var a=document.createElement('a'); a.className='card'; a.href=p.href||'#';
      if(!p.href) a.addEventListener('click',function(e){e.preventDefault();});
      a.innerHTML='<div class="row1"><span class="name">'+nameHTML(p.n)+'</span> '+chip+'</div>'+
        '<div class="desc">'+p.s+'</div>'+hit+
        '<div class="meta"><span class="badge">tier '+p.tier+'</span><span>'+p.mods+' module'+(p.mods>1?'s':'')+'</span>'+
        (p.native?'<span class="dot"></span><span>'+p.native+'</span>':'')+'</div>';
      grid.appendChild(a);
    });
    if(cnt) cnt.textContent=list.length+' of '+PKGS.length+' packages';
    if(empty) empty.style.display=list.length?'none':'block';
  }
  q.addEventListener('input',function(){
    var query=q.value.trim().toLowerCase();
    if(!query){render(PKGS);return;}
    render(PKGS.filter(function(p){return p.n.toLowerCase().indexOf(query)>=0||p.s.toLowerCase().indexOf(query)>=0||(p.syms||[]).some(function(s){return s.toLowerCase().indexOf(query)>=0});}),query);
  });
  render(PKGS);
})();
"""

MOON_MARK = ('<svg class="mark" viewBox="0 0 32 32" aria-label="A2 moon mark">'
 '<defs><radialGradient id="mg" cx="38%" cy="34%" r="72%">'
 '<stop offset="0%" stop-color="var(--accent-strong)"/><stop offset="55%" stop-color="var(--accent)"/>'
 '<stop offset="100%" stop-color="color-mix(in srgb,var(--accent) 45%,var(--bg))"/></radialGradient></defs>'
 '<circle cx="16" cy="16" r="13" fill="url(#mg)"/><circle cx="21.5" cy="12.5" r="12" fill="var(--bg)" opacity=".34"/>'
 '<circle cx="11" cy="19" r="2.1" fill="var(--bg)" opacity=".22"/><circle cx="14.5" cy="10.5" r="1.3" fill="var(--bg)" opacity=".22"/></svg>')

def top(active_home=True, rel=""):
    return (f'<header class="top"><div class="wrap"><a class="brand" href="{rel}index.html" style="text-decoration:none">'
      f'{MOON_MARK}<span class="wm">A<sup>2</sup></span><span class="sub">· registry</span></a>'
      f'<nav><a href="{rel}index.html">Packages</a><a href="https://github.com/active-oberon/minia2">SDK</a>'
      f'<button class="toggle" id="tt" title="Toggle theme" aria-label="Toggle light/dark">◑</button></nav></div></header>')

FOOT = ('<footer><div class="wrap"><span class="mono">A² registry · Active Oberon / A2</span>'
  '<span class="install"><span class="p">ob get</span> community/matrix</span>'
  '<span>Oberon — named for the moon of Uranus.</span></div></footer>')

def page(title, body, rel=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
      f'<meta name="viewport" content="width=device-width,initial-scale=1">'
      f'<title>{html.escape(title)}</title><link rel="stylesheet" href="{rel}assets/style.css">'
      f'</head><body>{top(rel=rel)}<main>{body}</main>{FOOT}'
      f'<script src="{rel}assets/app.js"></script></body></html>')

MODMAP = {}        # module name -> short package dir (built in build(), pass 1)
_LINK_RE = None

def _build_linkre():
    global _LINK_RE
    if MODMAP:
        names = sorted(MODMAP, key=len, reverse=True)
        _LINK_RE = re.compile(r'(?<![\w."#/=])(' + '|'.join(map(re.escape, names)) + r')\.([A-Za-z][A-Za-z0-9_]*)')

def linkify(inner, current, rel):
    # turn cross-module qualified names (Streams.Writer) into links to that module's
    # page + symbol anchor (Fox emits <a name="Module.Symbol">). Skip the current
    # module — Fox already anchors its own symbols within the page.
    if not _LINK_RE: return inner
    def repl(mo):
        mod, sym = mo.group(1), mo.group(2)
        if mod == current or mod not in MODMAP: return mo.group(0)
        return f'<a href="{rel}{MODMAP[mod]}/{mod}.html#{mod}.{sym}">{mod}.{sym}</a>'
    return _LINK_RE.sub(repl, inner)

def module_body(fox_html, name, short, module, modules, rel):
    m = re.search(r'<body>(.*)</body>', fox_html, re.S|re.I)
    inner = m.group(1) if m else fox_html
    inner = re.sub(r'<style.*?</style>', '', inner, flags=re.S|re.I)  # drop Fox inline CSS
    inner = linkify(inner, module, rel)
    CAP = 18
    rail_items = "".join(
        f'<li><a href="{rel}{short}/{mm}.html"'
        + (' style="color:var(--accent)"' if mm==module else '')
        + f'>{mm}</a></li>' for mm in modules[:CAP])
    if len(modules) > CAP:
        rail_items += f'<li><a href="{rel}{short}/index.html" style="color:var(--accent-strong)">+{len(modules)-CAP} more →</a></li>'
    return (f'<div class="wrap"><p class="crumb"><a href="{rel}index.html">registry</a> / '
      f'<a href="{rel}{short}/index.html">{name}</a> / <span style="color:var(--ink)">{module}</span></p>'
      f'<div class="modlayout"><aside class="rail"><p class="rlabel"><a href="{rel}{short}/index.html">{name}</a></p>'
      f'<ul>{rail_items}</ul></aside><div class="foxdoc">{inner}</div></div></div>')

def package_index_body(name, short, meta, modules, rel):
    status = meta.get("status", "pending")
    chipcls = {"bundled": "bundled", "validated": "ok"}.get(status, "pending")
    req = meta.get("requires", [])
    reqhtml = (" · requires " + ", ".join(req)) if req else ""
    if status == "validated":
        inst = f'<div class="install"><span class="p">ob get</span> {name}</div>'
    elif meta.get("install"):
        inst = f'<p class="hint">{meta["install"]}</p>'
    else:
        inst = ""
    items = "".join(f'<li><a href="{rel}{short}/{mm}.html">{mm}</a></li>' for mm in modules)
    n = len(modules)
    return (f'<div class="wrap"><p class="crumb"><a href="{rel}index.html">registry</a> / '
      f'<span style="color:var(--ink)">{name}</span></p>'
      f'<div style="padding:24px 0 70px;max-width:780px">'
      f'<h1 style="font-family:var(--mono);font-size:30px;margin:0 0 10px;letter-spacing:-.01em">{name} '
      f'<span class="chip {chipcls}" style="vertical-align:middle">{status}</span></h1>'
      f'<p class="lede" style="font-size:16.5px;margin:0 0 12px">{meta.get("summary","")}</p>'
      f'<p class="hint">tier {meta.get("tier","?")}{reqhtml} · {n} documented module{"" if n==1 else "s"}</p>'
      f'{inst}'
      f'<div class="sec-head"><h2>Modules</h2><span class="count">{n}</span></div>'
      f'<ul class="modindex">{items}</ul></div></div>')

def build():
    idx = json.load(open(os.path.join(ROOT, "index.json")))
    pkgs = idx["packages"]
    if os.path.isdir(SITE): shutil.rmtree(SITE)
    os.makedirs(os.path.join(SITE, "assets"))
    open(os.path.join(SITE, ".nojekyll"), "w").write("")  # serve _-prefixed files as-is
    open(os.path.join(SITE, "assets", "style.css"), "w").write(STYLE)

    # pass 1: collect modules per package + build the global module->page map
    pkgmods = {}
    for name, meta in pkgs.items():
        short = name.split("/", 1)[1]
        docdir = os.path.join(DOCS, short)
        modules = sorted(f[:-5] for f in os.listdir(docdir)
                         if f.endswith(".html") and f != "index.html") if os.path.isdir(docdir) else []
        pkgmods[name] = (short, modules)
        for mm in modules: MODMAP[mm] = short
    _build_linkre()

    # pass 2: render module pages + a package index page, with cross-links resolved
    cards = []
    for name, meta in pkgs.items():
        short, modules = pkgmods[name]
        if modules:
            os.makedirs(os.path.join(SITE, short), exist_ok=True)
            for mod in modules:
                fox = open(os.path.join(DOCS, short, mod + ".html"), encoding="utf-8", errors="replace").read()
                open(os.path.join(SITE, short, mod + ".html"), "w").write(
                    page(f"{mod} · {name}", module_body(fox, name, short, mod, modules, "../"), rel="../"))
            open(os.path.join(SITE, short, "index.html"), "w").write(
                page(f"{name}", package_index_body(name, short, meta, modules, "../"), rel="../"))
        href = f"{short}/index.html" if modules else None
        cards.append({"n": name, "s": meta.get("summary", ""), "mods": meta.get("modules", len(modules)),
                      "tier": meta.get("tier", 2), "status": meta.get("status", "pending"),
                      "native": meta.get("native", ""), "syms": modules or [short],
                      "href": href})

    # order: bundled stdlib first, then validated community, then pending; tier then size
    rank = {"bundled": 0, "validated": 1}
    cards.sort(key=lambda c: (rank.get(c["status"], 2), c["tier"], -c["mods"]))

    hero_moon = ('<svg class="moon" viewBox="0 0 200 200" aria-hidden="true">'
      '<defs><radialGradient id="hg" cx="38%" cy="34%" r="72%"><stop offset="0%" stop-color="var(--accent-strong)"/>'
      '<stop offset="55%" stop-color="var(--accent)"/><stop offset="100%" stop-color="color-mix(in srgb,var(--accent) 45%,var(--bg))"/></radialGradient></defs>'
      '<circle cx="100" cy="100" r="82" fill="url(#hg)"/><circle cx="132" cy="76" r="76" fill="var(--bg)" opacity=".33"/>'
      '<circle cx="70" cy="118" r="13" fill="var(--bg)" opacity=".16"/><circle cx="92" cy="62" r="8" fill="var(--bg)" opacity=".16"/>'
      '<circle cx="112" cy="128" r="6" fill="var(--bg)" opacity=".13"/></svg>')
    home_body = (
      '<div class="hero">' + hero_moon +
      '<div class="wrap"><div class="inner"><p class="eyebrow">Active Oberon · A2</p>'
      '<h1 class="title">Packages for a garbage-collected systems language with <span class="m">active objects</span>.</h1>'
      '<p class="lede">Community libraries for Active Oberon, installable with the minia2 SDK. One command — '
      '<code>ob get</code> — pulls sources, resolves the tier graph, and builds a standalone binary. No A2 install needed.</p>'
      '<div class="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
      '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>'
      '<input id="q" type="search" placeholder="Search packages and symbols — try “matrix”, “SVD”, “fft”…" autocomplete="off" aria-label="Search"></div>'
      '<p class="hint">Search spans package names, summaries and exported modules.</p></div></div></div>'
      '<div class="wrap"><div class="sec-head"><h2>Registry</h2><span class="count" id="cnt"></span></div>'
      '<div class="grid" id="grid"></div><p class="empty" id="empty" style="display:none">No package or symbol matches that.</p></div>'
      '<script>window.__PKGS__=' + json.dumps(cards) + ';</script>')
    open(os.path.join(SITE, "index.html"), "w").write(page("A² — Active Oberon packages", home_body, rel=""))
    open(os.path.join(SITE, "assets", "app.js"), "w").write(APP_JS)

    n_mod = sum(1 for _ in _walk_html(SITE)) - 1
    print(f"built site/: {len(cards)} packages, {n_mod} module pages")

def _walk_html(base):
    for dp, _, fs in os.walk(base):
        for f in fs:
            if f.endswith(".html"): yield os.path.join(dp, f)

if __name__ == "__main__":
    build()
