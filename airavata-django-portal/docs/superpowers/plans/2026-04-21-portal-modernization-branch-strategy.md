# Modernization Branch Strategy

The `modernization` branch is the long-lived integration branch for the
portal modernization umbrella (spec:
`docs/superpowers/specs/2026-04-21-portal-modernization-design.md`).

## Baseline

`modernization` was branched from `feat/sdk-and-devenv` (not `main`), so it
inherits in-flight foundational fixes that preceded the umbrella:

- SSE `SharedWorker`-based EventSource sharing across pages
- uvicorn / ASGI swap (replaces Django `runserver`)
- SQLite WAL + busy_timeout for session concurrency
- Save-deployment `SharingType` enum binding fix
- Multiple Vue 3 destroyed()→unmounted() fixes

When the umbrella PR is opened (Task 7), the base is `main`, so the PR will
roll up both the pre-umbrella fixes and the five modernization tracks.

## Rules

1. Every track (D, C, B, Pre-A, A) lands on its own feature branch.
2. Feature branches merge into `modernization`, not `main`.
3. `modernization` merges to `main` exactly once, at the end of the
   umbrella, after every track's done-criteria pass.
4. Any track can be reverted independently by a revert-merge against
   `modernization`.

Feature-branch naming: `track-<letter>/<short-slug>`.
Examples: `track-d/python-hygiene`, `track-c/monorepo-tooling`,
`track-b/library-swaps`, `track-pre-a/test-harness`,
`track-a/vue-composition-ts-pinia`.
