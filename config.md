# Editor Focus Mode Config

This add-on stores its configuration as a JSON dictionary.

## Keys

### `field_visibility_map`

Maps note type names to the list of fields that should remain visible.

Example:

```json
{
  "Basic": ["Front", "Back"],
  "Cloze": ["Text", "Extra"]
}
```

### `field_visibility_disabled`

Stores note types for which field hiding is temporarily disabled.

This is managed by the add-on when the toggle button is used, and usually does not need to be edited manually.
