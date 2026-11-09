#!/usr/bin/env python3
"""One-shot, idempotent December 2026 static-asset importer.
Runs only on staging; main is intentionally untouched until separate review/merge.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import urllib.parse
import urllib.request
import zipfile

EXPECTED = {
    "2026-12-01-dust-off-the-leaves": "4a77ed458962fd6b76bb716ee1e4405d3a811c457571efe68be6daa9aca1f93b",
    "2026-12-04-empty-the-saucer": "1ddd704ca8dbc81ede243c06e2b962fc4b5c86e9250f293827b6be50d7cf77bc",
    "2026-12-08-a-cactus-that-blooms-in-winter": "ef0ec4f60db763fb3e340e9e650f598abba5b33b32afc0c9f19eb32b217ae627",
    "2026-12-11-a-cutting-starts-at-a-node": "043bc8fd0193ab22ec6c017d9d8b25ed496f0ae5795f9dcb0da9fb21477eaac4",
    "2026-12-15-give-it-a-way-to-climb": "2ce64f81b1cc62d5d6e3caeea4c162fd7e3b60238239ba51b0ab6ab176a95c61",
    "2026-12-18-the-colour-comes-from-bracts": "443b44dd3fc1156e3c0ecf83ca0fd509a7728c634bd60113c6a6193f87e3fa22",
    "2026-12-22-some-leaves-fold-at-night": "b2d7d342b5b4e0b97b3dd382c8fd36721e9830dc2639901e61e5d17eec5cd4cf",
    "2026-12-25-give-your-terrarium-a-breather": "5bcd310d2ad707637a3acd699eaf79df2f1d50a0edb15946d652ff5993d587cd",
}
INDEX = Path("content/index.json")
SRC = Path("ops/december-import-source.json")

def checked_url(value):
    p = urllib.parse.urlparse(value)
    if p.scheme != "https" or not p.hostname:
        raise ValueError("HTTPS source URL required")
    if not (p.hostname.endswith(".cloudfront.net") or p.hostname == "d2ol7oe51mr4n9.cloudfront.net"):
        raise ValueError("The source URL must be a trusted Higgsfield CDN URL")
    return value

def get_zip(url):
    request = urllib.request.Request(url, headers={"User-Agent": "VerdeVivo-Editorial-Importer/1.0"})
    with urllib.request.urlopen(request, timeout=50) as response:
        payload = response.read(20000000)
    if len(payload) >= 20000000:
        raise ValueError("Archive too large")
    return zipfile.ZipFile(io.BytesIO(payload))

def validate_manifest(manifest, post_id):
    assert manifest["id"] == post_id
    assert manifest["status"] in ("draft", "approved")
    assert manifest["image"] == "social.png"
    assert manifest["publishAt"] == post_id[:10] + "T18:00:00+01:00"
    assert manifest["channels"] == ["bluesky", "mastodon", "youtube", "instagram"]
    assert len(manifest["caption"] + "\n\n" + " ".join("#" + x for x in manifest["hashtags"])) <= 300
    assert len(manifest["altText"]) > 0

def main():
    if os.environ.get("GITHUB_REF_NAME") != "staging/december-2026-eight-posts":
        raise RuntimeError("Import is restricted to isolated staging branch")
    source = json.loads(SRC.read_text(encoding="utf-8"))
    url = checked_url(source["zip_url"])
    zi = get_zip(url)
    previous = json.loads(INDEX.read_text(encoding="utf-8"))
    assert isinstance(previous, list)
    assert len(previous) == len(set(previous))
    pending = []
    for post_id, expected_hash in EXPECTED.items():
        image_name = f"content/{post_id}/social.png"
        manifest_path = Path("content") / post_id / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(manifest, post_id)
        payload = zi.read(image_name)
        digest = hashlib.sha256(payload).hexdigest()
        if digest != expected_hash:
            raise ValueError(f"{post_id} SHA256 mismatch")
        if len(payload) >= 2000000 or payload[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"{post_id} invalid PNG or Bluesky file-size limit")
        w, h = struct.unpack(">II", payload[16:24])
        if (w, h) != (1080, 1080):
            raise ValueError(f"{post_id}: unexpected image dimensions {w}x{h}")
        dest = Path(image_name)
        if dest.exists() and dest.read_bytes() != payload:
            raise ValueError(f"{post_id}: existing image differs; refusing overwrite")
        pending.append((post_id, dest, payload, manifest_path, manifest))
    # All eight archives and manifests are now verified before writing anything.
    for post_id, dest, payload, manifest_path, manifest in pending:
        dest.write_bytes(payload)
        manifest["status"] = "approved"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if post_id not in previous:
            previous.append(post_id)
    if len(previous) > 100 or len(previous) != len(set(previous)):
        raise ValueError("Index length or uniqueness constraint failed")
    INDEX.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
    receipts = [{"id": pid, "sha256": hashlib.sha256(payload).hexdigest(),
                 "size_bytes": len(payload), "status": "staging-validated"}
                for pid, _, payload, _, _ in pending]
    Path("ops/december-2026-staging-verified.json").write_text(
        json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(pending)} December posts; index now contains {len(previous)} IDs (STAGING ONLY)")

if __name__ == "__main__":
    main()
