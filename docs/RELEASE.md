# Release workflow

> **Internal document:** This release runbook is for the project maintainer.
> AI agents assisting with a release should read and follow it before taking
> any release-related action.

Up3date uses a manual, tag-driven release workflow. Updating the version does
not publish a release by itself. A release is published only after a matching
Git tag is pushed.

## 1. Update and synchronize the version

The release version is declared in three places. Update all three to the same
semantic version before creating a release:

```toml
# pyproject.toml
[project]
version = "0.1.1"

# blender_manifest.toml
version = "0.1.1"
```

Update the tuple in `__init__.py` to represent the same version:

```python
bl_info = {
    "version": (0, 1, 1),
}
```

Use the next semantic version for the release. The values in
`pyproject.toml`, `blender_manifest.toml`, and `__init__.py` must match and use
the `MAJOR.MINOR.PATCH` format without a `v` prefix. Run `uv lock` after
changing `pyproject.toml` so `uv.lock` records the same project version.

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
- the versions in `pyproject.toml`, `blender_manifest.toml`, `bl_info`, and
  `uv.lock` are identical;
- the matching changelog section contains release notes; and
- the tag points to a commit reachable from `main`.

If all checks pass, GitHub Actions builds an installable
`up3date-MAJOR.MINOR.PATCH.zip` and attaches it to the GitHub release. The ZIP
contains only the add-on runtime files:

- `blender_manifest.toml`;
- `__init__.py` and `addon.py`;
- the `core/` and `models/` packages; and
- `LICENSE`.

Tests, sample data, documentation, development configuration, scripts, and
GitHub infrastructure are not included in this installable ZIP. GitHub also
adds its standard **Source code** archives to every release automatically;
those are repository snapshots and are separate from the installable add-on
asset.

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
- If the tag already exists, the release helper stops. Check whether a GitHub
  release was published. Keep published release tags immutable; otherwise,
  follow the failed-tag recovery procedure below.

### Recovering from a failed release tag

If the release workflow rejects a tag before creating a GitHub release, an
administrator may delete and recreate the tag after correcting the release
metadata. The repository tag ruleset must grant that administrator **Always
allow** bypass permission for tag deletion and creation. Administrator access
alone does not necessarily bypass an active ruleset.

Delete the failed tag from the remote and the local repository:

```bash
git push origin --delete 0.0.0
git tag --delete 0.0.0
```

Replace `0.0.0` with the failed version. Then:

1. Synchronize the version in `pyproject.toml`, `blender_manifest.toml`,
   `bl_info`, and `uv.lock`.
2. Add or correct the matching `CHANGELOG.md` section.
3. Commit the correction and merge it into `main`.
4. Update the local `main` branch and run `./scripts/release.sh` again.

Only reuse a tag when the workflow failed before publishing the GitHub
release. If the release was successfully published or the tag may already be
in use, keep it immutable and prepare a new patch version such as `0.0.1`.
Never force-update a release tag.
