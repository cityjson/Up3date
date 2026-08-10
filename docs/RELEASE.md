# Release workflow

> **Internal document:** This release runbook is for the project maintainer.
> AI agents assisting with a release should read and follow it before taking
> any release-related action.

Up3date uses a manual, tag-driven release workflow. Updating the version does
not publish a release by itself. A release is published only after a matching
Git tag is pushed.

## 1. Update the version

Update the `project.version` value in `pyproject.toml`:

```toml
version = "0.1.1"
```

Use the next semantic version for the release. The version must use the
`MAJOR.MINOR.PATCH` format, without a `v` prefix.

## 2. Add the release notes

Add a changelog heading with exactly the same version in `CHANGELOG.md`:

```markdown
## [0.1.1]

- Describe the changes included in this release.
- Mention notable fixes or improvements.
```

The notes below this heading become both the annotated Git tag message and the
GitHub release notes. Notes from another version are not used.

## 3. Validate the changes

The GitHub quality pipeline automatically checks for formatting, linting, type
checking, unit tests, and runs Blender integration tests.

You may also run the checks locally before committing:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```



## 4. Merge the release preparation into `main`

Commit the version and changelog changes, then merge them into `main`. The
release tag must point to a commit that is already on `main`.

After merging, check out a clean local copy of `main` and make sure it is
up-to-date:

```bash
git switch main
git pull --ff-only origin main
git status
```

The working tree must be clean before creating the release.

## 5. Create and push the release tag

Run the release helper:

```bash
./scripts/release.sh
```

The script reads the version from `pyproject.toml`, checks that the working
tree is clean and that the current branch is `main`, extracts the matching
changelog section, creates an annotated tag, and pushes it to `origin`.

## 6. GitHub Actions publishes the release

Pushing the tag starts the release workflow. It verifies that:

- the tag uses the `MAJOR.MINOR.PATCH` format;
- the tag matches `project.version` in `pyproject.toml`;
- the matching changelog section contains release notes; and
- the tag points to a commit reachable from `main`.

If all checks pass, GitHub Actions creates the GitHub release using the
version-specific changelog notes.

## Protected tags

Release tags should be protected with a GitHub ruleset matching the release tag
pattern, for example `*.*.*`. Restrict updates and deletions so an existing
release tag cannot be moved or removed. If tag creation is restricted, grant
the release maintainer bypass permission so `scripts/release.sh` can create the
tag.

## If something goes wrong

- If the tag does not match `pyproject.toml`, update the version or tag the
  correct commit; do not force-update an existing release tag.
- If the changelog notes are missing, add the matching `## [version]` section, 
  compute the diff and add it as release notes in a consistent format with the 
  previous versions and always with formatting that can be rendered correctly 
  in a git/github annotated tag. Then create a new version tag only if that version 
  has not already been released.
- If the tag already exists, the release helper stops. Do not delete or
  force-update a protected release tag; investigate the existing GitHub
  release instead.
