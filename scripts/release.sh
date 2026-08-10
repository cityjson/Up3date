#!/usr/bin/env bash

set -euo pipefail

remote="${1:-origin}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to determine the project version." >&2
  exit 1
fi

if [[ "$(git branch --show-current)" != "main" ]]; then
  echo "Releases must be created from the main branch." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "The working tree must be clean before creating a release." >&2
  exit 1
fi

version="$(uv version --short)"

if [[ ! -f CHANGELOG.md ]]; then
  echo "CHANGELOG.md is required to create a release." >&2
  exit 1
fi

changelog_message="$(awk -v version="${version}" '
  index($0, "## [" version "]") == 1 { in_section = 1; next }
  in_section && /^## / { exit }
  in_section { print }
' CHANGELOG.md)"

if [[ -z "$(printf '%s' "${changelog_message}" | tr -d '[:space:]')" ]]; then
  echo "No notes found for version ${version} in CHANGELOG.md." >&2
  exit 1
fi

if git tag --list "${version}" | grep -Fxq "${version}"; then
  echo "Tag ${version} already exists locally." >&2
  exit 1
fi

tag_message_file="$(mktemp)"
trap 'rm -f "${tag_message_file}"' EXIT
{
  printf 'Release %s\n\n' "${version}"
  printf '%s\n' "${changelog_message}"
} > "${tag_message_file}"

echo "Creating annotated tag ${version}..."
git tag --annotate "${version}" --file "${tag_message_file}"

echo "Pushing ${version} to ${remote}..."
git push "${remote}" "${version}"

echo "Release tag ${version} pushed successfully."
