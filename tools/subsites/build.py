#!/usr/bin/env python3
"""Build each game's intro page for <host>.humblelogicgames.com.

Sources (single source of truth, same repo as the main site):
  _data/games.yml      names, store ids
  _data/gamepages.yml  page content (tagline, about, how to play, features, video, host)
  assets/icons/<slug>.png, assets/css/site.css

Output: _subsites/<host>/index.html + _subsites/<host>/assets/ (Jekyll ignores folders starting with "_").
Usage:  python3 tools/subsites/build.py            # all games
        python3 tools/subsites/build.py sudoku     # one game (slug)
Nothing is uploaded. Publishing is a separate, approved step.
"""
import html
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_subsites"
DOMAIN = "humblelogicgames.com"
SITE = f"https://{DOMAIN}"
PLAY = "https://play.google.com/store/apps/details?id="
APPSTORE = "https://apps.apple.com/app/id"
AMAZON = "https://www.amazon.com/dp/"

e = html.escape


def load():
    games = {g["slug"]: g for g in yaml.safe_load((ROOT / "_data/games.yml").read_text())}
    pages = yaml.safe_load((ROOT / "_data/gamepages.yml").read_text())
    return games, pages


def store_buttons(g, A="assets/"):
    # Official store badges (tools/subsites/badges/): Apple's SVG, Google Play and Amazon Appstore PNGs
    out = []
    if g.get("package"):
        out.append(f'<a class="badge" data-os="android" href="{PLAY}{e(g["package"])}&amp;referrer=utm_source%3D{e(g["slug"])}_site">'
                   f'<img src="{A}badges/googleplay.png" alt="Get it on Google Play" height="40"></a>')
    if g.get("apple_id"):
        out.append(f'<a class="badge" data-os="ios" href="{APPSTORE}{e(g["apple_id"])}">'
                   f'<img src="{A}badges/appstore.svg" alt="Download on the App Store" height="40"></a>')
    if g.get("amazon_asin"):
        out.append(f'<a class="badge" data-os="amazon" href="{AMAZON}{e(g["amazon_asin"])}">'
                   f'<img src="{A}badges/amazon.png" alt="Available at Amazon Appstore" height="40"></a>')
    return "\n    ".join(out)


def video_block(p, g):
    vid = p.get("video")
    if not vid:
        return ""
    # Load YouTube only on click: thumbnail first (lighter page, no YouTube cookies until the visitor asks)
    return f'''<section class="video">
  <button class="yt" data-id="{e(vid)}" aria-label="Play the {e(g["short"])} video">
    <img src="https://i.ytimg.com/vi/{e(vid)}/hqdefault.jpg" alt="" loading="lazy" width="480" height="360">
    <span class="yt-play" aria-hidden="true"></span>
  </button>
</section>'''


def more_games(slug, games, pages, I="assets/icons/"):
    items = []
    for s, p in pages.items():
        if s == slug or s not in games:
            continue
        g = games[s]
        items.append(f'<li><a href="https://{e(p["host"])}.{DOMAIN}/"><img src="{I}{e(s)}.png" alt="" width="64" height="64" loading="lazy">'
                     f'<span>{e(g["short"])}</span></a></li>')
    return "\n      ".join(items)


