# TODO

## Phase 1: Fix server import crash
- [ ] Inspect `backend/recommendations/services.py` for invalid characters / accidental markdown injection
- [ ] Replace file with a valid Python implementation (remove ASCII/box-drawing characters and markdown)
- [ ] Re-run Django `manage.py runserver` to confirm URLs import cleanly

## Phase 2: Fix any follow-up runtime issues
- [ ] Start celery worker with correct flags
- [ ] Run a quick Django system check
- [ ] Compile the full `recommendations` app

