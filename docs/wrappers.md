Yes. I checked the local Anki frontend in `/Users/moritzvitt/src/Anki`, and the precise current editor wrapper names are different from several selectors in your add-on.

The important current wrappers are:

- Root editor container: `.note-editor` in [NoteEditor.svelte](/Users/moritzvitt/src/Anki/ts/editor/NoteEditor.svelte#L647)
- Field list container: `.fields` in [Fields.svelte](/Users/moritzvitt/src/Anki/ts/editor/Fields.svelte#L14)
- Per-field outer wrapper: `.field-container` in [EditorField.svelte](/Users/moritzvitt/src/Anki/ts/editor/EditorField.svelte#L95)
- Stable field index attribute: `data-index={index}` on that same `.field-container` in [EditorField.svelte](/Users/moritzvitt/src/Anki/ts/editor/EditorField.svelte#L101)
- Main field body wrapper: `.editor-field` in [EditorField.svelte](/Users/moritzvitt/src/Anki/ts/editor/EditorField.svelte#L106)
- Label wrapper: `.label-container` in [LabelContainer.svelte](/Users/moritzvitt/src/Anki/ts/editor/LabelContainer.svelte#L15)
- Clickable collapse/label element: `.collapse-label` in [CollapseLabel.svelte](/Users/moritzvitt/src/Anki/ts/editor/CollapseLabel.svelte#L18)
- Actual field name element: `.label-name` in [LabelName.svelte](/Users/moritzvitt/src/Anki/ts/editor/LabelName.svelte#L6)

The field composition is visible in [NoteEditor.svelte](/Users/moritzvitt/src/Anki/ts/editor/NoteEditor.svelte#L685):
- `EditorField`
- inside it `LabelContainer`
- inside that `LabelName`
- then the editable body

The input wrappers are:
- `.editing-area` in [EditingArea.svelte](/Users/moritzvitt/src/Anki/ts/editor/EditingArea.svelte#L99)
- `.rich-text-input` in [RichTextInput.svelte](/Users/moritzvitt/src/Anki/ts/editor/rich-text-input/RichTextInput.svelte#L232)
- `.rich-text-editable` in [RichTextInput.svelte](/Users/moritzvitt/src/Anki/ts/editor/rich-text-input/RichTextInput.svelte#L244)
- `.plain-text-input` in [PlainTextInput.svelte](/Users/moritzvitt/src/Anki/ts/editor/plain-text-input/PlainTextInput.svelte#L155)

Two especially important findings for your add-on:

- `data-field-name` does not appear to exist in the current Anki editor source.
- `.field-row`, `.field-row-wrapper`, `.fieldname`, and `.field-name` also do not appear in the current editor source.

That means these selectors in your add-on are effectively legacy guesses, not current Anki structure.

One more big detail: the rich-text editable is attached into a shadow root via `attachShadow({ mode: "open" })` in [RichTextInput.svelte](/Users/moritzvitt/src/Anki/ts/editor/rich-text-input/RichTextInput.svelte#L103). So `document.querySelectorAll('[contenteditable="true"]')` is not a reliable way to discover rich-text editors from the light DOM.

So if you want the most stable current selectors for field hiding, I’d build around:
- `.field-container`
- `.editor-field`
- `.label-container`
- `.label-name`
- `[data-index]`

and not around:
- `[data-field-name]`
- `.field-row`
- `.field-row-wrapper`
- `.fieldname`
- `.field-name`

If you want, I can patch `field_visibility.py` next so it targets the current Anki DOM structure precisely.