---
name: release
description: Prepare, validate, and create an Up3date release tag by following docs/RELEASE.md. Use when the user asks to prepare, tag, publish, retry, or troubleshoot a project release.
---

# Release

Prepare and create an Up3date release tag using the repository's release
runbook as the authoritative procedure.

## Workflow

1. Locate the repository root and read `docs/RELEASE.md` completely before
   taking any release-related action. Follow its current contents even when
   they differ from this summary.
2. Inspect the current branch, working tree, remotes, version declarations,
   lockfile, changelog, existing tags, and relevant GitHub release state.
   Do not modify or discard unrelated user changes.
3. Determine the intended semantic version without a `v` prefix. If the user
   has not supplied it and it cannot be unambiguously inferred from completed
   release preparation, ask which version to release.
4. Prepare and synchronize the version and release notes exactly as required
   by `docs/RELEASE.md`. Run the prescribed local quality checks and resolve
   failures that are within the requested release scope.
5. Stop before tagging if the release commit is not on `main`, the local
   `main` is not current, the worktree is dirty, required checks have failed,
   versions disagree, release notes are missing, or the tag/release already
   exists. Explain the concrete blocker instead of bypassing a safeguard.
6. Summarize the version, target commit, validation results, and the command
   that will publish the tag. Obtain explicit user confirmation immediately
   before creating or pushing the tag unless the user's current request
   already explicitly authorizes creating and pushing that exact tag.
7. Create and push the release tag only through the helper specified by
   `docs/RELEASE.md`. Do not manually create a GitHub release; the tag-driven
   workflow owns that step.
8. Report the pushed tag and the release workflow result or link when it is
   available. If the workflow fails, diagnose it and follow the runbook's
   recovery rules.

## Safety Rules

- Never force-update a release tag.
- Never delete or recreate a tag unless the user explicitly authorizes the
  exact recovery operation and the runbook permits it.
- Treat a published release tag as immutable.
- Do not bypass branch protection, tag protection, required checks, or
  version synchronization.
- Do not invent release notes. Derive them from the actual changes and keep
  them consistent with the existing changelog style, asking the user when a
  product-facing description requires judgment.
- If `docs/RELEASE.md` is absent or contradictory, stop and report the issue.
