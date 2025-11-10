"""
Configuration and Constants for Entity Annotator
Centralized settings for colors, dimensions, and behavior
"""

# ============================================================================
# WINDOW SETTINGS
# ============================================================================
DEFAULT_WINDOW_WIDTH = 1400
DEFAULT_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700
FPS = 60

# ============================================================================
# COLORS - Modern Material Design Inspired Palette
# ============================================================================

# Background colors
COLOR_BG_MAIN = (248, 249, 250)  # Light gray background
COLOR_BG_TOOLBAR = (255, 255, 255)  # White toolbar
COLOR_BG_DOCUMENT = (255, 255, 255)  # White document area
COLOR_BG_HOVER = (240, 242, 245)  # Subtle hover

# Border and separator colors
COLOR_BORDER_LIGHT = (222, 226, 230)
COLOR_BORDER_MEDIUM = (173, 181, 189)
COLOR_BORDER_DARK = (108, 117, 125)

# Text colors
COLOR_TEXT_PRIMARY = (33, 37, 41)
COLOR_TEXT_SECONDARY = (108, 117, 125)
COLOR_TEXT_DISABLED = (173, 181, 189)

# Accent colors (for buttons and highlights)
COLOR_PRIMARY = (13, 110, 253)  # Blue
COLOR_PRIMARY_HOVER = (10, 88, 202)
COLOR_PRIMARY_DARK = (8, 66, 152)

COLOR_SUCCESS = (25, 135, 84)  # Green
COLOR_SUCCESS_HOVER = (20, 108, 67)

COLOR_DANGER = (220, 53, 69)  # Red
COLOR_DANGER_HOVER = (176, 42, 55)

COLOR_WARNING = (255, 193, 7)  # Yellow
COLOR_WARNING_HOVER = (204, 154, 5)

COLOR_INFO = (13, 202, 240)  # Cyan
COLOR_INFO_HOVER = (10, 162, 192)

COLOR_SECONDARY = (108, 117, 125)  # Gray
COLOR_SECONDARY_HOVER = (86, 94, 100)

# Selection and highlight colors
COLOR_SELECTION = (255, 235, 59, 120)  # Yellow with alpha
COLOR_ENTITY_HOVER_OVERLAY = (33, 150, 243, 40)  # Blue overlay with alpha
COLOR_SCROLLBAR = (173, 181, 189)
COLOR_SCROLLBAR_HOVER = (108, 117, 125)

# ============================================================================
# DIMENSIONS
# ============================================================================

# Toolbar
TOOLBAR_HEIGHT = 140
TOOLBAR_PADDING = 15

# Buttons
BUTTON_WIDTH = 140
BUTTON_HEIGHT = 36
BUTTON_MARGIN = 10
BUTTON_BORDER_RADIUS = 6

# Navigation bar
NAV_BAR_HEIGHT = 35
NAV_BAR_MARGIN = 10

# Document container
DOC_CONTAINER_MARGIN = 15
DOC_CONTAINER_PADDING = 20

# Tokens and entities
TOKEN_PADDING = 7
TOKEN_LINE_HEIGHT_EXTRA = 4  # Controls height of entity boxes (lower = shorter)
ENTITY_BORDER_WIDTH = 1
ENTITY_BORDER_RADIUS = 4
ENTITY_PADDING = 4

# Sentence/line spacing
SENTENCE_SPACING = 15  # Vertical space between sentences (clean spacing, no lines)

# Performance optimizations
ENABLE_VIRTUAL_SCROLLING = True  # Only render visible tokens (huge performance boost)
VIEWPORT_BUFFER = 200  # Pixels above/below viewport to pre-render
RENDER_CACHE_SIZE = 500  # Number of text surfaces to cache

# Relations
RELATION_ARROW_SIZE = 12
RELATION_LINE_WIDTH = 2
RELATION_CURVE_HEIGHT = 80
RELATION_LABEL_PADDING_H = 10
RELATION_LABEL_PADDING_V = 6
RELATION_LABEL_OFFSET = 25

# Scrolling
SCROLL_SPEED = 40
SMOOTH_SCROLL_FACTOR = 0.2

# Popups and dialogs
POPUP_WIDTH = 300
POPUP_HEIGHT = 450
POPUP_BORDER_RADIUS = 8
POPUP_OVERLAY_ALPHA = 180

# ============================================================================
# FONTS
# ============================================================================
FONT_FAMILY = 'Segoe UI'  # Modern, clean font (falls back to Arial on non-Windows)
FONT_FAMILY_FALLBACK = 'Arial'

FONT_SIZE_TITLE = 20
FONT_SIZE_NORMAL = 16
FONT_SIZE_SMALL = 14
FONT_SIZE_TINY = 12

# ============================================================================
# BEHAVIOR SETTINGS
# ============================================================================

