# Editor Focus Mode Config

This add-on stores its configuration as a JSON dictionary.

## Keys

### `field_visibility_layouts`

Maps note type names to one or more field layouts.

Example:

```json
{
  "Basic": [
    ["Front", "Back"],
    ["Front"]
  ],
  "Cloze": [
    ["Text", "Extra"],
    ["Text"]
  ]
}
```

Each inner list is one layout. The layout button rotates through the available layouts for the current note type.

### `field_visibility_active_layouts`

Stores the currently selected layout index for each note type.

Example:

```json
{
  "Basic": 0,
  "Cloze": 1
}
```

### `field_visibility_disabled`

Stores note types for which field hiding is temporarily disabled.

This is managed by the add-on when the toggle button is used, and usually does not need to be edited manually.
