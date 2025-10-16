"""
Utility Functions
Settings management, history persistence, and data loading
"""
import json
import os
import pickle
from typing import List, Dict, Tuple


# Default settings
DEFAULT_SETTINGS = {
    "entity_colors": {
        "Dataset": (255, 105, 180),
        "Task": (30, 144, 255),
        "Method": (50, 205, 50),
        "a": (153, 50, 204),
        "v": (138, 43, 226)
    },
    "relation_colors": {
        "Used-For": (0, 153, 255),
        "Part-Of": (255, 102, 0),
        "Synonym-Of": (153, 0, 204),
        "Evaluated-With": (204, 0, 102),
        "SubClass-Of": (255, 153, 0),
        "Compare-With": (0, 153, 102)
    },
    "known_entities": [],
    "known_relations": [],
    "custom_entities": [],
    "custom_relations": []
}


def load_settings(settings_file='incep/settings.json'):
    """Load settings from file or create with defaults"""
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = default_value
                
                return loaded_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    return DEFAULT_SETTINGS.copy()


def save_settings(settings, settings_file='incep/settings.json'):
    """Save settings to file"""
    try:
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_history(history_file='incep/history.pickle'):
    """Load undo/redo history from file"""
    try:
        if os.path.exists(history_file):
            with open(history_file, 'rb') as f:
                history = pickle.load(f)
                return history.get("undo_stack", []), history.get("redo_stack", [])
    except Exception as e:
        print(f"Error loading history: {e}")
    return [], []


def save_history(undo_stack, redo_stack, history_file='incep/history.pickle'):
    """Save undo/redo history to file"""
    try:
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        history = {
            "undo_stack": list(undo_stack)[-25:],  # Keep only last 25
            "redo_stack": list(redo_stack)[-25:]
        }
        with open(history_file, 'wb') as f:
            pickle.dump(history, f)
    except Exception as e:
        print(f"Error saving history: {e}")


def read_jsonl(file_path):
    """Read JSONL file and yield documents"""
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                yield data
            except json.JSONDecodeError:
                continue
            except Exception:
                continue


def load_jsonl(input_path):
    """Load all documents from JSONL file"""
    content = []
    for obj in read_jsonl(input_path):
        content.append(obj)
    return content


def save_jsonl(documents: List[Dict], output_path: str):
    """Save documents to JSONL file"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        print(f"Error saving JSONL: {e}")
        return False


def generate_random_color(seed_text: str) -> Tuple[int, int, int]:
    """Generate a deterministic random color from text"""
    r = (hash(seed_text) % 200) + 50
    g = ((hash(seed_text) * 2) % 200) + 50
    b = ((hash(seed_text) * 3) % 200) + 50
    return (r, g, b)


def normalize_type(entity_type):
    """Normalize entity/relation type (handle list or string)"""
    if isinstance(entity_type, list):
        return entity_type[0] if entity_type else "Unknown"
    return entity_type