# History
MAX_UNDO_HISTORY = 50

# Auto-save
AUTO_SAVE_ENABLED = False
AUTO_SAVE_INTERVAL = 300  # seconds

# Animation
ENABLE_SMOOTH_SCROLLING = True
ENABLE_BUTTON_ANIMATIONS = True

# Visual feedback
SHOW_SAVE_NOTIFICATION_DURATION = 3000  # milliseconds
HOVER_FEEDBACK_DELAY = 100  # milliseconds

# Entity/Relation visibility
SHOW_ALL_RELATIONS = False  # If False, only show on hover
ENTITY_HOVER_EFFECT = True

# ============================================================================
# FILE SETTINGS
# ============================================================================
SETTINGS_FILE = 'settings.json'
HISTORY_FILE = 'history.pickle'
RECENT_FILES_FILE = 'recent_files.json'
MAX_RECENT_FILES = 10

# ============================================================================
# DEFAULT ENTITY COLORS (Material Design Colors)
# ============================================================================
DEFAULT_ENTITY_COLORS = {
    "Dataset": (233, 30, 99),      # Pink
    "Task": (33, 150, 243),         # Blue
    "Method": (76, 175, 80),        # Green
    "Metric": (255, 152, 0),        # Orange
    "Material": (156, 39, 176),     # Purple
    "Generic": (96, 125, 139),      # Blue Gray
    "OtherScientificTerm": (255, 193, 7),  # Amber
}

# ============================================================================
# DEFAULT RELATION COLORS
# ============================================================================
DEFAULT_RELATION_COLORS = {
    "Used-For": (33, 150, 243),       # Blue
    "Feature-Of": (76, 175, 80),      # Green
    "Hyponym-Of": (156, 39, 176),     # Purple
    "Part-Of": (255, 152, 0),         # Orange
    "Compare": (244, 67, 54),         # Red
    "Conjunction": (96, 125, 139),    # Blue Gray
}

# ============================================================================
# UI TEXT
# ============================================================================
WINDOW_TITLE = "PLMarker Entity Annotator"
STATUS_DEFAULT = "Ready - Press Ctrl+O to open a file or F1 for help"
STATUS_LOADING = "Loading document..."
STATUS_SAVING = "Saving..."
STATUS_SAVED = "✓ Saved successfully"
STATUS_ERROR = "✗ Error occurred"

# ============================================================================
# KEYBOARD SHORTCUTS (for documentation)
# ============================================================================
SHORTCUTS = {
    "General": [
        ("Ctrl + O", "Open file browser"),
        ("Ctrl + S", "Save annotations"),
        ("Ctrl + Z", "Undo last action"),
        ("Ctrl + Y", "Redo last action"),
        ("F1 or ?", "Show keyboard shortcuts"),
        ("Esc", "Close dialogs/popups"),
    ],
    "Navigation": [
        ("←/→", "Previous/Next document"),
        ("Ctrl + ←/→", "Jump 10 documents"),
        ("Home/End", "First/Last document"),
        ("Ctrl + G", "Go to document number"),
        ("Page ↑/↓", "Scroll document"),
    ],
    "Annotation": [
        ("Click + Drag", "Select tokens for entity"),
        ("Right Click Entity", "Start relation from entity"),
        ("Click Entity", "Select/deselect entity"),
        ("D", "Delete selected entity"),
        ("E + Hover", "Quick entity highlight"),
    ],
}

# ============================================================================
# VALIDATION
# ============================================================================
MIN_ENTITY_LENGTH = 1  # Minimum tokens in entity
MAX_ENTITY_LENGTH = 50  # Maximum tokens in entity
MIN_RELATION_DISTANCE = 0  # Minimum distance between entities for relation

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_entity_color(entity_type: str) -> tuple:
    """Get color for entity type with fallback"""
    return DEFAULT_ENTITY_COLORS.get(entity_type, DEFAULT_ENTITY_COLORS["Generic"])

def get_relation_color(relation_type: str) -> tuple:
    """Get color for relation type with fallback"""
    return DEFAULT_RELATION_COLORS.get(relation_type, COLOR_SECONDARY)

def rgba_to_rgb_with_alpha(rgb: tuple, alpha: int) -> tuple:
    """Convert RGB to RGBA tuple"""
    return (*rgb, alpha)

def lighten_color(color: tuple, factor: float = 0.3) -> tuple:
    """Lighten a color by a factor (0.0 to 1.0)"""
    return tuple(min(255, int(c + (255 - c) * factor)) for c in color[:3])

def darken_color(color: tuple, factor: float = 0.3) -> tuple:
    """Darken a color by a factor (0.0 to 1.0)"""
    return tuple(max(0, int(c * (1 - factor))) for c in color[:3])

