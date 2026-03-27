# Editor Focus Mode

An Anki add-on for the Browser editor that hides non-relevant note fields based on note type configuration.

## What It Does

- shows only the configured subset of fields for a note type
- adds a toggle button to temporarily show all fields
- lets the user hide non-allowed fields again on the next click
- adds a layout button that rotates through the available field subsets for the current note type

## Demo

[![Watch the demo on YouTube](https://img.youtube.com/vi/6XNraKFZiZc/hqdefault.jpg)](https://youtu.be/6XNraKFZiZc)

## Main Files

- [`__init__.py`](./__init__.py): hook registration
- [`field_visibility.py`](./field_visibility.py): hide/show logic
- [`config.py`](./config.py): config helpers
- [`browser_utils.py`](./browser_utils.py): Browser tracking
## Help Wanted

The main hard parts are:

- Anki editor lifecycle timing
- reliable toggle behavior across note reloads
- keeping the DOM selectors robust across Anki versions

## Future Plans

- support more than the initial three layouts per note type
- make layout names and layout editing easier

## Docs

- Detailed README: [`docs/README-detailed.md`](./docs/README-detailed.md)
- Architecture: [`docs/architecture.md`](./docs/architecture.md)
- Current problems: [`docs/current-problems.md`](./docs/current-problems.md)
- Wrapper reference: [`docs/wrappers.md`](./docs/wrappers.md)
- User flow: [`docs/user-flow.md`](./docs/user-flow.md)
- Charts: [`docs/charts/`](./docs/charts/)
