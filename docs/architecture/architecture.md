# Editor Focus Mode Architecture

This document explains how the add-on is structured, which functions are part of the active runtime path, and how data moves through the program.

## Big Picture

The add-on has one main job:

1. Read configuration for a note type.
2. Decide which fields should stay visible.
3. Inject JavaScript into Anki's editor webview to hide the rest.
4. Let the user temporarily override that behavior with a toolbar button.

At runtime, most behavior starts from Anki hooks registered in [`__init__.py`](../__init__.py).

## Module Overview

### [`__init__.py`](../__init__.py)

This is the entry point. It does not contain business logic itself. Its job is to wire the add-on into Anki.

Responsibilities:

- Create the Tools menu action for opening the configuration dialog.
- Register the browser-tracking hook.
- Register editor hooks for:
  - code injection before a note loads
  - DOM updates after a note loads
  - adding the custom toolbar button

### [`config.py`](../config.py)

This module is the configuration layer.

Responsibilities:

- Read raw config from Anki with `mw.addonManager.getConfig(...)`.
- Fill in defaults when keys are missing.
- Expose helpers for:
  - `get_field_visibility_map()`
  - `get_field_visibility_disabled()`
  - `save_addon_config()`

Important config keys:

- `field_visibility_map`
  - Maps note type name -> list of fields that should remain visible.
- `field_visibility_layouts`
  - Maps note type name -> list of field layouts.
- `field_visibility_active_layouts`
  - Stores the currently selected layout index per note type.
- `field_visibility_disabled`
  - Stores note types for which hiding is temporarily turned off.

The toggle button does not store state in the UI. It stores state in `field_visibility_disabled`.

Maintenance note:

- `FIELD_VISIBILITY_MAP` and `get_field_visibility_map()` still exist mainly for backward compatibility with older config data.
- This legacy path is used for migration into the newer layout-based config structure.
- It can likely be removed later once migration from older configs is no longer needed.

### [`browser_utils.py`](../browser_utils.py)

This module tracks the current Browser window and provides helpers for working with notes selected there.

Main functions:

- `register_browser_instance(browser)`
- `current_browser()`

For the current field-hiding feature, the most important function is `current_browser()`. The hiding code uses it to make sure it only acts on the Browser editor, not every editor Anki may open.

### [`field_visibility.py`](../field_visibility.py)

This is the core module.

Main responsibilities:

- Decide whether visibility rules should apply.
- Build JavaScript to hide or reset fields.
- Toggle temporary visibility overrides.
- Add and update the toolbar button.

Main public functions:

- `apply_field_visibility(editor)`
- `editor_will_load_note(js, note, editor)`
- `toggle_field_visibility(editor)`
- `editor_init_buttons(buttons, editor)`

## Startup Flow

When Anki loads the add-on:

1. [`__init__.py`](../__init__.py) runs.
2. Hook handlers are registered:
   - browser open/show -> `register_browser_instance()`
   - editor will load note -> `editor_will_load_note()`
   - editor did load note -> `apply_field_visibility()`
   - editor toolbar init -> `editor_init_buttons()`

Nothing is hidden yet at startup. The real work begins when an editor loads a note.

## Note Load Flow

Two hooks participate in note loading.

### 1. `editor_will_load_note(js, note, editor)`

This runs before the editor finishes loading the note HTML/JS.

Its job is to append JavaScript to the existing editor script string that Anki is about to execute.

Decision flow:

1. If `_TOGGLE_BYPASS_UNTIL` is still active:
   - append reset JS
   - return
2. If there is no current browser or the editor is not the browser editor:
   - return original `js`
3. Determine note type name.
4. Load config and field map.
5. If the note type is unsupported or currently disabled:
   - append reset JS
6. Otherwise:
   - compute allowed fields
   - append hide JS

This gives the editor an initial visibility state as the note is loading.

### 2. `apply_field_visibility(editor)`

This runs after the editor has loaded the note.

Its purpose is similar, but now it can directly call `editor.web.eval(...)` against the live DOM.

Decision flow:

1. If `_TOGGLE_BYPASS_UNTIL` is active:
   - reset all fields
   - return
2. Reject non-browser editors.
3. Read the current note and note type.
4. Load config.
5. If note type is unsupported:
   - update button label
   - reset fields
   - return
6. If note type is in `field_visibility_disabled`:
   - update button label
   - reset fields
   - return
7. Otherwise:
   - compute allowed field indices and names
   - build hide JS
   - execute it now and again after short delays
   - update button label
   - write a debug dump

Those delayed JS re-runs exist because the editor DOM may still be settling after load.

## How Field Selection Is Computed

The helper `_allowed_field_indices(note, allowed_fields)` translates configuration into something the DOM code can use.

It returns:

- `allowed_indices`
  - numeric positions of allowed fields in the note model
- `field_count`
  - total number of fields in the note model
- `all_names`
  - all field names on the note type

This is important because the DOM does not always expose field names cleanly, so the JavaScript uses both:

- field names when possible
- field index position as a fallback

## JavaScript Injection Layer

The actual hiding happens in JavaScript generated by Python.