def page(slug, games, pages, root=False):
    """root=False: <host>.humblelogicgames.com/   root=True: humblelogicgames.com/games/<slug>/ (Jekyll include)"""
    g, p = games[slug], pages[slug]
    A = "/assets/sub/" if root else "assets/"          # css, js, fonts, badges
    I = "/assets/icons/" if root else "assets/icons/"  # icons
    t = p.get("theme", {})
    deep, acc, pat = t.get("deep", "#26365a"), t.get("acc", "#f0a35e"), t.get("pat", "dots")
    privacy = f"{SITE}/docs/privacypolicy-dominoes" if slug == "dominoes" else f"{SITE}/docs/privacypolicy"
    play = ""
    if p.get("play"):
        purl = p.get("root_play_url", f"https://{p['host']}.{DOMAIN}/") if root else p.get("play_url", "play/")
        play = f'''<a class="play" href="{e(purl)}" id="play"><span aria-hidden="true">▶</span> Play in browser</a>
      <p class="hint">Free in your browser · get the app for the full game</p>'''
    about = "\n      ".join(f"<p>{e(x)}</p>" for x in p["about"])
    steps = "\n        ".join(f"<li><span>{e(x)}</span></li>" for x in p["howto"])
    feats = "\n        ".join(f"<li>{e(x)}</li>" for x in p["features"])
    title = f'{g["short"]} — {p["tagline"]}'
    support_meta = ""
    og = {} if root else p   # invite-preview overrides (dominoes) apply only on the subdomain page
    og_size = "".join(f'\n  <meta property="og:image:{k}" content="{v}">' for k, v in og.get("og_image_size", {}).items())
    support = ""
    if root:
        support = f'''<section>
      <h2>Support and policies</h2>
      <ul class="feats plain">
        <li><a href="mailto:humblelogicgames@gmail.com">Support: humblelogicgames@gmail.com</a></li>
        <li><a href="{privacy}">Privacy Policy</a></li>
        <li><a href="{SITE}/docs/termsofservice">Terms of Service</a></li>
        <li><a href="https://{e(p["host"])}.{DOMAIN}/">Game website: {e(p["host"])}.{DOMAIN}</a></li>
      </ul>
    </section>'''
    return f'''<!doctype html>
<html lang="en" style="--deep:{deep};--acc:{acc}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{e(title)} · Humble Logic Games</title>
  <meta name="description" content="{e(g["desc"])}">
  <link rel="canonical" href="https://{e(p["host"])}.{DOMAIN}/">{support_meta}
  <meta property="og:type" content="website">
  <meta property="og:title" content="{e(og.get("og_title", g["name"]))}">
  <meta property="og:site_name" content="Humble Logic Games">
  <meta property="og:url" content="https://{e(p["host"])}.{DOMAIN}/">
  <meta property="og:description" content="{e(og.get("og_desc", g["desc"]))}">
  <meta property="og:image" content="https://{e(p["host"])}.{DOMAIN}{e(og.get("og_image", "/assets/icons/" + slug + ".png"))}">{og_size}
  <meta name="twitter:card" content="summary">
  <meta name="theme-color" content="{deep}">
  <link rel="icon" href="{I}{e(slug)}.png">
  <link rel="apple-touch-icon" href="{I}{e(slug)}.png">
  <link rel="preload" href="{A}fonts/jakarta-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{A}sub.css">
</head>
<body>
  <header class="hero pat-{e(pat)}">
    <nav class="bar">
      <a class="mark" href="{SITE}/"><span class="dot" aria-hidden="true"></span>Humble Logic Games</a>
      <a class="all" href="{SITE}/">All games <span aria-hidden="true">→</span></a>
    </nav>
    <div class="hero-in">
      <img class="icon" src="{I}{e(slug)}.png" alt="{e(g["short"])} icon" width="128" height="128">
      <p class="genre">{e(p["genre"])}</p>
      <h1>{e(g["name"])}</h1>
      <p class="tagline">{e(p["tagline"])}</p>
      {play}
      <div class="stores" id="stores">
      {store_buttons(g, A)}
      </div>
    </div>
  </header>
  <main class="body">
    {video_block(p, g)}
    <section class="about">
      {about}
    </section>
    <section>
      <h2>How to play</h2>
      <ol class="steps">
        {steps}
      </ol>
    </section>
    <section>
      <h2>Features</h2>
      <ul class="feats">
        {feats}
      </ul>
    </section>
    {support}
    <section class="more-wrap">
      <h2>More from Humble Logic Games</h2>
      <ul class="more">
      {more_games(slug, games, pages, I)}
      </ul>
    </section>
  </main>
  <footer class="foot">
    <nav>
      <a href="{SITE}/">Humble Logic Games</a>
      <a href="{privacy}">Privacy</a>
      <a href="{SITE}/docs/termsofservice">Terms</a>
      <a href="mailto:humblelogicgames@gmail.com">humblelogicgames@gmail.com</a>
    </nav>
    <p>© 2020–2026 Humble Logic Games</p>
  </footer>
  <script src="{A}sub.js"></script>
</body>
</html>
'''


def build(slugs=None):
    games, pages = load()
    here = Path(__file__).resolve().parent
    for slug, p in pages.items():
        if slugs and slug not in slugs:
            continue
        if slug not in games:
            sys.exit(f"{slug}: missing in _data/games.yml")
        d = OUT / p["host"]
        (d / "assets/icons").mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(slug, games, pages))
        (d / "assets/site.css").unlink(missing_ok=True)
        shutil.copytree(here / "fonts", d / "assets/fonts", dirs_exist_ok=True)
        shutil.copy(here / "sub.css", d / "assets/sub.css")
        shutil.copy(here / "sub.js", d / "assets/sub.js")
        shutil.copytree(here / "badges", d / "assets/badges", dirs_exist_ok=True)
        for s in pages:
            shutil.copy(ROOT / f"assets/icons/{s}.png", d / f"assets/icons/{s}.png")
        inc = ROOT / "_includes/gamepage"
        inc.mkdir(parents=True, exist_ok=True)
        (inc / f"{slug}.html").write_text("{% raw %}" + page(slug, games, pages, root=True) + "{% endraw %}")
        print(f"  {p['host']}.{DOMAIN}  +  {DOMAIN}/games/{slug}/  ←  {slug}")
    a = ROOT / "assets/sub"
    a.mkdir(exist_ok=True)
    shutil.copy(here / "sub.css", a / "sub.css")
    shutil.copy(here / "sub.js", a / "sub.js")
    shutil.copytree(here / "fonts", a / "fonts", dirs_exist_ok=True)
    shutil.copytree(here / "badges", a / "badges", dirs_exist_ok=True)


if __name__ == "__main__":
    build(set(sys.argv[1:]) or None)
