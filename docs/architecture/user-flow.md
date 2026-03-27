# Typical User Flow

This document explains the add-on by following one normal user journey:

1. open the Browser
2. select a note
3. click `Show Fields` to unhide everything
4. click `Hide Fields` to hide non-allowed fields again

It is intentionally higher-level than [`architecture.md`](./architecture.md).

## 1. Browser Opens

When Anki loads the add-on, [`__init__.py`](../__init__.py) registers the menu action and the relevant hooks.

When the Browser window is created, Anki fires a browser hook and the add-on calls:

- `register_browser_instance(browser)` in [`browser_utils.py`](../browser_utils.py)

That stores a reference to the current Browser window in `_LAST_BROWSER`.

Why this matters:

- later, the add-on can ask `current_browser()`
- this lets it limit field hiding to the Browser editor

## 2. User Selects a Note

When the user selects a note in the Browser, the editor loads that note.

Two hook-driven steps happen around that load.

### Before the note finishes loading

Anki calls:

- `editor_will_load_note(js, note, editor)` in [`field_visibility.py`](../field_visibility.py)

This function decides what JavaScript should be appended to the editor load process.

It checks:

- is the current editor really the Browser editor?
- what is the note type?
- is this note type configured in `field_visibility_map`?
- is field hiding currently disabled for this note type?

Based on those checks, it appends either:

- hide JS from `_hide_fields_js(...)`
- or reset JS from `_reset_fields_js(...)`

### After the note finishes loading

Anki then calls:

- `apply_field_visibility(editor)` in [`field_visibility.py`](../field_visibility.py)

This is the second pass. It applies the same decision again, but now against the live DOM using `editor.web.eval(...)`.

If hiding is active:

- it computes the allowed fields for the note type
- it builds JS that hides the non-allowed `.field-container` elements
- it runs that JS immediately and again after short delays

If hiding is not active:

- it resets the field wrappers so all fields are visible

At the end of this step, the user sees the note in the Browser editor with the current visibility mode applied.

## 3. User Clicks `Show Fields`

The toolbar button is created by:

- `editor_init_buttons(buttons, editor)` in [`field_visibility.py`](../field_visibility.py)

When the user clicks the button, Anki calls:

- `toggle_field_visibility(editor)`

At this moment, the add-on does not inspect the DOM to decide what mode it is in.
Instead, it flips persistent config state.

What happens:

1. get the current note type
2. load the config
3. read `field_visibility_disabled`
4. add the note type to that list
5. save the config

This means:

- for this note type, field hiding is now temporarily disabled

The function then:

- sets `_TOGGLE_BYPASS_UNTIL` to a short future timestamp
- calls `_reset_visibility(...)`
- schedules a button label refresh

Visible result:

- all fields become visible
- the button label changes to `Hide Fields` or `Show Fields` depending on the current wording logic

Conceptually, this click means:

- stop hiding fields for this note type right now

## 4. User Clicks `Hide Fields` Again

On the next click, `toggle_field_visibility(editor)` runs again.

This time the note type is already in `field_visibility_disabled`, so the function:

1. removes the note type from that list
2. saves the config
3. clears `_TOGGLE_BYPASS_UNTIL`

That means:

- field hiding is active again for this note type

The function then:

- rebuilds hide JS with `_hide_fields_js(...)`
- runs it immediately
- schedules a couple more delayed runs
- may reload the note through `editor.loadNote()` or `call_after_note_saved(...)`

Visible result:

- only the configured fields remain visible
- the button label is updated again

Conceptually, this click means:

- re-enable the configured visibility rules

## What State Actually Changes

There are three important pieces of state during this interaction.

### Browser state

- `_LAST_BROWSER` in [`browser_utils.py`](../browser_utils.py)
- tells the add-on which Browser instance is current

### Persistent config state

- `field_visibility_map`
- `field_visibility_disabled`

These live in Anki config and survive between interactions.

### Short-lived runtime state

- `_TOGGLE_BYPASS_UNTIL` in [`field_visibility.py`](../field_visibility.py)

This is a timing flag used during toggle transitions so the note does not immediately get re-hidden during reload timing.

## Short Summary

The typical cycle is:

1. Browser opens
2. current browser is registered
3. note loads
4. add-on decides hide vs reset
5. user clicks toggle
6. config state flips for that note type
7. add-on either resets all fields or reapplies hiding

So the core of the program is really:

- hook into Browser editor lifecycle
- read config
- choose hide or reset
- inject JavaScript into the editor DOM
