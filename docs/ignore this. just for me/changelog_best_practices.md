A good default is: keep change history concise, user-facing, and chronological.

The most common best practices are:

- Keep a `CHANGELOG.md` in the repo root.
- Use reverse chronological order.
- Group unreleased work under `Unreleased`.
- When you cut a release, move those entries under a version heading like `## 0.2.0`.
- Write changes in terms of outcomes, not implementation details.
- Prefer categories like:
  - `Added`
  - `Changed`
  - `Fixed`
  - `Removed`
- Keep entries short and scannable.
- Avoid listing every tiny refactor unless it changes behavior, workflow, or maintenance in a meaningful way.

For a project like yours, it helps to think about audience:

- `README` explains what the project is.
- `CHANGELOG` explains what changed over time.
- `docs/` explains how it works.

A strong changelog entry usually answers:
- what changed
- who it affects
- why it matters

Examples:

Good:
- Added a layout button that rotates through configured field subsets per note type.
- Switched to Anki’s native `config.json` / `config.md` configuration flow.
- Removed the custom Tools menu configuration dialog.

Less useful:
- Refactored `field_visibility.py`
- Renamed helper functions
- Cleaned code

Those are only worth listing if they affect contributors significantly.

Two especially common conventions:
- “Keep a Changelog” style
- Semantic Versioning for release numbers, if you want versioning discipline

For your addon, I’d recommend:
- keep `Unreleased`
- only record meaningful behavioral or contributor-facing changes
- move internals-only cleanup into commits, not necessarily the changelog
- add release dates once you start making real releases

A nice rule of thumb:
- if a user or contributor would care after skipping 2 weeks of work, it belongs in the changelog
- if only the person who edited the file would care, it usually doesn’t

If you want, I can also rewrite your current `CHANGELOG.md` into a cleaner “Keep a Changelog” style.