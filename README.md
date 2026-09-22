# VerdeVivo Social Content

Repository sorgente per contenuti social editoriali approvati di VerdeVivo. Ogni pezzo vive in `content/<post-id>/manifest.json` con la grafica approvata `content/<post-id>/social.png`.

## Approval and scheduling

Only manifests with `status: "approved"` may be considered for publication. A maintainer must review the English caption, hashtags, channels, publish time, image, and alternative text before changing a draft to approved. `publishAt` is authoritative and must include a timezone offset. The editorial cadence is Tuesday and Friday at 18:00 Europe/Rome, with at most two distinct content pieces in an ISO week.

The independent Editorial scheduler checks every 15 minutes. It does not wait for Primary comment quotas or Growth sessions. `publishAt` is the earliest permitted publication time, not a provider receipt. Temporary failures and unresolved outcomes remain subject to the Engine's retry/reconciliation policy.

Use a stable, lowercase `id` matching the directory name. Increment `version` for a pre-publication technical revision. Never edit a post after a channel has a confirmed or unresolved publication receipt; create a new post id for a materially revised piece.

## Atomic delivery contract

After the user approves the creative, include these in one commit:

1. `content/<post-id>/manifest.json` conforming to `schema/manifest-v1.json`.
2. The approved `content/<post-id>/social.png`.
3. The id in `content/index.json` (strict array of at most 100 unique valid ids).

The index is authoritative. A folder that is absent from the index is not scheduled. Do not add placeholder posts or fabricate approvals. Image generation and creative review belong to VerdeVivo Social Studio.

## Provider preflight for shared assets

For a post targeting Bluesky, the PNG must not exceed **2,000,000 bytes** (not 2 MiB). The full caption including appended hashtags must fit within **300 graphemes**. Check each selected provider's current official requirements before approving a future delivery; the Engine's larger repository download bound is not a provider upload limit.

Preserve the original approved artwork and branding. Lossless PNG recompression is allowed as a technical size correction only when decoded pixels and color/metadata chunks remain identical, and only before any publication attempt. Record the revision and validation evidence. Do not replace an image with a new AI rendition or silently change captions, dates, or branding.

## Validated first month

Eight approved posts are indexed for 2026-09-22, 2026-09-25, 2026-09-29, 2026-10-02, 2026-10-06, 2026-10-09, 2026-10-13 and 2026-10-16, at 18:00 Europe/Rome, on Bluesky, Mastodon and YouTube. Dates in ids are stable identifiers; the manifest's `publishAt` controls scheduling.

See `ops/editorial-media-validation-20260922.json` for the eight-file size, hash, caption-length and calendar checks. The second PNG was losslessly recompressed from 2,000,596 to 1,950,573 bytes; its manifest is version 2. This evidence validates assets, not social publication receipts.
