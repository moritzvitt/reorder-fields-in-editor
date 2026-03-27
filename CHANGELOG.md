# Changelog

All notable changes to this project will be documented in this file.

## 0.2.0 - 2026-03-27

### Added

- Added native Anki add-on configuration files via [`config.json`](./config.json) and [`config.md`](./config.md).
- Added support for multiple field layouts per note type.
- Added a layout-rotation toolbar button that cycles through configured field subsets.
- Added documentation for architecture, wrappers, user flow, current problems, and Mermaid charts.
- Added a project `.gitignore`.

### Changed

- Switched configuration to Anki's native add-on config flow and removed the custom Tools menu configuration dialog.
- Updated field-hiding selectors to target current Anki editor wrappers like `.field-container`, `.label-name`, and `[data-index]`.
- Simplified the repository README and moved longer-form documentation into `docs/`.
- Reorganized chart documentation into [`docs/charts/`](./docs/charts/).
- Cleaned out unused ChatGPT-related config code and unused browser helper functions.

### Removed

- Removed the custom `Editor Focus Mode Configuration` menu action.
- Removed the obsolete [`ui.py`](./ui.py) configuration dialog module.

## 0.1.0

### Added

- Initial field visibility control by note type.
- Hide/show toggle button in the editor toolbar.
- Browser-scoped editor integration.
