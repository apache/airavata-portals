# Track D — Python Hygiene Design

> Track D of the portal modernization umbrella. Umbrella spec:
> `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

## Goal

Clean up the portal's Python-side hygiene so the umbrella's remaining tracks
build on an explicit, modern foundation. The work is entirely server-side
text changes with a strict functional-parity guardrail.

## Scope

Four work items, landed as one commit on `track-d/python-hygiene`.

### 1. `pytz` → `zoneinfo`

Only one call site remains in the portal:

- `django_airavata/apps/api/view_utils.py:220`
  `timestamp = timestamp.replace(tzinfo=pytz.UTC)`

Swap for stdlib:

```python
from datetime import timezone
timestamp = timestamp.replace(tzinfo=timezone.utc)
```

Remove the `import pytz` at line 9 and remove `"pytz"` from
`pyproject.toml`'s `[project].dependencies`.

### 2. `wagtailcodeblock` 1.28 → 1.30 and drop the `setuptools<81` pin

Context: `setuptools<81` was pinned because `wagtailcodeblock` 1.28.0.1
imports `pkg_resources`, which setuptools 81 removed. `wagtailcodeblock`
1.30.0.0 (2024+) declares `wagtail>=6` and is compatible with the portal's
Wagtail 6.3.

Changes:

- `pyproject.toml`: `wagtailcodeblock>=1.28,<1.29` → `wagtailcodeblock>=1.30`
- `pyproject.toml`: delete `"setuptools<81"`
- `uv lock` to refresh `uv.lock`
- Smoke-verify that Wagtail admin renders a CMS page containing a code block
  (see Testing, below)

**Fallback (only if 1.30 still uses `pkg_resources`):** keep the
`setuptools<81` pin but add an inline rationale comment:
`"setuptools<81",  # wagtailcodeblock 1.30 still imports pkg_resources`.
The fallback is only accepted if the pkg_resources dependency is
reproduced on the current `wagtailcodeblock` release — not speculatively.

### 3. `<` version pin audit

Every `<` pin in `pyproject.toml` must either be widened or carry an inline
`# rationale` comment after this track.

| Pin | Action | Resulting line |
|---|---|---|
| `Django>=5.1,<5.2` | Keep, add rationale | `"Django>=5.1,<5.2",  # LTS series (5.1 is LTS through 2026-12)` |
| `djangorestframework>=3.15,<4` | Widen (drop speculative major cap) | `"djangorestframework>=3.15",` |
| `wagtail>=6.3,<7` | Keep, add rationale | `"wagtail>=6.3,<7",  # avoid major 7.x until migration assessed` |
| `wagtailcodeblock>=1.28,<1.29` | Widen (handled by item 2) | `"wagtailcodeblock>=1.30",` |
| `setuptools<81` | Remove (handled by item 2) | *deleted* |

Rule of thumb encoded in the audit script (see Testing):
*"every line containing `<` in a dependency string must have an inline `#`
comment on the same line or a `#` comment on the line immediately above it."*

### 4. Dead-code sweep

Run a full audit with `vulture` + `ruff --select F401,F811`, manually triage
the output, and delete confirmed dead code in the same commit.

**Known dead (delete):**

- `django_airavata/apps/groups/` — 3.3 MB directory with no Python source,
  not in `INSTALLED_APPS`, no references anywhere in the tree. Casualty of
  the SDK-facade migration.

**Candidates requiring triage:**

- Unreferenced modules, functions, and classes reported by
  `vulture django_airavata --min-confidence 80`.
- `F401` unused imports and `F811` duplicate definitions.

**Protection against false positives:**

- Dynamic-dispatch modules (`django_airavata/dynamic_apps/`,
  entry-point-loaded apps) must stay even if vulture flags them. Use
  `#  vulture: off` / `--ignore-names` as appropriate.
- Django signal handlers, management commands, template tags, and DRF
  serializer fields are commonly flagged false-positive — spot-check before
  deletion.
- Anything used via string import (`"django_airavata.X.Y"`) won't be seen by
  vulture. Preserve middleware, authentication backends, context processors,
  and INSTALLED_APPS entries.

## Out of scope (deferred)

- `proto_compat.py` refactor — used pervasively, worth its own track.
- Wagtail template modernization.
- Any behavioural change (Track D is functional-parity only).
- `Django<5.2` bump to 5.2 (separate upgrade decision).

## Design Decisions

| # | Decision | Alternatives considered |
|---|---|---|
| Q1 | Upgrade `wagtailcodeblock` to 1.30 to drop the `setuptools<81` pin | Keep pin + rationale comment; replace wagtailcodeblock with a lighter custom block |
| Q2 | Rationalize pins that have a reason (`Django<5.2`, `wagtail<7`); widen speculative ones (`djangorestframework<4`, `wagtailcodeblock<1.29`) | Pure documentation (rationalize all); pure widening (drop all major caps) |
| Q3 | Full dead-code audit using vulture + ruff + manual review | Surgical removal of known-dead `groups/` only; targeted sweep |
| Q4 | Full smoke suite: pytest + booted-portal curl diffs on 8 key endpoints | Existing pytest only; targeted regression tests around the pytz call site |
| Q5 | One commit for all four scopes | One commit per scope; low-risk vs high-risk split |

## Testing protocol (functional-parity enforcement)

Run every layer before and after Track D's commit. Divergence blocks merge.

### Layer 1 — Static checks

```bash
uv sync
uv run ruff check .
uv run ty check .
```

