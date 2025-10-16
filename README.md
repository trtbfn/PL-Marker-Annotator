# Entity Annotator v2.0 - Refactored

A modern, modular entity and relation annotation tool built with Pygame.

## 🎯 Key Improvements

### **Better Code Organization**
- Modular structure with separate files for different components
- Clear separation of concerns
- Easier to maintain and extend

### **New Features**
- ✨ Modern file browser with recent files support
- 📊 Navigation bar with progress tracking
- ⌨️ Comprehensive keyboard shortcuts
- ❓ Built-in help overlay (press F1)
- 🖱️ Drag & drop file support
- 🎨 Improved UI with better visual feedback

### **Enhanced UX**
- Faster navigation (Ctrl+Arrow to jump 10 documents)
- Quick jump to any document (Ctrl+G)
- Persistent history (undo/redo saved between sessions)
- Better visual indicators for progress
- Cleaner, more professional interface

## 📁 Project Structure

```
incep/plmarker_annotator/
├── __init__.py              # Package initialization
├── main.py                  # Entry point
├── entity_annotator.py      # Main application class
├── ui_components.py         # Button, Popup, InputDialog
├── file_browser.py          # File loading dialog
├── navigation.py            # Navigation bar & help overlay
├── utils.py                 # Settings, history, data I/O
├── entity_annotator_part2.py  # (Can be deleted - merged into main)
└── README.md               # This file
```

## 🚀 Usage

### Running the Application

```bash
# From the project root
python incep/plmarker_annotator/main.py [optional_file.jsonl]

# Or as a module
python -m incep.plmarker_annotator.main [optional_file.jsonl]
```

### Quick Start

1. **Open a file**: Press `Ctrl+O` or click "Open File" button
2. **Navigate**: Use arrow keys or "Prev/Next" buttons
3. **Annotate entities**: 
   - Click and drag to select tokens
   - Choose entity type from popup
4. **Create relations**:
   - Right-click on an entity
   - Drag to another entity
   - Select relation type
5. **Save**: Press `Ctrl+S` or click "Save" button

## ⌨️ Keyboard Shortcuts

### General
| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file browser |
| `Ctrl+S` | Save annotations |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `F1` or `?` | Show/hide help overlay |
| `Esc` | Close dialogs |

### Navigation
| Shortcut | Action |
|----------|--------|
| `Left/Right Arrow` | Previous/Next document |
| `Ctrl+Left/Right` | Jump 10 documents backward/forward |
| `Home` | First document |
| `End` | Last document |
| `Ctrl+G` | Jump to specific document |
| `Page Up/Down` | Scroll document up/down |

### Annotation
| Shortcut | Action |
|----------|--------|
| `Click + Drag` | Select tokens for entity |
| `Right Click Entity` | Start creating relation |
| `Left Click Entity` | Select/deselect entity |
| `D` | Delete selected entity |
| `E + Hover` | Quick entity highlight (from old version) |

## 🎨 Features

### File Browser
- Navigate directories with up/home buttons
- View recent files (last 10)
- File size display
- Supports .jsonl and .json files
- Drag & drop support (drop files into window)

### Navigation Bar
- Visual progress bar
- Document counter (current/total)
- Quick jump to any document number

### Annotation Tools
- Entity highlighting with color coding
- Relation arrows with Bezier curves
- Multi-line entity support
- Undo/redo with persistent history
- Custom entity/relation types

## 🛠️ Configuration

### Settings File
Location: `incep/settings.json`

```json
{
  "entity_colors": {
    "Dataset": [255, 105, 180],
    "Task": [30, 144, 255],
    "Method": [50, 205, 50]
  },
  "relation_colors": {
    "Used-For": [0, 153, 255],
    "Part-Of": [255, 102, 0]
  },
  "known_entities": [],
  "known_relations": [],
  "custom_entities": [],
  "custom_relations": []
}
```

### History File
Location: `incep/history.pickle`
- Stores last 25 undo/redo actions
- Persists between sessions

### Recent Files
Location: `incep/recent_files.json`
- Stores paths to last 10 opened files

## 📝 Data Format

Input files should be in JSONL format with the following structure:

```json
{
  "doc_id": "document_123",
  "sentences": [
    ["token1", "token2", "token3"],
    ["token4", "token5"]
  ],
  "ner": [
    [[0, 1, "Entity-Type"], [3, 4, "Another-Type"]]
  ],
  "relations": [
    [[0, 1, 3, 4, "Relation-Type"]]
  ]
}
```

### Entity Format
`[start_token_idx, end_token_idx, entity_type]`

### Relation Format
`[src_start, src_end, tgt_start, tgt_end, relation_type]`

## 🐛 Troubleshooting

### Application won't start
- Ensure pygame is installed: `pip install pygame`
- Check that all module files are present
- Verify Python version (3.7+)

### File won't load
- Check file format (must be valid JSONL)
- Verify file path and permissions
- Check console for error messages

### Changes not saving
- Ensure you have write permissions
- Check that file path is valid
- Try "Save As" to a different location

## 🔄 Migration from Old Version

The old version (`pg copy.py`) is now superseded by this refactored version.

**Key Differences:**
1. Modular file structure vs single file
2. File browser instead of hardcoded path
3. Better keyboard navigation
4. More consistent state management

**To migrate:**
1. Your existing annotation files work without changes
2. Settings are stored in the same format
3. Just use the new `main.py` entry point

## 💡 Tips

1. **Faster Annotation**: Master keyboard shortcuts to speed up workflow
2. **Recent Files**: Use the file browser's recent files list for quick access
3. **Batch Navigation**: Use Ctrl+Arrow to skip through documents quickly
4. **Visual Progress**: Watch the progress bar to track annotation progress
5. **Help Reference**: Press F1 anytime to see all shortcuts

## 🎓 Best Practices

1. Save frequently (Ctrl+S)
2. Use consistent naming for entity/relation types
3. Organize annotation files in dedicated folders
4. Use recent files feature for active projects
5. Take advantage of undo/redo for corrections

## 📊 Performance

- Handles documents with 1000+ tokens smoothly
- Efficient rendering with viewport clipping
- Minimal memory footprint
- 60 FPS UI refresh rate

## 🔧 Extending

To add new features:

1. **New UI Component**: Add to `ui_components.py`
2. **New Tool**: Extend `EntityAnnotator` class methods
3. **Custom Colors**: Modify `DEFAULT_SETTINGS` in `utils.py`
4. **Keyboard Shortcuts**: Update `handle_key_down()` method

## 📞 Support

For issues or questions:
1. Check this README
2. Review keyboard shortcuts (F1)
3. Check console output for error messages
4. Review the code comments (well-documented)

## 🎉 Version 2.0 Features

- ✅ Modular architecture
- ✅ File browser dialog
- ✅ Navigation improvements
- ✅ Keyboard shortcut help
- ✅ Recent files support
- ✅ Drag & drop files
- ✅ Progress tracking
- ✅ Persistent history
- ✅ Better error handling
- ✅ Improved UI/UX

---

**Happy Annotating!** 🎯



