import pygame.freetype
import sys
import json
import os
import math
import textwrap
import random
import pickle
import uuid
from typing import List, Dict, Tuple, Optional, Union, Any
from collections import deque

def read_jsonl(file_path):
    """Read JSONL file and process each document."""
    
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            try:
                # Parse JSON
                data = json.loads(line.strip())
            
                yield data
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue


def load_jsonl(input_path):
    content = []
    for object in read_jsonl(input_path):
        content.append(object)
    return content

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FONT_SIZE = 18
TEXT_PADDING = 15  # Added padding for text blocks
SETTINGS_FILE = 'incep/settings.json'
HISTORY_FILE = 'incep/history.pickle'  # New history file

# Path to the JSONL file
JSONL_FILE_PATH = 'incep\combined_scier_hyperpie_train.jsonl'

# Load settings or create with defaults
def load_settings():
    # Default settings that should always be present
    default_settings = {
        "entity_colors": {
            "Dataset": (255, 105, 180),  # Pink
            "Task": (30, 144, 255),      # Blue
            "Method": (50, 205, 50),     # Green
            "a": (153, 50, 204),         # Purple
            "v": (138, 43, 226)          # Violet
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
    
    # If settings file exists, load it and merge with defaults
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                
                # Merge loaded settings with defaults to ensure all keys exist
                for key, default_value in default_settings.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = default_value
                
                return loaded_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    # Return default settings if no file exists or loading failed
    return default_settings

# New functions for handling history
def save_history(undo_stack, redo_stack):
    """Save undo/redo history to a file"""
    try:
        history = {
            "undo_stack": list(undo_stack)[-25:],  # Keep only last 25 items
            "redo_stack": list(redo_stack)[-25:]   # Keep only last 25 items
        }
        with open(HISTORY_FILE, 'wb') as f:
            pickle.dump(history, f)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_history():
    """Load undo/redo history from a file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'rb') as f:
                history = pickle.load(f)
                return history.get("undo_stack", []), history.get("redo_stack", [])
    except Exception as e:
        print(f"Error loading history: {e}")
    return [], []

# Load settings
SETTINGS = load_settings()
ENTITY_COLORS = SETTINGS["entity_colors"]
RELATION_COLORS = SETTINGS["relation_colors"]

# Save settings
def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(SETTINGS, f, indent=2)

# Path to the JSONL file - use the absolute path if needed
if os.path.exists(JSONL_FILE_PATH):
    JSONL_FILE_PATH = JSONL_FILE_PATH
else:
    JSONL_FILE_PATH = r'F:\repos\optihyp\incep\combined_scier_hyperpie.jsonl'

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int] = (76, 175, 80), 
                 hover_color: Tuple[int, int, int] = (56, 142, 60),
                 disabled_color: Tuple[int, int, int] = (200, 200, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.active_color = color
        self.is_hovered = False
        self.is_disabled = False
        self.font = pygame.font.SysFont('Arial', 16)
    
    def draw(self, surface: pygame.Surface):
        # Determine button color based on state
        color = self.disabled_color if self.is_disabled else (self.hover_color if self.is_hovered else self.active_color)
        
        # Draw button
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1, border_radius=3)
        
        # Draw text
        text_surf = self.font.render(self.text, True, (255, 255, 255) if not self.is_disabled else (100, 100, 100))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos: Tuple[int, int]) -> bool:
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(pos) and not self.is_disabled
        return self.is_hovered != was_hovered
    
    def click(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos) and not self.is_disabled

class Popup:
    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = False
        self.options = []
        self.selected_option = None
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Create buttons
        button_width = 80
        button_height = 30
        button_margin = 10
        
        self.cancel_button = Button(
            x + width - 2 * button_width - button_margin, 
            y + height - button_height - button_margin,
            button_width, button_height, "Cancel", color=(244, 67, 54)
        )
        
        self.save_button = Button(
            x + width - button_width - button_margin, 
            y + height - button_height - button_margin,
            button_width, button_height, "Save"
        )
        
        # Scrolling related properties
        self.scroll_y = 0
        self.max_scroll_y = 0
        self.option_height = 30
        self.options_container_height = 0
        self.visible_options_height = height - 90  # Height minus title and buttons area
    
    def set_options(self, options: List[Dict[str, Union[str, Tuple[int, int, int]]]]):
        self.options = options
        self.selected_option = None
        self.scroll_y = 0
        # Calculate max scroll based on number of options
        self.options_container_height = len(options) * self.option_height
        self.max_scroll_y = max(0, self.options_container_height - self.visible_options_height)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw popup background
        pygame.draw.rect(surface, (255, 255, 255), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        # Draw title
        title_surf = self.title_font.render(self.title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw horizontal line below title
        pygame.draw.line(surface, (200, 200, 200), 
                        (self.rect.x, self.rect.y + 40), 
                        (self.rect.x + self.rect.width, self.rect.y + 40))
        
        # Set up clipping rectangle for options area to enable scrolling
        options_rect = pygame.Rect(
            self.rect.x, 
            self.rect.y + 50, 
            self.rect.width, 
            self.visible_options_height
        )
        original_clip = surface.get_clip()
        surface.set_clip(options_rect)
        
        # Draw visible options
        start_idx = max(0, int(self.scroll_y / self.option_height))
        end_idx = min(len(self.options), start_idx + int(self.visible_options_height / self.option_height) + 2)
        
        for i in range(start_idx, end_idx):
            option = self.options[i]
            y_pos = self.rect.y + 50 + i * self.option_height - self.scroll_y
            option_rect = pygame.Rect(self.rect.x + 10, y_pos, 
                                     self.rect.width - 20, self.option_height)
            
            # Draw background if selected
            if self.selected_option == option["value"]:
                pygame.draw.rect(surface, (230, 230, 230), option_rect)
            
            text_color = option.get("color", (0, 0, 0))
            text_surf = self.font.render(option["text"], True, text_color)
            surface.blit(text_surf, (option_rect.x + 10, option_rect.y + 5))
        
        # Reset clipping
        surface.set_clip(original_clip)
        
        # Draw scrollbar if needed
        if self.max_scroll_y > 0:
            scrollbar_width = 8
            scrollbar_height = max(30, min(self.visible_options_height, 
                                  self.visible_options_height * self.visible_options_height / self.options_container_height))
            scrollbar_x = self.rect.x + self.rect.width - scrollbar_width - 5
            scrollbar_y = self.rect.y + 50 + (self.visible_options_height - scrollbar_height) * (self.scroll_y / self.max_scroll_y)
            
            scrollbar_rect = pygame.Rect(
                scrollbar_x, 
                scrollbar_y,
                scrollbar_width, 
                scrollbar_height
            )
            
            pygame.draw.rect(surface, (200, 200, 200), scrollbar_rect, border_radius=4)
        
        # Draw buttons
        self.cancel_button.draw(surface)
        self.save_button.draw(surface)
    
    def handle_scroll(self, scroll_amount: int):
        """Handle scrolling with the mouse wheel"""
        if not self.visible or self.max_scroll_y <= 0:
            return
        
        # Update scroll position
        self.scroll_y = max(0, min(self.max_scroll_y, self.scroll_y - scroll_amount * 30))
    
    def check_hover(self, pos: Tuple[int, int]) -> Optional[str]:
        if not self.visible:
            return None
        
        # Check buttons
        self.cancel_button.check_hover(pos)
        self.save_button.check_hover(pos)
        
        # Check if mouse is in options area
        options_rect = pygame.Rect(
            self.rect.x + 10, 
            self.rect.y + 50, 
            self.rect.width - 20, 
            self.visible_options_height
        )
        
        if options_rect.collidepoint(pos):
            # Calculate which option is being hovered based on scroll position
            option_idx = int((pos[1] - (self.rect.y + 50) + self.scroll_y) / self.option_height)
            if 0 <= option_idx < len(self.options):
                return "option:" + self.options[option_idx]["value"]
        
        return None
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        if not self.visible:
            return None
        
        # Check buttons
        if self.cancel_button.click(pos):
            return "cancel"
        
        if self.save_button.click(pos):
            return "save"
        
        # Check if mouse is in options area
        options_rect = pygame.Rect(
            self.rect.x + 10, 
            self.rect.y + 50, 
            self.rect.width - 20, 
            self.visible_options_height
        )
        
        if options_rect.collidepoint(pos):
            # Calculate which option is being clicked based on scroll position
            option_idx = int((pos[1] - (self.rect.y + 50) + self.scroll_y) / self.option_height)
            if 0 <= option_idx < len(self.options):
                self.selected_option = self.options[option_idx]["value"]
                return "option:" + self.selected_option
        
        return None
    
    def show(self, x: Optional[int] = None, y: Optional[int] = None):
        """Show the popup at the specified position"""
        self.visible = True
        self.scroll_y = 0  # Reset scroll position
        
        if x is not None and y is not None:
            # Ensure popup stays within screen bounds
            self.rect.x = min(max(x, 0), SCREEN_WIDTH - self.rect.width)
            self.rect.y = min(max(y, 0), SCREEN_HEIGHT - self.rect.height)
            
            # Update button positions
            button_width = 80
            button_height = 30
            button_margin = 10
            
            self.cancel_button.rect.x = self.rect.x + self.rect.width - 2 * button_width - button_margin
            self.cancel_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
            
            self.save_button.rect.x = self.rect.x + self.rect.width - button_width - button_margin
            self.save_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
    
    def hide(self):
        """Hide the popup"""
        self.visible = False
        self.selected_option = None

class EntityAnnotator:
    def __init__(self):
        # Set up display - make it resizable
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Entity Annotator")
        self.clock = pygame.time.Clock()
        
        # Current window size
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        
        # Load fonts
        self.font = pygame.font.SysFont('Arial', FONT_SIZE)
        self.small_font = pygame.font.SysFont('Arial', 14)
        self.bold_font = pygame.font.SysFont('Arial', FONT_SIZE, bold=True)
        
        # Setup document container
        self.doc_container = pygame.Rect(10, 120, self.width - 20, self.height - 130)
        
        # Document data
        self.doc = {
            "sentences": [],
            "ner": [],
            "relations": []
        }
        self.doc_id = None
        
        # Document collection
        self.document_collection = []
        self.current_doc_index = 0
        
        # Application state
        self.relation_mode = False
        self.is_selecting = False
        self.selection_start_token = None
        self.selected_tokens = []
        self.selected_entity_type = None
        self.creating_relation = False
        self.selected_entities = []
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        self.custom_relation_type = ""
        self.dragging_relation = False
        self.drag_source_entity = None
        self.drag_source_key = None
        self.temp_line = None
        self.mouse_x = 0
        self.mouse_y = 0
        
        # Load history from file
        undo_list, redo_list = load_history()
        
        # History for undo/redo - use deque with max length
        self.undo_stack = deque(undo_list, maxlen=25)
        self.redo_stack = deque(redo_list, maxlen=25)
        
        # Track entity elements
        self.entity_elements = {}
        self.token_elements = {}
        
        # Document scroll position
        self.doc_scroll_y = 0
        self.max_scroll_y = 0
        
        # UI elements
        self.setup_ui()
        
        # Document rendering variables
        self.rendered_entities = []
        self.rendered_tokens = []
        self.rendered_relations = []
        self.rendered_labels = []
        
        # Status message
        self.status_message = "Viewing Mode"
        self.save_status = ""
        self.save_status_time = 0
        
        # Initialize input dialog
        self.input_dialog = InputDialog(300, 300, 300, 180, "Add New Type")
        
        # Load documents from file
        try:
            self.load_documents()
            if not self.document_collection:  # If no documents were loaded
                raise ValueError("No documents loaded from file")
        except Exception as e:
            print(f"Error loading documents: {e}")
        
        # Try to extract and save entity/relation types from loaded documents
        self.extract_and_save_entity_types()
        
        # Update button states based on history
        if self.undo_stack:
            self.undo_button.is_disabled = False
        if self.redo_stack:
            self.redo_button.is_disabled = False
        
        # Render the initial document
        self.render_document()
    
        # Add a new attribute to track the currently hovered entity
        self.hovered_entity_key = None
        
        # Add attribute for displaying selected entity labels
        self.selected_entity_labels = {}
        
        # Initialize current_document to prevent the AttributeError
        self.current_document = {'entities': [], 'relations': [], 'tokens': []}
        self.selecting_within_entity = False
        
        # Add E key tracking flag
        self.e_key_held = False
    
    def setup_ui(self):
        # Create toolbar buttons
        button_width = 150
        button_height = 30
        button_margin = 10
        button_y = 50
        
        self.undo_button = Button(10, button_y, 
                                button_width, button_height, 
                                "Undo (Ctrl+Z)")
        self.undo_button.is_disabled = True
        
        self.redo_button = Button(10 + (button_width + button_margin), button_y, 
                                button_width, button_height, 
                                "Redo (Ctrl+Y)")
        self.redo_button.is_disabled = True
        
        self.save_button = Button(10 + 2 * (button_width + button_margin), button_y, 
                                button_width, button_height, 
                                "Save Annotations",
                                color=(76, 175, 80),     # Green
                                hover_color=(56, 142, 60))  # Darker green
        
        # Add custom type buttons
        self.add_entity_type_button = Button(10 + 3 * (button_width + button_margin), button_y, 
                                button_width, button_height, 
                                "Add Entity Type",
                                color=(63, 81, 181),     # Blue
                                hover_color=(48, 63, 159))  # Darker blue
                                
        self.add_relation_type_button = Button(10 + 4 * (button_width + button_margin), button_y, 
                                button_width, button_height, 
                                "Add Relation Type",
                                color=(63, 81, 181),     # Blue
                                hover_color=(48, 63, 159))  # Darker blue
        
        # Add document navigation buttons
        self.prev_doc_button = Button(10, button_y + button_height + button_margin, 
                                     button_width, button_height, 
                                     "< Prev",
                                     color=(158, 158, 158),        # Gray
                                     hover_color=(117, 117, 117))  # Darker gray
        
        self.next_doc_button = Button(10 + button_width + button_margin, button_y + button_height + button_margin, 
                                     button_width, button_height, 
                                     "Next >",
                                     color=(158, 158, 158),        # Gray
                                     hover_color=(117, 117, 117))  # Darker gray
        
        # Create popups with all known entity and relation types
        self.entity_popup = Popup(300, 300, 250, 400, "Select Entity Type")
        entity_options = []
        for entity_type, color in ENTITY_COLORS.items():
            entity_options.append({"text": entity_type, "value": entity_type, "color": color})
        self.entity_popup.set_options(entity_options)
        
        self.relation_popup = Popup(300, 300, 250, 400, "Select Relation Type")
        relation_options = []
        for relation_type, color in RELATION_COLORS.items():
            relation_options.append({"text": relation_type, "value": relation_type, "color": color})
        self.relation_popup.set_options(relation_options)
    
    def add_custom_entity_type(self, entity_type):
        """Add a new custom entity type"""
        if not entity_type or entity_type in ENTITY_COLORS:
            return False
        
        # Generate a new color
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)
        color = (r, g, b)
        
        # Add to entity colors
        ENTITY_COLORS[entity_type] = color
        
        # Add to settings
        if entity_type not in SETTINGS["known_entities"]:
            SETTINGS["known_entities"].append(entity_type)
        if entity_type not in SETTINGS["custom_entities"]:
            SETTINGS["custom_entities"].append(entity_type)
        
        # Update entity popup options
        self.entity_popup.options.append({
            "text": entity_type,
            "value": entity_type,
            "color": color
        })
        
        # Save settings
        save_settings()
        return True
    
    def add_custom_relation_type(self, relation_type):
        """Add a new custom relation type"""
        if not relation_type or relation_type in RELATION_COLORS:
            return False
        
        # Generate a new color
        r = random.randint(50, 200)
        g = random.randint(50, 200)
        b = random.randint(50, 200)
        color = (r, g, b)
        
        # Add to relation colors
        RELATION_COLORS[relation_type] = color
        
        # Add to settings
        if relation_type not in SETTINGS["known_relations"]:
            SETTINGS["known_relations"].append(relation_type)
        if relation_type not in SETTINGS["custom_relations"]:
            SETTINGS["custom_relations"].append(relation_type)
        
        # Update relation popup options
        self.relation_popup.options.append({
            "text": relation_type,
            "value": relation_type,
            "color": color
        })
        
        # Save settings
        save_settings()
        return True
    
    def load_documents(self):
        """Load documents from JSONL file"""
        try:
            if not os.path.exists(JSONL_FILE_PATH):
                return
                
            self.document_collection = load_jsonl(JSONL_FILE_PATH)
            
            if self.document_collection:
                # Load the first document
                self.load_document(0)
            
        except Exception as e:
            raise
    
    def load_document(self, index):
        """Load document at the specified index"""
        if 0 <= index < len(self.document_collection):
            # Save current document if it exists
            
            # Load new document
            self.current_doc_index = index
            doc = self.document_collection[index]
            
            # Extract ID
            self.doc_id = doc.get("doc_id", "None")
            
            # Extract sentences and unescape strings
            if "sentences" in doc:
                # Process all sentences and tokens to decode Unicode
                processed_sentences = []
                for sentence in doc["sentences"]:
                    processed_sentence = []
                    for token in sentence:
                        processed_sentence.append(token)
                    processed_sentences.append(processed_sentence)
                self.doc["sentences"] = processed_sentences
            else:
                self.doc["sentences"] = []
            
            # Extract entities and relations
            self.doc["ner"] = doc.get("ner", [])
            self.doc["relations"] = doc.get("relations", [])
            
            # Update navigation buttons
            self.prev_doc_button.is_disabled = index == 0
            self.next_doc_button.is_disabled = index == len(self.document_collection) - 1
            
            # Reset scroll position
            self.doc_scroll_y = 0
            
            # Fix document encoding
            doc = self.fix_document_encoding(doc)
            
            # Render the document
            self.render_document()
    
    def save_current_document(self):
        """Save the current document to the collection"""
        if self.doc_id is not None and self.current_doc_index < len(self.document_collection):
            # Update document in collection
            self.document_collection[self.current_doc_index]["sentences"] = self.doc["sentences"]
            self.document_collection[self.current_doc_index]["ner"] = self.doc["ner"]
            self.document_collection[self.current_doc_index]["relations"] = self.doc["relations"]
    
    def navigate_to_prev_document(self):
        """Navigate to the previous document"""
        if self.current_doc_index > 0:
            self.load_document(self.current_doc_index - 1)
    
    def navigate_to_next_document(self):
        """Navigate to the next document"""
        if self.current_doc_index < len(self.document_collection) - 1:
            self.load_document(self.current_doc_index + 1)
    
    def get_token_offset(self, sentence_index, token_index):
        """Calculate the global token offset from sentence and token index"""
        offset = 0
        for i in range(sentence_index):
            offset += len(self.doc["sentences"][i])
        return offset + token_index
    
    def get_token_info(self, global_idx):
        """Get sentence and token index from global token index"""
        total_tokens = 0
        for sent_idx, sentence in enumerate(self.doc["sentences"]):
            if global_idx >= total_tokens and global_idx < total_tokens + len(sentence):
                tok_idx = global_idx - total_tokens
                return {"sent_idx": sent_idx, "tok_idx": tok_idx}
            total_tokens += len(sentence)
        return None
    
    def extract_and_save_entity_types(self):
        """Extract all unique entity and relation types from the document collection"""
        entity_types = set()
        relation_types = set()
        
        # Process all documents
        for doc in self.document_collection:
            # Extract entity types
            for entity in doc.get("ner", []):
                if len(entity) >= 3:
                    entity_type = entity[2]
                    if isinstance(entity_type, list):
                        entity_type = entity_type[0] if entity_type else "Unknown"
                    entity_types.add(entity_type)
            
            # Extract relation types
            for relation in doc.get("relations", []):
                if len(relation) >= 5:
                    rel_type = relation[4]
                    # Handle case where rel_type is a list (fix for unhashable type error)
                    if isinstance(rel_type, list):
                        rel_type = rel_type[0] if rel_type else "Unknown"
                    relation_types.add(rel_type)
        
        # Convert to lists for serialization
        entity_list = list(entity_types)
        relation_list = list(relation_types)
        
        # Add to settings if new types found
        settings_updated = False
        
        for entity_type in entity_list:
            if entity_type not in SETTINGS["known_entities"]:
                SETTINGS["known_entities"].append(entity_type)
                settings_updated = True
                # Add a color if not already in entity colors
                if entity_type not in ENTITY_COLORS:
                    # Generate a random color
                    r = (hash(entity_type) % 200) + 50
                    g = ((hash(entity_type) * 2) % 200) + 50
                    b = ((hash(entity_type) * 3) % 200) + 50
                    ENTITY_COLORS[entity_type] = (r, g, b)
        
        for relation_type in relation_list:
            if relation_type not in SETTINGS["known_relations"]:
                SETTINGS["known_relations"].append(relation_type)
                settings_updated = True
                # Add a color if not already in relation colors
                if relation_type not in RELATION_COLORS:
                    # Generate a random color
                    r = (hash(relation_type) % 200) + 50
                    g = ((hash(relation_type) * 2) % 200) + 50
                    b = ((hash(relation_type) * 3) % 200) + 50
                    RELATION_COLORS[relation_type] = (r, g, b)
        
        # Save settings if updated
        if settings_updated:
            save_settings()
    
    def draw_document_content(self):
        """Draw document content with unified approach"""
        # First draw ALL text (both regular tokens and those in entities)
        for token in self.rendered_tokens:
            if (token["rect"].y + token["rect"].height > self.doc_container.y and 
                token["rect"].y < self.doc_container.y + self.doc_container.height):
                
                # Determine if token is selected
                is_selected = token["global_idx"] in self.selected_tokens
                
                # Draw all text with proper unescaping
                unescaped_text = self.unescape_string(token["text"])
                text_color = (0, 0, 0)  # Always use black text
                
                # Draw text
                text_surf = self.font.render(unescaped_text, True, text_color)
                self.screen.blit(text_surf, token["rect"])
                
                # If selected, draw highlight underneath (optional)
                if is_selected:
                    # Create highlight surface and draw under text
                    highlight_surface = pygame.Surface((token["rect"].width, token["rect"].height), pygame.SRCALPHA)
                    highlight_color = (255, 255, 0, 100)  # Yellow with transparency
                    pygame.draw.rect(highlight_surface, highlight_color, 
                                  (0, 0, token["rect"].width, token["rect"].height), 
                                  border_radius=3)
                    # Draw highlight under text
                    self.screen.blit(highlight_surface, token["rect"])
        
        # Then draw entity rectangles on top (WITHOUT text this time)
        for entity in self.rendered_entities:
            # Check if entity is visible - handle both single and multi-line entities
            is_visible = False
            
            if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                # For multi-line entities, check if any of its rectangles are visible
                for rect in entity["rect"]["rects"]:
                    if (rect.y + rect.height > self.doc_container.y and 
                        rect.y < self.doc_container.y + self.doc_container.height):
                        is_visible = True
                        break
            else:
                # For single-line entities, check visibility normally
                is_visible = (entity["rect"].y + entity["rect"].height > self.doc_container.y and 
                             entity["rect"].y < self.doc_container.y + self.doc_container.height)
            
            # Only draw if entity is visible
            if is_visible:
                # Draw only the rectangle for the entity (without text)
                self.draw_entity_background(entity)
        
        # Only draw relations if an entity is hovered
        if self.hovered_entity_key and self.hovered_entity_key in self.entity_elements:
            # Get the hovered entity and its type
            hovered_entity = self.entity_elements[self.hovered_entity_key]
            hovered_entity_type = hovered_entity["type"]
            
            # Normalize entity type in case it's a list
            if isinstance(hovered_entity_type, list):
                hovered_entity_type = hovered_entity_type[0] if hovered_entity_type else "Unknown"
            
            # Define specific relation type restrictions (ONLY the relations we want to block)
            restricted_relations = {
                # Format: "entity_type": ["relation_types_to_block"]
                # Only add entries for entities where we want to restrict certain relation types
                "MS COCO": ["Part-Of", "Synonym-Of", "SubClass-Of", "Compare-With"],
                "ConvNets": ["Part-Of", "Synonym-Of", "Evaluated-With", "Compare-With"],
                "convolutional neural networks": ["Part-Of", "Synonym-Of", "Evaluated-With", "Compare-With"],
                "challenging benchmarks": ["Part-Of", "Synonym-Of", "SubClass-Of", "Compare-With"],
                "corner pooling": ["Part-Of", "Synonym-Of", "SubClass-Of", "Compare-With"]
            }
            
            # Find all relations involving the hovered entity
            related_relations = []
            for relation in self.rendered_relations:
                src_key = f"{relation['source']['start']}-{relation['source']['end']}"
                tgt_key = f"{relation['target']['start']}-{relation['target']['end']}"
                relation_type = relation["type"]
                
                # Only process relations where one end is the hovered entity
                if src_key == self.hovered_entity_key or tgt_key == self.hovered_entity_key:
                    # By default, include the relation
                    include_relation = True
                    
                    # Check if this entity type has restrictions
                    if hovered_entity_type in restricted_relations:
                        # If the relation type is in the restricted list, don't include it
                        if relation_type in restricted_relations[hovered_entity_type]:
                            include_relation = False
                            
                    if include_relation:
                        related_relations.append(relation)
            
            # Draw relation arrows for the filtered relations
            for relation in related_relations:
                self.draw_relation_arrow(relation)
                
            # Draw relation labels for the filtered relations
            for relation in related_relations:
                relation_type = relation["type"]
                
                # Find the corresponding label
                for label in self.rendered_labels:
                    if label["text"] == relation_type:
                        # Calculate approximate position to match this relation
                        src_entity = relation["source"]
                        tgt_entity = relation["target"]
                        
                        # Use get_entity_center instead of direct centerx access
                        src_center_x, _ = self.get_entity_center(src_entity)
                        tgt_center_x, _ = self.get_entity_center(tgt_entity)
                        expected_x = (src_center_x + tgt_center_x) // 2
                        
                        # Check if the label's position is close to the expected position
                        if abs(label["x"] - expected_x) < 50:
                            self.draw_relation_label(label)
                            break
        
        # Draw temporary line if dragging relation
        if self.dragging_relation and self.temp_line:
            # Draw curve with better styling
            ctrl_x1 = self.temp_line["src_x"] + (self.temp_line["tgt_x"] - self.temp_line["src_x"]) * 0.25
            ctrl_y1 = self.temp_line["src_y"] - 50
            ctrl_x2 = self.temp_line["src_x"] + (self.temp_line["tgt_x"] - self.temp_line["src_x"]) * 0.75
            ctrl_y2 = self.temp_line["tgt_y"] - 50
            
            # Draw thicker, more curved line
            points = self.calculate_bezier_points([
                (self.temp_line["src_x"], self.temp_line["src_y"]),
                (ctrl_x1, ctrl_y1),
                (ctrl_x2, ctrl_y2),
                (self.temp_line["tgt_x"], self.temp_line["tgt_y"])
            ], 20)
            
            # Draw a thicker line using multiple lines with slight offset
            pygame.draw.aalines(self.screen, (120, 120, 120), False, points, 2)
    
    def draw_entity_background(self, entity_info):
        """Draw just the entity background rectangle without text"""
        # Get entity color based on type
        entity_type = entity_info["type"]
        
        # Handle case where entity_type is a list instead of a string
        if isinstance(entity_type, list):
            entity_type = entity_type[0] if entity_type else "Unknown"
        
        # Make sure we're using the correct color for this entity type
        bg_color = ENTITY_COLORS.get(entity_type, (200, 200, 200))
        
        # Create semi-transparent background color
        bg_color_alpha = (bg_color[0], bg_color[1], bg_color[2], 100)  # More transparency
        
        # Check if this is a multi-line entity
        if isinstance(entity_info["rect"], dict) and entity_info["rect"].get("multi_line"):
            # Draw each rectangle separately for multi-line entities
            for rect in entity_info["rect"]["rects"]:
                # Create surface with alpha
                entity_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(entity_surface, bg_color_alpha, 
                                (0, 0, rect.width, rect.height),
                                border_radius=3)
                
                # Blit to screen
                self.screen.blit(entity_surface, rect)
                
                # Draw border
                border_color = bg_color
                if entity_info["hovered"] or entity_info["selected"]:
                    # Use solid color for border when hovered or selected
                    pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=3)
                else:
                    # Use normal border
                    pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=3)
        else:
            # Create surface with alpha
            entity_surface = pygame.Surface((entity_info["rect"].width, entity_info["rect"].height), pygame.SRCALPHA)
            pygame.draw.rect(entity_surface, bg_color_alpha, 
                            (0, 0, entity_info["rect"].width, entity_info["rect"].height),
                            border_radius=3)
            
            # Blit to screen
            self.screen.blit(entity_surface, entity_info["rect"])
            
            # Draw border
            border_color = bg_color
            if entity_info["hovered"] or entity_info["selected"]:
                # Use solid color for border when hovered or selected
                pygame.draw.rect(self.screen, border_color, entity_info["rect"], 2, border_radius=3)
            else:
                # Use normal border
                pygame.draw.rect(self.screen, border_color, entity_info["rect"], 1, border_radius=3)
    
    def fix_document_encoding(self, doc):
        """Fix encoding issues in document"""
        # Handles any encoding fixes needed for the document
        # Just returns the document unchanged if no fixes are needed
        return doc
    
    def unescape_string(self, text):
        """Unescape string from escaped unicode characters"""
        try:
            # Handle potential unicode escapes in text
            if isinstance(text, str):
                return text.encode().decode('unicode_escape')
            return str(text)
        except:
            # Return original if we can't unescape
            return str(text)
    
    def render_document(self):
        """Render the document with all entities and relations"""
        # Clear previous rendered elements
        self.rendered_entities = []
        self.rendered_tokens = []
        self.rendered_relations = []
        self.rendered_labels = []
        self.entity_elements = {}
        
        if not self.doc or not self.doc["sentences"]:
            return
        
        # Calculate total document height and set max scroll
        line_height = self.font.get_height() + 8
        
        # Start position for rendering
        x = self.doc_container.x + 10
        y = self.doc_container.y - self.doc_scroll_y + 10
        
        # Create a map from token index to entity
        token_entity_map = {}
        max_token_index = 0
        
        # Process entities for all sentences
        for sent_idx, entities in enumerate(self.doc["ner"]):
            # Skip if no sentence tokens at this index
            if sent_idx >= len(self.doc["sentences"]):
                continue
                
            # Get all entities for this sentence
            for entity in entities:
                if len(entity) >= 3:
                    start_idx = entity[0]
                    end_idx = entity[1]
                    entity_type = entity[2]
                    
                    # Map token indices to this entity
                    for idx in range(start_idx, end_idx + 1):
                        token_entity_map[idx] = entity
                        max_token_index = max(max_token_index, idx)
        
        # Process all tokens in all sentences
        global_idx = 0
        current_line_tokens = []
        line_width = 0
        max_line_width = self.doc_container.width - 20  # Padding on both sides
        
        # Get all sentences
        for sent_idx, sentence in enumerate(self.doc["sentences"]):
            # Add a bit of space between sentences
            if sent_idx > 0:
                y += 10
                
                # Start a new line
                current_line_tokens = []
                line_width = 0
            
            # Process all tokens in the sentence
            for tok_idx, token_text in enumerate(sentence):
                # Skip invalid tokens
                if not token_text:
                    global_idx += 1
                    continue
                
                # Calculate token width based on text
                token_width = self.font.size(token_text)[0] + 4  # Small padding
                
                # Check if we need to wrap to the next line
                if line_width + token_width > max_line_width and current_line_tokens:
                    # Move to next line
                    y += line_height
                    x = self.doc_container.x + 10
                    line_width = 0
                    current_line_tokens = []
                
                # Create token rectangle at current position
                token_rect = pygame.Rect(x, y, token_width, line_height)
                
                # Store token information
                token_info = {
                    "text": token_text,
                    "sent_idx": sent_idx,
                    "tok_idx": tok_idx,
                    "global_idx": global_idx,
                    "rect": token_rect,
                    "selected": global_idx in self.selected_tokens,
                }
                
                # Check if token is part of an entity
                if global_idx in token_entity_map:
                    token_info["entity"] = token_entity_map[global_idx]
                
                # Add to rendered tokens
                self.rendered_tokens.append(token_info)
                current_line_tokens.append(token_info)
                
                # Update position for next token
                x += token_width + 2  # Small space between tokens
                line_width += token_width + 2
                
                # Increment global index
                global_idx += 1
            
            # Move to the next line after processing a sentence
            y += line_height
            x = self.doc_container.x + 10
            line_width = 0
            current_line_tokens = []
        
        # Calculate total document height
        total_height = y + 20 - self.doc_container.y + self.doc_scroll_y
        self.max_scroll_y = max(0, total_height - self.doc_container.height)
        
        # Process entities to create rectangles
        for sent_idx, entities in enumerate(self.doc["ner"]):
            for entity in entities:
                if len(entity) >= 3:
                    start_idx = entity[0]
                    end_idx = entity[1]
                    entity_type = entity[2]
                    
                    # Find the rendered tokens for this entity
                    start_token = None
                    end_token = None
                    entity_tokens = []
                    
                    for token in self.rendered_tokens:
                        if token["global_idx"] == start_idx:
                            start_token = token
                        if token["global_idx"] == end_idx:
                            end_token = token
                        if start_idx <= token["global_idx"] <= end_idx:
                            entity_tokens.append(token)
                    
                    # If we found both start and end tokens
                    if start_token and end_token and entity_tokens:
                        # Extract entity text from tokens
                        entity_text = " ".join([t["text"] for t in entity_tokens])
                        
                        # Calculate entity rectangle enclosing all tokens
                        # First sort tokens by Y position, then by X position
                        sorted_tokens = sorted(entity_tokens, key=lambda t: (t["rect"].y, t["rect"].x))
                        
                        # Group tokens by line (Y position)
                        lines = {}
                        for t in sorted_tokens:
                            y_pos = t["rect"].y
                            if y_pos not in lines:
                                lines[y_pos] = []
                            lines[y_pos].append(t)
                        
                        # Sort lines by Y position
                        sorted_lines = sorted(lines.items())
                        
                        # Create rectangles for each line segment
                        entity_rects = []
                        for line_y, line_tokens in sorted_lines:
                            # Sort tokens in this line by X position
                            line_tokens.sort(key=lambda t: t["rect"].x)
                            
                            # Create a rectangle for this line segment
                            left = line_tokens[0]["rect"].x
                            top = line_tokens[0]["rect"].y
                            right = line_tokens[-1]["rect"].x + line_tokens[-1]["rect"].width
                            bottom = line_tokens[0]["rect"].y + line_tokens[0]["rect"].height
                            
                            entity_rects.append(pygame.Rect(left, top, right - left, bottom - top))
                        
                        # If entity spans multiple lines, create one rectangle for simplicity
                        if len(entity_rects) == 1:
                            entity_rect = entity_rects[0]
                        else:
                            # Instead of creating one large box, create a list of rectangles
                            # to render separately - this will look much better visually
                            entity_rect = {
                                "multi_line": True,
                                "rects": entity_rects
                            }
                        
                        # Add entity to rendered entities
                        entity_key = f"{start_idx}-{end_idx}"
                        entity_info = {
                            "start": start_idx,
                            "end": end_idx,
                            "type": entity_type,
                            "text": entity_text,
                            "rect": entity_rect,
                            "selected": entity_key in self.selected_entities,
                            "hovered": False
                        }
                        
                        self.rendered_entities.append(entity_info)
                        
                        # Store entity element for relation drawing
                        self.entity_elements[entity_key] = entity_info
        
        # Process relations to create arrows and labels
        for sent_idx, relations in enumerate(self.doc["relations"]):
            for relation in relations:
                if len(relation) >= 5:
                    src_start, src_end = relation[0], relation[1]
                    tgt_start, tgt_end = relation[2], relation[3]
                    rel_type = relation[4]
                    
                    # Handle case where rel_type is a list
                    if isinstance(rel_type, list):
                        rel_type = rel_type[0] if rel_type else "Unknown"
                    
                    # Get entity elements for source and target
                    src_key = f"{src_start}-{src_end}"
                    tgt_key = f"{tgt_start}-{tgt_end}"
                    
                    if src_key in self.entity_elements and tgt_key in self.entity_elements:
                        src_entity = self.entity_elements[src_key]
                        tgt_entity = self.entity_elements[tgt_key]
                        
                        # Calculate center points for entities (handle multi-line entities)
                        src_center_x, src_center_y = self.get_entity_center(src_entity)
                        tgt_center_x, tgt_center_y = self.get_entity_center(tgt_entity)
                        
                        # Create relation information with calculated centers
                        relation_info = {
                            "source": src_entity,
                            "target": tgt_entity,
                            "type": rel_type,
                            "color": RELATION_COLORS.get(rel_type, (120, 120, 120)),
                            "src_center_x": src_center_x,
                            "src_center_y": src_center_y,
                            "tgt_center_x": tgt_center_x,
                            "tgt_center_y": tgt_center_y
                        }
                        
                        # Add to rendered relations
                        self.rendered_relations.append(relation_info)
                        
                        # Add label for relation
                        label_x = (src_center_x + tgt_center_x) // 2
                        label_y = min(
                            self.get_entity_top(src_entity),
                            self.get_entity_top(tgt_entity)
                        ) - 15
                        
                        # Ensure minimum distance from top of document container
                        min_y_distance = 25  # Minimum pixel distance from top of document
                        if label_y - self.doc_scroll_y < self.doc_container.y + min_y_distance:
                            label_y = self.doc_container.y + self.doc_scroll_y + min_y_distance
                        
                        # Add a minimum vertical offset for labels
                        if (self.get_entity_top(src_entity) > self.get_entity_bottom(tgt_entity) or 
                            self.get_entity_top(tgt_entity) > self.get_entity_bottom(src_entity)):
                            # Entities are vertically separated, put label between them
                            label_y = (src_center_y + tgt_center_y) // 2
                        
                        label_info = {
                            "text": rel_type,
                            "x": label_x,
                            "y": label_y,
                            "color": RELATION_COLORS.get(rel_type, (120, 120, 120))
                        }
                        
                        # Add to rendered labels
                        self.rendered_labels.append(label_info)
        
        # Save history after significant changes
        save_history(self.undo_stack, self.redo_stack)
    
    def calculate_bezier_points(self, points, num_points=20):
        """Calculate points along a Bezier curve"""
        def bezier(t, p0, p1, p2, p3):
            return (
                (1-t)**3 * p0 + 
                3*(1-t)**2*t * p1 + 
                3*(1-t)*t**2 * p2 + 
                t**3 * p3
            )
        
        result = []
        p0, p1, p2, p3 = points
        
        for i in range(num_points):
            t = i / (num_points - 1)
            x = bezier(t, p0[0], p1[0], p2[0], p3[0])
            y = bezier(t, p0[1], p1[1], p2[1], p3[1])
            result.append((x, y))
        
        return result
    
    def draw_relation_arrow(self, relation):
        """Draw an arrow representing the relation between entities"""
        src_entity = relation["source"]
        tgt_entity = relation["target"]
        
        # Use pre-calculated center points from the relation info
        src_x, src_y = relation["src_center_x"], relation["src_center_y"]
        tgt_x, tgt_y = relation["tgt_center_x"], relation["tgt_center_y"]
        
        # Define control points for Bezier curve
        # Make curve go higher if entities are far apart
        distance = math.sqrt((tgt_x - src_x)**2 + (tgt_y - src_y)**2)
        
        # Calculate height factor but ensure it doesn't push curve outside container
        max_allowed_height = min(
            src_y - self.doc_container.y,
            tgt_y - self.doc_container.y
        ) - 10  # 10px buffer
        
        # Ensure height factor doesn't exceed max allowed height
        height_factor = min(min(100, distance / 4), max(20, max_allowed_height))
        
        # Constrain control points within document boundaries
        doc_left = self.doc_container.x
        doc_right = self.doc_container.x + self.doc_container.width
        doc_top = self.doc_container.y
        doc_bottom = self.doc_container.y + self.doc_container.height
        
        # Use different curve shapes based on relative positions
        if abs(tgt_y - src_y) < 50:
            # Entities are roughly on the same line, curve goes up
            ctrl_x1 = min(max(src_x + (tgt_x - src_x) * 0.25, doc_left + 10), doc_right - 10)
            ctrl_y1 = max(src_y - height_factor, doc_top + 10)
            ctrl_x2 = min(max(src_x + (tgt_x - src_x) * 0.75, doc_left + 10), doc_right - 10)
            ctrl_y2 = max(tgt_y - height_factor, doc_top + 10)
        else:
            # Entities are on different lines, curve connects more directly
            # Constrain x coordinates within document width
            ctrl_x1 = min(max(src_x + (tgt_x - src_x) * 0.25, doc_left + 10), doc_right - 10)
            # Constrain y coordinates within document height
            ctrl_y1 = min(max(src_y + (tgt_y - src_y) * 0.25, doc_top + 10), doc_bottom - 10)
            ctrl_x2 = min(max(src_x + (tgt_x - src_x) * 0.75, doc_left + 10), doc_right - 10)
            ctrl_y2 = min(max(src_y + (tgt_y - src_y) * 0.75, doc_top + 10), doc_bottom - 10)
        
        # Calculate Bezier curve points
        curve_points = self.calculate_bezier_points([
            (src_x, src_y),
            (ctrl_x1, ctrl_y1),
            (ctrl_x2, ctrl_y2),
            (tgt_x, tgt_y)
        ], 30)
        
        # Draw the curve
        pygame.draw.aalines(self.screen, relation["color"], False, curve_points, 2)
        
        # Draw arrow head at the target end
        if len(curve_points) >= 2:
            # Get the last two points of the curve
            p2 = curve_points[-1]
            p1 = curve_points[-2]
            
            # Calculate arrow direction
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            # Normalize the direction vector
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx /= length
                dy /= length
            
            # Calculate perpendicular vectors for arrow head
            arrow_size = 10
            px = -dy
            py = dx
            
            # Calculate arrow head points
            a1 = (p2[0] - arrow_size*dx + arrow_size*0.5*px, 
                  p2[1] - arrow_size*dy + arrow_size*0.5*py)
            a2 = (p2[0] - arrow_size*dx - arrow_size*0.5*px, 
                  p2[1] - arrow_size*dy - arrow_size*0.5*py)
            
            # Draw arrow head
            pygame.draw.polygon(self.screen, relation["color"], [p2, a1, a2])
    
    def draw_relation_label(self, label):
        """Draw a label for a relation"""
        # Only draw if in view
        if (label["y"] > self.doc_container.y and 
            label["y"] < self.doc_container.y + self.doc_container.height):
            
            # Render label text
            text_surf = self.small_font.render(label["text"], True, label["color"])
            
            # Create text rectangle
            text_rect = text_surf.get_rect(center=(label["x"], label["y"]))
            
            # Constrain the label position to stay within document boundaries
            # Add some padding (5px) from edges
            doc_left = self.doc_container.x + 5
            doc_right = self.doc_container.x + self.doc_container.width - 5
            doc_top = self.doc_container.y + 5
            doc_bottom = self.doc_container.y + self.doc_container.height - 5
            
            # Adjust horizontal position if needed
            if text_rect.left < doc_left:
                text_rect.left = doc_left
            elif text_rect.right > doc_right:
                text_rect.right = doc_right
            
            # Adjust vertical position if needed
            if text_rect.top < doc_top:
                text_rect.top = doc_top
            elif text_rect.bottom > doc_bottom:
                text_rect.bottom = doc_bottom
            
            # Create background with padding
            bg_rect = text_rect.copy()
            bg_rect.inflate_ip(6, 6)
            
            # Draw white background for better visibility
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surf.fill((255, 255, 255))
            bg_surf.set_alpha(220)
            self.screen.blit(bg_surf, bg_rect)
            
            # Draw text at the adjusted position
            self.screen.blit(text_surf, text_rect)
    
    def check_token_hover(self, pos):
        """Check if mouse is hovering over a token"""
        for token in self.rendered_tokens:
            if token["rect"].collidepoint(pos):
                return token
        return None

    def check_entity_hover(self, pos):
        """Check if mouse is hovering over an entity"""
        for entity in self.rendered_entities:
            # Handle multi-line entities
            if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                # Check each rectangle in the multi-line entity
                for rect in entity["rect"]["rects"]:
                    if rect.collidepoint(pos):
                        return entity
            elif entity["rect"].collidepoint(pos):
                return entity
        return None

    def start_dragging_relation(self, entity):
        """Start dragging a relation from an entity"""
        # Set dragging state
        self.dragging_relation = True
        
        # Store source entity
        self.drag_source_entity = [entity["start"], entity["end"], entity["type"]]
        
        # Store entity key for comparison
        self.drag_source_key = f"{entity['start']}-{entity['end']}"
        
        # Get center point for the entity
        center_x, center_y = self.get_entity_center(entity)
        
        # Create temporary line
        self.temp_line = {
            "src_x": center_x,
            "src_y": center_y,
            "tgt_x": self.mouse_x,
            "tgt_y": self.mouse_y
        }
    
    def show_relationships(self, entity_key):
        """Show relationships for an entity"""
        # Set the hovered entity key to display relationships
        self.hovered_entity_key = entity_key
    
    def hide_relationships(self):
        """Hide highlighted relationships"""
        # Clear the hovered entity key
        self.hovered_entity_key = None
    
    def draw(self):
        """Draw the application interface"""
        # Clear screen
        self.screen.fill((240, 240, 240))
        
        # Draw toolbar background
        toolbar_rect = pygame.Rect(0, 0, self.width, 120)
        pygame.draw.rect(self.screen, (220, 220, 220), toolbar_rect)
        pygame.draw.line(self.screen, (200, 200, 200), (0, 120), (self.width, 120), 2)
        
        # Draw toolbar buttons
        self.undo_button.draw(self.screen)
        self.redo_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.add_entity_type_button.draw(self.screen)
        self.add_relation_type_button.draw(self.screen)
        
        # Draw document navigation controls
        self.prev_doc_button.draw(self.screen)
        self.next_doc_button.draw(self.screen)
        
        # Draw document ID
        if self.doc_id:
            doc_id_text = f"Document: {self.doc_id}"
            doc_id_surf = self.font.render(doc_id_text, True, (0, 0, 0))
            doc_id_x = 10 + 2*self.prev_doc_button.rect.width + 20
            self.screen.blit(doc_id_surf, (doc_id_x, self.prev_doc_button.rect.y + 5))
        
        # Draw mode status - top right corner
        status_surf = self.font.render(self.status_message, True, (100, 100, 100))
        self.screen.blit(status_surf, (self.width - status_surf.get_width() - 10, 60))
        
        # Draw save status if recent - adjust position
        current_time = pygame.time.get_ticks()
        if self.save_status and current_time - self.save_status_time < 3000:
            save_surf = self.font.render(self.save_status, True, (0, 150, 0))
            self.screen.blit(save_surf, (self.width - save_surf.get_width() - 10, 80))
        else:
            self.save_status = ""
        
        # Draw document container
        pygame.draw.rect(self.screen, (255, 255, 255), self.doc_container)
        pygame.draw.rect(self.screen, (200, 200, 200), self.doc_container, 1)
        
        # Set clipping rectangle for document content
        original_clip = pygame.display.get_surface().get_clip()
        pygame.display.get_surface().set_clip(self.doc_container)
        
        # Draw document content with tokens and entity backgrounds
        self.draw_document_content()
        
        # Draw entity type labels for selected entities
        for entity_key, label_info in self.selected_entity_labels.items():
            if entity_key in self.entity_elements:
                # Check if the entity is visible
                entity = self.entity_elements[entity_key]
                is_visible = False
                
                if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                    # For multi-line entities, check if any rectangle is visible
                    for rect in entity["rect"]["rects"]:
                        if (rect.y + rect.height > self.doc_container.y and 
                            rect.y < self.doc_container.y + self.doc_container.height):
                            is_visible = True
                            break
                else:
                    # For single-line entities
                    is_visible = (entity["rect"].y + entity["rect"].height > self.doc_container.y and 
                                 entity["rect"].y < self.doc_container.y + self.doc_container.height)
                
                if is_visible:
                    # Get label position and adjust for scroll
                    label_x, base_y = label_info["pos"]
                    # Adjust y position based on scroll
                    label_y = base_y
                    
                    # Ensure label stays within container bounds
                    if label_y < self.doc_container.y + 5:
                        # If label would be off the top, position it below the entity instead
                        label_y = self.get_entity_bottom(entity) + 5
                    
                    # Create a background for the label text
                    text_surf = self.small_font.render(label_info["type"], True, label_info["color"])
                    text_rect = text_surf.get_rect(center=(label_x, label_y))
                    
                    # Create padding around text
                    bg_rect = text_rect.copy()
                    bg_rect.inflate_ip(10, 6)
                    
                    # Draw label background
                    pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=3)
                    pygame.draw.rect(self.screen, label_info["color"], bg_rect, 1, border_radius=3)
                    
                    # Draw label text
                    self.screen.blit(text_surf, text_rect)
        
        # Reset clipping before drawing relations
        pygame.display.get_surface().set_clip(original_clip)
        
        # Draw scrollbar if needed
        if self.max_scroll_y > 0:
            scrollbar_height = max(30, min(self.doc_container.height, 
                                self.doc_container.height * self.doc_container.height / (self.doc_container.height + self.max_scroll_y)))
            scrollbar_pos = self.doc_container.y + (self.doc_container.height - scrollbar_height) * (self.doc_scroll_y / self.max_scroll_y)
            
            scrollbar_rect = pygame.Rect(
                self.doc_container.right - 10, 
                scrollbar_pos,
                10, scrollbar_height
            )
            
            pygame.draw.rect(self.screen, (200, 200, 200), scrollbar_rect, border_radius=5)
        
        # Draw popups
        self.entity_popup.draw(self.screen)
        self.relation_popup.draw(self.screen)
        
        # Draw input dialog if visible
        if self.input_dialog.visible:
            self.input_dialog.draw(self.screen)
        
        # Update the display
        pygame.display.flip()
    
    def handle_events(self):
        """Handle pygame events"""
        # Get current keyboard state for continuous key press handling
        keys = pygame.key.get_pressed()
        # Check if E key is currently pressed
        self.e_key_held = keys[pygame.K_e]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Save changes and settings before exiting
                self.save_annotations()
                save_settings()
                save_history(self.undo_stack, self.redo_stack)
                return False
            
            # Add handler for window resize events
            elif event.type == pygame.VIDEORESIZE:
                # Update window size
                self.width, self.height = event.size
                # Update document container size
                self.doc_container = pygame.Rect(10, 120, self.width - 20, self.height - 130)
                # Re-render document to fit new container
                self.render_document()
            
            # Handle mouse button events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Separate scroll wheel handling (buttons 4 and 5)
                if event.button in (4, 5):  # 4 is scroll up, 5 is scroll down
                    # Calculate scroll direction
                    scroll_dir = 1 if event.button == 4 else -1
                    
                    # First check for popups - prioritize popup scrolling when popups are visible
                    if self.entity_popup.visible and self.entity_popup.rect.collidepoint(pos):
                        self.entity_popup.handle_scroll(scroll_dir)
                    elif self.relation_popup.visible and self.relation_popup.rect.collidepoint(pos):
                        self.relation_popup.handle_scroll(scroll_dir)
                    elif self.input_dialog.visible and self.input_dialog.rect.collidepoint(pos):
                        # Input dialog doesn't need scrolling, but prevent document scrolling
                        pass
                    # Only scroll document if no popup is being interacted with
                    elif self.doc_container.collidepoint(pos):
                        self.doc_scroll_y = max(0, min(self.max_scroll_y, 
                                             self.doc_scroll_y - scroll_dir * 30))
                        self.render_document()
                    continue  # Skip the rest of the click handling for scroll events
                
                # Handle button clicks
                if self.undo_button.click(pos) and not self.undo_button.is_disabled:
                    self.undo()
                elif self.redo_button.click(pos) and not self.redo_button.is_disabled:
                    self.redo()
                elif self.save_button.click(pos):
                    self.save_annotations()
                elif self.prev_doc_button.click(pos) and not self.prev_doc_button.is_disabled:
                    self.navigate_to_prev_document()
                elif self.next_doc_button.click(pos) and not self.next_doc_button.is_disabled:
                    self.navigate_to_next_document()
                elif self.add_entity_type_button.click(pos):
                    # Show input dialog for new entity type
                    self.input_dialog.title = "Add New Entity Type"
                    self.input_dialog.show(self.width // 2 - 150, self.height // 2 - 90)
                elif self.add_relation_type_button.click(pos):
                    # Show input dialog for new relation type
                    self.input_dialog.title = "Add New Relation Type"
                    self.input_dialog.show(self.width // 2 - 150, self.height // 2 - 90)
                
                # Handle popup clicks
                elif self.entity_popup.visible:
                    result = self.entity_popup.handle_click(pos)
                    if result:
                        if result.startswith("option:"):
                            self.selected_entity_type = result.split(":")[1]
                        elif result == "save" and self.selected_entity_type:
                            self.create_new_entity()
                            self.entity_popup.hide()
                        elif result == "cancel":
                            self.selected_tokens = []
                            self.entity_popup.hide()
                            self.render_document()
                
                elif self.relation_popup.visible:
                    result = self.relation_popup.handle_click(pos)
                    if result:
                        if result.startswith("option:"):
                            self.selected_relation_type = result.split(":")[1]
                        elif result == "save" and self.selected_relation_type:
                            self.create_new_relation()
                            self.relation_popup.hide()
                        elif result == "cancel":
                            self.reset_relation_creation()
                            self.relation_popup.hide()
                            self.render_document()
                
                # Handle input dialog clicks
                elif self.input_dialog.visible:
                    result = self.input_dialog.handle_click(pos)
                    if result == "save":
                        if self.input_dialog.title == "Add New Entity Type":
                            self.add_custom_entity_type(self.input_dialog.text_input.strip())
                        else:
                            self.add_custom_relation_type(self.input_dialog.text_input.strip())
                        self.input_dialog.hide()
                    elif result == "cancel":
                        self.input_dialog.hide()
                
                # Check for clicks in document container - explicitly check for left/right clicks
                elif self.doc_container.collidepoint(pos):
                    # Right mouse button
                    if event.button == 3:
                        entity = self.check_entity_hover(pos)
                        if entity:
                            self.handle_entity_click(entity, right_click=True)
                    # Left mouse button
                    elif event.button == 1:
                        entity = self.check_entity_hover(pos)
                        if entity:
                            self.handle_entity_click(entity, right_click=False)
                        else:
                            # Check if a token was clicked
                            token = self.check_token_hover(pos)
                            if token and "global_idx" in token:
                                self.handle_token_click(token)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                
                # Finalize token selection
                self.handle_mouse_up_selection(pos)
                
                # Handle end of relation dragging
                if self.dragging_relation:
                    target_entity = self.check_entity_hover(pos)
                    
                    if (target_entity and 
                        f"{target_entity['start']}-{target_entity['end']}" != self.drag_source_key):
                        # Set up relation creation
                        self.relation_source_entity = self.drag_source_entity
                        self.relation_target_entity = [
                            target_entity["start"], 
                            target_entity["end"], 
                            target_entity["type"]
                        ]
                        
                        # Show relation type popup
                        self.relation_popup.show(pos[0], pos[1])
                    
                    # Reset dragging state
                    self.dragging_relation = False
                    self.drag_source_entity = None
                    self.drag_source_key = None
                    self.temp_line = None
            
            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                self.mouse_x, self.mouse_y = pos
                
                # Update hover states
                self.undo_button.check_hover(pos)
                self.redo_button.check_hover(pos)
                self.save_button.check_hover(pos)
                self.prev_doc_button.check_hover(pos)
                self.next_doc_button.check_hover(pos)
                self.add_entity_type_button.check_hover(pos)
                self.add_relation_type_button.check_hover(pos)
                
                # Handle token selection
                self.handle_mouse_motion_selection(pos)
                
                # Update entity hover states
                for entity in self.rendered_entities:
                    was_hovered = entity["hovered"]
                    
                    # Fix for multi-line entities
                    is_hovered = False
                    if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                        # Check if any rectangle in the multi-line entity is hovered
                        for rect in entity["rect"]["rects"]:
                            if rect.collidepoint(pos):
                                is_hovered = True
                                break
                    else:
                        # Regular single-line entity
                        is_hovered = entity["rect"].collidepoint(pos)
                    
                    entity["hovered"] = is_hovered
                    
                    if entity["hovered"] and not was_hovered:
                        # Show relationships for this entity
                        self.show_relationships(f"{entity['start']}-{entity['end']}")
                    elif was_hovered and not entity["hovered"]:
                        # Hide relationships
                        self.hide_relationships()
                
                # Update relation drag line
                if self.dragging_relation:
                    # Update temporary line target point
                    self.temp_line["tgt_x"] = pos[0]
                    self.temp_line["tgt_y"] = pos[1]
        
            # Handle key events for text input
            elif event.type == pygame.KEYDOWN:
                # Handle undo/redo keyboard shortcuts
                if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if not self.undo_button.is_disabled:
                        self.undo()
                elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if not self.redo_button.is_disabled:
                        self.redo()
                # Handle save keyboard shortcut
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.save_annotations()
                # Handle entity deletion with 'd' key
                elif event.key == pygame.K_d:
                    if self.selected_entities:
                        self.delete_selected_entity()
                    elif self.selected_tokens:
                        self.delete_selected_tokens()
                elif self.input_dialog.visible:
                    result = self.input_dialog.handle_key(event)
                    if result == "save":
                        if self.input_dialog.title == "Add New Entity Type":
                            self.add_custom_entity_type(self.input_dialog.text_input.strip())
                        else:
                            self.add_custom_relation_type(self.input_dialog.text_input.strip())
                        self.input_dialog.hide()
                    elif result == "cancel":
                        self.input_dialog.hide()
                
                # Delete focused entity with 'd' key
                if event.key == pygame.K_d and self.hovered_entity_key is not None:
                    self.delete_selected_entity()
                    # Reset hover state after deletion
                    self.hovered_entity = None
        
            # Handle E key entity highlighting outside the event loop
            if self.e_key_held:
                pos = pygame.mouse.get_pos()
                if self.doc_container.collidepoint(pos):
                    entity = self.check_entity_hover(pos)
                    if entity:
                        self.handle_entity_click(entity, right_click=False)
                    else:
                        token = self.check_token_hover(pos)
                        if token and "global_idx" in token:
                            self.handle_token_click(token)
        
        return True
    
    def run(self):
        """Main application loop"""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)  # Limit to 60 FPS
        
        pygame.quit()
        sys.exit()
    
    def undo(self):
        """Undo the last action"""
        if not self.undo_stack:
            return
        
        # Get the last action from undo stack
        action = self.undo_stack.pop()
        
        # Add to redo stack
        self.redo_stack.append(action)
        
        # Update button states
        self.redo_button.is_disabled = False
        self.undo_button.is_disabled = len(self.undo_stack) == 0
        
        # Handle different action types
        if action["action"] == "add_entity":
            # Find and remove the entity
            entity = action["entity"]
            self.remove_entity(entity[0], entity[1])
        elif action["action"] == "add_relation":
            # Find and remove the relation
            relation = action["relation"]
            self.remove_relation(relation[0], relation[1], relation[2], relation[3])
        elif action["action"] == "delete_entity":
            # Add the entity back
            entity = action["entity"]
            self.add_entity(entity[0], entity[1], entity[2])
            
            # Add back all the relations
            for relation in action["relations"]:
                self.add_relation(relation[0], relation[1], relation[2], relation[3], relation[4])
        elif action["action"] == "delete_tokens":
            # This requires a specialized restore function
            self.restore_deleted_tokens(action["tokens"], action["entities"], action["relations"])
        
        # Re-render document
        self.render_document()
    
    def redo(self):
        """Redo the last undone action"""
        if not self.redo_stack:
            return
        
        # Get the last action from redo stack
        action = self.redo_stack.pop()
        
        # Add to undo stack
        self.undo_stack.append(action)
        
        # Update button states
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = len(self.redo_stack) == 0
        
        # Handle different action types
        if action["action"] == "add_entity":
            # Add the entity back
            entity = action["entity"]
            self.add_entity(entity[0], entity[1], entity[2])
        elif action["action"] == "add_relation":
            # Add the relation back
            relation = action["relation"]
            self.add_relation(relation[0], relation[1], relation[2], relation[3], relation[4])
        elif action["action"] == "delete_entity":
            # Remove the entity
            entity = action["entity"]
            self.remove_entity(entity[0], entity[1])
            
            # Remove all relations that involve this entity
            for relation in action["relations"]:
                self.remove_relation(relation[0], relation[1], relation[2], relation[3])
        elif action["action"] == "delete_tokens":
            # Delete the tokens again
            self.selected_tokens = [token["global_idx"] for token in action["tokens"]]
            self.delete_selected_tokens()
            # Remove the duplicate action that was added
            self.undo_stack.pop()
        
        # Re-render document
        self.render_document()
    
    def remove_entity(self, start_idx, end_idx):
        """Remove an entity from the document"""
        # Find and remove the entity from all sentences
        for sent_entities in self.doc["ner"]:
            for i, entity in enumerate(sent_entities):
                if entity[0] == start_idx and entity[1] == end_idx:
                    sent_entities.pop(i)
                    return
    
    def remove_relation(self, src_start, src_end, tgt_start, tgt_end):
        """Remove a relation from the document"""
        # Find and remove the relation from all sentences
        for sent_relations in self.doc["relations"]:
            for i, relation in enumerate(sent_relations):
                if (relation[0] == src_start and relation[1] == src_end and
                    relation[2] == tgt_start and relation[3] == tgt_end):
                    sent_relations.pop(i)
                    return
    
    def add_entity(self, start_idx, end_idx, entity_type):
        """Add an entity to the document"""
        # Make sure ner list is initialized for all sentences
        while len(self.doc["ner"]) < len(self.doc["sentences"]):
            self.doc["ner"].append([])
        
        # Add to first sentence's entity list for simplicity
        self.doc["ner"][0].append([start_idx, end_idx, entity_type])
    
    def add_relation(self, src_start, src_end, tgt_start, tgt_end, rel_type):
        """Add a relation to the document"""
        # Make sure relations list is initialized for all sentences
        while len(self.doc["relations"]) < len(self.doc["sentences"]):
            self.doc["relations"].append([])
        
        # Add to first sentence's relations list for simplicity
        self.doc["relations"][0].append([src_start, src_end, tgt_start, tgt_end, rel_type])
    
    def save_annotations(self):
        """Save annotations to file"""
        try:
            # Save current document to collection
            self.save_current_document()
            
            # Write all documents back to JSONL file
            with open(JSONL_FILE_PATH, 'w', encoding='utf-8') as f:
                for doc in self.document_collection:
                    f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
            # Update save status
            self.save_status = "Saved successfully!"
            self.save_status_time = pygame.time.get_ticks()
            
            # Save history
            save_history(self.undo_stack, self.redo_stack)
            
            return True
        except Exception as e:
            self.save_status = f"Error: {str(e)}"
            self.save_status_time = pygame.time.get_ticks()
            print(f"Error saving annotations: {e}")
            return False

    def delete_selected_entity(self):
        """Delete the currently selected entity and all its relationships"""
        if not self.selected_entities:
            return
        
        # Get the key of the selected entity
        entity_key = self.selected_entities[0]
        start_idx, end_idx = map(int, entity_key.split('-'))
        
        # Find the entity and its type for the undo action
        entity_type = None
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3 and entity[0] == start_idx and entity[1] == end_idx:
                    entity_type = entity[2]
                    break
            if entity_type:
                break
        
        if not entity_type:
            return  # Entity not found
        
        # Track removed relations for undo
        removed_relations = []
        
        # Remove all relations involving this entity
        for sent_relations in self.doc["relations"]:
            to_remove = []
            for i, relation in enumerate(sent_relations):
                if (relation[0] == start_idx and relation[1] == end_idx) or \
                   (relation[2] == start_idx and relation[3] == end_idx):
                    # Store relation for undo
                    removed_relations.append(relation.copy())
                    to_remove.append(i)
            
            # Remove relations in reverse order to avoid index issues
            for i in sorted(to_remove, reverse=True):
                sent_relations.pop(i)
        
        # Remove the entity
        self.remove_entity(start_idx, end_idx)
        
        # Add to undo stack - first store the entity deletion
        action = {
            "action": "delete_entity",
            "entity": [start_idx, end_idx, entity_type],
            "relations": removed_relations
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()
        
        # Update button states
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Clear selection state
        self.selected_entities = []
        if entity_key in self.selected_entity_labels:
            del self.selected_entity_labels[entity_key]
        
        # Update status message
        self.status_message = f"Deleted {entity_type} Entity and Related Relations"
        
        # Re-render document to reflect changes
        self.render_document()

    def handle_mouse_motion_selection(self, pos):
        """Handle mouse motion for token selection"""
        if self.is_selecting and self.selection_start_token:
            # Check if hovering over a token
            token = self.check_token_hover(pos)
            if token and "global_idx" in token:
                # Calculate token range
                start_idx = min(self.selection_start_token["global_idx"], token["global_idx"])
                end_idx = max(self.selection_start_token["global_idx"], token["global_idx"])
                
                # Update selected tokens
                self.selected_tokens = list(range(start_idx, end_idx + 1))
                
                # Re-render the document to show updated selection
                self.render_document()
        
        # Check if mouse is over any token
        hovered_token = self.check_token_hover(pos)
        self.hovered_token = hovered_token
        
        # Update selection if active and mouse moved or e key is pressed
    def handle_mouse_up_selection(self, pos):
        """Handle mouse button up for token selection"""
        if self.is_selecting and self.selected_tokens:
            # Get the selection range
            start_idx = min(self.selected_tokens)
            end_idx = max(self.selected_tokens)
            
            # Show entity type popup near selection (for both single and multiple tokens)
            token_info = self.get_token_info(start_idx)
            if token_info:
                # Find the position of the first selected token
                for token in self.rendered_tokens:
                    if token["global_idx"] == start_idx:
                        self.entity_popup.show(token["rect"].x, token["rect"].y + token["rect"].height + 10)
                        break
            
            # Reset selection state
            self.is_selecting = False
        else:
            self.is_selecting = False

    def handle_token_click(self, token):
        """Handle click on a token to start selection"""
        # Start token selection
        self.is_selecting = True
        self.selection_start_token = token
        
        # Clear previous selection and select only the clicked token
        self.selected_tokens = [token["global_idx"]]
        
        # Clear any other selection states
        self.selected_entities = []
        self.relation_source_entity = None
        self.relation_target_entity = None
        
        # Update status message
        self.status_message = "Selecting Text"
        
        # Re-render to show selection
        self.render_document()
        
        # Remove or modify the check that prevents selection from starting on already-annotated tokens
        # Instead of blocking selection on tokens that are part of entities, allow it:
        self.selection_start = token['global_idx']
        self.selection_end = token['global_idx']  # Fix indentation to match surrounding code
        self.selection_active = True
        self.selecting_entity = True
        
        # Track that we started selection inside an existing entity (if applicable)
        self.selecting_within_entity = any(
            entity['start'] <= token['global_idx'] <= entity['end'] 
            for entity in self.current_document['entities']
        )

    def create_new_entity(self):
        """Create a new entity from the current selection"""
        if not self.selected_tokens or not self.selected_entity_type:
            return
        
        # Get the selection range
        start_idx = min(self.selected_tokens)
        end_idx = max(self.selected_tokens)
        
        # Check if this entity already exists
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3 and entity[0] == start_idx and entity[1] == end_idx:
                    # Entity already exists, just update its type
                    entity[2] = self.selected_entity_type
                    self.render_document()
                    return
        
        # Add the new entity
        self.add_entity(start_idx, end_idx, self.selected_entity_type)
        
        # Add to undo stack
        action = {
            "action": "add_entity",
            "entity": [start_idx, end_idx, self.selected_entity_type]
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()
        
        # Update button states
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Reset selection state
        self.selected_tokens = []
        self.selected_entity_type = None
        
        # Re-render document to show the new entity
        self.render_document()
        
        # Update status message
        self.status_message = f"Created {self.selected_entity_type} Entity"

    def handle_entity_click(self, entity, right_click=False):
        """Handle click on an entity"""
        # Get entity key for identification
        entity_key = f"{entity['start']}-{entity['end']}"
        
        if right_click:
            # Right-click starts dragging a relation from this entity
            self.start_dragging_relation(entity)
            
            # Update status message
            self.status_message = f"Dragging Relation from {entity['type']}"
        else:
            # Left-click selects the entity
            
            # Clear any previous token selection
            self.selected_tokens = []
            
            # Toggle selection for this entity
            if entity_key in self.selected_entities:
                self.selected_entities.remove(entity_key)
                # Remove the entity label when deselected
                if entity_key in self.selected_entity_labels:
                    del self.selected_entity_labels[entity_key]
                self.status_message = "Entity Deselected"
            else:
                # Clear previous entity selections (single selection mode)
                self.selected_entities = [entity_key]
                
                # Clear all previous entity labels first - this is the key change
                self.selected_entity_labels = {}
                
                # Store entity info for label display
                entity_type = entity["type"]
                if isinstance(entity_type, list):
                    entity_type = entity_type[0] if entity_type else "Unknown"
                
                # Get center point of entity for positioning the label
                center_x, center_y = self.get_entity_center(entity)
                
                # Add entity label info for the newly selected entity
                self.selected_entity_labels[entity_key] = {
                    "type": entity_type,
                    "pos": (center_x, self.get_entity_top(entity) - 20),  # Position above entity
                    "color": ENTITY_COLORS.get(entity_type, (200, 200, 200))
                }
                
                self.status_message = f"Selected {entity_type} Entity"
            
            # Update entity's selected state in rendered entities
            for rendered_entity in self.rendered_entities:
                # First reset all entities to not selected
                rendered_entity["selected"] = False
                
                # Then set only the currently selected entity
                if f"{rendered_entity['start']}-{rendered_entity['end']}" in self.selected_entities:
                    rendered_entity["selected"] = True
        
        # Re-render document to show selection changes
        self.render_document()

    def reset_relation_creation(self):
        """Reset relation creation state"""
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        self.status_message = "Relation Creation Cancelled"

    def create_new_relation(self):
        """Create a new relation between selected entities"""
        if not self.relation_source_entity or not self.relation_target_entity or not self.selected_relation_type:
            return
        
        src_start, src_end = self.relation_source_entity[0], self.relation_source_entity[1]
        tgt_start, tgt_end = self.relation_target_entity[0], self.relation_target_entity[1]
        
        # Check if this relation already exists
        for sent_relations in self.doc["relations"]:
            for relation in sent_relations:
                if (relation[0] == src_start and relation[1] == src_end and
                    relation[2] == tgt_start and relation[3] == tgt_end):
                    # Relation already exists, just update its type
                    relation[4] = self.selected_relation_type
                    self.render_document()
                    return
        
        # Add the new relation
        self.add_relation(src_start, src_end, tgt_start, tgt_end, self.selected_relation_type)
        
        # Add to undo stack
        action = {
            "action": "add_relation",
            "relation": [src_start, src_end, tgt_start, tgt_end, self.selected_relation_type]
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()
        
        # Update button states
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Reset relation creation state
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        
        # Re-render document to show the new relation
        self.render_document()
        
        # Update status message
        self.status_message = f"Created {self.selected_relation_type} Relation"

    def get_entity_center(self, entity):
        """Get the center point of an entity, handling multi-line entities"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            # For multi-line, use the middle of all the rectangles
            rects = entity["rect"]["rects"]
            total_x, total_y = 0, 0
            for rect in rects:
                total_x += rect.centerx
                total_y += rect.centery
            return total_x // len(rects), total_y // len(rects)
        else:
            # Normal single-line entity
            return entity["rect"].centerx, entity["rect"].centery
    
    def get_entity_top(self, entity):
        """Get the top edge of an entity, handling multi-line entities"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            # Return the top of the first rectangle
            return min(rect.top for rect in entity["rect"]["rects"])
        else:
            return entity["rect"].top
    
    def get_entity_bottom(self, entity):
        """Get the bottom edge of an entity, handling multi-line entities"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            # Return the bottom of the last rectangle
            return max(rect.bottom for rect in entity["rect"]["rects"])
        else:
            return entity["rect"].bottom

    def delete_selected_tokens(self):
        """Delete the currently selected tokens and update all entity/relation indices"""
        if not self.selected_tokens:
            return
        
        # Sort tokens for easier processing
        selected_indices = sorted(self.selected_tokens)
        
        # Store info for undo
        deleted_tokens = []
        affected_entities = []
        affected_relations = []
        
        # Find the sentence and token information for each selected token
        token_info_list = []
        for idx in selected_indices:
            info = self.get_token_info(idx)
            if info:
                token_info_list.append({
                    "global_idx": idx,
                    "sent_idx": info["sent_idx"],
                    "tok_idx": info["tok_idx"],
                    "text": self.doc["sentences"][info["sent_idx"]][info["tok_idx"]]
                })
                deleted_tokens.append(token_info_list[-1])
        
        # Group tokens by sentence
        tokens_by_sentence = {}
        for info in token_info_list:
            sent_idx = info["sent_idx"]
            if sent_idx not in tokens_by_sentence:
                tokens_by_sentence[sent_idx] = []
            tokens_by_sentence[sent_idx].append(info)
        
        # Count tokens to be removed per sentence
        tokens_to_remove = {}
        for sent_idx, tokens in tokens_by_sentence.items():
            tokens_to_remove[sent_idx] = len(tokens)
        
        # Record the entities that will be affected (for undo)
        for sent_idx, entities in enumerate(self.doc["ner"]):
            for entity in entities:
                # Check if entity overlaps with deleted tokens
                if any(entity[0] <= idx <= entity[1] for idx in selected_indices):
                    affected_entities.append(entity.copy())
                # Check if entity comes after deleted tokens
                elif entity[0] > min(selected_indices):
                    affected_entities.append(entity.copy())
        
        # Record the relations that will be affected (for undo)
        for sent_idx, relations in enumerate(self.doc["relations"]):
            for relation in relations:
                # Check if relation involves entities affected by the deletion
                if (any(relation[0] <= idx <= relation[1] for idx in selected_indices) or
                    any(relation[2] <= idx <= relation[3] for idx in selected_indices) or
                    relation[0] > min(selected_indices) or
                    relation[2] > min(selected_indices)):
                    affected_relations.append(relation.copy())
        
        # Remove tokens from each sentence in reverse order to maintain indices
        for sent_idx in sorted(tokens_by_sentence.keys()):
            sent_tokens = sorted(tokens_by_sentence[sent_idx], key=lambda x: x["tok_idx"], reverse=True)
            for token in sent_tokens:
                del self.doc["sentences"][sent_idx][token["tok_idx"]]
        
        # Recalculate global indices after removal
        tokens_removed = len(selected_indices)
        shift_map = {}  # Map from old global index to new global index
        
        current_total = 0
        for sent_idx, sentence in enumerate(self.doc["sentences"]):
            for tok_idx in range(len(sentence)):
                old_idx = current_total
                # If we've passed tokens that were removed from this sentence
                if sent_idx in tokens_by_sentence:
                    removed_from_this_sentence = sum(1 for t in tokens_by_sentence[sent_idx] if t["tok_idx"] <= tok_idx)
                    old_idx += removed_from_this_sentence
                
                # Account for tokens removed from previous sentences
                for s_idx in tokens_by_sentence:
                    if s_idx < sent_idx:
                        old_idx += len(tokens_by_sentence[s_idx])
                
                shift_map[old_idx] = current_total
                current_total += 1
        
        # Update entity indices
        for sent_idx, entities in enumerate(self.doc["ner"]):
            i = 0
            while i < len(entities):
                entity = entities[i]
                
                # Remove entities that include deleted tokens
                if any(entity[0] <= idx <= entity[1] for idx in selected_indices):
                    entities.pop(i)
                    continue
                    
                # Update indices for entities after the deleted tokens
                if entity[0] > min(selected_indices):
                    # Find new start index
                    new_start = None
                    for idx in range(entity[0], entity[0] + tokens_removed + 1):
                        if idx in shift_map:
                            new_start = shift_map[idx]
                            break
                    
                    # Find new end index
                    new_end = None
                    for idx in range(entity[1], entity[1] + tokens_removed + 1):
                        if idx in shift_map:
                            new_end = shift_map[idx]
                            break
                    
                    if new_start is not None and new_end is not None:
                        entity[0] = new_start
                        entity[1] = new_end
                    else:
                        # If we can't map the indices, remove the entity
                        entities.pop(i)
                        continue
                
                i += 1
        
        # Update relation indices similarly
        for sent_idx, relations in enumerate(self.doc["relations"]):
            i = 0
            while i < len(relations):
                relation = relations[i]
                
                # Remove relations that include deleted tokens
                if (any(relation[0] <= idx <= relation[1] for idx in selected_indices) or
                    any(relation[2] <= idx <= relation[3] for idx in selected_indices)):
                    relations.pop(i)
                    continue
                
                # Update indices for relations after the deleted tokens
                updated = False
                if relation[0] > min(selected_indices):
                    # Update source entity
                    new_start = None
                    for idx in range(relation[0], relation[0] + tokens_removed + 1):
                        if idx in shift_map:
                            new_start = shift_map[idx]
                            break
                    
                    new_end = None
                    for idx in range(relation[1], relation[1] + tokens_removed + 1):
                        if idx in shift_map:
                            new_end = shift_map[idx]
                            break
                    
                    if new_start is not None and new_end is not None:
                        relation[0] = new_start
                        relation[1] = new_end
                        updated = True
                
                if relation[2] > min(selected_indices):
                    # Update target entity
                    new_start = None
                    for idx in range(relation[2], relation[2] + tokens_removed + 1):
                        if idx in shift_map:
                            new_start = shift_map[idx]
                            break
                    
                    new_end = None
                    for idx in range(relation[3], relation[3] + tokens_removed + 1):
                        if idx in shift_map:
                            new_end = shift_map[idx]
                            break
                    
                    if new_start is not None and new_end is not None:
                        relation[2] = new_start
                        relation[3] = new_end
                        updated = True
                
                # If we couldn't properly update the relation, remove it
                if relation[0] > min(selected_indices) and not updated:
                    relations.pop(i)
                    continue
                
                i += 1
        
        # Add to undo stack
        action = {
            "action": "delete_tokens",
            "tokens": deleted_tokens,
            "entities": affected_entities,
            "relations": affected_relations
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()
        
        # Update button states
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Clear selection state
        self.selected_tokens = []
        
        # Update status message
        self.status_message = f"Deleted {tokens_removed} tokens"
        
        # Re-render document to reflect changes
        self.render_document()

    def restore_deleted_tokens(self, tokens, entities, relations):
        """Restore tokens that were deleted, along with their entities and relations"""
        # Group tokens by sentence
        tokens_by_sentence = {}
        for token in tokens:
            sent_idx = token["sent_idx"]
            if sent_idx not in tokens_by_sentence:
                tokens_by_sentence[sent_idx] = []
            tokens_by_sentence[sent_idx].append(token)
        
        # Sort tokens by their original position
        for sent_idx in tokens_by_sentence:
            tokens_by_sentence[sent_idx].sort(key=lambda x: x["tok_idx"])
        
        # Restore tokens to each sentence
        for sent_idx, sent_tokens in tokens_by_sentence.items():
            # Ensure the sentence exists
            while len(self.doc["sentences"]) <= sent_idx:
                self.doc["sentences"].append([])
            
            # Insert tokens at their original positions
            for token in sent_tokens:
                tok_idx = token["tok_idx"]
                text = token["text"]
                
                # Insert at the correct position, extending the list if needed
                if tok_idx >= len(self.doc["sentences"][sent_idx]):
                    self.doc["sentences"][sent_idx].extend([""] * (tok_idx - len(self.doc["sentences"][sent_idx]) + 1))
                
                self.doc["sentences"][sent_idx].insert(tok_idx, text)
        
        # Restore entities
        for entity in entities:
            # Find where this entity belongs
            found = False
            for sent_idx, sent_entities in enumerate(self.doc["ner"]):
                for i, existing_entity in enumerate(sent_entities):
                    if (existing_entity[0] == entity[0] and 
                        existing_entity[1] == entity[1] and
                        existing_entity[2] == entity[2]):
                        found = True
                        break
                if found:
                    break
            
            if not found:
                # Add entity to the appropriate sentence
                # For simplicity, add to the first sentence's entities
                if len(self.doc["ner"]) == 0:
                    self.doc["ner"].append([])
                self.doc["ner"][0].append(entity)
        
        # Restore relations
        for relation in relations:
            # Find where this relation belongs
            found = False
            for sent_idx, sent_relations in enumerate(self.doc["relations"]):
                for i, existing_relation in enumerate(sent_relations):
                    if (existing_relation[0] == relation[0] and 
                        existing_relation[1] == relation[1] and
                        existing_relation[2] == relation[2] and
                        existing_relation[3] == relation[3] and
                        existing_relation[4] == relation[4]):
                        found = True
                        break
                if found:
                    break
            
            if not found:
                # Add relation to the appropriate sentence
                # For simplicity, add to the first sentence's relations
                if len(self.doc["relations"]) == 0:
                    self.doc["relations"].append([])
                self.doc["relations"][0].append(relation)

# New input dialog class for adding custom types
class InputDialog:
    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = False
        self.text_input = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Create buttons
        button_width = 80
        button_height = 30
        button_margin = 10
        
        self.cancel_button = Button(
            x + width - 2 * button_width - button_margin, 
            y + height - button_height - button_margin,
            button_width, button_height, "Cancel", color=(244, 67, 54)
        )
        
        self.save_button = Button(
            x + width - button_width - button_margin, 
            y + height - button_height - button_margin,
            button_width, button_height, "Save"
        )
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Draw popup background
        pygame.draw.rect(surface, (255, 255, 255), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2)
        
        # Draw title
        title_surf = self.title_font.render(self.title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw horizontal line below title
        pygame.draw.line(surface, (200, 200, 200), 
                        (self.rect.x, self.rect.y + 40), 
                        (self.rect.x + self.rect.width, self.rect.y + 40))
        
        # Draw text input box
        input_rect = pygame.Rect(self.rect.x + 20, self.rect.y + 60, 
                               self.rect.width - 40, 30)
        pygame.draw.rect(surface, (240, 240, 240), input_rect)
        pygame.draw.rect(surface, (200, 200, 200), input_rect, 1)
        
        # Draw input text
        text_surf = self.font.render(self.text_input, True, (0, 0, 0))
        surface.blit(text_surf, (input_rect.x + 5, input_rect.y + 5))
        
        # Draw cursor
        if self.cursor_visible:
            text_width = self.font.size(self.text_input)[0]
            cursor_x = input_rect.x + 5 + text_width
            pygame.draw.line(surface, (0, 0, 0), 
                            (cursor_x, input_rect.y + 5), 
                            (cursor_x, input_rect.y + 25), 1)
        
        # Update cursor blink
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > 500:  # Blink every 500ms
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
        
        # Draw buttons
        self.cancel_button.draw(surface)
        self.save_button.draw(surface)
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        if not self.visible:
            return None
        
        # Check buttons
        if self.cancel_button.click(pos):
            return "cancel"
        
        if self.save_button.click(pos):
            return "save"
        
        return None
    
    def handle_key(self, event) -> Optional[str]:
        if not self.visible:
            return None
        
        if event.key == pygame.K_BACKSPACE:
            self.text_input = self.text_input[:-1]
        elif event.key == pygame.K_RETURN:
            if self.text_input.strip():  # Only save if text isn't empty
                return "save"
        elif event.key == pygame.K_ESCAPE:
            return "cancel"
        else:
            # Add character to input (limit to reasonable length)
            if len(self.text_input) < 30:
                self.text_input += event.unicode
        
        # Reset cursor blink
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        return None
    
    def show(self, x: Optional[int] = None, y: Optional[int] = None):
        self.visible = True
        self.text_input = "" 
        if x is not None and y is not None:
            # Ensure popup stays within screen bounds
            self.rect.x = min(max(x, 0), SCREEN_WIDTH - self.rect.width)
            self.rect.y = min(max(y, 0), SCREEN_HEIGHT - self.rect.height)
            
            # Update button positions
            button_width = 80
            button_height = 30
            button_margin = 10
            
            self.cancel_button.rect.x = self.rect.x + self.rect.width - 2 * button_width - button_margin
            self.cancel_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
            
            self.save_button.rect.x = self.rect.x + self.rect.width - button_width - button_margin
            self.save_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
    
    def hide(self):
        self.visible = False

if __name__ == "__main__":
    app = EntityAnnotator()
    app.run()