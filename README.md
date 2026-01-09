# BFont Editor

A Blender add-on for editing TrueType fonts (TTF) directly in Blender's 3D viewport.

## Description

BFont Editor allows you to import TTF font files as editable curve objects in Blender, edit them using Blender's powerful curve editing tools, and export them back as TTF files. Perfect for font designers who want to leverage Blender's modeling capabilities.

## Requirements

### Blender Version
- Blender 4.2.0 or higher

### Python Dependencies
- **fonttools** - Required for reading and writing TTF files

## Installation

### 1. Install Python Dependencies

The add-on requires the `fonttools` library to be installed in Blender's Python environment.

**Windows (Blender 5.0):**
```powershell
& "D:\Softs\Blender\5.0\5.0\python\bin\python.exe" -m pip install fonttools
```

**Windows (Blender 4.5):**
```powershell
& "D:\Softs\Blender\4.5\4.5\python\bin\python.exe" -m pip install fonttools
```

**macOS/Linux:**
```bash
/path/to/blender/python/bin/python3.11 -m pip install fonttools
```

To find your Blender Python path:
1. Open Blender
2. Go to Scripting workspace
3. Run: `import sys; print(sys.executable)`

### 2. Install the Add-on

1. Download or clone this repository
2. In Blender: Edit → Preferences → Add-ons → Install
3. Navigate to the `bfonteditor` folder and select it
4. Enable "BFont Editor" in the add-ons list

## Usage

### Importing a Font

1. Open the **N-panel** in the 3D Viewport (press `N`)
2. Navigate to the **BFont** tab
3. Click **Import TTF**
4. Select your `.ttf` file
5. All glyphs will be imported as curve objects with bounding guides

### Editing Glyphs

- Each glyph is a Blender curve object parented to a guide mesh
- The guide mesh shows: Circle within square within square (for reference)
- Select any glyph and enter Edit Mode (`Tab`) to modify the curves
- Use Blender's curve editing tools (extrude, scale, rotate, etc.)

### Exporting Changes

1. Make your edits to the glyph curves
2. Click **Export TTF** (no selection needed)
3. The font file will be updated with your changes

### Utilities

#### Organization
- **Group to Center**: Moves all guide meshes to origin
- **Group Orderly**: Arranges glyphs in a grid mosaic (20 per row by default)
- **Toggle Guides**: Show/hide all bounding guide meshes

#### Marking Glyphs
- **Set Used**: Mark selected glyphs as used (white color)
- **Set Unused**: Mark selected glyphs as unused (dark gray color)

#### Text Display
- **Display as Text**: Creates a Blender text object showing all characters in unicode order
- **Refresh Text**: Updates the text display with current font data

## Features

- ✅ Import TTF/OTF fonts as editable Blender curves
- ✅ Export modified curves back to TTF format
- ✅ Visual bounding guides (circle within squares)
- ✅ Automatic cubic-to-quadratic Bezier conversion
- ✅ Support for all glyphs (including empty ones)
- ✅ Non-destructive workflow (original font metadata preserved)
- ✅ Batch operations (no selection needed for most operations)
- ✅ Visual marking system for tracking edited glyphs
- ✅ Font preview as Blender text object

## Technical Details

### File Structure
```
bfonteditor/
├── __init__.py          # Add-on registration
├── operators.py         # All operator classes
├── ui.py               # UI panel definitions
├── font_utils.py       # Core font import/export logic
├── blender_manifest.toml  # Blender add-on manifest
└── README.md           # This file
```

### How It Works

1. **Import**: Uses `fontTools` to read TTF file, converts quadratic Bezier curves to cubic for Blender
2. **Edit**: Standard Blender curve editing
3. **Export**: Converts cubic curves back to quadratic using `Cu2QuPen`, updates TTF file

### Coordinate Systems

- Font units are scaled to Blender units (typically 1/unitsPerEm)
- Origin is at the baseline (standard font coordinate system)
- Guide meshes are offset by `x: +0.5m, y: -0.097m`

## Limitations

- Only supports TrueType fonts (TTF) with glyf table
- Requires existing font file for export (creates from existing metadata)
- Complex font features (OpenType features, kerning) are preserved but not editable

## Troubleshooting

### "fonttools library not found"
Install fonttools in Blender's Python environment (see Installation section above)

### Curves appear straight after export
Make sure you're using smooth handles (not VECTOR type) for curved segments

### Export fails
Ensure you imported a font first - the export uses the stored file path

## License

[Add your license here]

## Author

[Your Name]

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
