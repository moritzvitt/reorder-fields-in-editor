# Editor Focus Mode

An Anki addon that helps you focus on specific fields in the note editor by hiding irrelevant fields based on note type configuration.

## Features

- **Field Visibility Control**: Configure which fields are visible for each note type
- **Toggle Button**: Temporarily show/hide fields with a single click
- **Per-Note-Type Configuration**: Different field visibility settings for different note types
- **Automatic Application**: Fields are hidden automatically when editing notes

## Installation

1. Download the addon files
2. Place the `editor_focus_mode` folder in your Anki addons directory:
   - Windows: `%APPDATA%\Anki2\addons21\`
   - macOS: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`
3. Restart Anki

Alternatively, you can install it directly from Anki by entering the addon code (if available on AnkiWeb).

## Usage

### Basic Usage

1. Open Anki's add-on config for this add-on
2. Configure which fields should be visible for each note type
3. When editing notes, only the configured fields will be visible
4. Use the **"Layout"** button in the editor to rotate through the configured field subsets
5. Use the **"Show Fields"** button in the editor to temporarily show all fields

### Toggle Button

- **"Show Fields"**: Temporarily shows all fields for the current note type
- **"Hide Fields"**: Re-enables field hiding for the current note type
- The toggle state is remembered per note type

### Layout Button

- **"Layout 1/3"**: Shows the first configured field subset for the current note type
- Clicking the button rotates through the available layouts
- The current layout index is remembered per note type

## Configuration

The configuration is done through Anki's native add-on config system with [`config.json`](../config.json) providing the defaults and [`config.md`](../config.md) documenting the keys.

### Field Visibility Layouts

The main configuration is a JSON object where:

- **Keys**: Note type names such as `Basic`, `Cloze`, or `Moritz Language Reactor`
- **Values**: Arrays of layouts, where each layout is a list of field names that should remain visible

Example:

```json
{
  "Basic": [
    ["Front", "Back"],
    ["Front"]
  ],
  "Moritz Language Reactor": [
    ["Lemma", "Cloze", "Synonyms", "Japanese Notes"],
    ["Cloze"],
    ["Cloze", "Lemma"]
  ]
}
```

Default:

```json
{
  "Moritz Language Reactor": [
    ["Lemma", "Cloze", "Synonyms", "Japanese Notes"],
    ["Cloze"],
    ["Cloze", "Lemma"]
  ]
}
```

### How It Works

- When you open a note for editing, the add-on checks the note type
- It looks up the available layouts for that note type in your configuration
- The active layout determines which fields remain visible
- The toggle button allows you to temporarily override this behavior

## Advanced Features

### Browser Integration

The add-on integrates with Anki's Browser to track the current context, enabling Browser-scoped editor behavior.

### Debug Information

For troubleshooting, the add-on can generate debug information about field detection. Check `field_visibility_debug.txt` in the add-on directory.

## Planned Features

- **More Layout Presets**: Allow one note type to define more than the initial three subsets of visible fields
- **Named Layouts**: Support human-readable layout names instead of just numbered rotation
- **Faster Note Inspection**: Make it easier to switch between different editing contexts without opening the full field list every time

## Compatibility

- **Anki Version**: 2.1.0+
- **Platforms**: Windows, macOS, Linux
- **Python**: Bundled with Anki

## Troubleshooting

### Fields Not Hiding

- Ensure the note type name in your configuration exactly matches the note type name in Anki
- Check that field names are spelled correctly
- Try restarting Anki after configuration changes

### Toggle Button Not Working

- Make sure you're in the note editor
- The button appears on the right side of the editor toolbar

### Configuration Not Saving

- Ensure the JSON is valid
- Note type names and field names should be strings
- Field lists should be arrays of strings

## Development

### Project Structure

```text
editor_focus_mode/
├── __init__.py
├── config.py
├── field_visibility.py
├── browser_utils.py
├── config.json
├── config.md
├── manifest.json
└── docs/
```

### Further Reading

- Architecture overview: [`architecture.md`](./architecture.md)
- Wrapper reference: [`wrappers.md`](./wrappers.md)
- User walkthrough: [`user-flow.md`](./user-flow.md)

## License

This addon is released under the MIT License. See [`LICENSE`](../LICENSE) for details.
