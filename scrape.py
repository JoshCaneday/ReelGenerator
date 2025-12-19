#!/usr/bin/env python3
"""
Download openly-licensed animation/cartoon videos from Wikimedia Commons.

Examples:
  python download_cc_cartoons.py --query "cartoon animation" --limit 10 --out ./videos
  python download_cc_cartoons.py --query "public domain animation" --limit 5
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://commons.wikimedia.org/w/api.php"

SESSION = requests.Session()
SESSION.headers.update({
    # Put something identifying here; Wikimedia wants contact info if possible.
    "User-Agent": "Python requests",
    "Accept": "application/json",
})
retries = Retry(
    total=5,
    backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
SESSION.mount("https://", HTTPAdapter(max_retries=retries))
VIDEO_EXTS = {".webm", ".ogv", ".mp4"}  # commons most commonly serves webm/ogv

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-. ]+", "_", name).strip()
    return re.sub(r"\s+", " ", name)

def get_json(params: dict, timeout=30) -> dict:
    params = dict(params)
    params["format"] = "json"
    r = SESSION.get(API, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def search_files(query: str, limit: int):
    """
    Use MediaWiki 'list=search' to find file pages on Commons.
    """
    results = []
    srlimit = min(50, max(1, limit))
    sroffset = 0

    while len(results) < limit:
        data = get_json({
            "action": "query",
            "list": "search",
            "srsearch": f'{query} filetype:video',
            "srlimit": srlimit,
            "sroffset": sroffset,
            "srnamespace": 6,  # File:
        })

        batch = data.get("query", {}).get("search", [])
        if not batch:
            break

        for item in batch:
            title = item.get("title", "")
            if title.startswith("File:"):
                results.append(title)
                if len(results) >= limit:
                    break

        sroffset += len(batch)

    return results[:limit]

def get_file_info(file_title: str) -> dict:
    """
    Fetch download URL + attribution/license-ish fields if available.
    Commons' licensing is complex; we grab what we can safely:
    - canonical file page url
    - direct download url
    - uploader username
    - description URL
    """
    data = get_json({
        "action": "query",
        "prop": "imageinfo|info",
        "titles": file_title,
        "iiprop": "url|user|extmetadata|mime",
        "inprop": "url",
    })

    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    if "missing" in page:
        raise RuntimeError(f"Missing file page: {file_title}")

    imageinfo = (page.get("imageinfo") or [{}])[0]
    direct_url = imageinfo.get("url")
    mime = imageinfo.get("mime", "")
    extmeta = imageinfo.get("extmetadata") or {}

    # Try to extract structured licensing/attribution (best-effort; varies by file)
    def meta_field(key):
        v = extmeta.get(key, {})
        if isinstance(v, dict):
            return v.get("value")
        return None

    file_page_url = page.get("fullurl")

    return {
        "title": page.get("title"),
        "file_page_url": file_page_url,
        "direct_url": direct_url,
        "mime": mime,
        "uploader": imageinfo.get("user"),
        "artist": meta_field("Artist"),
        "credit": meta_field("Credit"),
        "license_short_name": meta_field("LicenseShortName"),
        "license_url": meta_field("LicenseUrl"),
        "usage_terms": meta_field("UsageTerms"),
        "attribution_required": meta_field("AttributionRequired"),
        "source": meta_field("ImageDescription") or meta_field("ObjectName"),
    }

def download(url: str, out_path: str, timeout=60):
    headers = {
        # Wikimedia sometimes expects a decent UA on uploads too
        "User-Agent": SESSION.headers.get("User-Agent", "ReelGenerator/1.0"),
        # Often helps with CDN/WAF rules
        "Referer": "https://commons.wikimedia.org/",
        "Accept": "*/*",
    }

    with SESSION.get(url, stream=True, timeout=timeout, headers=headers) as r:
        r.raise_for_status()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Search query, e.g. 'cartoon animation' or 'public domain animation'")
    ap.add_argument("--limit", type=int, default=10, help="Max number of videos to download")
    ap.add_argument("--out", default="./commons_videos", help="Output folder")
    ap.add_argument("--min-license", default="", help="Optional: only keep files whose LicenseShortName contains this substring, e.g. 'Public domain' or 'CC BY'")
    args = ap.parse_args()

    titles = search_files(args.query, args.limit * 3)  # overfetch to allow filtering
    if not titles:
        print("No results found.")
        return 1

    downloaded = 0
    for t in titles:
        if downloaded >= args.limit:
            break

        try:
            info = get_file_info(t)
            url = info.get("direct_url")
            if not url:
                continue

            # Filter to likely video file extensions
            path = urlparse(url).path
            ext = os.path.splitext(path)[1].lower()
            if ext not in VIDEO_EXTS:
                continue

            lic = (info.get("license_short_name") or "") + " " + (info.get("usage_terms") or "")
            if args.min_license and args.min_license.lower() not in lic.lower():
                continue

            base = safe_filename(info["title"].replace("File:", ""))
            video_path = os.path.join(args.out, base)
            meta_path = video_path + ".json"

            # If the title has no extension, add from URL
            if not os.path.splitext(video_path)[1]:
                video_path += ext

            print(f"Downloading: {info['title']} -> {video_path}")
            download(url, video_path)

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False, indent=2)

            downloaded += 1

        except Exception as e:
            print(f"Skipping {t}: {e}", file=sys.stderr)
            continue

    print(f"\nDone. Downloaded {downloaded} video(s) to: {os.path.abspath(args.out)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
