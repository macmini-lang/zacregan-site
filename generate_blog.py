#!/usr/bin/env python3
"""Fetch YouTube RSS feed and generate blog posts for zacregan.com"""

import re
import urllib.request
from pathlib import Path
from datetime import datetime

CHANNEL_ID = "UC5GaAcL0CDVP01lGF-WHhfA"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
BLOG_DIR = Path("blog")


def slugify(title):
    s = title.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def fetch_videos():
    with urllib.request.urlopen(FEED_URL) as resp:
        raw = resp.read().decode()

    entries = re.findall(
        r'<yt:videoId>([^<]+)</yt:videoId>\s*<[^>]*>[^<]*</[^>]*>\s*<title>([^<]+)</title>\s*<link[^/]*/>\s*<[^>]*>[^<]*</[^>]*>\s*<published>([^<]+)</published>',
        raw
    )

    if not entries:
        ids = re.findall(r'<yt:videoId>([^<]+)</yt:videoId>', raw)
        titles = re.findall(r'<title>([^<]+)</title>', raw)[1:]
        dates = re.findall(r'<published>([^<]+)</published>', raw)[1:]
        entries = list(zip(ids, titles, dates))

    videos = []
    for vid, title, pub in entries:
        title = title.replace('&quot;', '"').replace('&amp;', '&')
        videos.append({'id': vid, 'title': title, 'date': pub[:10]})
    return videos


