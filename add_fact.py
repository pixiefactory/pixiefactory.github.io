#!/usr/bin/env python3
"""Add (or update) a Pixie's Factory fact page and rebuild the home grid + sitemap.

Usage:
  python3 add_fact.py ../upload-fun-friday.md --video ../fun-friday.mp4 --date 2026-10-16 \
      [--script ../script-fun-friday.json] [--slug bananas-are-berries] [--frame 3] [--youtube-id ID]
  python3 add_fact.py --rebuild      # just regenerate home page, fact pages and sitemap

To add a YouTube ID later, edit the one line `"youtube_id": ""` for that fact in facts.json and run
--rebuild, OR edit the single `data-youtube-id=""` line in the fact's HTML page.
"""
import argparse, datetime, html, json, os, re, subprocess, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json")))
FACTS = os.path.join(HERE, "facts.json")
E = html.escape
DAYS = [("Monday","Mystery Monday","Puzzles, riddles and unsolved oddities"),
        ("Tuesday","Tech Tuesday","Gadgets, inventions and how stuff works"),
        ("Wednesday","Weird Wednesday","The strangest true facts about our world"),
        ("Thursday","Throwback Thursday","History facts that bend your brain"),
        ("Friday","Fun Friday","Silly, surprising everyday facts"),
        ("Saturday","Space Saturday","Planets, stars and the cosmos"),
        ("Sunday","Science Sunday","Cool science, explained simply")]

def load():
    return json.load(open(FACTS)) if os.path.exists(FACTS) else []

def save(facts):
    json.dump(sorted(facts, key=lambda f: f["date"]), open(FACTS, "w"), indent=2, ensure_ascii=False)

def parse_upload(path):
    t = open(path, encoding="utf-8").read()
    sec = {m.group(1).strip().lower(): m.group(2).strip()
           for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", t, re.S | re.M)}
    title = sec["title"].splitlines()[0].strip()
    desc = sec.get("description", "")
    sources = re.findall(r"https?://\S+", desc)
    body = desc.split("Sources:")[0].strip()
    hashtags = re.findall(r"#(\w+)", desc)
    tags = [x.strip() for x in sec.get("tags", "").split(",") if x.strip()]
    m = re.search(r"#(\w+)\s*$", title)
    theme = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", m.group(1)) if m else ""
    clean = re.sub(r"\s*#\w+\s*$", "", title).strip()
    return dict(title=clean, full_title=title, theme=theme, summary=body, sources=sources, tags=tags, hashtags=hashtags)

def parse_script(path):
    if not path: return []
    if path.endswith(".json"):
        lines = [x["text"] for x in json.load(open(path, encoding="utf-8"))]
    else:
        lines = [l.strip() for l in open(path, encoding="utf-8") if l.strip()]
    # drop the intro and outro lines (greeting / "come back tomorrow")
    return [l for l in lines if not re.match(r"(Hi, I'm Pixie|Come back tomorrow)", l)]

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:60]

def make_thumb(video, slug, t):
    out = os.path.join(HERE, "img", f"{slug}.jpg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
                    "-vf", "scale=540:-2", "-q:v", "4", out], check=True)
    return f"img/{slug}.jpg"

def nice_date(d):
    return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")

def head(title, desc, path, image, og_type="website", extra=""):
    url = CFG["base_url"].rstrip("/") + "/" + path
    img = CFG["base_url"].rstrip("/") + "/" + image
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{E(CFG['site_name'])}"><meta property="og:type" content="{og_type}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#2a1052">
<link rel="icon" href="/img/favicon.png"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<link rel="preload" href="/fonts/LuckiestGuy-Regular.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/style.css">
{extra}</head><body>
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/img/favicon.png" alt="" width="36" height="36">Pixie's Factory</a>
<nav><a href="/#facts">Facts</a><a href="/about.html">About</a><a href="{CFG['channel_url']}" rel="noopener">YouTube</a></nav></div></header>
"""

FOOT = """<footer><div class="wrap"><p>© {y} Pixie's Factory · <a href="{ch}">YouTube @pixiesfactory</a> · <a href="/about.html">About</a></p>
<p>Pixie and her voice are made with AI tools. Every fact is checked against real sources.</p></div></footer>
</body></html>"""

def foot(): return FOOT.format(y=datetime.date.today().year, ch=CFG["channel_url"])

def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>\n"

def card(f):
    return f"""<a class="card" href="/facts/{f['slug']}.html"><img src="/{f['thumb']}" alt="{E(f['title'])}" width="540" height="960" loading="lazy">
