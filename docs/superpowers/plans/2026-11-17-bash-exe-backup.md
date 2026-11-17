# bash-exe Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deploy an independent five-minute GitHub backup of all upstream Git branches and tags.

**Architecture:** A public controller repository runs a trusted Bash script without checking out upstream files. A repository-scoped SSH deploy key writes into the independent backup, where Actions is disabled.

**Tech Stack:** Git, Bash, Python unittest, GitHub Actions, gh CLI.

**Spec:** ../specs/2026-11-17-bash-exe-backup-design.md

## Global Constraints
- Schedule every 5 minutes; scheduling latency is allowed.
- No pruning or mirroring deletions; fail before pushing on upstream read failures or empty refs.
- Never execute upstream code; never commit secrets.
- Keep controller active with a commit at least every 30 days.

## Review Focus
- An unavailable or empty upstream must leave existing backup refs unchanged.
- Deleted upstream refs must remain available in the backup.
- Force-updated branches/tags must match upstream without dropping untouched refs.
- Upstream workflow files must not execute in the backup repository.
- A no-change poll must skip cloning/pushing; failed sync must still permit controller keepalive.

### Task 1: Tested non-destructive sync
**Files:** scripts/sync.sh; tests/test_sync.py.
**Interfaces:** `bash scripts/sync.sh SOURCE_URL TARGET_URL`; zero on success/no change, nonzero on read/push failure.
- [x] Write unittest fixtures using disposable local Git repos; test branches, annotated tags, history, new commits, forced changes, retained deletions, no-change, missing/empty upstream.
- [x] Run `python -I -m unittest discover -s tests -v` and observe missing-script failures.
- [x] Implement read-before-write, temporary bare fetch and explicit heads/tags atomic push; no checkout, no prune.
- [x] Run the tests and Bash syntax validation; require all passing.

### Task 2: Deploy and verify
**Files:** .github/workflows/sync.yml; README.md; .gitignore.
**Interfaces:** secret BACKUP_SSH_KEY; trusted GitHub SSH host key; upstream/destination fixed in workflow.
- [x] Write five-minute/manual workflow with pinned checkout, job concurrency, timeouts, minimal permissions, SSH secret cleanup, monthly controller keepalive running even after sync failure.
- [x] Create independent public backup and disable its Actions BEFORE copying upstream refs.
- [x] Create public controller, scoped deploy key and secret, push trusted workflow; never stage the key.
- [x] Run workflow_dispatch; inspect logs and require success.
- [x] Compare every upstream branch/tag SHA with backup, check repository independence and disabled target Actions.
- [x] Record deployment URLs and verification in local execution index.