### `_hide_fields_js(...)`

This function builds a string of JavaScript that:

1. Creates `Set`s of:
   - allowed field names
   - all field names
   - allowed field indices
2. Searches the editor DOM for likely field containers.
3. Tries to determine each field's name.
4. Sets `style.display` to hide non-allowed fields.
5. Re-runs after short delays to handle late DOM updates.

This is the most fragile part of the add-on, because it depends on Anki's editor HTML structure and CSS class names.

### `_reset_fields_js(all_names)`

This builds the inverse operation: JavaScript that clears inline `display` styles so fields become visible again.

This is used when:

- a note type is unsupported
- hiding is disabled for a note type
- the toggle button is used to temporarily show all fields

## Toggle Button Flow

The toolbar button is added by `editor_init_buttons(...)`.

It calls `toggle_field_visibility(editor)` when clicked.

### `toggle_field_visibility(editor)`

This function does not directly ask "are fields currently hidden in the DOM?".

Instead, it flips persistent state in config:

1. Get current note type.
2. Load config.
3. Read `field_visibility_disabled`.
4. If note type is already in that list:
   - remove it
   - hiding should become active again
5. Otherwise:
   - add it
   - hiding should be bypassed for that note type
6. Save config.
7. Update `_TOGGLE_BYPASS_UNTIL`:
   - short future timeout when visibility is disabled
   - `0.0` when hiding is re-enabled
8. If the note type is now disabled:
   - reset visibility immediately
9. Otherwise:
   - re-run hide JS
   - schedule delayed hide JS runs
   - reload the note if needed
10. Schedule label updates

### `_TOGGLE_BYPASS_UNTIL`

This is a short-lived global timestamp used to avoid immediately re-hiding fields during the reload cycle after a toggle.

Conceptually:

- user clicks button to show all fields
- add-on briefly enters a "do not hide right now" window
- note/editor reloads
- reset logic wins during that window

This works as a timing hack, but it is also global process state, so it can be a source of race conditions.

### `_update_toggle_button_label(editor)`

This reads config again and changes the button text:

- `Hide Fields` when hiding is active
- `Show Fields` when hiding is disabled for this note type

The label is derived from config state, not from inspecting the DOM.

## Why `current_browser()` Matters

The code in [`field_visibility.py`](../field_visibility.py) intentionally checks that the editor being processed is the Browser editor.

Without that guard, the same hide logic might affect:

- the main Add Cards window
- Edit Current
- reviewer editor instances
- other editors Anki creates internally

So the browser-tracking utility acts like a scope boundary for the feature.

## Current Active Call Graph

The most important active relationships are:

- `__init__.py`
  - registers hooks
- browser hook
  - `register_browser_instance()`
- `editor_will_load_note`
  - `editor_will_load_note()`
  - `_hide_fields_js()` or `_reset_fields_js()`
- `editor_did_load_note`
  - `apply_field_visibility()`
  - `_allowed_field_indices()`
  - `_hide_fields_js()` or `_reset_visibility()`
  - `_update_toggle_button_label()`
  - `_debug_dump_fields()`
- toolbar button
  - `toggle_field_visibility()`
  - `_reset_visibility()` or `_hide_fields_js()`
  - `_update_toggle_button_label()`

## State in the Program

There are three main kinds of state:

### 1. Persistent config state

Stored by Anki:

- `field_visibility_map`
- `field_visibility_disabled`

### 2. Runtime global state

Stored in Python module globals:

- `_LAST_BROWSER` in [`browser_utils.py`](../browser_utils.py)
- `_TOGGLE_BYPASS_UNTIL` in [`field_visibility.py`](../field_visibility.py)
### 3. Editor DOM state

Stored in the webview:

- inline `style.display` changes applied by injected JavaScript
- current button label text

## Debugging Tips

If you want to trace behavior while reading the code, start in this order:

1. [`__init__.py`](../__init__.py)
2. [`field_visibility.py`](../field_visibility.py)
3. [`config.py`](../config.py)
4. [`browser_utils.py`](../browser_utils.py)

For runtime inspection:

- `field_visibility_debug.txt` can show which field-like elements the webview code found.
- The label text on the toggle button tells you what `field_visibility_disabled` currently says.
- If behavior is inconsistent, inspect the branches around `_TOGGLE_BYPASS_UNTIL`.

## Known Design Weak Spots

These are useful to know while reading the code:

- The DOM-hiding logic is heuristic-based and depends on Anki HTML structure.
- The reset path and hide path are not perfectly symmetric.
- `_TOGGLE_BYPASS_UNTIL` is global, so timing issues can cross editor instances.
## Suggested Reading Order for Learning the Code

If your goal is understanding rather than changing it, this order usually feels best:

1. Read [`__init__.py`](../__init__.py) to see the entry points.
2. Read `apply_field_visibility()` and `toggle_field_visibility()` in [`field_visibility.py`](../field_visibility.py).
3. Read the helpers in [`config.py`](../config.py).
4. Read `_hide_fields_js()` and `_reset_fields_js()` last, because they are the lowest-level DOM details.