<div class="meta"><span class="tag">{E(f['theme'])}</span><h3>{E(f['title'])}</h3><small>{nice_date(f['date'])}</small></div></a>"""

def render_fact(f):
    base = CFG["base_url"].rstrip("/")
    desc = re.sub(r"\s+", " ", re.sub(r"[^\w\s.,!?'’—:;()-]", "", f["summary"])).strip()
    desc = (desc[:152].rsplit(" ", 1)[0] + "…") if len(desc) > 155 else desc
    page_title = f"{f['title']} | {f['theme']} Fun Fact | Pixie's Factory"
    srcs = "\n".join(f'<li><a href="{E(u)}" rel="noopener">{E(urlparse(u).netloc.replace("www.",""))}{E(urlparse(u).path)}</a></li>' for u in f["sources"])
    paras = f.get("script", [])
    hook = paras[0] if paras else ""
    body = "".join(f"<p>{E(p)}</p>\n" for p in paras[1:])
    yid = f.get("youtube_id", "")
    obj = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": f["title"], "description": desc, "datePublished": f["date"],
         "image": base + "/" + f["thumb"], "author": {"@type": "Organization", "name": "Pixie's Factory", "url": CFG["channel_url"]},
         "publisher": {"@type": "Organization", "name": "Pixie's Factory", "logo": {"@type": "ImageObject", "url": base + "/img/pixie-wink-400.png"}},
         "mainEntityOfPage": f"{base}/facts/{f['slug']}.html", "keywords": ", ".join(f["tags"]), "citation": f["sources"]},
        {"@type": "VideoObject", "name": f["full_title"], "description": f["summary"], "thumbnailUrl": base + "/" + f["thumb"],
         "uploadDate": f["date"], **({"embedUrl": f"https://www.youtube.com/embed/{yid}", "contentUrl": f"https://www.youtube.com/shorts/{yid}"} if yid else {})},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": base + "/"},
            {"@type": "ListItem", "position": 2, "name": f["title"], "item": f"{base}/facts/{f['slug']}.html"}]}]}
    out = head(page_title, desc, f"facts/{f['slug']}.html", f["thumb"], "article", ld(obj)) + f"""
<main class="wrap"><article>
<span class="tag">{E(f['theme'])} · {nice_date(f['date'])}</span>
<h1>{E(f['title'])}</h1>
<p class="lede">{E(hook)}</p>
<div class="short"
  data-youtube-id="{E(yid)}"
  data-title="{E(f['full_title'])}">
  <img src="/{f['thumb']}" alt="Frame from the Pixie's Factory Short: {E(f['title'])}" width="540" height="960">
  <div class="ph"><p>🎬 The Short is coming soon on YouTube!</p><a class="btn" href="{CFG['subscribe_url']}" rel="noopener">Subscribe</a></div>
