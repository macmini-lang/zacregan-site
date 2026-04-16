#!/usr/bin/env python3
"""
Regenerate the YouTube blog for zacregan.com.

What this script does on every run:
  1. Pulls the 15 most recent videos from the channel RSS feed.
  2. For each video, creates a SEO/AEO optimized post page at
     blog/<slug>/index.html if no page already exists at that slug.
     Existing posts are never overwritten, so manual edits survive.
  3. Regenerates blog/index.html as a clean grid of all posts the
     script knows about (existing manual posts plus auto-generated).
  4. Regenerates sitemap.xml at the repo root containing the homepage,
     /blog/, and every blog/<slug>/ folder that has an index.html.

No third-party dependencies. Python 3.10 or newer.
"""
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

CHANNEL_ID = "UC5GaAcL0CDVP01lGF-WHhfA"
CHANNEL_URL = f"https://www.youtube.com/channel/{CHANNEL_ID}"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
SITE_URL = "https://zacregan.com"
AUTHOR_NAME = "Zac Regan"

BLOG_DIR = Path("blog")
BLOG_INDEX = BLOG_DIR / "index.html"
SITEMAP = Path("sitemap.xml")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch_videos():
    req = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "Mozilla/5.0 (zacregan.com blog builder)"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    root = ET.fromstring(data)
    videos = []
    for entry in root.findall("atom:entry", NS):
        vid = entry.find("yt:videoId", NS).text
        title = (entry.find("atom:title", NS).text or "").strip()
        published = (entry.find("atom:published", NS).text or "").strip()
        link = entry.find("atom:link", NS).get("href")
        media_group = entry.find("media:group", NS)
        description = ""
        if media_group is not None:
            desc_el = media_group.find("media:description", NS)
            if desc_el is not None and desc_el.text:
                description = desc_el.text.strip()
        videos.append({
            "id": vid,
            "title": title,
            "published": published,
            "youtube_url": link,
            "description": description,
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg",
            "thumbnail_fallback": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "slug": slugify(title),
        })
    return videos


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80] or "video"


