#!/usr/bin/env bash
set -euo pipefail

limit="${1:-1000}"
changed_lines="$(git diff --cached --numstat | awk '{ added += $1; deleted += $2 } END { print added + deleted + 0 }')"

if [ "$changed_lines" -gt "$limit" ]; then
  echo "Staged change size is ${changed_lines} lines, above limit ${limit}."
  echo "Split the commit by subsystem before committing."
  exit 1
fi

echo "Staged change size: ${changed_lines}/${limit} lines."