</div>
<h2>The fact</h2>
<p>{E(f['summary'])}</p>
<h2>What Pixie says</h2>
{body}
<div class="box"><h2>Sources</h2><ul class="sources">{srcs}</ul></div>
<div class="cta"><p><b>Want a fun fact every day?</b></p><a class="btn" href="{CFG['subscribe_url']}" rel="noopener">Subscribe on YouTube</a></div>
<p><a href="/#facts">← More facts</a></p>
</article></main>
<script>
document.querySelectorAll('.short[data-youtube-id]').forEach(function(d){{var id=d.dataset.youtubeId;if(!id)return;
d.innerHTML='<iframe src="https://www.youtube-nocookie.com/embed/'+id+'" title="'+d.dataset.title.replace(/"/g,'&quot;')+'" loading="lazy" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>';}});
</script>
""" + foot()
    open(os.path.join(HERE, "facts", f["slug"] + ".html"), "w", encoding="utf-8").write(out)

def render_index(facts):
    base = CFG["base_url"].rstrip("/")
    latest = sorted(facts, key=lambda f: f["date"], reverse=True)
    cards = "\n".join(card(f) for f in latest)
    days = "\n".join(f"<li><b>{t}</b><span>{d[:3]} · {s}</span></li>" for d, t, s in DAYS)
    desc = "Pixie the robot serves up a true, source-checked fun fact every day in a YouTube Short: Weird Wednesday, Throwback Thursday, Space Saturday and more."
    obj = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": "Pixie's Factory", "url": base + "/"},
        {"@type": "Organization", "name": "Pixie's Factory", "url": base + "/", "logo": base + "/img/pixie-wink-400.png", "sameAs": [CFG["channel_url"]]},
        {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{base}/facts/{f['slug']}.html", "name": f["title"]} for i, f in enumerate(latest)]}]}
    out = head(f"Pixie's Factory | {CFG['tagline']}", desc, "", "img/og-default.jpg", "website", ld(obj)) + f"""
<main>
<section class="hero"><div class="wrap">
<img class="pixie" src="/img/pixie-wink-400.png" alt="Pixie, a pink and purple robot with a winking screen face" width="200" height="200" fetchpriority="high">
<h1>Pixie's Factory</h1><p>{E(CFG['tagline'])}</p>
<a class="btn" href="{CFG['subscribe_url']}" rel="noopener">▶ Subscribe on YouTube</a>
</div></section>
<section id="facts"><div class="wrap"><h2>Latest facts</h2><div class="grid">
<!-- FACTS:START (generated by add_fact.py) -->
{cards}
<!-- FACTS:END -->
</div></div></section>
<section><div class="wrap"><h2>A theme for every day</h2><ul class="days">
{days}
</ul></div></section>
<section class="cta"><div class="wrap"><h2>New Short every day!</h2><a class="btn alt" href="{CFG['channel_url']}" rel="noopener">Visit the channel</a></div></section>
</main>
""" + foot()
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(out)

def render_sitemap(facts):
    base = CFG["base_url"].rstrip("/")
    newest = max([f["date"] for f in facts] or [datetime.date.today().isoformat()])
    urls = [(base + "/", newest), (base + "/about.html", newest)] + [(f"{base}/facts/{f['slug']}.html", f["date"]) for f in facts]
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    x += "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
    open(os.path.join(HERE, "sitemap.xml"), "w").write(x)
    open(os.path.join(HERE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")

def rebuild(facts):
    for f in facts: render_fact(f)
    render_index(facts); render_sitemap(facts)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("upload", nargs="?"); ap.add_argument("--video"); ap.add_argument("--date")
    ap.add_argument("--script"); ap.add_argument("--slug"); ap.add_argument("--frame", type=float, default=3.0)
    ap.add_argument("--youtube-id", default=""); ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    facts = load()
    if a.upload:
        if not (a.video and a.date): sys.exit("--video and --date are required with an upload file")
        f = parse_upload(a.upload)
        f["date"] = a.date
        f["slug"] = a.slug or slugify(f["title"])
        f["script"] = parse_script(a.script)
        f["thumb"] = make_thumb(a.video, f["slug"], a.frame)
        old = next((x for x in facts if x["slug"] == f["slug"]), None)
        f["youtube_id"] = a.youtube_id or (old or {}).get("youtube_id", "")
        facts = [x for x in facts if x["slug"] != f["slug"]] + [f]
        save(facts); print("added", f["slug"])
    elif not a.rebuild:
        ap.print_help(); return
    rebuild(load())
    print("rebuilt", len(load()), "fact pages, index.html, sitemap.xml, robots.txt")

if __name__ == "__main__": main()
