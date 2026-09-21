# VerdeVivo Social Content

Repository sorgente per contenuti social editoriali approvati di VerdeVivo. Ogni pezzo vive in `content/<post-id>/manifest.json` con la grafica approvata `content/<post-id>/social.png`.

## Approval and scheduling

Only manifests with `status: "approved"` may be considered for publication. A maintainer must review the English caption, hashtags, channels, publish time, image, and alternative text before changing a draft to approved. `publishAt` is authoritative and must include a timezone offset. The suggested editorial cadence is Tuesday and Friday at 18:00 Europe/Rome, with at most two distinct content pieces in an ISO week; the Engine validates the cadence.

Use a stable, lowercase `id` matching the directory name. Increment `version` when changing a draft. Never edit a post after a channel has a confirmed or unresolved publication receipt; create a new post id for a materially revised piece.

See [`schema/manifest-v1.json`](schema/manifest-v1.json) for the strict manifest contract. This repository starts empty; do not add placeholder posts or generated graphics.