def fmt_date(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return ""


def description_to_html(text):
    if not text:
        return ""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in paragraphs:
        escaped = html.escape(p).replace("\n", "<br>")
        escaped = re.sub(
            r"(https?://[^\s<]+)",
            r'<a href="\1" target="_blank" rel="noopener nofollow">\1</a>',
            escaped,
        )
        out.append(f"<p>{escaped}</p>")
    return "\n".join(out)


# Post page template
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_safe} | Zac Regan</title>
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="{canonical}">
    <link rel="icon" type="image/png" href="/logo.png">

    <meta property="og:title" content="{title_safe}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{thumbnail}">
    <meta property="og:video" content="{youtube_url}">
    <meta property="article:published_time" content="{published}">
    <meta property="article:author" content="Zac Regan">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_safe}">
    <meta name="twitter:description" content="{meta_desc}">
    <meta name="twitter:image" content="{thumbnail}">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <script type="application/ld+json">
{schema_blogposting}
    </script>
    <script type="application/ld+json">
{schema_videoobject}
    </script>
    <script type="application/ld+json">
{schema_breadcrumb}
    </script>

    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #FFFFFF; color: #111111;
            -webkit-font-smoothing: antialiased; min-height: 100vh;
            display: flex; flex-direction: column;
        }}
        .bg-dots {{
            position: fixed; inset: 0; z-index: 0; pointer-events: none;
            background-image: radial-gradient(circle, rgba(0,0,0,0.10) 1.2px, transparent 1.2px);
            background-size: 32px 32px;
        }}
        .page {{ position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; }}
        header {{
            padding: 22px 32px; display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,0,0,0.06); background: rgba(255,255,255,0.92); backdrop-filter: blur(10px);
        }}
        header a.logo {{ font-weight: 700; font-size: 1.05rem; color: #111; text-decoration: none; letter-spacing: -0.01em; }}
        header nav a {{ color: #555; text-decoration: none; font-size: 0.95rem; margin-left: 22px; }}
        header nav a:hover {{ color: #111; }}
        article {{ max-width: 760px; margin: 0 auto; padding: 56px 24px 80px; width: 100%; }}
        .crumbs {{ font-size: 0.85rem; color: #777; margin-bottom: 22px; }}
        .crumbs a {{ color: #555; text-decoration: none; }}
        .crumbs a:hover {{ text-decoration: underline; }}
        h1 {{ font-size: 2.1rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.015em; margin-bottom: 14px; }}
        .meta {{ color: #666; font-size: 0.92rem; margin-bottom: 32px; }}
        .meta a {{ color: #444; text-decoration: none; font-weight: 500; }}
        .meta a:hover {{ text-decoration: underline; }}
        .video-embed {{
            position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;
            border-radius: 12px; background: #000; margin-bottom: 36px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }}
        .video-embed iframe {{ position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }}
        .description {{ font-size: 1.02rem; line-height: 1.75; color: #222; }}
        .description p {{ margin-bottom: 18px; }}
        .description a {{ color: #2956c6; word-break: break-word; }}
        .post-cta {{
            margin-top: 48px; padding: 28px 28px; border: 1px solid rgba(0,0,0,0.08); border-radius: 12px;
            display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
        }}
        .post-cta strong {{ font-size: 1.05rem; }}
        .post-cta a {{ color: #2956c6; font-weight: 500; text-decoration: none; }}
        .post-cta a:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-top: 36px; color: #555; text-decoration: none; font-size: 0.95rem; }}
        .back-link:hover {{ color: #111; text-decoration: underline; }}
        footer {{ padding: 32px; text-align: center; color: #888; font-size: 0.85rem; border-top: 1px solid rgba(0,0,0,0.06); }}
        @media (max-width: 640px) {{
            header {{ padding: 16px 18px; }}
            article {{ padding: 36px 18px 60px; }}
            h1 {{ font-size: 1.55rem; }}
        }}
    </style>
</head>
<body>
<div class="bg-dots"></div>
<div class="page">
    <header>
        <a href="/" class="logo">Zac Regan</a>
        <nav>
            <a href="/">Home</a>
            <a href="/blog/">Blog</a>
            <a href="{channel_url}" target="_blank" rel="noopener">YouTube</a>
        </nav>
    </header>

    <article>
        <nav class="crumbs" aria-label="Breadcrumb">
            <a href="/">Home</a> &nbsp;/&nbsp; <a href="/blog/">Blog</a> &nbsp;/&nbsp; <span>{title_safe}</span>
        </nav>

        <h1>{title_safe}</h1>
        <div class="meta">
            By <a href="/">Zac Regan</a> &middot; Published {date_pretty} &middot;
            <a href="{youtube_url}" target="_blank" rel="noopener">Watch on YouTube</a>
        </div>

        <div class="video-embed">
            <iframe
                src="https://www.youtube.com/embed/{video_id}"
                title="{title_safe}"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowfullscreen
                loading="lazy"
            ></iframe>
        </div>

        <div class="description">
{description_html}
        </div>

        <div class="post-cta">
            <strong>Want help scaling your business with paid ads?</strong>
            <span>I run paid advertising for education companies, capital-raising funds, and local businesses at <a href="https://justscale.co" target="_blank" rel="noopener">JustScale</a>.</span>
        </div>

        <a class="back-link" href="/blog/">&larr; Back to all posts</a>
    </article>

    <footer>&copy; {year} Zac Regan. All rights reserved.</footer>
</div>
</body>
</html>
"""


# Index page template
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learn How to Scale with Paid Ads | Zac Regan</title>
    <meta name="description" content="Free content from Zac Regan on scaling high-ticket businesses with paid advertising. New posts auto-published from the YouTube channel.">
    <link rel="canonical" href="https://zacregan.com/blog/">
    <link rel="icon" type="image/png" href="/logo.png">
    <meta property="og:title" content="Learn How to Scale with Paid Ads | Zac Regan">
    <meta property="og:description" content="Free content on scaling high-ticket businesses with paid advertising.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://zacregan.com/blog/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <script type="application/ld+json">
{schema_collection}
    </script>

    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #FFFFFF; color: #111111;
            -webkit-font-smoothing: antialiased; min-height: 100vh;
            display: flex; flex-direction: column;
        }}
        .bg-dots {{
            position: fixed; inset: 0; z-index: 0; pointer-events: none;
            background-image: radial-gradient(circle, rgba(0,0,0,0.10) 1.2px, transparent 1.2px);
            background-size: 32px 32px;
        }}
        .page {{ position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; }}
        header {{
            padding: 22px 32px; display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,0,0,0.06); background: rgba(255,255,255,0.92); backdrop-filter: blur(10px);
        }}
        header a.logo {{ font-weight: 700; font-size: 1.05rem; color: #111; text-decoration: none; letter-spacing: -0.01em; }}
        header nav a {{ color: #555; text-decoration: none; font-size: 0.95rem; margin-left: 22px; }}
        header nav a:hover {{ color: #111; }}
        .hero {{ padding: 64px 32px 28px; max-width: 1180px; margin: 0 auto; width: 100%; }}
        .hero h1 {{ font-size: 2.4rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.15; margin-bottom: 12px; }}
        .hero p {{ color: #555; font-size: 1.02rem; max-width: 640px; line-height: 1.55; }}
        main {{ padding: 24px 32px 80px; max-width: 1180px; margin: 0 auto; width: 100%; }}
        .video-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 26px; }}
        .video-card {{
            display: block; text-decoration: none; color: inherit;
            border-radius: 12px; overflow: hidden;
            background: #fff; border: 1px solid rgba(0,0,0,0.06);
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }}
        .video-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 28px rgba(0,0,0,0.08);
            border-color: rgba(0,0,0,0.12);
        }}
        .thumb-wrap {{ aspect-ratio: 16/9; background: #f3f3f3; overflow: hidden; }}
        .thumb-wrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
        .card-body {{ padding: 14px 16px 16px; }}
        .card-body h2 {{ font-size: 1rem; font-weight: 600; line-height: 1.35; margin-bottom: 6px; }}
        .card-body .date {{ font-size: 0.8rem; color: #777; }}
        footer {{ padding: 32px; text-align: center; color: #888; font-size: 0.85rem; border-top: 1px solid rgba(0,0,0,0.06); }}
        @media (max-width: 640px) {{
            header {{ padding: 16px 18px; }}
            .hero {{ padding: 40px 18px 18px; }}
            .hero h1 {{ font-size: 1.7rem; }}
            main {{ padding: 18px 18px 60px; }}
            .video-grid {{ grid-template-columns: 1fr; gap: 16px; }}
        }}
    </style>
</head>
<body>
<div class="bg-dots"></div>
<div class="page">
    <header>
        <a href="/" class="logo">Zac Regan</a>
        <nav>
            <a href="/">Home</a>
            <a href="{channel_url}" target="_blank" rel="noopener">YouTube</a>
        </nav>
    </header>

    <section class="hero">
        <h1>Learn how to scale with paid ads</h1>
        <p>Free content on scaling high-ticket businesses with paid advertising. New posts auto-published the moment a video goes live on the channel.</p>
    </section>

    <main>
        <div class="video-grid">
{cards}
        </div>
    </main>

    <footer>&copy; {year} Zac Regan. All rights reserved. &middot; Last updated {updated}</footer>
</div>
</body>
</html>
"""


def write_post_page(video):
    slug = video["slug"]
    post_dir = BLOG_DIR / slug
    post_path = post_dir / "index.html"
    if post_path.exists():
        return False  # never overwrite existing posts

    title_safe = html.escape(video["title"])
    canonical = f"{SITE_URL}/blog/{slug}/"
    description = video["description"] or video["title"]
    meta_desc = html.escape(description[:155].rsplit(" ", 1)[0] + ("…" if len(description) > 155 else ""))
    description_html_block = description_to_html(description)
    date_pretty = fmt_date(video["published"])

    blogposting = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": video["title"],
        "datePublished": video["published"],
        "dateModified": video["published"],
        "author": {"@type": "Person", "name": AUTHOR_NAME, "url": SITE_URL + "/"},
        "publisher": {"@type": "Organization", "name": "Zac Regan", "logo": {"@type": "ImageObject", "url": SITE_URL + "/logo.png"}},
        "image": video["thumbnail"],
        "url": canonical,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "description": description[:300],
    }
    videoobject = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": video["title"],
        "description": description[:500] or video["title"],
        "thumbnailUrl": [video["thumbnail"], video["thumbnail_fallback"]],
        "uploadDate": video["published"],
        "contentUrl": video["youtube_url"],
        "embedUrl": f"https://www.youtube.com/embed/{video['id']}",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE_URL + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": video["title"], "item": canonical},
        ],
    }

    out = POST_TEMPLATE.format(
        title_safe=title_safe,
        meta_desc=meta_desc,
        canonical=canonical,
        thumbnail=video["thumbnail"],
        youtube_url=video["youtube_url"],
        published=video["published"],
        video_id=video["id"],
        date_pretty=date_pretty,
        description_html=description_html_block,
        channel_url=CHANNEL_URL,
        year=datetime.now(timezone.utc).year,
        schema_blogposting=json.dumps(blogposting, indent=2),
        schema_videoobject=json.dumps(videoobject, indent=2),
        schema_breadcrumb=json.dumps(breadcrumb, indent=2),
    )
    post_dir.mkdir(parents=True, exist_ok=True)
    post_path.write_text(out, encoding="utf-8")
    return True


def collect_all_posts():
    """Return list of dicts for every blog/<slug>/index.html on disk.
    Reads each file once to extract title, video id, thumbnail, and date so the
    index page can render real data for posts that aren't in the current RSS."""
    posts = []
    if not BLOG_DIR.exists():
        return posts
    for child in sorted(BLOG_DIR.iterdir()):
        index_path = child / "index.html"
        if not (child.is_dir() and index_path.exists()):
            continue
        mtime = datetime.fromtimestamp(index_path.stat().st_mtime, tz=timezone.utc)
        try:
            content = index_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""

        title_match = re.search(r"<title>([^<]+)</title>", content)
        title = (
            title_match.group(1).replace(" | Zac Regan", "").strip()
            if title_match else humanize_slug(child.name)
        )
        vid_match = re.search(r"i\.ytimg\.com/vi/([A-Za-z0-9_-]+)/", content)
        video_id = vid_match.group(1) if vid_match else None
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

        date_match = (
            re.search(r'"datePublished"\s*:\s*"([^"]+)"', content)
            or re.search(r'"uploadDate"\s*:\s*"([^"]+)"', content)
        )
        published = date_match.group(1) if date_match else mtime.isoformat()

        posts.append({
            "slug": child.name,
            "mtime": mtime,
            "title": title,
            "video_id": video_id,
            "thumbnail": thumbnail,
            "published": published,
        })
    return posts


def write_index(videos):
    """Render blog/index.html with cards for the latest 15 RSS videos plus
    any additional existing posts on disk (older posts). Existing posts use
    metadata extracted from their HTML so titles and thumbnails are accurate."""
    # Map of slug -> card data, using current RSS data when available (most accurate).
    by_slug = {}
    for v in videos:
        by_slug[v["slug"]] = {
            "slug": v["slug"],
            "title": v["title"],
            "thumbnail": v["thumbnail"],
            "published": v["published"],
        }
    # Merge in disk-only posts using metadata extracted from their HTML files.
    for p in collect_all_posts():
        if p["slug"] not in by_slug:
            by_slug[p["slug"]] = {
                "slug": p["slug"],
                "title": p["title"],
                "thumbnail": p["thumbnail"],
                "published": p["published"],
            }

    # Sort newest first by published date.
    posts_sorted = sorted(by_slug.values(), key=lambda x: x["published"], reverse=True)

    cards = []
    for p in posts_sorted:
        title_safe = html.escape(p["title"])
        slug = p["slug"]
        date = fmt_date(p["published"])
        thumb = html.escape(p["thumbnail"]) if p["thumbnail"] else ""
        thumb_html = (
            f'<div class="thumb-wrap"><img src="{thumb}" alt="{title_safe}" loading="lazy"></div>'
            if thumb else
            '<div class="thumb-wrap"></div>'
        )
        cards.append(
            f'        <a class="video-card" href="/blog/{slug}/">\n'
            f'            {thumb_html}\n'
            f'            <div class="card-body">\n'
            f'                <h2>{title_safe}</h2>\n'
            f'                <span class="date">{date}</span>\n'
            f'            </div>\n'
            f'        </a>'
        )

    schema_collection = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Zac Regan Blog",
        "url": f"{SITE_URL}/blog/",
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": p["title"],
                "url": f"{SITE_URL}/blog/{p['slug']}/",
                "datePublished": p["published"],
            }
            for p in posts_sorted
        ],
    }

    out = INDEX_TEMPLATE.format(
        cards="\n".join(cards),
        channel_url=CHANNEL_URL,
        year=datetime.now(timezone.utc).year,
        updated=datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC"),
        schema_collection=json.dumps(schema_collection, indent=2),
    )
    BLOG_INDEX.parent.mkdir(parents=True, exist_ok=True)
    BLOG_INDEX.write_text(out, encoding="utf-8")


def humanize_slug(slug):
    return " ".join(w.capitalize() for w in slug.split("-"))


def write_sitemap():
    """Regenerate sitemap.xml at the repo root."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [
        (f"{SITE_URL}/", today, "1.0"),
        (f"{SITE_URL}/blog/", today, "0.9"),
    ]
    for p in collect_all_posts():
        lastmod = p["mtime"].strftime("%Y-%m-%d")
        urls.append((f"{SITE_URL}/blog/{p['slug']}/", lastmod, "0.7"))

    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority in urls:
        body.append("  <url>")
        body.append(f"    <loc>{html.escape(loc)}</loc>")
        body.append(f"    <lastmod>{lastmod}</lastmod>")
        body.append(f"    <priority>{priority}</priority>")
        body.append("  </url>")
    body.append("</urlset>")
    SITEMAP.write_text("\n".join(body) + "\n", encoding="utf-8")


def main():
    videos = fetch_videos()
    if not videos:
        raise SystemExit("No videos returned from RSS feed.")

    new_post_count = 0
    for v in videos:
        if write_post_page(v):
            new_post_count += 1

    write_index(videos)
    write_sitemap()

    print(f"Fetched {len(videos)} videos from RSS.")
    print(f"Created {new_post_count} new post page(s); existing posts preserved.")
    print(f"Regenerated {BLOG_INDEX} and {SITEMAP}.")


if __name__ == "__main__":
    main()
