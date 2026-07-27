# Contributing

## Setup

```bash
conda env create -f environment.yml
conda activate activity
npm install
```

This gives you Python, `gh`, and Node (via `nodeenv`) in one environment. Without conda,
you just need Python 3.x, Node, and `pip install -r requirements.txt` + `npm install`.

## Code style

- **No class definitions, anywhere.** Enforced by `scripts/no_classes_check.py` across the
  whole repo (CI fails on any `class`). Write functions, not objects. If a third-party
  library forces a class-based API (e.g. Django's ORM/management commands), avoid that API
  rather than adding an exception — see [gateway/proxyauth/db.py](gateway/proxyauth/db.py)
  and [gateway/scripts/](gateway/scripts/) for how the Django gateway does this with raw
  SQL and plain scripts instead of models/management commands.
- **One bare `import` line per file.** If a file has multiple top-level `import x` statements,
  `scripts/combined_imports_check.py` wants them combined onto one line
  (`import os, sys, django`). `from x import y` statements are untouched. Auto-fixable with
  `--fix` (see below) — but if setup code has to run between imports (e.g. `django.setup()`
  before importing anything Django-dependent), keep those imports separate and add
  `# noqa: E402` rather than letting the combiner merge them incorrectly.
- Ruff handles the rest (`pyproject.toml`, line length 180).

## Before pushing

```bash
tox -e all       # auto-fixes formatting, then runs the full check chain
```

`tox -e all` runs `format` (ruff format/fix, prettier `--write` on scss/js/html/json/yml/md,
taplo fmt on toml, import-combining `--fix`) and then `github`, which is the same
`no-classes-check → lint → txt-lint → prettier --check → toml-lint → combined-imports-check`
chain CI runs on every push/PR (`.github/workflows/tests.yml`). If `tox -e all` passes
locally, CI will too.

Compiling the gateway's SCSS is separate from `tox`:

```bash
make css   # gateway/scss/login.scss -> gateway/static/css/login.css
```

(The Docker build does this itself in a node stage — `make css` is only for local iteration.)

## Testing the stack

There's no automated test suite yet; verify changes by actually running the stack:

```bash
cp .env.example .env   # if you don't already have one
docker compose up -d --build
docker compose exec aw-gateway python scripts/create_user.py <name>
```

See [README.md](README.md) for the full setup, including optional Authentik login.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat:`, `fix:`,
`docs:`, `refactor:`, `perf:`, `test:`, `chore:`). PR titles, descriptions, and labels are
auto-generated from commit history (`.github/workflows/pr-description.yml`) and read these
prefixes to group changes — an untyped commit history falls back to weaker heuristics.

## Branches & PRs

- `main` and `staging` are protected: no direct pushes or force-pushes, no deletions, and
  changes go through a PR requiring one approval from `@Self-Host-Server/code-owners`
  (see [CODEOWNERS](CODEOWNERS)). Repo admins can bypass in a genuine emergency, but that's
  the exception, not the workflow.
- Opening a PR auto-assigns code owners for the paths you touched, applies area/type labels,
  and generates a description from your commits — you generally don't need to write one
  by hand if your commits are well-formed.
