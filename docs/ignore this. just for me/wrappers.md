# Editor Wrapper Reference

These are the current editor wrapper names confirmed against the local Anki source in `/Users/moritzvitt/src/Anki`.

## Current Selectors

- `.note-editor`
  - Root editor container in `ts/editor/NoteEditor.svelte`
- `.fields`
  - Wrapper around the full field list in `ts/editor/Fields.svelte`
- `.field-container`
  - Outer wrapper for one field in `ts/editor/EditorField.svelte`
- `[data-index]`
  - Stable field index stored on `.field-container`
- `.label-container`
  - Sticky top label bar for a field
- `.collapse-label`
  - Clickable collapse/expand label wrapper
- `.label-name`
  - Actual field name text
- `.editor-field`
  - Main editable body wrapper for the field
- `.editing-area`
  - Wrapper around the field inputs
- `.rich-text-input`
  - Rich text input wrapper
- `.plain-text-input`
  - Plain text input wrapper

## Important Notes

- Current Anki does not appear to expose `data-field-name` in the editor DOM.
- Current Anki does not use `.field-row` or `.field-row-wrapper` in the editor source.
- The rich text editable is attached inside a shadow root, so plain `document.querySelectorAll('[contenteditable="true"]')` is not a reliable way to discover rich text fields.

## Selector Strategy For This Add-on

For field hiding, the most stable current anchors are:

- `.field-container`
- `.label-name`
- `[data-index]`

That is why the add-on should prefer:

1. Match by visible field name from `.label-name`
2. Fall back to `data-index` when needed
3. Hide/show the whole `.field-container`
