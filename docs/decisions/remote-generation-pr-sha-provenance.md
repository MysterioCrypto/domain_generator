# Remote generation PR SHA provenance

Status: accepted clarification of `remote-github-actions-generation-adapter-v0.1`.

## Context

On GitHub `pull_request` workflows, `GITHUB_SHA` / `github.sha` may identify GitHub's synthetic PR merge commit rather than the PR head commit that the generation workflow explicitly checks out.

The accepted remote-generation design requires provenance to identify the exact generator revision actually executed.

## Decision

- `generator_commit` in `remote-execution.json` MUST equal the exact revision passed to `actions/checkout`.
- For `pull_request`, that revision is `github.event.pull_request.head.sha`.
- For `workflow_dispatch`, that revision is `github.sha` for the dispatched ref.
- The workflow passes this value explicitly as `GENERATOR_COMMIT` to the repository helper.
- Raw `GITHUB_SHA` is recorded separately as `github_sha` for GitHub event provenance and MUST NOT override `generator_commit`.
- No second checkout or cross-revision generation is introduced.

This is a provenance correction, not a change to Core or generation semantics.
