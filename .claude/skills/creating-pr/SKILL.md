---
name: creating-pr
description: Create a GitHub pull request with a markdown-formatted description. Use when opening a PR from this repository, and default the base branch to develop unless instructed otherwise.
disable-model-invocation: true
---

# Creating PR

Use this skill when opening a pull request for this repository.

## Start Here

- Confirm the current branch and the intended base branch.
- Default the base branch to `develop` unless the user says otherwise.
- Review the diff and gather the key changes, tests, and risks. Do not describe only the recent commit(s); describe the overall PR changes.
- Ensure the description is well-formatted with appropriate headings and lists for readability
- Do not mention any unrelated files or changes that are not part of the PR.

## Workflow

1. Confirm the branch to publish and the base branch.
2. Inspect the diff and identify the main changes.
3. Draft the PR body in markdown using [PR Description Template](pr-description-template.md).
4. Make sure the PR description is properly formatted with headings and lists.
5. Create the PR against `develop` unless otherwise instructed.
6. Verify the created PR title, base branch, and body formatting.

## Rules

- Do not use plain text descriptions.
- Do not target any branch other than `develop` unless the user explicitly says so.
- Keep the description concise, accurate, and markdown formatted.
- Do not include unrelated changes or files in the description.
  - Notes like "There is an unrelated untracked ADR file in the worktree that is not part of this PR" should not be mentioned in the PR description.
- Include tests run and any known limitations.

## Gotchas

- Codex usually creates PRs with malformed descriptions. Always use markdown and check the formatting.
- Keep unrelated changes out of the PR description. They simply do not belong there. Do not mention anything left out.

## Suggested Commands

- `git branch --show-current`
- `git diff --stat develop...HEAD`
- `git diff develop...HEAD`
- `gh pr create --base develop --title "<title>" --body-file <file>`

## Output Shape

Use a markdown body with these sections:

- `Summary`
- `Changes`
- `Tests`
- `Notes`
- `Validation`
