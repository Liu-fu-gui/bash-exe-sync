#!/usr/bin/env bash
set -euo pipefail
export GIT_TERMINAL_PROMPT=0

source_url=${1:?Usage: sync.sh SOURCE_URL TARGET_URL}
target_url=${2:?Usage: sync.sh SOURCE_URL TARGET_URL}
workspace=$(mktemp -d)
trap 'rm -rf -- "$workspace"' EXIT

git ls-remote --refs "$source_url" 'refs/heads/*' 'refs/tags/*' > "$workspace/source.refs"
if [[ ! -s "$workspace/source.refs" ]]; then
  printf '%s\n' 'Upstream is empty; refusing to modify the backup.' >&2
  exit 1
fi

declare -A source_refs target_refs
while read -r sha ref; do
  if [[ "$ref" == refs/tags/__backup_history/* ]]; then
    printf '%s\n' 'Upstream uses the reserved backup archive namespace; stopping safely.' >&2
    exit 1
  fi
  source_refs["$ref"]=$sha
done < "$workspace/source.refs"
git ls-remote --refs "$target_url" 'refs/heads/*' 'refs/tags/*' > "$workspace/target.refs"
while read -r sha ref; do
  target_refs["$ref"]=$sha
done < "$workspace/target.refs"

changed=false
for ref in "${!source_refs[@]}"; do
  if [[ "${source_refs[$ref]}" != "${target_refs[$ref]:-}" ]]; then
    changed=true
    break
  fi
done
if [[ "$changed" == false ]]; then
  printf '%s\n' 'Already up to date; retained any refs deleted upstream.'
  exit 0
fi

# Never check out or execute any upstream files. A failed fetch never reaches push.
repo="$workspace/backup.git"
git init --bare --quiet "$repo"
git -C "$repo" fetch --no-tags "$source_url" \
  '+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'
git -C "$repo" fetch --no-tags "$target_url" \
  '+refs/heads/*:refs/previous/heads/*' '+refs/tags/*:refs/previous/tags/*'

# Preserve every overwritten tip (including moved annotated tags) before replacing it.
while read -r sha ref; do
  if [[ "$ref" == refs/tags/__backup_history/* ]]; then
    printf '%s\n' 'Upstream archive namespace changed during fetch; stopping safely.' >&2
    exit 1
  fi
  old=$(git -C "$repo" rev-parse --verify "refs/previous/${ref#refs/}" 2>/dev/null || true)
  if [[ -n "$old" && "$old" != "$sha" ]]; then
    if [[ "$ref" == refs/heads/* ]] && git -C "$repo" merge-base --is-ancestor "$old" "$sha"; then
      continue
    fi
    git -C "$repo" update-ref "refs/tags/__backup_history/$old" "$old"
  fi
done < <(git -C "$repo" for-each-ref --format='%(objectname) %(refname)' refs/heads refs/tags)

# Explicit refspecs: no mirror, no prune, no delete. Archive and updates land together.
git -C "$repo" push --atomic "$target_url" \
  '+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'
printf '%s\n' 'Backup synchronized successfully.'
