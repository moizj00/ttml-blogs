# blog-queue/

Staging area for the drip publisher (`scripts/drip-publish.py`).

- Queue-ready posts land here as `status: draft` with a `publish_after` date.
- `drip-publish.py` releases the best 3/day -> live REST API -> moves them into `_published/`.
- `_published/` is the archive of already-dripped posts (kept for provenance).
