# 🚀 Quick Start Guide

Get started with the refactored Entity Annotator in 5 minutes!

## ⚡ Installation

```bash
# 1. Ensure pygame is installed
pip install pygame

# 2. Navigate to your project directory
cd F:\repos\optihyp

# 3. Run the application
python incep/plmarker_annotator/main.py
```

## 🎯 First Run

When you first start the application:

1. Press `Ctrl+O` to open the file browser
2. Navigate to your `.jsonl` file
3. Click "Load File"

Or simply drag & drop a `.jsonl` file into the window!

## 💡 Essential Shortcuts (Learn These First)

| What | How |
|------|-----|
| Open file | `Ctrl+O` |
| Save work | `Ctrl+S` |
| Get help | `F1` |
| Navigate docs | `←` / `→` |
| Jump to doc | `Ctrl+G` |

## 📝 Basic Workflow

### Annotate an Entity
1. Click and drag to select tokens
2. Choose entity type from the popup
3. Click "Save"

### Create a Relation
1. Right-click on an entity
2. Drag to another entity
3. Choose relation type
4. Click "Save"

### Delete Something
1. Click to select an entity
2. Press `D` to delete

## ⌨️ Most Used Shortcuts

```
Ctrl+O  → Open file
Ctrl+S  → Save
Ctrl+Z  → Undo
Ctrl+Y  → Redo
F1      → Show all shortcuts
←/→     → Navigate documents
Ctrl+G  → Jump to document
D       → Delete selected
Esc     → Close dialogs
```

## 🎨 Understanding the UI

```
┌─────────────────────────────────────────┐
│ Entity Annotator         [Status]       │
│ [Undo] [Redo] [Save] [Open] [+E] [+R]  │  ← Toolbar
│ [<Prev] [Next>]  Doc: 5                 │  ← Navigation
│ [████████░░░░░░] 5/10  Go to: [___]     │  ← Progress Bar
├─────────────────────────────────────────┤
│                                         │
│  Your document text appears here...     │  ← Document Area
│  [Highlighted entities] show colored    │
│  Relations shown on hover              │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

## 💪 Power User Tips

1. **Navigate Fast**: Use `Ctrl+Left/Right` to jump 10 documents
2. **Quick Access**: Recent files appear in the file browser
3. **Scroll Easy**: Use `Page Up/Down` instead of mouse wheel
4. **See Progress**: Watch the progress bar to track completion
5. **Get Help**: Press `F1` anytime to see all shortcuts

## 🔥 Pro Workflow

```
Ctrl+O              → Open your annotation file
Ctrl+G, type "50"   → Jump to document 50
Click + Drag        → Select tokens for entity
Choose type         → Pick from popup
Ctrl+S              → Save progress
Right-click entity  → Start creating relation
Drag to target      → Complete relation
Ctrl+→ (repeatedly) → Move to next documents
Ctrl+S              → Save when done
```

## 🎓 Learn More

- Full shortcuts: Press `F1` in the application
- Detailed docs: See `README.md`
- Technical details: See `REFACTORING_SUMMARY.md`

## ❓ Common Questions

**Q: Where's my old file (`pg copy.py`)?**
A: It's still there! This is the new, improved version. Use `main.py` instead.

**Q: Do my old annotation files still work?**
A: Yes! 100% compatible with existing files.

**Q: How do I add custom entity types?**
A: Click "Add Entity Type" button and enter the name.

**Q: Can I use my old settings?**
A: Yes! Uses the same `settings.json` file.

**Q: How do I see my progress?**
A: Look at the progress bar showing X/Total documents.

## 🐛 Something Wrong?

1. Check the console for error messages
2. Try `Ctrl+Z` to undo recent changes
3. Press `Esc` to close any stuck dialogs
4. Restart the application if needed
5. Check `README.md` for troubleshooting

## 🎉 You're Ready!

Now you know the basics. Start annotating and discover more features as you go!

**Remember**: Press `F1` anytime to see all shortcuts!

Happy Annotating! 🎯


