"""
Entity Annotator Package
A modern, refactored entity annotation tool for NLP tasks
"""

from .entity_annotator import EntityAnnotator
from .ui_components import Button, Popup, InputDialog
from .file_browser import FileBrowser
from .navigation import NavigationBar, ShortcutHelp
from .utils import load_settings, save_settings, load_jsonl, save_jsonl

__version__ = "2.0.0"
__all__ = [
    "EntityAnnotator",
    "Button",
    "Popup",
    "InputDialog",
    "FileBrowser",
    "NavigationBar",
    "ShortcutHelp",
    "load_settings",
    "save_settings",
    "load_jsonl",
    "save_jsonl",
]


