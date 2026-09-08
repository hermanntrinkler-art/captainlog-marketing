#!/usr/bin/env python3
"""
Build production-ready, standalone static HTML pages from the .dc.html
design-canvas artboards. Strips the Claude Design Canvas editor scaffolding
and DCLogic dependency, replacing it with a small vanilla-JS re-render
engine that does the exact same {{token}} -> T[key][lang] substitution the
canvas editor's DCLogic.renderVals() does, plus a lang-select change
listener (event delegation, survives re-renders).
"""
import re, os

SRC_DIR = "/home/claude/captainslog-landing"
OUT_DIR = "/home/claude/captainslog-landing/dist"
os.makedirs(OUT_DIR, exist_ok=True)

PAGES = [
    ("Main.dc.html", "index.html", "Captain's Log – dein digitales Cockpit an Bord"),
    ("Chartplotter.dc.html", "chartplotter.html", "Chartplotter – Captain's Log"),
    ("SmartBoat.dc.html", "smartboat.html", "Smart-Boat – Captain's Log"),
]

RUNTIME_JS = """
(function () {
  var tplEl = document.getElementById('tpl');
  var appEl = document.getElementById('app');
  var template = tplEl.textContent;
  var SUPPORTED = ['de','en','es','fr','it','nl','pt'];
  var state = { lang: (function(){
    try {
      var saved = localStorage.getItem('cl_lang');
      return (saved && SUPPORTED.indexOf(saved) !== -1) ? saved : 'de';
    } catch(e) { return 'de'; }
  })() };

  function render() {
    var lang = state.lang;
    var html = template.replace(/\\{\\{(\\w+)\\}\\}/g, function (m, key) {
      if (key === 'lang') return lang;
      var entry = T[key];
      if (!entry) return '';
      return entry[lang] || entry.de || '';
    });
    appEl.innerHTML = html;
    var sel = appEl.querySelector('.lang-select');
    if (sel) sel.value = lang;
    document.documentElement.setAttribute('lang', lang);
  }

  appEl.addEventListener('change', function (e) {
    if (e.target && e.target.classList.contains('lang-select')) {
      state.lang = e.target.value;
      try { localStorage.setItem('cl_lang', state.lang); } catch (e) {}
      render();
    }
  });

  render();
})();
""".strip()


def extract(src_path):
    src = open(src_path, encoding="utf-8").read()

    style_m = re.search(r"<helmet>\s*<style>(.*?)</style>\s*</helmet>", src, re.S)
    style = style_m.group(1)

    body_m = re.search(r"</helmet>\s*(.*?)\s*</x-dc>", src, re.S)
    body = body_m.group(1)

    # Neutralize the DCLogic-specific select bindings; the vanilla runtime
    # binds via event delegation instead, and sets .value via JS (an HTML
    # `value` attribute on <select> is a no-op in real browsers anyway).
    body = body.replace('value="{{lang}}" onChange="{{setLang}}"', 'value="de"')

    t_m = re.search(r"const T = (\{.*?\n\});", src, re.S)
    t_obj = t_m.group(1)

    return style, body, t_obj


def build_page(src_file, out_file, title):
    style, body, t_obj = extract(os.path.join(SRC_DIR, src_file))

    html = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Captain's Log – das digitale Bordbuch für Segler.">
<link rel="icon" href="logo-icon.png">
<style>
{style}
</style>
</head>
<body>
<div id="app"></div>
<script id="tpl" type="text/x-template">
{body}
</script>
<script>
var T = {t_obj};
{RUNTIME_JS}
</script>
</body>
</html>
"""
    out_path = os.path.join(OUT_DIR, out_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", out_path, len(html), "bytes")


for src, out, title in PAGES:
    build_page(src, out, title)

# copy image assets alongside
import shutil
for img in ["logo-icon.png"]:
    shutil.copy(os.path.join(SRC_DIR, img), os.path.join(OUT_DIR, img))
    print("copied", img)