`uv.lock` must not contain `pkg_resources`-adjacent fossils post-commit.

### Layer 2 — pytest parity

```bash
# Pre (on modernization)
git checkout modernization
uv run pytest -q --json-report --json-report-file=/tmp/td-pre.json

# Post (on track-d/python-hygiene)
git checkout track-d/python-hygiene
uv run pytest -q --json-report --json-report-file=/tmp/td-post.json

# Compare
python3 -c "
import json
pre = json.load(open('/tmp/td-pre.json'))['summary']
post = json.load(open('/tmp/td-post.json'))['summary']
assert pre == post, f'pytest summary drift: pre={pre} post={post}'
print('OK pytest parity', pre)
"
```

### Layer 3 — Smoke suite against a running portal

`scripts/smoke.sh` (introduced by this track) takes one argument (`pre` or
`post`) and writes response bodies to `/tmp/td-<arg>/<endpoint>.json`.

Endpoints probed (after a successful Keycloak login):

1. `GET /health/` — liveness.
2. `GET /api/projects/?limit=5` — ORM + Keycloak groups path.
3. `GET /api/applications/?limit=5` — application catalog service.
4. `GET /api/experiments/?limit=5` — exercises `view_utils` pagination
   (the pytz-using file).
5. `GET /api/user-profile/` — `proto_compat` conversions.
6. `GET /api/project-profiles/` — server REST passthrough.
7. `GET /pages/home/` — Wagtail CMS render (touches `wagtailcodeblock` if
   any block on the homepage uses it).
8. `GET /workspace/` — main workspace SPA shell.

```bash
# On modernization
tilt up &
sleep 60  # wait for boot
bash scripts/smoke.sh pre
tilt down

# On track-d/python-hygiene
git checkout track-d/python-hygiene
tilt up &
sleep 60
bash scripts/smoke.sh post
tilt down

diff -r /tmp/td-pre /tmp/td-post
```

Expected: no substantive diff. Timestamps, session ids, and CSRF tokens
vary and are filtered by the helper. Anything else is a parity violation.

## Done criteria (gate checks)

The umbrella plan's Task 1 Step 5 runs these checks. All must pass.

```bash
# 1. No pytz imports anywhere.
grep -rn "^import pytz\|^from pytz\|[^a-z]pytz\." django_airavata \
  --include='*.py' | grep -v __pycache__ | grep -v .venv
# Expected: empty.

# 2. pyproject.toml no longer lists pytz.
grep -n '"pytz"' pyproject.toml
# Expected: empty.

# 3. setuptools<81 pin is gone (or retained with explicit rationale).
grep -n 'setuptools<81' pyproject.toml
# Expected: empty, OR matched line contains '# wagtailcodeblock' as
# rationale (fallback path only).

# 4. wagtailcodeblock is at >=1.30.
python3 -c "
import tomllib, sys
d = tomllib.loads(open('pyproject.toml','rb').read().decode())
ok = any('wagtailcodeblock' in s and '>=1.30' in s
        for s in d['project']['dependencies'])
sys.exit(0 if ok else 1)
"
# Expected: exit 0.

# 5. pkg_resources is gone from uv.lock.
grep -cn '^name = "pkg_resources"' uv.lock
# Expected: 0.

# 6. Every `<` pin has an inline or preceding rationale comment.
python3 scripts/pin_audit.py
# Expected: 'OK'.

# 7. django_airavata/apps/groups/ is deleted.
test ! -d django_airavata/apps/groups
# Expected: exit 0.

# 8. Vulture + ruff report no *new* unjustified dead code.
uv run vulture django_airavata --min-confidence 80
uv run ruff check --select F401,F811 .
# Expected: vulture output contains only intentionally-ignored dynamic
# imports; ruff exit 0.

# 9. Static checks unchanged.
uv run ruff check .
uv run ty check .
# Expected: both exit 0.

# 10. pytest parity.
uv run pytest -q
# Expected: identical summary to modernization baseline.

# 11. Smoke suite identical.
diff -r /tmp/td-pre /tmp/td-post
# Expected: no substantive diffs (only filtered timestamps/tokens).
```

## New files introduced by this track

- `scripts/pin_audit.py` — enforces the "every `<` pin has a rationale
  comment" invariant. Also used unchanged by the umbrella's Task 6.
- `scripts/smoke.sh` — reusable curl-based smoke suite. Takes one argument
  (`pre` or `post`); outputs to `/tmp/td-<arg>/`. Filters out timestamps,
  CSRF tokens, and session IDs before writing so `diff -r` is meaningful.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| wagtailcodeblock 1.30 still imports `pkg_resources` | Fallback: keep `setuptools<81` pin + inline rationale comment; abandon the bump |
| wagtailcodeblock 1.30 changes CMS block template output | Smoke Layer 3 endpoint #7 (`/pages/home/`) catches byte diffs |
| vulture false positives delete Django dynamic-dispatch code | Manual triage required before any deletion; protection list documented above |
| pyproject pin widening breaks resolution | `uv sync` in Layer 1 catches |
| Test suite is flaky enough that "identical summary" is too strict | Re-run up to 3× on any parity failure before declaring drift real |

## Not in scope

- No behavioural changes. Any diff in response bodies that isn't a
  timestamp/session/CSRF token is a Track D failure, even if the new
  behaviour "looks better".
- No Wagtail 7 bump, no Django 5.2 bump, no DRF 4 bump.
- No monorepo-tooling changes (that's Track C).
- No test-framework introduction (that's Track Pre-A).
