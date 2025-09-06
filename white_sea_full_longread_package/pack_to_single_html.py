#!/usr/bin/env python3
"""
Inline local images into an HTML as data: URIs to produce a single-file page.
Usage:
  python pack_to_single_html.py input.html output.single.html

Notes:
- Only local relative paths are inlined. Absolute http(s) URLs are kept as-is.
- Supports common raster formats: jpg/jpeg/png/webp/gif, and svg.
- Leaves missing files unchanged and prints a warning.
"""
import sys, os, base64, mimetypes
from bs4 import BeautifulSoup

def to_data_uri(path):
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        # Fallback to binary octet-stream (rarely used by browsers as image)
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        b = f.read()
    b64 = base64.b64encode(b).decode("ascii")
    return f"data:{mime};base64,{b64}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python pack_to_single_html.py input.html output.single.html")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    if not os.path.exists(in_path):
        print(f"Error: input not found: {in_path}")
        sys.exit(2)

    with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    base_dir = os.path.dirname(os.path.abspath(in_path))

    changed = 0
    skipped = 0

    # Process <img> tags
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        if src.startswith("http://") or src.startswith("https://"):
            skipped += 1
            continue
        # Resolve path
        local_path = os.path.normpath(os.path.join(base_dir, src))
        if not os.path.exists(local_path):
            print(f"[warn] file not found for <img src='{src}'> -> {local_path}")
            skipped += 1
            continue
        try:
            img["src"] = to_data_uri(local_path)
            changed += 1
        except Exception as e:
            print(f"[warn] failed to inline {local_path}: {e}")
            skipped += 1

        # Also try data-full (if present)
        data_full = img.get("data-full")
        if data_full and not data_full.startswith(("http://","https://","data:")):
            full_path = os.path.normpath(os.path.join(base_dir, data_full))
            if os.path.exists(full_path):
                try:
                    img["data-full"] = to_data_uri(full_path)
                except Exception as e:
                    print(f"[warn] failed to inline data-full {full_path}: {e}")

    # Optional: inline <source srcset> or img srcset — skipping for simplicity
    # Optional: inline CSS background images — could be added if needed

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"Done. Inlined images: {changed}, skipped: {skipped}")
    print(f"Written: {out_path}")

if __name__ == "__main__":
    main()