def make_post(v):
    slug = slugify(v['title'])
    title_cap = v['title'].title()
    date_formatted = datetime.strptime(v['date'], '%Y-%m-%d').strftime('%B %d, %Y')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_cap} | Zac Regan</title>
    <meta name="description" content="{title_cap} — Zac Regan breaks down what you need to know about scaling high-ticket products and services with paid advertising.">
    <meta property="og:title" content="{title_cap} | Zac Regan">
    <meta property="og:description" content="{title_cap} — scaling high-ticket with paid ads.">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://zacregan.com/blog/{slug}/">
    <meta property="og:image" content="https://i.ytimg.com/vi/{v['id']}/maxresdefault.jpg">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="https://zacregan.com/blog/{slug}/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #FFFFFF; color: #111111; line-height: 1.6; -webkit-font-smoothing: antialiased; }}
        a {{ color: #111111; }}
        .bg-dots {{ position: fixed; inset: 0; z-index: 0; pointer-events: none; background-image: radial-gradient(circle, rgba(0,0,0,0.12) 1.2px, transparent 1.2px); background-size: 32px 32px; }}
        .page {{ position: relative; z-index: 1; }}
        .nav {{ padding: 18px 0; border-bottom: 2px solid rgba(0,0,0,0.08); }}
        .nav .container {{ display: flex; align-items: center; justify-content: space-between; max-width: 720px; margin: 0 auto; padding: 0 20px; }}
        .nav img {{ height: 44px; width: auto; }}
        .nav a.back {{ font-size: 0.82rem; color: #555; text-decoration: none; }}
        .nav a.back:hover {{ color: #111; }}
        .container {{ max-width: 720px; margin: 0 auto; padding: 0 20px; }}
        .post-header {{ padding: 48px 0 24px; }}
        .post-header h1 {{ font-size: clamp(1.6rem, 4vw, 2.2rem); font-weight: 700; letter-spacing: -0.03em; line-height: 1.2; margin-bottom: 8px; }}
        .post-date {{ font-size: 0.8rem; color: #999; }}
        .video-embed {{ margin: 24px 0 32px; position: relative; width: 100%; aspect-ratio: 16/9; border-radius: 10px; overflow: hidden; background: #111; }}
        .video-embed iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }}
        .post-body {{ padding: 0 0 60px; }}
        .post-body p {{ font-size: 1rem; color: #333; line-height: 1.8; margin-bottom: 16px; }}
        .cta-box {{ background: #111; color: #fff; border-radius: 10px; padding: 32px; text-align: center; margin: 40px 0; }}
        .cta-box p {{ color: rgba(255,255,255,0.7); font-size: 0.95rem; margin-bottom: 16px; }}
        .cta-box a {{ display: inline-block; background: #fff; color: #111; padding: 12px 28px; border-radius: 8px; font-weight: 600; font-size: 0.9rem; text-decoration: none; }}
        .footer {{ background: #000; padding: 24px 0; text-align: center; }}
        .footer p {{ font-size: 0.68rem; color: rgba(255,255,255,0.35); }}
        @media (max-width: 600px) {{ .post-header {{ padding: 32px 0 16px; }} .post-header h1 {{ font-size: 1.4rem; }} }}
    </style>
</head>
<body>
<div class="bg-dots"></div>
<div class="page">
    <nav class="nav">
        <div class="container">
            <a href="/"><img src="/logo.png" alt="Zac Regan"></a>
            <a href="/blog/" class="back">All posts</a>
        </div>
    </nav>
    <article>
        <div class="container">
            <div class="post-header">
                <h1>{title_cap}</h1>
                <span class="post-date">{date_formatted}</span>
            </div>
            <div class="video-embed">
                <iframe src="https://www.youtube.com/embed/{v['id']}" title="{title_cap}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe>
            </div>
            <div class="post-body">
                <p>In this video, I break down {v['title']}. If you're scaling a high-ticket product or service with paid ads, this is something you need to understand.</p>
                <p>Watch the full video above for the complete breakdown.</p>
                <div class="cta-box">
                    <p>Want the SOPs, funnels, and coaching behind everything I teach?</p>
                    <a href="https://vault.justscale.co">Get access to the vault</a>
                </div>
            </div>
        </div>
    </article>
    <div class="footer">
        <p>&copy; 2026 Zac Regan. All rights reserved.</p>
    </div>
</div>
</body>
</html>'''


def make_index(videos):
    cards = ""
    for v in videos:
        slug = slugify(v['title'])
        title_cap = v['title'].title()
        date_formatted = datetime.strptime(v['date'], '%Y-%m-%d').strftime('%B %d, %Y')
        cards += f'''
            <a href="/blog/{slug}/" class="post-card">
                <img src="https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg" alt="{title_cap}" loading="lazy">
                <div class="post-info">
                    <h2>{title_cap}</h2>
                    <span class="date">{date_formatted}</span>
                </div>
            </a>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog | Zac Regan</title>
    <meta name="description" content="Videos and insights on scaling high-ticket products and services with paid advertising.">
    <link rel="canonical" href="https://zacregan.com/blog/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #FFFFFF; color: #111; -webkit-font-smoothing: antialiased; }}
        a {{ color: inherit; text-decoration: none; }}
        .bg-dots {{ position: fixed; inset: 0; z-index: 0; pointer-events: none; background-image: radial-gradient(circle, rgba(0,0,0,0.12) 1.2px, transparent 1.2px); background-size: 32px 32px; }}
        .page {{ position: relative; z-index: 1; }}
        .nav {{ padding: 18px 0; border-bottom: 2px solid rgba(0,0,0,0.08); }}
        .nav .container {{ display: flex; align-items: center; justify-content: space-between; }}
        .nav img {{ height: 44px; width: auto; }}
        .nav a.back {{ font-size: 0.82rem; color: #555; text-decoration: none; }}
        .nav a.back:hover {{ color: #111; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}
        .blog-header {{ padding: 48px 0 32px; }}
        .blog-header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.03em; }}
        .posts {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; padding-bottom: 60px; }}
        .post-card {{ border: 2px solid rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden; transition: border-color 0.2s, transform 0.15s; }}
        .post-card:hover {{ border-color: rgba(0,0,0,0.3); transform: translateY(-2px); }}
        .post-card img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
        .post-info {{ padding: 16px; }}
        .post-info h2 {{ font-size: 0.95rem; font-weight: 600; line-height: 1.4; margin-bottom: 4px; }}
        .post-info .date {{ font-size: 0.75rem; color: #999; }}
        .footer {{ background: #000; padding: 24px 0; text-align: center; }}
        .footer p {{ font-size: 0.68rem; color: rgba(255,255,255,0.35); }}
        @media (max-width: 600px) {{ .posts {{ grid-template-columns: 1fr; }} .blog-header h1 {{ font-size: 1.5rem; }} }}
    </style>
</head>
<body>
<div class="bg-dots"></div>
<div class="page">
    <nav class="nav">
        <div class="container">
            <a href="/"><img src="/logo.png" alt="Zac Regan"></a>
            <a href="/" class="back">Home</a>
        </div>
    </nav>
    <div class="container">
        <div class="blog-header">
            <h1>Blog</h1>
        </div>
        <div class="posts">{cards}
        </div>
    </div>
    <div class="footer">
        <p>&copy; 2026 Zac Regan. All rights reserved.</p>
    </div>
</div>
</body>
</html>'''


def make_sitemap(videos):
    base = "https://zacregan.com"
    today = datetime.now().strftime('%Y-%m-%d')
    urls = [
        (f'{base}/', today, '1.0'),
        (f'{base}/blog/', today, '0.9'),
    ]
    for v in videos:
        slug = slugify(v['title'])
        urls.append((f'{base}/blog/{slug}/', v['date'], '0.7'))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for loc, mod, pri in urls:
        xml += f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{mod}</lastmod>\n    <priority>{pri}</priority>\n  </url>\n'
    xml += '</urlset>\n'
    return xml


if __name__ == "__main__":
    videos = fetch_videos()
    print(f"Found {len(videos)} videos")

    BLOG_DIR.mkdir(exist_ok=True)

    # Write index
    (BLOG_DIR / "index.html").write_text(make_index(videos))

    # Write individual posts (skip if already exists)
    new_count = 0
    for v in videos:
        slug = slugify(v['title'])
        post_dir = BLOG_DIR / slug
        if not post_dir.exists():
            post_dir.mkdir()
            (post_dir / "index.html").write_text(make_post(v))
            new_count += 1
            print(f"  New: /blog/{slug}/")

    # Always regenerate index (picks up new posts)
    (BLOG_DIR / "index.html").write_text(make_index(videos))

    # Regenerate sitemap
    Path("sitemap.xml").write_text(make_sitemap(videos))
    print(f"Sitemap updated with {len(videos) + 2} URLs")

    print(f"Done. {new_count} new posts. {len(videos)} total.")
