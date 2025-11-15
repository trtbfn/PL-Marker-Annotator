# PLMarker Entity Annotator

An annotation tool for Named Entity Recognition (NER) and Relation Extraction tasks. Built with Python and Pygame, featuring DuckDB storage.

# Presentation
[presentation](https://github.com/trtbfn/PL-Marker-Annotator/blob/main/PL-Marker_annotation_tool_presentation.pdf) (russian). Project have been presented on [conference-biennale "Information Technologies in Humanitarian Research"](http://dhri.ru/wp-content/uploads/2025/11/SFU-DH-2025.pdf). 

## 📦 Quick Start

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python main.py
```

## 🖥️ Usage

### Basic Workflow

1. **Open a file** - Click "Open File" or press `Ctrl+O`
2. **Annotate entities** - Click and drag to select tokens
3. **Create relations** - Hover on entity, press `E`, click target
4. **Save work** - Auto-saves after each change
5. **Export** - Click "Export to JSONL" when done

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file browser |
| `Ctrl+S` | Manual save |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `E` | Create relation |
| `Delete` | Delete entity/relation |
| `F1` | Show help |
| `←` `→` | Previous/Next document |

---

## 📊 Input Format

The application accepts **JSONL** files with pre-tokenized sentences:

```json
{
  "doc_key": "unique_id",
  "sentences": [
    ["John", "works", "at", "Google", "in", "California", "."]
  ],
  "ner": [
    [[0, 0, "PERSON"], [3, 3, "ORG"], [5, 5, "LOC"]]
  ],
  "relations": [
    [[0, 0, 3, 3, "WORKS_AT"], [3, 3, 5, 5, "LOCATED_IN"]]
  ]
}
```

**Format Details:**
- Each line is a separate JSON document
- `ner` arrays: `[start_idx, end_idx, "TYPE"]`
- `relations` arrays: `[src_start, src_end, tgt_start, tgt_end, "TYPE"]`


## 📄 License

MIT License - See LICENSE file for details

