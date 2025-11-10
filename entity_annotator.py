"""
Entity Annotator - Main Application Class
Refactored for better organization and maintainability
"""
import pygame
import sys
import math
import random
from collections import deque
from typing import List, Dict, Tuple, Optional
import os

# Handle both relative and absolute imports
try:
    from .ui_components import Button, Popup, InputDialog
    from .file_browser import FileBrowser
    from .navigation import NavigationBar, ShortcutHelp
    from .utils import (
        load_settings, save_settings, load_history, save_history,
        load_jsonl, save_jsonl, generate_random_color, normalize_type
    )
    from . import config as cfg
    from .db_manager import AnnotationDatabase
except ImportError:
    from ui_components import Button, Popup, InputDialog
    from file_browser import FileBrowser
    from navigation import NavigationBar, ShortcutHelp
    from utils import (
        generate_random_color, normalize_type
    )
    import config as cfg
    try:
        from db_manager import AnnotationDatabase
    except ImportError:
        AnnotationDatabase = None  # DuckDB not available


class EntityAnnotator:
    """Main Entity Annotation Application"""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Window setup with config
        self.width = cfg.DEFAULT_WINDOW_WIDTH
        self.height = cfg.DEFAULT_WINDOW_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        
        # Set custom icon (simple annotation icon)
        try:
            icon_surface = pygame.Surface((32, 32))
            icon_surface.fill((255, 255, 255))
            # Draw a simple "A" icon for Annotator
            pygame.draw.rect(icon_surface, (63, 81, 181), (4, 4, 24, 24), border_radius=4)
            font = pygame.font.SysFont('Arial', 20, bold=True)
            text = font.render('A', True, (255, 255, 255))
            text_rect = text.get_rect(center=(16, 16))
            icon_surface.blit(text, text_rect)
            pygame.display.set_icon(icon_surface)
        except:
            pass  # If icon creation fails, use default
        
        self.clock = pygame.time.Clock()
        
        # Load fonts with fallback
        font_family = cfg.FONT_FAMILY
        try:
            self.font = pygame.font.SysFont(font_family, cfg.FONT_SIZE_NORMAL)
            self.small_font = pygame.font.SysFont(font_family, cfg.FONT_SIZE_SMALL)
            self.tiny_font = pygame.font.SysFont(font_family, cfg.FONT_SIZE_TINY)
            self.bold_font = pygame.font.SysFont(font_family, cfg.FONT_SIZE_NORMAL, bold=True)
            self.title_font = pygame.font.SysFont(font_family, cfg.FONT_SIZE_TITLE, bold=True)
        except:
            # Fallback to Arial
            self.font = pygame.font.SysFont(cfg.FONT_FAMILY_FALLBACK, cfg.FONT_SIZE_NORMAL)
            self.small_font = pygame.font.SysFont(cfg.FONT_FAMILY_FALLBACK, cfg.FONT_SIZE_SMALL)
            self.tiny_font = pygame.font.SysFont(cfg.FONT_FAMILY_FALLBACK, cfg.FONT_SIZE_TINY)
            self.bold_font = pygame.font.SysFont(cfg.FONT_FAMILY_FALLBACK, cfg.FONT_SIZE_NORMAL, bold=True)
            self.title_font = pygame.font.SysFont(cfg.FONT_FAMILY_FALLBACK, cfg.FONT_SIZE_TITLE, bold=True)
        
        # Default colors (no persistent settings)
        self.entity_colors = {}
        self.relation_colors = {}
        self.settings = {
            "known_entities": [],
            "known_relations": [],
            "custom_entities": [],
            "custom_relations": []
        }
        
        # Document data (DuckDB only)
        self.current_doc_index = 0
        self.doc = {"sentences": [], "ner": [], "relations": []}
        self.doc_id = None
        self.current_file_path = None
        
        # Database
        self.database = None
        self.doc_ids = []  # List of document IDs
        
        # UI State
        self.status_message = cfg.STATUS_DEFAULT
        self.save_status = ""
        self.save_status_time = 0
        
        # Smooth scrolling
        self.target_scroll_y = 0
        self.current_scroll_velocity = 0
        
        # Annotation state
        self.is_selecting = False
        self.selection_start_token = None
        self.selected_tokens = []
        self.selected_entity_type = None
        self.selected_entities = []
        self.selected_entity_labels = {}
        
        # Relation creation state
        self.dragging_relation = False
        self.drag_source_entity = None
        self.drag_source_key = None
        self.temp_line = None
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        
        # Mouse tracking
        self.mouse_x = 0
        self.mouse_y = 0
        self.hovered_entity_key = None
        self.e_key_held = False
        
        # History (no persistence)
        self.undo_stack = deque(maxlen=cfg.MAX_UNDO_HISTORY)
        self.redo_stack = deque(maxlen=cfg.MAX_UNDO_HISTORY)
        
        # Rendering data
        self.rendered_entities = []
        self.rendered_tokens = []
        self.rendered_relations = []
        self.rendered_labels = []
        self.entity_elements = {}
        
        # Scrolling
        self.doc_scroll_y = 0
        self.max_scroll_y = 0
        
        # Document container with config-based layout
        toolbar_bottom = cfg.TOOLBAR_HEIGHT + cfg.NAV_BAR_HEIGHT + cfg.NAV_BAR_MARGIN * 2
        self.doc_container = pygame.Rect(
            cfg.DOC_CONTAINER_MARGIN, 
            toolbar_bottom,
            self.width - cfg.DOC_CONTAINER_MARGIN * 2, 
            self.height - toolbar_bottom - cfg.DOC_CONTAINER_MARGIN
        )
        
        # Initialize UI components
        self.setup_ui()
        
        # Deferred file loading (after first frame to prevent freeze)
        self.pending_file_load = None
        default_file = 'combined_scier_hyperpie_test.jsonl'
        if hasattr(sys, 'argv') and len(sys.argv) > 1:
            self.pending_file_load = sys.argv[1]
        elif os.path.exists(default_file):
            self.pending_file_load = default_file
    
    def setup_ui(self):
        """Initialize all UI components with modern styling"""
        button_width = cfg.BUTTON_WIDTH
        button_height = cfg.BUTTON_HEIGHT
        button_margin = cfg.BUTTON_MARGIN
        toolbar_y = cfg.TOOLBAR_PADDING + 35  # Below title
        
        # Toolbar buttons with modern colors
        x_pos = cfg.TOOLBAR_PADDING
        
        self.undo_button = Button(x_pos, toolbar_y, button_width, button_height, "Undo",
                                  color=cfg.COLOR_SECONDARY, hover_color=cfg.COLOR_SECONDARY_HOVER)
        self.undo_button.is_disabled = len(self.undo_stack) == 0
        x_pos += button_width + button_margin
        
        self.redo_button = Button(x_pos, toolbar_y, button_width, button_height, "Redo",
                                  color=cfg.COLOR_SECONDARY, hover_color=cfg.COLOR_SECONDARY_HOVER)
        self.redo_button.is_disabled = len(self.redo_stack) == 0
        x_pos += button_width + button_margin
        
        self.save_button = Button(x_pos, toolbar_y, button_width, button_height, "Save",
                                  color=cfg.COLOR_SUCCESS, hover_color=cfg.COLOR_SUCCESS_HOVER)
        x_pos += button_width + button_margin
        
        self.open_file_button = Button(x_pos, toolbar_y, button_width, button_height, "Open File",
                                       color=cfg.COLOR_PRIMARY, hover_color=cfg.COLOR_PRIMARY_HOVER)
        x_pos += button_width + button_margin
        
        self.add_entity_type_button = Button(x_pos, toolbar_y, button_width, button_height, "+ Entity",
                                             color=cfg.COLOR_INFO, hover_color=cfg.COLOR_INFO_HOVER)
        x_pos += button_width + button_margin
        
        self.add_relation_type_button = Button(x_pos, toolbar_y, button_width, button_height, "+ Relation",
                                               color=cfg.COLOR_INFO, hover_color=cfg.COLOR_INFO_HOVER)
        
        # Navigation buttons
        nav_y = toolbar_y + button_height + button_margin
        self.prev_doc_button = Button(cfg.TOOLBAR_PADDING, nav_y, button_width, button_height, "Previous",
                                      color=cfg.COLOR_SECONDARY, hover_color=cfg.COLOR_SECONDARY_HOVER)
        
        self.next_doc_button = Button(cfg.TOOLBAR_PADDING + button_width + button_margin, nav_y,
                                      button_width, button_height, "Next",
                                      color=cfg.COLOR_SECONDARY, hover_color=cfg.COLOR_SECONDARY_HOVER)
        
        # Export button
        x_pos = cfg.TOOLBAR_PADDING + (button_width + button_margin) * 2
        self.export_button = Button(x_pos, nav_y, button_width, button_height, "Export JSONL",
                                    color=cfg.COLOR_SUCCESS, hover_color=cfg.COLOR_SUCCESS_HOVER)
        
        # Popups
        self.entity_popup = Popup(300, 300, 250, 400, "Select Entity Type")
        entity_options = [{"text": et, "value": et, "color": color} 
                         for et, color in self.entity_colors.items()]
        self.entity_popup.set_options(entity_options)
        
        self.relation_popup = Popup(300, 300, 250, 400, "Select Relation Type")
        relation_options = [{"text": rt, "value": rt, "color": color}
                           for rt, color in self.relation_colors.items()]
        self.relation_popup.set_options(relation_options)
        
        self.input_dialog = InputDialog(300, 300, 350, 180, "Add New Type")
        
        # New components with config-based layout
        self.file_browser = FileBrowser(width=900, height=600)
        nav_bar_y = cfg.TOOLBAR_HEIGHT + cfg.NAV_BAR_MARGIN
        self.navigation_bar = NavigationBar(cfg.TOOLBAR_PADDING, nav_bar_y, 
                                           self.width - cfg.TOOLBAR_PADDING * 2, 
                                           cfg.NAV_BAR_HEIGHT)
        self.shortcut_help = ShortcutHelp()
    
    def load_file(self, file_path: str) -> bool:
        """Load annotations from DuckDB or create from JSONL"""
        try:
            if not file_path:
                return False
            
            # If it's a JSONL file, convert to DuckDB
            if file_path.endswith('.jsonl'):
                db_path = file_path.replace('.jsonl', '.duckdb')
                
                # Always create/recreate database from JSONL
                if os.path.exists(db_path):
                    self.status_message = f"Loading existing database..."
                    return self.load_from_database(db_path)
                else:
                    self.status_message = f"Creating database from JSONL..."
                    return self.import_and_use_database(file_path, db_path)
            
            # If it's already a DuckDB file, load it directly
            elif file_path.endswith('.duckdb'):
                return self.load_from_database(file_path)
            
            else:
                self.status_message = "Error: Only .jsonl and .duckdb files supported"
                return False
            
        except Exception as e:
            self.status_message = f"Error loading file: {str(e)}"
            print(f"Error loading file: {e}")
            return False
    
    def import_and_use_database(self, jsonl_path: str, db_path: str) -> bool:
        """Import JSONL into database"""
        try:
            # Show import progress
            self.draw_progress_bar(0.0, "Creating database...")
            
            self.database = AnnotationDatabase(db_path)
            
            # Create progress callback that updates UI
            def import_progress(progress, message):
                self.draw_progress_bar(progress, message)
                pygame.event.pump()  # Keep window responsive
            
            self.draw_progress_bar(0.3, "Starting import...")
            count = self.database.import_from_jsonl(jsonl_path, progress_callback=import_progress)
            
            self.draw_progress_bar(0.6, "Indexing database...")
            pygame.event.pump()
            
            self.current_file_path = db_path
            self.doc_ids = self.database.get_document_ids()
            
            if self.doc_ids:
                self.draw_progress_bar(0.8, "Loading first document...")
                pygame.event.pump()
                self.load_document(0)
                self.extract_and_save_entity_types(scan_all_docs=True)
            
            self.save_status = f"✓ Imported {count} documents to database"
            self.save_status_time = pygame.time.get_ticks()
            self.status_message = f"Using database: {db_path}"
            
            return True
        except Exception as e:
            self.status_message = f"Database import failed: {e}"
            print(f"Database import failed: {e}")
            return False
    
    def load_from_database(self, db_path: str) -> bool:
        """Load from existing database"""
        try:
            self.draw_progress_bar(0.0, "Opening database...")
            pygame.event.pump()
            
            self.database = AnnotationDatabase(db_path)
            
            self.draw_progress_bar(0.3, "Loading document list...")
            pygame.event.pump()
            
            self.current_file_path = db_path
            self.doc_ids = self.database.get_document_ids()
            
            if self.doc_ids:
                self.draw_progress_bar(0.5, "Loading first document...")
                pygame.event.pump()
                self.load_document(0)
                self.extract_and_save_entity_types(scan_all_docs=True)
            
            count = len(self.doc_ids)
            self.save_status = f"✓ Loaded database ({count} documents)"
            self.save_status_time = pygame.time.get_ticks()
            self.status_message = f"Using database: {db_path}"
            
            return True
        except Exception as e:
            print(f"Database load failed: {e}")
            return False
    
    def load_document(self, index: int):
        """Load document at specified index from database"""
        if 0 <= index < len(self.doc_ids):
            self.current_doc_index = index
            doc = self.database.get_document(self.doc_ids[index])
            
            if doc:
                self.doc_id = doc.get("doc_id", f"doc_{index}")
                self.doc["sentences"] = doc.get("sentences", [])
                self.doc["ner"] = doc.get("ner", [])
                self.doc["relations"] = doc.get("relations", [])
                
                # Update navigation buttons
                self.prev_doc_button.is_disabled = (index == 0)
                self.next_doc_button.is_disabled = (index == len(self.doc_ids) - 1)
                
                # Reset scroll and state
                self.doc_scroll_y = 0
                self.target_scroll_y = 0
                self.selected_entities = []
                self.selected_tokens = []
                self.selected_entity_labels = {}
                
                self.render_document()
                self.status_message = f"Document {index + 1}/{len(self.doc_ids)}"
    
    def save_annotations(self, show_immediate_feedback=False) -> bool:
        """Save annotations to database"""
        try:
            if not self.current_file_path:
                self.save_status = "✗ No file loaded to save"
                self.save_status_time = pygame.time.get_ticks()
                return False
            
            # Show immediate feedback if requested (for manual saves)
            if show_immediate_feedback:
                self.save_status = "Saving..."
                self.save_status_time = pygame.time.get_ticks()
                self.draw()
                pygame.display.flip()
                pygame.event.pump()  # Keep responsive
            
            # Save current document to database
            doc_to_save = {
                'doc_id': self.doc_id,
                'sentences': self.doc["sentences"],
                'ner': self.doc["ner"],
                'relations': self.doc["relations"]
            }
            
            # Pass pygame.event.pump to keep window responsive
            success = self.database.save_document(doc_to_save, event_pump_callback=pygame.event.pump)
            
            if success:
                self.save_status = cfg.STATUS_SAVED
                self.save_status_time = pygame.time.get_ticks()
                return True
            else:
                self.save_status = "✗ Database save failed"
                self.save_status_time = pygame.time.get_ticks()
                return False
                
        except Exception as e:
            self.save_status = f"✗ Error: {str(e)}"
            self.save_status_time = pygame.time.get_ticks()
            print(f"Error saving: {e}")
            return False
    
    def delete_all_relations(self):
        """Delete all relations in current document"""
        if not self.doc["relations"]:
            self.status_message = "No relations to delete"
            return
        
        # Store for undo
        old_relations = [sent_rels[:] for sent_rels in self.doc["relations"]]
        
        # Clear all relations
        self.doc["relations"] = [[] for _ in self.doc["sentences"]]
        
        # Save to undo stack
        self.undo_stack.append({
            "action": "delete_all_relations",
            "relations": old_relations
        })
        self.redo_stack.clear()
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Save and re-render
        self.save_annotations()
        self.render_document()
        self.status_message = "All relations deleted"
    
    def export_to_jsonl(self):
        """Export all database documents to JSONL file"""
        try:
            if not self.database or not self.current_file_path:
                self.status_message = "No database loaded"
                return
            
            # Generate output filename
            output_path = self.current_file_path.replace('.duckdb', '_export.jsonl')
            
            self.status_message = "Exporting to JSONL..."
            count = self.database.export_to_jsonl(output_path)
            
            self.save_status = f"✓ Exported {count} documents to {os.path.basename(output_path)}"
            self.save_status_time = pygame.time.get_ticks()
            self.status_message = f"Exported to: {output_path}"
            print(f"Exported {count} documents to {output_path}")
            
        except Exception as e:
            self.status_message = f"Export failed: {str(e)}"
            print(f"Export error: {e}")
    
    def draw_progress_bar(self, progress, message):
        """Draw a progress bar overlay"""
        # Draw the main screen first
        self.draw()
        
        # Semi-transparent background
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Progress bar dimensions
        bar_width = 600
        bar_height = 40
        bar_x = (self.width - bar_width) // 2
        bar_y = (self.height - bar_height) // 2
        
        # Background
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=8)
        
        # Progress fill
        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(self.screen, (76, 175, 80), (bar_x, bar_y, fill_width, bar_height), border_radius=8)
        
        # Border
        pygame.draw.rect(self.screen, (180, 180, 180), (bar_x, bar_y, bar_width, bar_height), 2, border_radius=8)
        
        # Progress text
        progress_text = self.font.render(f"{int(progress * 100)}%", True, (255, 255, 255))
        text_rect = progress_text.get_rect(center=(self.width // 2, bar_y + bar_height // 2))
        self.screen.blit(progress_text, text_rect)
        
        # Message
        msg_surf = self.small_font.render(message, True, (255, 255, 255))
        msg_rect = msg_surf.get_rect(center=(self.width // 2, bar_y - 30))
        self.screen.blit(msg_surf, msg_rect)
        
        pygame.display.flip()
    
    def extract_and_save_entity_types(self, scan_all_docs=False):
        """Extract unique entity/relation types from documents"""
        entity_types = set()
        relation_types = set()
        
        if scan_all_docs and self.database and self.doc_ids:
            # Extract from all documents in database (on initial load)
            print("Scanning all documents for entity and relation types...")
            total_docs = len(self.doc_ids)
            
            for idx, doc_id in enumerate(self.doc_ids):
                # Update progress bar every 10 documents or on last
                if idx % 10 == 0 or idx == total_docs - 1:
                    progress = (idx + 1) / total_docs
                    self.draw_progress_bar(progress, f"Scanning document {idx + 1}/{total_docs}")
                    # Process pygame events to keep window responsive
                    pygame.event.pump()
                
                doc = self.database.get_document(doc_id)
                if doc:
                    # Extract entity types
                    for sent_entities in doc.get("ner", []):
                        for entity in sent_entities:
                            if len(entity) >= 3:
                                entity_type = normalize_type(entity[2])
                                entity_types.add(entity_type)
                    
                    # Extract relation types
                    for sent_relations in doc.get("relations", []):
                        for relation in sent_relations:
                            if len(relation) >= 5:
                                rel_type = normalize_type(relation[4])
                                relation_types.add(rel_type)
        else:
            # Extract from current document only
            doc = self.doc
            
            # Extract entity types
            for sent_entities in doc.get("ner", []):
                for entity in sent_entities:
                    if len(entity) >= 3:
                        entity_type = normalize_type(entity[2])
                        entity_types.add(entity_type)
            
            # Extract relation types
            for sent_relations in doc.get("relations", []):
                for relation in sent_relations:
                    if len(relation) >= 5:
                        rel_type = normalize_type(relation[4])
                        relation_types.add(rel_type)
        
        # Add to settings if new
        settings_updated = False
        
        for entity_type in entity_types:
            if entity_type not in self.settings["known_entities"]:
                self.settings["known_entities"].append(entity_type)
                settings_updated = True
                if entity_type not in self.entity_colors:
                    self.entity_colors[entity_type] = generate_random_color(entity_type)
        
        for relation_type in relation_types:
            if relation_type not in self.settings["known_relations"]:
                self.settings["known_relations"].append(relation_type)
                settings_updated = True
                if relation_type not in self.relation_colors:
                    self.relation_colors[relation_type] = generate_random_color(relation_type)
        
        # Update popup options after processing all types
        self.entity_popup.set_options([{"text": et, "value": et, "color": color}
                                      for et, color in self.entity_colors.items()])
        self.relation_popup.set_options([{"text": rt, "value": rt, "color": color}
                                        for rt, color in self.relation_colors.items()])
    
    # ========================================================================
    # RENDERING
    # ========================================================================
    
    def render_document(self):
        """Render the current document"""
        self.rendered_entities = []
        self.rendered_tokens = []
        self.rendered_relations = []
        self.rendered_labels = []
        self.entity_elements = {}
        
        if not self.doc or not self.doc["sentences"]:
            return
        
        line_height = self.font.get_height() + cfg.TOKEN_LINE_HEIGHT_EXTRA
        x = self.doc_container.x + 10
        y = self.doc_container.y - self.doc_scroll_y + 10
        max_line_width = self.doc_container.width - 20
        
        # Create token-to-entity mapping
        token_entity_map = {}
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3:
                    for idx in range(entity[0], entity[1] + 1):
                        token_entity_map[idx] = entity
        
        # Render all tokens
        global_idx = 0
        line_tokens = []
        line_width = 0
        
        for sent_idx, sentence in enumerate(self.doc["sentences"]):
            if sent_idx > 0:
                # Add spacing between sentences
                y += cfg.SENTENCE_SPACING
                line_tokens = []
                line_width = 0
            
            for tok_idx, token_text in enumerate(sentence):
                if not token_text:
                    global_idx += 1
                    continue
                
                token_width = self.font.size(token_text)[0] + cfg.TOKEN_PADDING
                
                # Word wrap
                if line_width + token_width > max_line_width and line_tokens:
                    y += line_height
                    x = self.doc_container.x + 10
                    line_width = 0
                    line_tokens = []
                
                token_rect = pygame.Rect(x, y, token_width, line_height)
                
                token_info = {
                    "text": token_text,
                    "sent_idx": sent_idx,
                    "tok_idx": tok_idx,
                    "global_idx": global_idx,
                    "rect": token_rect,
                    "selected": global_idx in self.selected_tokens,
                }
                
                if global_idx in token_entity_map:
                    token_info["entity"] = token_entity_map[global_idx]
                
                self.rendered_tokens.append(token_info)
                line_tokens.append(token_info)
                
                x += token_width + 2
                line_width += token_width + 2
                global_idx += 1
            
            y += line_height
            x = self.doc_container.x + 10
            line_width = 0
            line_tokens = []
        
        # Calculate document height
        total_height = y + 20 - self.doc_container.y + self.doc_scroll_y
        self.max_scroll_y = max(0, total_height - self.doc_container.height)
        
        # Render entities
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3:
                    self._render_entity(entity)
        
        # Render relations
        for sent_relations in self.doc["relations"]:
            for relation in sent_relations:
                if len(relation) >= 5:
                    self._render_relation(relation)
    
    def _render_entity(self, entity):
        """Render a single entity"""
        start_idx, end_idx, entity_type = entity[0], entity[1], entity[2]
        entity_type = normalize_type(entity_type)
        
        # Find tokens for this entity
        entity_tokens = [t for t in self.rendered_tokens 
                        if start_idx <= t["global_idx"] <= end_idx]
        
        if not entity_tokens:
            return
        
        # Group tokens by line
        lines = {}
        for t in entity_tokens:
            y_pos = t["rect"].y
            if y_pos not in lines:
                lines[y_pos] = []
            lines[y_pos].append(t)
        
        # Create rectangles for each line
        entity_rects = []
        for line_y in sorted(lines.keys()):
            line_tokens = sorted(lines[line_y], key=lambda t: t["rect"].x)
            left = line_tokens[0]["rect"].x
            top = line_tokens[0]["rect"].y
            right = line_tokens[-1]["rect"].right
            bottom = line_tokens[0]["rect"].bottom
            entity_rects.append(pygame.Rect(left, top, right - left, bottom - top))
        
        # Create entity info
        entity_key = f"{start_idx}-{end_idx}"
        entity_text = " ".join([t["text"] for t in entity_tokens])
        
        if len(entity_rects) == 1:
            entity_rect = entity_rects[0]
        else:
            entity_rect = {"multi_line": True, "rects": entity_rects}
        
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
        self.entity_elements[entity_key] = entity_info
    
    def _render_relation(self, relation):
        """Render a single relation"""
        src_start, src_end = relation[0], relation[1]
        tgt_start, tgt_end = relation[2], relation[3]
        rel_type = normalize_type(relation[4])
        
        src_key = f"{src_start}-{src_end}"
        tgt_key = f"{tgt_start}-{tgt_end}"
        
        if src_key not in self.entity_elements or tgt_key not in self.entity_elements:
            return
        
        src_entity = self.entity_elements[src_key]
        tgt_entity = self.entity_elements[tgt_key]
        
        src_center_x, src_center_y = self.get_entity_center(src_entity)
        tgt_center_x, tgt_center_y = self.get_entity_center(tgt_entity)
        
        # Calculate label position with bounds checking
        label_x = (src_center_x + tgt_center_x) // 2
        
        # Position label above the arrow arc
        # If entities are on similar vertical positions, place label above
        # Otherwise place it near the middle of the arc
        src_top = self.get_entity_top(src_entity)
        tgt_top = self.get_entity_top(tgt_entity)
        vertical_diff = abs(src_center_y - tgt_center_y)
        
        if vertical_diff < 50:
            # Entities are roughly horizontally aligned - place label above
            label_y = min(src_top, tgt_top) - 20
        else:
            # Entities are at different heights - place label at midpoint, offset upward
            label_y = min(src_center_y, tgt_center_y) + (abs(src_center_y - tgt_center_y) // 4) - 30
        
        # Keep label within document container bounds
        label_margin = 30
        if label_y < self.doc_container.y + label_margin:
            label_y = min(src_center_y, tgt_center_y) + 20  # Place below if too high
        if label_y > self.doc_container.bottom - label_margin:
            label_y = self.doc_container.bottom - label_margin
        
        # Keep horizontal position within bounds
        if label_x < self.doc_container.x + label_margin:
            label_x = self.doc_container.x + label_margin
        if label_x > self.doc_container.right - label_margin:
            label_x = self.doc_container.right - label_margin
        
        relation_info = {
            "source": src_entity,
            "target": tgt_entity,
            "type": rel_type,
            "color": self.relation_colors.get(rel_type, (120, 120, 120)),
            "src_center_x": src_center_x,
            "src_center_y": src_center_y,
            "tgt_center_x": tgt_center_x,
            "tgt_center_y": tgt_center_y,
            "label_x": label_x,
            "label_y": label_y
        }
        
        self.rendered_relations.append(relation_info)
    
    def draw(self):
        """Draw the application with modern styling"""
        # Main background
        self.screen.fill(cfg.COLOR_BG_MAIN)
        
        # Toolbar background
        toolbar_rect = pygame.Rect(0, 0, self.width, cfg.TOOLBAR_HEIGHT)
        pygame.draw.rect(self.screen, cfg.COLOR_BG_TOOLBAR, toolbar_rect)
        
        # Subtle shadow under toolbar
        pygame.draw.line(self.screen, cfg.COLOR_BORDER_LIGHT, 
                        (0, cfg.TOOLBAR_HEIGHT), (self.width, cfg.TOOLBAR_HEIGHT), 2)
        
        # Status message with secondary text color (no title, just status)
        status_surf = self.small_font.render(self.status_message[:120], True, cfg.COLOR_TEXT_SECONDARY)
        self.screen.blit(status_surf, (cfg.TOOLBAR_PADDING, cfg.TOOLBAR_PADDING))
        
        # Draw buttons
        self.undo_button.draw(self.screen)
        self.redo_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.open_file_button.draw(self.screen)
        self.add_entity_type_button.draw(self.screen)
        self.add_relation_type_button.draw(self.screen)
        self.prev_doc_button.draw(self.screen)
        self.next_doc_button.draw(self.screen)
        self.export_button.draw(self.screen)
        
        # Navigation bar
        total_docs = len(self.doc_ids)
        if total_docs > 0:
            self.navigation_bar.draw(self.screen, self.current_doc_index, total_docs)
        
        # Save status with modern styling
        current_time = pygame.time.get_ticks()
        if self.save_status and current_time - self.save_status_time < cfg.SHOW_SAVE_NOTIFICATION_DURATION:
            # Determine color based on status
            if "✓" in self.save_status or "success" in self.save_status.lower():
                status_color = cfg.COLOR_SUCCESS
            elif "✗" in self.save_status or "error" in self.save_status.lower():
                status_color = cfg.COLOR_DANGER
            else:
                status_color = cfg.COLOR_INFO
            
            save_surf = self.small_font.render(self.save_status, True, status_color)
            # Position in top-right
            self.screen.blit(save_surf, (self.width - save_surf.get_width() - cfg.TOOLBAR_PADDING, 
                                        cfg.TOOLBAR_PADDING))
        
        # Document container with modern styling
        pygame.draw.rect(self.screen, cfg.COLOR_BG_DOCUMENT, self.doc_container, border_radius=8)
        pygame.draw.rect(self.screen, cfg.COLOR_BORDER_LIGHT, self.doc_container, 1, border_radius=8)
        
        # Draw document content
        original_clip = self.screen.get_clip()
        self.screen.set_clip(self.doc_container)
        self.draw_document_content()
        self.screen.set_clip(original_clip)
        
        # Modern scrollbar
        if self.max_scroll_y > 0:
            scrollbar_height = max(40, min(self.doc_container.height,
                self.doc_container.height * self.doc_container.height / 
                (self.doc_container.height + self.max_scroll_y)))
            scrollbar_pos = self.doc_container.y + (self.doc_container.height - scrollbar_height) * \
                           (self.doc_scroll_y / self.max_scroll_y)
            
            # Scrollbar track (background)
            track_rect = pygame.Rect(self.doc_container.right - 12, self.doc_container.y,
                                    8, self.doc_container.height)
            pygame.draw.rect(self.screen, cfg.COLOR_BORDER_LIGHT, track_rect, border_radius=4)
            
            # Scrollbar thumb
            scrollbar_rect = pygame.Rect(self.doc_container.right - 12, scrollbar_pos, 
                                        8, scrollbar_height)
            pygame.draw.rect(self.screen, cfg.COLOR_SCROLLBAR, scrollbar_rect, border_radius=4)
        
        # Popups and dialogs
        self.entity_popup.draw(self.screen)
        self.relation_popup.draw(self.screen)
        
        if self.input_dialog.visible:
            self.input_dialog.draw(self.screen)
        
        if self.file_browser.visible:
            self.file_browser.draw(self.screen)
        
        self.shortcut_help.draw(self.screen)
        
        pygame.display.flip()
    
    def draw_document_content(self):
        """Draw document tokens, entities, and relations - OPTIMIZED"""
        # Calculate visible range for virtual scrolling
        if cfg.ENABLE_VIRTUAL_SCROLLING:
            visible_top = self.doc_container.y - cfg.VIEWPORT_BUFFER
            visible_bottom = self.doc_container.bottom + cfg.VIEWPORT_BUFFER
            
            # Filter to only visible tokens (HUGE performance boost)
            visible_tokens = [t for t in self.rendered_tokens 
                            if visible_top <= t["rect"].y <= visible_bottom]
        else:
            visible_tokens = self.rendered_tokens
        
        # Draw only visible tokens
        for token in visible_tokens:
            if self.doc_container.y <= token["rect"].y < self.doc_container.bottom:
                text_surf = self.font.render(token["text"], True, (0, 0, 0))
                self.screen.blit(text_surf, token["rect"])
                
                if token["selected"]:
                    highlight = pygame.Surface((token["rect"].width, token["rect"].height), 
                                              pygame.SRCALPHA)
                    pygame.draw.rect(highlight, (255, 255, 0, 100), 
                                   (0, 0, token["rect"].width, token["rect"].height),
                                   border_radius=3)
                    self.screen.blit(highlight, token["rect"])
        
        # Draw entities (only visible ones)
        if cfg.ENABLE_VIRTUAL_SCROLLING:
            visible_entities = []
            for entity in self.rendered_entities:
                # Check if entity is in visible range
                entity_rects = [entity["rect"]] if isinstance(entity["rect"], pygame.Rect) else entity["rect"]["rects"]
                for rect in (entity_rects if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line") else [entity["rect"]]):
                    if visible_top <= rect.y <= visible_bottom:
                        visible_entities.append(entity)
                        break
        else:
            visible_entities = self.rendered_entities
        
        for entity in visible_entities:
            self.draw_entity_background(entity)
        
        # Draw relations (only for hovered entity)
        if self.hovered_entity_key:
            # Draw relations connected to the hovered entity
            for relation in self.rendered_relations:
                src_key = f"{relation['source']['start']}-{relation['source']['end']}"
                tgt_key = f"{relation['target']['start']}-{relation['target']['end']}"
                
                if src_key == self.hovered_entity_key or tgt_key == self.hovered_entity_key:
                    # Draw arrow
                    self.draw_relation_arrow(relation)
                    
                    # Draw label with the relation
                    label_info = {
                        "text": relation["type"],
                        "x": relation["label_x"],
                        "y": relation["label_y"],
                        "color": relation["color"]
                    }
                    self.draw_relation_label(label_info)
        
        # Draw temp relation line
        if self.dragging_relation and self.temp_line:
            points = self.calculate_bezier_points([
                (self.temp_line["src_x"], self.temp_line["src_y"]),
                (self.temp_line["src_x"] + (self.temp_line["tgt_x"] - self.temp_line["src_x"]) * 0.25,
                 self.temp_line["src_y"] - 50),
                (self.temp_line["src_x"] + (self.temp_line["tgt_x"] - self.temp_line["src_x"]) * 0.75,
                 self.temp_line["tgt_y"] - 50),
                (self.temp_line["tgt_x"], self.temp_line["tgt_y"])
            ], 20)
            pygame.draw.aalines(self.screen, (120, 120, 120), False, points, 2)
        
        # Draw entity labels
        for entity_key, label_info in self.selected_entity_labels.items():
            if entity_key in self.entity_elements:
                entity = self.entity_elements[entity_key]
                label_x, label_y = label_info["pos"]
                
                text_surf = self.small_font.render(label_info["type"], True, label_info["color"])
                text_rect = text_surf.get_rect(center=(label_x, label_y))
                
                bg_rect = text_rect.copy()
                bg_rect.inflate_ip(10, 6)
                
                pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=3)
                pygame.draw.rect(self.screen, label_info["color"], bg_rect, 1, border_radius=3)
                self.screen.blit(text_surf, text_rect)
    
    def draw_entity_background(self, entity_info):
        """Draw entity background rectangle with enhanced hover effects"""
        entity_type = normalize_type(entity_info["type"])
        bg_color = self.entity_colors.get(entity_type, cfg.COLOR_SECONDARY)
        
        # Adjust opacity based on state
        if entity_info["hovered"]:
            bg_alpha = 160  # More opaque on hover
        elif entity_info["selected"]:
            bg_alpha = 140  # Medium opacity for selected
        else:
            bg_alpha = 100  # Light opacity for normal
        
        bg_color_alpha = (*bg_color[:3], bg_alpha)
        
        # Get all rectangles (handle multi-line entities)
        rects = [entity_info["rect"]] if isinstance(entity_info["rect"], pygame.Rect) else entity_info["rect"]["rects"]
        
        for rect in (rects if isinstance(entity_info["rect"], dict) and entity_info["rect"].get("multi_line") else [entity_info["rect"]]):
            # Draw background with alpha
            entity_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(entity_surface, bg_color_alpha, 
                           (0, 0, rect.width, rect.height), 
                           border_radius=cfg.ENTITY_BORDER_RADIUS)
            self.screen.blit(entity_surface, rect)
            
            # Draw border - slightly thicker on hover/selection
            if entity_info["hovered"] or entity_info["selected"]:
                border_width = 2
                border_color = bg_color  # Full color for border
            else:
                border_width = 1
                border_color = bg_color  # Full color always
            
            pygame.draw.rect(self.screen, border_color, rect, border_width, 
                           border_radius=cfg.ENTITY_BORDER_RADIUS)
    
    def draw_relation_arrow(self, relation):
        """Draw relation arrow with smart curve adjustment"""
        src_x, src_y = relation["src_center_x"], relation["src_center_y"]
        tgt_x, tgt_y = relation["tgt_center_x"], relation["tgt_center_y"]
        
        distance = math.sqrt((tgt_x - src_x)**2 + (tgt_y - src_y)**2)
        height_factor = min(100, distance / 4)
        
        # Check if we're near the top of the container
        min_y = min(src_y, tgt_y)
        max_y = max(src_y, tgt_y)
        near_top = min_y - height_factor < self.doc_container.y + 30
        near_bottom = max_y + height_factor > self.doc_container.bottom - 30
        
        if abs(tgt_y - src_y) < 50:
            ctrl_x1 = src_x + (tgt_x - src_x) * 0.25
            ctrl_x2 = src_x + (tgt_x - src_x) * 0.75
            
            # Adjust curve direction based on space available
            if near_top and not near_bottom:
                # Curve downward instead
                ctrl_y1 = src_y + height_factor * 0.5
                ctrl_y2 = tgt_y + height_factor * 0.5
            elif near_bottom and not near_top:
                # Curve upward (more)
                ctrl_y1 = src_y - height_factor * 1.2
                ctrl_y2 = tgt_y - height_factor * 1.2
            else:
                # Normal upward curve
                ctrl_y1 = src_y - height_factor
                ctrl_y2 = tgt_y - height_factor
        else:
            ctrl_x1 = src_x + (tgt_x - src_x) * 0.25
            ctrl_y1 = src_y + (tgt_y - src_y) * 0.25
            ctrl_x2 = src_x + (tgt_x - src_x) * 0.75
            ctrl_y2 = src_y + (tgt_y - src_y) * 0.75
        
        curve_points = self.calculate_bezier_points([
            (src_x, src_y), (ctrl_x1, ctrl_y1), (ctrl_x2, ctrl_y2), (tgt_x, tgt_y)
        ], 30)
        
        pygame.draw.aalines(self.screen, relation["color"], False, curve_points, 2)
        
        # Arrow head
        if len(curve_points) >= 2:
            p2 = curve_points[-1]
            p1 = curve_points[-2]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                dx /= length
                dy /= length
            
            arrow_size = 10
            px = -dy
            py = dx
            
            a1 = (p2[0] - arrow_size*dx + arrow_size*0.5*px, 
                  p2[1] - arrow_size*dy + arrow_size*0.5*py)
            a2 = (p2[0] - arrow_size*dx - arrow_size*0.5*px, 
                  p2[1] - arrow_size*dy - arrow_size*0.5*py)
            
            pygame.draw.polygon(self.screen, relation["color"], [p2, a1, a2])
    
    def draw_relation_label(self, label):
        """Draw relation label with bounds clamping"""
        # Clamp label position to visible area
        label_x = max(self.doc_container.x + 40, 
                     min(label["x"], self.doc_container.right - 40))
        label_y = max(self.doc_container.y + 20, 
                     min(label["y"], self.doc_container.bottom - 20))
        
        # Check if label is within extended visible area
        padding = 50
        if (self.doc_container.y - padding <= label_y <= self.doc_container.bottom + padding and
            self.doc_container.x - padding <= label_x <= self.doc_container.right + padding):
            
            text_surf = self.small_font.render(label["text"], True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=(label_x, label_y))
            
            bg_rect = text_rect.copy()
            bg_rect.inflate_ip(8, 6)
            
            # Draw white background with border
            pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, border_radius=3)
            pygame.draw.rect(self.screen, label["color"], bg_rect, 2, border_radius=3)
            
            # Draw text
            self.screen.blit(text_surf, text_rect)
    
    def calculate_bezier_points(self, points, num_points=20):
        """Calculate Bezier curve points"""
        def bezier(t, p0, p1, p2, p3):
            return (
                (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 
                3*(1-t)*t**2 * p2 + t**3 * p3
            )
        
        result = []
        p0, p1, p2, p3 = points
        
        for i in range(num_points):
            t = i / (num_points - 1)
            x = bezier(t, p0[0], p1[0], p2[0], p3[0])
            y = bezier(t, p0[1], p1[1], p2[1], p3[1])
            result.append((x, y))
        
        return result
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_entity_center(self, entity):
        """Get entity center point"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            rects = entity["rect"]["rects"]
            total_x = sum(r.centerx for r in rects)
            total_y = sum(r.centery for r in rects)
            return total_x // len(rects), total_y // len(rects)
        return entity["rect"].centerx, entity["rect"].centery
    
    def get_entity_top(self, entity):
        """Get entity top edge"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            return min(r.top for r in entity["rect"]["rects"])
        return entity["rect"].top
    
    def get_entity_bottom(self, entity):
        """Get entity bottom edge"""
        if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
            return max(r.bottom for r in entity["rect"]["rects"])
        return entity["rect"].bottom
    
    def check_token_hover(self, pos):
        """Check if mouse is hovering over a token"""
        for token in self.rendered_tokens:
            if token["rect"].collidepoint(pos):
                return token
        return None
    
    def check_entity_hover(self, pos):
        """Check if mouse is hovering over an entity"""
        for entity in self.rendered_entities:
            if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                for rect in entity["rect"]["rects"]:
                    if rect.collidepoint(pos):
                        return entity
            elif entity["rect"].collidepoint(pos):
                return entity
        return None
    
    def get_token_info(self, global_idx):
        """Get sentence and token index from global token index"""
        total_tokens = 0
        for sent_idx, sentence in enumerate(self.doc["sentences"]):
            if global_idx >= total_tokens and global_idx < total_tokens + len(sentence):
                tok_idx = global_idx - total_tokens
                return {"sent_idx": sent_idx, "tok_idx": tok_idx}
            total_tokens += len(sentence)
        return None
    
    # ========================================================================
    # EVENT HANDLING
    # ========================================================================
    
    def handle_events(self):
        """Main event loop"""
        keys = pygame.key.get_pressed()
        self.e_key_held = keys[pygame.K_e]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Quick cleanup - no need to save (auto-saved after each change)
                try:
                    if self.database:
                        self.database.close()
                except Exception as e:
                    print(f"Error closing database: {e}")
                
                return False
            
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.doc_container = pygame.Rect(10, 160, self.width - 20, self.height - 170)
                self.navigation_bar.rect.width = self.width - 20
                self.render_document()
            
            elif event.type == pygame.DROPFILE:
                # Drag and drop file support
                dropped_file = event.file
                if dropped_file.endswith('.jsonl') or dropped_file.endswith('.json'):
                    self.load_file(dropped_file)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_up(event)
            
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event)
            
            elif event.type == pygame.KEYDOWN:
                self.handle_key_down(event)
        
        return True
    
    def handle_mouse_down(self, event):
        """Handle mouse button down events"""
        pos = pygame.mouse.get_pos()
        
        # Handle file browser
        if self.file_browser.visible:
            if event.button in (4, 5):  # Scroll
                scroll_dir = 1 if event.button == 4 else -1
                screen_offset = ((self.width - self.file_browser.width) // 2,
                               (self.height - self.file_browser.height) // 2)
                self.file_browser.handle_scroll(scroll_dir, screen_offset)
            elif event.button == 1:  # Left click
                screen_offset = ((self.width - self.file_browser.width) // 2,
                               (self.height - self.file_browser.height) // 2)
                result = self.file_browser.handle_click(pos, screen_offset)
                if result == "cancel":
                    self.file_browser.hide()
                elif result and result != "cancel":
                    self.load_file(result)
                    self.file_browser.hide()
            return
        
        # Handle scroll wheel
        if event.button in (4, 5):
            scroll_dir = 1 if event.button == 4 else -1
            
            if self.entity_popup.visible and self.entity_popup.rect.collidepoint(pos):
                self.entity_popup.handle_scroll(scroll_dir)
            elif self.relation_popup.visible and self.relation_popup.rect.collidepoint(pos):
                self.relation_popup.handle_scroll(scroll_dir)
            elif self.doc_container.collidepoint(pos):
                # Scrolling (works with virtual scrolling for performance)
                if cfg.ENABLE_SMOOTH_SCROLLING:
                    self.target_scroll_y = max(0, min(self.max_scroll_y, 
                                         self.target_scroll_y - scroll_dir * cfg.SCROLL_SPEED))
                else:
                    self.doc_scroll_y = max(0, min(self.max_scroll_y, 
                                         self.doc_scroll_y - scroll_dir * cfg.SCROLL_SPEED))
                    self.render_document()  # Re-render with new scroll position
            return
        
        # Handle button clicks
        if self.undo_button.click(pos) and not self.undo_button.is_disabled:
            self.undo()
        elif self.redo_button.click(pos) and not self.redo_button.is_disabled:
            self.redo()
        elif self.save_button.click(pos):
            self.save_annotations(show_immediate_feedback=True)
        elif self.open_file_button.click(pos):
            self.file_browser.show(self.current_file_path if self.current_file_path else None)
        elif self.prev_doc_button.click(pos) and not self.prev_doc_button.is_disabled:
            self.load_document(self.current_doc_index - 1)
        elif self.next_doc_button.click(pos) and not self.next_doc_button.is_disabled:
            self.load_document(self.current_doc_index + 1)
        elif self.export_button.click(pos):
            self.export_to_jsonl()
        elif self.add_entity_type_button.click(pos):
            self.input_dialog.title = "Add New Entity Type"
            self.input_dialog.show(self.width // 2 - 175, self.height // 2 - 90)
        elif self.add_relation_type_button.click(pos):
            self.input_dialog.title = "Add New Relation Type"
            self.input_dialog.show(self.width // 2 - 175, self.height // 2 - 90)
        
        # Navigation bar
        elif self.navigation_bar.rect.collidepoint(pos):
            self.navigation_bar.handle_click(pos)
        
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
        
        # Document content clicks
        elif self.doc_container.collidepoint(pos):
            if event.button == 3:  # Right click
                entity = self.check_entity_hover(pos)
                if entity:
                    self.start_dragging_relation(entity)
            elif event.button == 1:  # Left click
                entity = self.check_entity_hover(pos)
                if entity:
                    self.handle_entity_click(entity)
                else:
                    token = self.check_token_hover(pos)
                    if token:
                        self.handle_token_click(token)
    
    def handle_mouse_up(self, event):
        """Handle mouse button up events"""
        pos = pygame.mouse.get_pos()
        
        # Finalize token selection
        if self.is_selecting and self.selected_tokens:
            start_idx = min(self.selected_tokens)
            for token in self.rendered_tokens:
                if token["global_idx"] == start_idx:
                    self.entity_popup.show(token["rect"].x, token["rect"].y + token["rect"].height + 10)
                    break
            self.is_selecting = False
        
        # Handle end of relation dragging
        if self.dragging_relation:
            target_entity = self.check_entity_hover(pos)
            
            if target_entity and f"{target_entity['start']}-{target_entity['end']}" != self.drag_source_key:
                self.relation_source_entity = self.drag_source_entity
                self.relation_target_entity = [
                    target_entity["start"], 
                    target_entity["end"], 
                    target_entity["type"]
                ]
                self.relation_popup.show(pos[0], pos[1])
            
            self.dragging_relation = False
            self.drag_source_entity = None
            self.drag_source_key = None
            self.temp_line = None
    
    def handle_mouse_motion(self, event):
        """Handle mouse motion events"""
        pos = pygame.mouse.get_pos()
        self.mouse_x, self.mouse_y = pos
        
        # Handle file browser hover
        if self.file_browser.visible:
            screen_offset = ((self.width - self.file_browser.width) // 2,
                           (self.height - self.file_browser.height) // 2)
            self.file_browser.handle_hover(pos, screen_offset)
            return
        
        # Update button hover states
        self.undo_button.check_hover(pos)
        self.redo_button.check_hover(pos)
        self.save_button.check_hover(pos)
        self.open_file_button.check_hover(pos)
        self.prev_doc_button.check_hover(pos)
        self.next_doc_button.check_hover(pos)
        self.add_entity_type_button.check_hover(pos)
        self.add_relation_type_button.check_hover(pos)
        self.export_button.check_hover(pos)
        
        # Handle token selection
        if self.is_selecting and self.selection_start_token:
            token = self.check_token_hover(pos)
            if token:
                start_idx = min(self.selection_start_token["global_idx"], token["global_idx"])
                end_idx = max(self.selection_start_token["global_idx"], token["global_idx"])
                self.selected_tokens = list(range(start_idx, end_idx + 1))
                self.render_document()
        
        # Update entity hover states
        hovered_entity_found = False
        for entity in self.rendered_entities:
            was_hovered = entity["hovered"]
            
            is_hovered = False
            if isinstance(entity["rect"], dict) and entity["rect"].get("multi_line"):
                for rect in entity["rect"]["rects"]:
                    if rect.collidepoint(pos):
                        is_hovered = True
                        break
            else:
                is_hovered = entity["rect"].collidepoint(pos)
            
            entity["hovered"] = is_hovered
            
            if entity["hovered"]:
                self.hovered_entity_key = f"{entity['start']}-{entity['end']}"
                hovered_entity_found = True
        
        # Clear hover state if no entity is hovered
        if not hovered_entity_found:
            self.hovered_entity_key = None
        
        # Update relation drag line
        if self.dragging_relation and self.temp_line:
            self.temp_line["tgt_x"] = pos[0]
            self.temp_line["tgt_y"] = pos[1]
    
    def handle_key_down(self, event):
        """Handle keyboard events"""
        # File browser active
        if self.file_browser.visible:
            return
        
        # Shortcut help
        if event.key == pygame.K_F1 or (event.key == pygame.K_SLASH and 
                                       pygame.key.get_mods() & pygame.KMOD_SHIFT):
            self.shortcut_help.toggle()
            return
        
        # Close overlays
        if event.key == pygame.K_ESCAPE:
            if self.shortcut_help.visible:
                self.shortcut_help.visible = False
            elif self.input_dialog.visible:
                self.input_dialog.hide()
            return
        
        # Navigation bar input
        if self.navigation_bar.jump_active:
            total_docs = len(self.doc_ids)
            result = self.navigation_bar.handle_key(event, total_docs)
            if result is not None:
                self.load_document(result)
            return
        
        # Input dialog
        if self.input_dialog.visible:
            result = self.input_dialog.handle_key(event)
            if result == "save":
                if self.input_dialog.title == "Add New Entity Type":
                    self.add_custom_entity_type(self.input_dialog.text_input.strip())
                else:
                    self.add_custom_relation_type(self.input_dialog.text_input.strip())
                self.input_dialog.hide()
            elif result == "cancel":
                self.input_dialog.hide()
            return
        
        # Keyboard shortcuts
        mods = pygame.key.get_mods()
        
        # Ctrl+O - Open file
        if event.key == pygame.K_o and mods & pygame.KMOD_CTRL:
            self.file_browser.show(self.current_file_path if self.current_file_path else None)
        
        # Ctrl+S - Save
        elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
            self.save_annotations()
        
        # Ctrl+Z - Undo
        elif event.key == pygame.K_z and mods & pygame.KMOD_CTRL:
            if not self.undo_button.is_disabled:
                self.undo()
        
        # Ctrl+Y - Redo
        elif event.key == pygame.K_y and mods & pygame.KMOD_CTRL:
            if not self.redo_button.is_disabled:
                self.redo()
        
        # Ctrl+G - Go to document
        elif event.key == pygame.K_g and mods & pygame.KMOD_CTRL:
            self.navigation_bar.jump_active = True
            self.navigation_bar.jump_input = ""
        
        # Arrow keys - Navigate documents
        elif event.key == pygame.K_LEFT:
            total_docs = len(self.doc_ids)
            if mods & pygame.KMOD_CTRL:
                new_idx = max(0, self.current_doc_index - 10)
                self.load_document(new_idx)
            else:
                if not self.prev_doc_button.is_disabled:
                    self.load_document(self.current_doc_index - 1)
        
        elif event.key == pygame.K_RIGHT:
            total_docs = len(self.doc_ids)
            if mods & pygame.KMOD_CTRL:
                new_idx = min(total_docs - 1, self.current_doc_index + 10)
                self.load_document(new_idx)
            else:
                if not self.next_doc_button.is_disabled:
                    self.load_document(self.current_doc_index + 1)
        
        # Home/End - First/Last document
        elif event.key == pygame.K_HOME:
            self.load_document(0)
        
        elif event.key == pygame.K_END:
            total_docs = len(self.doc_ids)
            self.load_document(total_docs - 1)
        
        # Page Up/Down - Scroll
        elif event.key == pygame.K_PAGEUP:
            if cfg.ENABLE_SMOOTH_SCROLLING:
                self.target_scroll_y = max(0, self.target_scroll_y - 150)
            else:
                self.doc_scroll_y = max(0, self.doc_scroll_y - 150)
                self.render_document()
        
        elif event.key == pygame.K_PAGEDOWN:
            if cfg.ENABLE_SMOOTH_SCROLLING:
                self.target_scroll_y = min(self.max_scroll_y, self.target_scroll_y + 150)
            else:
                self.doc_scroll_y = min(self.max_scroll_y, self.doc_scroll_y + 150)
                self.render_document()
        
        # D - Delete
        elif event.key == pygame.K_d:
            if self.selected_entities:
                self.delete_selected_entity()
            elif self.selected_tokens:
                self.delete_selected_tokens()
    
    # ========================================================================
    # ANNOTATION ACTIONS
    # ========================================================================
    
    def handle_token_click(self, token):
        """Handle click on a token"""
        self.is_selecting = True
        self.selection_start_token = token
        self.selected_tokens = [token["global_idx"]]
        self.selected_entities = []
        self.status_message = "Selecting tokens..."
        self.render_document()
    
    def handle_entity_click(self, entity):
        """Handle click on an entity"""
        entity_key = f"{entity['start']}-{entity['end']}"
        
        # Clear previous selections
        self.selected_tokens = []
        self.selected_entity_labels = {}
        
        # Toggle selection
        if entity_key in self.selected_entities:
            self.selected_entities.remove(entity_key)
            self.status_message = "Entity deselected"
        else:
            self.selected_entities = [entity_key]
            
            entity_type = normalize_type(entity["type"])
            center_x, center_y = self.get_entity_center(entity)
            
            self.selected_entity_labels[entity_key] = {
                "type": entity_type,
                "pos": (center_x, self.get_entity_top(entity) - 20),
                "color": self.entity_colors.get(entity_type, (200, 200, 200))
            }
            
            self.status_message = f"Selected {entity_type} entity"
        
        # Update rendered entities
        for rendered_entity in self.rendered_entities:
            rendered_entity["selected"] = False
            if f"{rendered_entity['start']}-{rendered_entity['end']}" in self.selected_entities:
                rendered_entity["selected"] = True
        
        self.render_document()
    
    def start_dragging_relation(self, entity):
        """Start dragging a relation from an entity"""
        self.dragging_relation = True
        self.drag_source_entity = [entity["start"], entity["end"], entity["type"]]
        self.drag_source_key = f"{entity['start']}-{entity['end']}"
        
        center_x, center_y = self.get_entity_center(entity)
        self.temp_line = {
            "src_x": center_x,
            "src_y": center_y,
            "tgt_x": self.mouse_x,
            "tgt_y": self.mouse_y
        }
        
        self.status_message = f"Dragging relation from {normalize_type(entity['type'])}"
    
    def create_new_entity(self):
        """Create a new entity from selected tokens"""
        if not self.selected_tokens or not self.selected_entity_type:
            return
        
        start_idx = min(self.selected_tokens)
        end_idx = max(self.selected_tokens)
        
        # Check if entity already exists
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3 and entity[0] == start_idx and entity[1] == end_idx:
                    entity[2] = self.selected_entity_type
                    self.render_document()
                    return
        
        # Add new entity
        while len(self.doc["ner"]) < len(self.doc["sentences"]):
            self.doc["ner"].append([])
        
        self.doc["ner"][0].append([start_idx, end_idx, self.selected_entity_type])
        
        # Add to undo stack
        self.undo_stack.append({
            "action": "add_entity",
            "entity": [start_idx, end_idx, self.selected_entity_type]
        })
        self.redo_stack.clear()
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Reset state
        self.selected_tokens = []
        self.selected_entity_type = None
        self.status_message = f"Created entity"
        
        self.render_document()
    
    def create_new_relation(self):
        """Create a new relation between entities"""
        if not self.relation_source_entity or not self.relation_target_entity or not self.selected_relation_type:
            return
        
        src_start, src_end = self.relation_source_entity[0], self.relation_source_entity[1]
        tgt_start, tgt_end = self.relation_target_entity[0], self.relation_target_entity[1]
        
        # Check if relation already exists
        for sent_relations in self.doc["relations"]:
            for relation in sent_relations:
                if (relation[0] == src_start and relation[1] == src_end and
                    relation[2] == tgt_start and relation[3] == tgt_end):
                    relation[4] = self.selected_relation_type
                    self.render_document()
                    return
        
        # Add new relation
        while len(self.doc["relations"]) < len(self.doc["sentences"]):
            self.doc["relations"].append([])
        
        self.doc["relations"][0].append([src_start, src_end, tgt_start, tgt_end, self.selected_relation_type])
        
        # Add to undo stack
        self.undo_stack.append({
            "action": "add_relation",
            "relation": [src_start, src_end, tgt_start, tgt_end, self.selected_relation_type]
        })
        self.redo_stack.clear()
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Reset state
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        self.status_message = "Created relation"
        
        self.render_document()
    
    def delete_selected_entity(self):
        """Delete the selected entity and its relations"""
        if not self.selected_entities:
            return
        
        entity_key = self.selected_entities[0]
        start_idx, end_idx = map(int, entity_key.split('-'))
        
        # Find entity type
        entity_type = None
        for sent_entities in self.doc["ner"]:
            for entity in sent_entities:
                if len(entity) >= 3 and entity[0] == start_idx and entity[1] == end_idx:
                    entity_type = entity[2]
                    break
            if entity_type:
                break
        
        if not entity_type:
            return
        
        # Remove relations
        removed_relations = []
        for sent_relations in self.doc["relations"]:
            to_remove = []
            for i, relation in enumerate(sent_relations):
                if ((relation[0] == start_idx and relation[1] == end_idx) or
                    (relation[2] == start_idx and relation[3] == end_idx)):
                    removed_relations.append(relation.copy())
                    to_remove.append(i)
            
            for i in sorted(to_remove, reverse=True):
                sent_relations.pop(i)
        
        # Remove entity
        for sent_entities in self.doc["ner"]:
            for i, entity in enumerate(sent_entities):
                if entity[0] == start_idx and entity[1] == end_idx:
                    sent_entities.pop(i)
                    break
        
        # Add to undo stack
        self.undo_stack.append({
            "action": "delete_entity",
            "entity": [start_idx, end_idx, entity_type],
            "relations": removed_relations
        })
        self.redo_stack.clear()
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = True
        
        # Clear selection
        self.selected_entities = []
        if entity_key in self.selected_entity_labels:
            del self.selected_entity_labels[entity_key]
        
        self.status_message = "Deleted entity"
        self.render_document()
    
    def delete_selected_tokens(self):
        """Delete selected tokens (placeholder - complex operation)"""
        # This is a complex operation that requires reindexing
        # For now, just clear selection
        self.selected_tokens = []
        self.status_message = "Token deletion not yet implemented"
        self.render_document()
    
    def add_custom_entity_type(self, entity_type):
        """Add a custom entity type"""
        if not entity_type or entity_type in self.entity_colors:
            return False
        
        color = generate_random_color(entity_type)
        self.entity_colors[entity_type] = color
        
        if entity_type not in self.settings["known_entities"]:
            self.settings["known_entities"].append(entity_type)
        if entity_type not in self.settings["custom_entities"]:
            self.settings["custom_entities"].append(entity_type)
        
        self.entity_popup.options.append({
            "text": entity_type,
            "value": entity_type,
            "color": color
        })
        
        self.status_message = f"Added entity type: {entity_type}"
        return True
    
    def add_custom_relation_type(self, relation_type):
        """Add a custom relation type"""
        if not relation_type or relation_type in self.relation_colors:
            return False
        
        color = generate_random_color(relation_type)
        self.relation_colors[relation_type] = color
        
        if relation_type not in self.settings["known_relations"]:
            self.settings["known_relations"].append(relation_type)
        if relation_type not in self.settings["custom_relations"]:
            self.settings["custom_relations"].append(relation_type)
        
        self.relation_popup.options.append({
            "text": relation_type,
            "value": relation_type,
            "color": color
        })
        
        self.status_message = f"Added relation type: {relation_type}"
        return True
    
    def reset_relation_creation(self):
        """Reset relation creation state"""
        self.relation_source_entity = None
        self.relation_target_entity = None
        self.selected_relation_type = None
        self.status_message = "Relation creation cancelled"
    
    # ========================================================================
    # UNDO/REDO
    # ========================================================================
    
    def undo(self):
        """Undo last action"""
        if not self.undo_stack:
            return
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        self.redo_button.is_disabled = False
        self.undo_button.is_disabled = len(self.undo_stack) == 0
        
        if action["action"] == "add_entity":
            entity = action["entity"]
            for sent_entities in self.doc["ner"]:
                for i, e in enumerate(sent_entities):
                    if e[0] == entity[0] and e[1] == entity[1]:
                        sent_entities.pop(i)
                        break
        
        elif action["action"] == "add_relation":
            relation = action["relation"]
            for sent_relations in self.doc["relations"]:
                for i, r in enumerate(sent_relations):
                    if (r[0] == relation[0] and r[1] == relation[1] and
                        r[2] == relation[2] and r[3] == relation[3]):
                        sent_relations.pop(i)
                        break
        
        elif action["action"] == "delete_entity":
            entity = action["entity"]
            while len(self.doc["ner"]) < len(self.doc["sentences"]):
                self.doc["ner"].append([])
            self.doc["ner"][0].append(entity)
            
            for relation in action["relations"]:
                while len(self.doc["relations"]) < len(self.doc["sentences"]):
                    self.doc["relations"].append([])
                self.doc["relations"][0].append(relation)
        
        self.render_document()
        self.status_message = "Undone"
    
    def redo(self):
        """Redo last undone action"""
        if not self.redo_stack:
            return
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        self.undo_button.is_disabled = False
        self.redo_button.is_disabled = len(self.redo_stack) == 0
        
        if action["action"] == "add_entity":
            entity = action["entity"]
            while len(self.doc["ner"]) < len(self.doc["sentences"]):
                self.doc["ner"].append([])
            self.doc["ner"][0].append(entity)
        
        elif action["action"] == "add_relation":
            relation = action["relation"]
            while len(self.doc["relations"]) < len(self.doc["sentences"]):
                self.doc["relations"].append([])
            self.doc["relations"][0].append(relation)
        
        elif action["action"] == "delete_entity":
            entity = action["entity"]
            for sent_entities in self.doc["ner"]:
                for i, e in enumerate(sent_entities):
                    if e[0] == entity[0] and e[1] == entity[1]:
                        sent_entities.pop(i)
                        break
            
            for relation in action["relations"]:
                for sent_relations in self.doc["relations"]:
                    for i, r in enumerate(sent_relations):
                        if (r[0] == relation[0] and r[1] == relation[1] and
                            r[2] == relation[2] and r[3] == relation[3]):
                            sent_relations.pop(i)
                            break
        
        self.render_document()
        self.status_message = "Redone"
    
    # ========================================================================
    # MAIN LOOP
    # ========================================================================
    
    def run(self):
        """Main application loop with smooth animations"""
        running = True
        first_frame = True
        
        while running:
            running = self.handle_events()
            
            # Load deferred file after first frame (prevents startup freeze)
            if first_frame:
                first_frame = False
                self.draw()  # Render empty window first
                pygame.display.flip()
                
                if self.pending_file_load:
                    try:
                        self.load_file(self.pending_file_load)
                    except Exception as e:
                        print(f"Error loading initial file: {e}")
                        self.status_message = f"Error loading file: {str(e)}"
                    finally:
                        self.pending_file_load = None
                elif not self.doc_ids:
                    # No file loaded - open file browser automatically
                    self.file_browser.show()
            
            # Update smooth scrolling
            if cfg.ENABLE_SMOOTH_SCROLLING and abs(self.target_scroll_y - self.doc_scroll_y) > 0.5:
                # Smooth interpolation
                scroll_diff = self.target_scroll_y - self.doc_scroll_y
                self.doc_scroll_y += scroll_diff * cfg.SMOOTH_SCROLL_FACTOR
                
                # Clamp to valid range
                self.doc_scroll_y = max(0, min(self.max_scroll_y, self.doc_scroll_y))
                
                # Re-render with new scroll position (virtual scrolling makes this fast)
                self.render_document()
            elif cfg.ENABLE_SMOOTH_SCROLLING:
                # Snap to target when close enough
                if self.doc_scroll_y != self.target_scroll_y:
                    self.doc_scroll_y = self.target_scroll_y
                    self.render_document()
            
            self.draw()
            self.clock.tick(cfg.FPS)
        
        pygame.quit()
        sys.exit()

