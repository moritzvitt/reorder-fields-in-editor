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

1. Open Anki and go to **Tools → Editor Focus Mode Configuration**
2. Configure which fields should be visible for each note type (see Configuration section below)
3. When editing notes, only the configured fields will be visible
4. Use the **"Hide Fields"** button in the editor to temporarily show all fields

### Toggle Button

- **"Hide Fields"**: Hides fields according to your configuration
- **"Show Fields"**: Temporarily shows all fields for the current note type
- The toggle state is remembered per note type

## Configuration

The configuration is done through a JSON editor accessible via **Tools → Editor Focus Mode Configuration**.

### Field Visibility Map

The main configuration is a JSON object where:
- **Keys**: Note type names (e.g., "Basic", "Cloze", "Moritz Language Reactor")
- **Values**: Arrays of field names that should remain visible

#### Example Configuration

```json
{
  "Basic": ["Front", "Back"],
  "Cloze": ["Text", "Extra"],
  "Moritz Language Reactor": ["Lemma", "Cloze", "Synonyms", "Japanese Notes"]
}
```

#### Default Configuration

If no configuration is set, the addon uses:
```json
{
  "Moritz Language Reactor": ["Lemma", "Cloze", "Synonyms", "Japanese Notes"]
}
```

### How It Works

- When you open a note for editing, the addon checks the note type
- It looks up the allowed fields for that note type in your configuration
- Fields not in the allowed list are hidden using CSS
- The toggle button allows you to temporarily override this behavior

## Advanced Features

### Browser Integration

The addon integrates with Anki's browser to track the current context, enabling future batch processing features.

### Debug Information

For troubleshooting, the addon can generate debug information about field detection. Check the `field_visibility_debug.txt` file in the addon directory.

## Future Plans

- **Layout Rotation Button**: Add a button that rotates through multiple predefined field layouts for the current note type
- **Multiple Visibility Presets**: Allow one note type to define several subsets of visible fields instead of just one
- **Faster Note Inspection**: Make it easier to switch between different editing contexts without opening the full field list every time

## Compatibility

- **Anki Version**: 2.1.0+
- **Platforms**: Windows, macOS, Linux
- **Python**: 3.6+ (bundled with Anki)

## Troubleshooting

### Fields Not Hiding

- Ensure the note type name in your configuration exactly matches the note type name in Anki
- Check that field names are spelled correctly
- Try restarting Anki after configuration changes

### Toggle Button Not Working

- Make sure you're in the note editor (not the browser)
- The button appears on the right side of the editor toolbar

### Configuration Not Saving

- Ensure the JSON is valid (use a JSON validator)
- Note type names and field names should be strings
- Field lists should be arrays of strings

## Development

### Project Structure

```
editor_focus_mode/
├── __init__.py          # Main addon entry point
├── config.py            # Configuration management
├── field_visibility.py  # Core visibility logic
├── ui.py               # Configuration dialog
├── browser_utils.py    # Browser integration utilities
├── flow.py             # Editor flow tracking
├── manifest.json       # Anki addon manifest
└── docs/               # Documentation
```

### Architecture Guide

For a code-level walkthrough of the runtime flow, hook registration, toggle behavior, and module responsibilities, see [`docs/architecture.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/architecture.md).

For a concise DOM selector reference, see [`docs/wrappers.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/wrappers.md).

For a user-journey walkthrough of opening the Browser, selecting a note, and toggling visibility, see [`docs/user-flow.md`](/Users/moritzvitt/src/addons/editor_focus_mode/docs/user-flow.md).

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in Anki
5. Submit a pull request

### Building and Testing

1. Copy the addon folder to Anki's addons directory
2. Restart Anki
3. Test with different note types and configurations
4. Check the Anki console for any errors

## License

This addon is released under the MIT License. See LICENSE file for details.

## Support

For issues, questions, or feature requests:
- Create an issue on the GitHub repository
- Check the Anki forums for community support

## Changelog

### Version 0.1.0
- Initial release
- Field visibility control
- Configuration dialog
- Toggle button functionality
- Basic browser integration</content>
<parameter name="filePath">/Users/moritzvitt/src/addons/editor_focus_mode/README.md
