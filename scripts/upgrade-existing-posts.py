#!/usr/bin/env python3
"""
One-time upgrade: add BreadcrumbList + standalone VideoObject schema
to every existing blog/<slug>/index.html that doesn't already have them.

Strategy:
  - Extract metadata (title, description, video id, canonical) from each post.
  - Get an accurate uploadDate from the YouTube RSS feed when possible
    (covers the 15 most recent videos), else fall back to the git first-commit
    date for the post folder.
  - Inject two new <script type="application/ld+json"> blocks before </head>.
  - Idempotent: skip files that already contain "BreadcrumbList".
  - Never touches body content or existing schema.
"""
import json
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

CHANNEL_ID = "UC5GaAcL0CDVP01lGF-WHhfA"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
SITE_URL = "https://zacregan.com"
BLOG_DIR = Path("blog")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch_rss_dates():
    """Return {video_id: iso_upload_date} for the 15 most recent uploads."""
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0 (zacregan upgrader)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    root = ET.fromstring(data)
    out = {}
    for entry in root.findall("atom:entry", NS):
        vid = entry.find("yt:videoId", NS).text
        published = (entry.find("atom:published", NS).text or "").strip()
        if vid and published:
            out[vid] = published
    return out


def git_first_date(path_str):
    """ISO datetime of the commit that first added a file, or None."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--reverse", "--format=%aI", "--", path_str],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return out.split("\n")[0] if out else None
    except subprocess.CalledProcessError:
        return None


def extract(content, pattern, group=1, default=""):
    m = re.search(pattern, content)
    return m.group(group) if m else default


def upgrade_post(post_path, rss_dates):
    content = post_path.read_text(encoding="utf-8")
    if "BreadcrumbList" in content:
        return False  # already upgraded

    # Extract metadata
    title_full = extract(content, r"<title>([^<]+)</title>")
    title = title_full.replace(" | Zac Regan", "").strip()
    description = extract(content, r'<meta\s+name="description"\s+content="([^"]+)"')
    canonical = extract(content, r'<link\s+rel="canonical"\s+href="([^"]+)"')
    video_id = extract(content, r"i\.ytimg\.com/vi/([A-Za-z0-9_-]+)/")
    slug = post_path.parent.name

    if not (title and canonical and video_id):
        print(f"  SKIP {slug}: missing required metadata")
        return False

    # Resolve upload date: RSS first, then git first-commit, then sensible default
    upload_date = (
        rss_dates.get(video_id)
        or git_first_date(str(post_path))
        or "2025-01-01T00:00:00+00:00"
    )

    video_obj = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": title,
        "description": description or title,
        "thumbnailUrl": [
            f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        ],
        "uploadDate": upload_date,
        "contentUrl": f"https://www.youtube.com/watch?v={video_id}",
        "embedUrl": f"https://www.youtube.com/embed/{video_id}",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE_URL + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
        ],
    }

    injected = (
        '    <script type="application/ld+json">\n'
        + json.dumps(video_obj, indent=2)
        + "\n    </script>\n"
        + '    <script type="application/ld+json">\n'
        + json.dumps(breadcrumb, indent=2)
        + "\n    </script>\n"
    )

    new_content = content.replace("</head>", injected + "</head>", 1)
    if new_content == content:
        print(f"  SKIP {slug}: no </head> found")
        return False

    post_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    rss_dates = fetch_rss_dates()
    print(f"Loaded {len(rss_dates)} accurate dates from RSS.")

    posts = sorted(BLOG_DIR.glob("*/index.html"))
    upgraded = 0
    skipped = 0
    for p in posts:
        if upgrade_post(p, rss_dates):
            upgraded += 1
        else:
            skipped += 1

    print(f"Done. Upgraded: {upgraded}. Skipped (already done or missing data): {skipped}.")


if __name__ == "__main__":
    main()
