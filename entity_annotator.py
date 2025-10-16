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

# Handle both relative and absolute imports
try:
    from .ui_components import Button, Popup, InputDialog
    from .file_browser import FileBrowser
    from .navigation import NavigationBar, ShortcutHelp
    from .utils import (
        load_settings, save_settings, load_history, save_history,
        load_jsonl, save_jsonl, generate_random_color, normalize_type
    )
except ImportError:
    from ui_components import Button, Popup, InputDialog
    from file_browser import FileBrowser
    from navigation import NavigationBar, ShortcutHelp
    from utils import (
        load_settings, save_settings, load_history, save_history,
        load_jsonl, save_jsonl, generate_random_color, normalize_type
    )


class EntityAnnotator:
    """Main Entity Annotation Application"""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Window setup
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Entity Annotator - Enhanced")
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.font = pygame.font.SysFont('Arial', 18)
        self.small_font = pygame.font.SysFont('Arial', 14)
        self.bold_font = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Load settings
        self.settings = load_settings()
        self.entity_colors = self.settings["entity_colors"]
        self.relation_colors = self.settings["relation_colors"]
        
        # Document data
        self.document_collection = []
        self.current_doc_index = 0
        self.doc = {"sentences": [], "ner": [], "relations": []}
        self.doc_id = None
        self.current_file_path = None
        
        # UI State
        self.status_message = "Press Ctrl+O to open a file"
        self.save_status = ""
        self.save_status_time = 0
        
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
        
        # History
        undo_list, redo_list = load_history()
        self.undo_stack = deque(undo_list, maxlen=25)
        self.redo_stack = deque(redo_list, maxlen=25)
        
        # Rendering data
        self.rendered_entities = []
        self.rendered_tokens = []
        self.rendered_relations = []
        self.rendered_labels = []
        self.entity_elements = {}
        
        # Scrolling
        self.doc_scroll_y = 0
        self.max_scroll_y = 0
        self.doc_container = pygame.Rect(10, 160, self.width - 20, self.height - 170)
        
        # Initialize UI components
        self.setup_ui()
        
        # Load initial file if exists
        default_file = 'incep/combined_scier_hyperpie_train.jsonl'
        if hasattr(sys, 'argv') and len(sys.argv) > 1:
            self.load_file(sys.argv[1])
        elif self.file_browser.recent_files:
            # Try to load most recent file
            try:
                self.load_file(self.file_browser.recent_files[0])
            except:
                pass
    
    def setup_ui(self):
        """Initialize all UI components"""
        button_width = 150
        button_height = 30
        button_margin = 10
        toolbar_y = 50
        
        # Toolbar buttons
        self.undo_button = Button(10, toolbar_y, button_width, button_height, "Undo (Ctrl+Z)")
        self.undo_button.is_disabled = len(self.undo_stack) == 0
        
        self.redo_button = Button(10 + (button_width + button_margin), toolbar_y, 
                                  button_width, button_height, "Redo (Ctrl+Y)")
        self.redo_button.is_disabled = len(self.redo_stack) == 0
        
        self.save_button = Button(10 + 2 * (button_width + button_margin), toolbar_y, 
                                  button_width, button_height, "Save (Ctrl+S)",
                                  color=(76, 175, 80), hover_color=(56, 142, 60))
        
        self.open_file_button = Button(10 + 3 * (button_width + button_margin), toolbar_y,
                                       button_width, button_height, "Open File (Ctrl+O)",
                                       color=(63, 81, 181), hover_color=(48, 63, 159))
        
        self.add_entity_type_button = Button(10 + 4 * (button_width + button_margin), toolbar_y,
                                             button_width, button_height, "Add Entity Type",
                                             color=(156, 39, 176), hover_color=(123, 31, 162))
        
        self.add_relation_type_button = Button(10 + 5 * (button_width + button_margin), toolbar_y,
                                               button_width, button_height, "Add Relation Type",
                                               color=(156, 39, 176), hover_color=(123, 31, 162))
        
        # Navigation buttons
        nav_y = toolbar_y + button_height + button_margin
        self.prev_doc_button = Button(10, nav_y, button_width, button_height, "◀ Prev",
                                      color=(158, 158, 158), hover_color=(117, 117, 117))
        
        self.next_doc_button = Button(10 + button_width + button_margin, nav_y,
                                      button_width, button_height, "Next ▶",
                                      color=(158, 158, 158), hover_color=(117, 117, 117))
        
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
        
        # New components
        self.file_browser = FileBrowser(width=900, height=600)
        self.navigation_bar = NavigationBar(10, 125, self.width - 20, 30)
        self.shortcut_help = ShortcutHelp()
    
    def load_file(self, file_path: str) -> bool:
        """Load annotations from a JSONL file"""
        try:
            if not file_path:
                return False
            
            self.document_collection = load_jsonl(file_path)
            
            if not self.document_collection:
                self.status_message = "Error: No documents found in file"
                return False
            
            self.current_file_path = file_path
            self.load_document(0)
            self.extract_and_save_entity_types()
            
            self.save_status = f"Loaded {len(self.document_collection)} documents"
            self.save_status_time = pygame.time.get_ticks()
            self.status_message = f"Loaded: {file_path}"
            
            return True
            
        except Exception as e:
            self.status_message = f"Error loading file: {str(e)}"
            print(f"Error loading file: {e}")
            return False
    
    def load_document(self, index: int):
        """Load document at specified index"""
        if 0 <= index < len(self.document_collection):
            self.current_doc_index = index
            doc = self.document_collection[index]
            
            self.doc_id = doc.get("doc_id", f"doc_{index}")
            self.doc["sentences"] = doc.get("sentences", [])
            self.doc["ner"] = doc.get("ner", [])
            self.doc["relations"] = doc.get("relations", [])
            
            # Update navigation buttons
            self.prev_doc_button.is_disabled = (index == 0)
            self.next_doc_button.is_disabled = (index == len(self.document_collection) - 1)
            
            # Reset scroll and state
            self.doc_scroll_y = 0
            self.selected_entities = []
            self.selected_tokens = []
            self.selected_entity_labels = {}
            
            self.render_document()
            self.status_message = f"Document {index + 1}/{len(self.document_collection)}"
    
    def save_current_document(self):
        """Save current document back to collection"""
        if self.current_doc_index < len(self.document_collection):
            self.document_collection[self.current_doc_index]["sentences"] = self.doc["sentences"]
            self.document_collection[self.current_doc_index]["ner"] = self.doc["ner"]
            self.document_collection[self.current_doc_index]["relations"] = self.doc["relations"]
    
    def save_annotations(self) -> bool:
        """Save all annotations to file"""
        try:
            if not self.current_file_path or not self.document_collection:
                self.save_status = "No file loaded to save"
                self.save_status_time = pygame.time.get_ticks()
                return False
            
            self.save_current_document()
            save_jsonl(self.document_collection, self.current_file_path)
            
            self.save_status = "Saved successfully!"
            self.save_status_time = pygame.time.get_ticks()
            save_history(self.undo_stack, self.redo_stack)
            
            return True
        except Exception as e:
            self.save_status = f"Error: {str(e)}"
            self.save_status_time = pygame.time.get_ticks()
            print(f"Error saving: {e}")
            return False
    
    def extract_and_save_entity_types(self):
        """Extract unique entity/relation types from documents"""
        entity_types = set()
        relation_types = set()
        
        for doc in self.document_collection:
            # Extract entity types from all sentences
            for sent_entities in doc.get("ner", []):
                for entity in sent_entities:
                    if len(entity) >= 3:
                        entity_type = normalize_type(entity[2])
                        entity_types.add(entity_type)
            
            # Extract relation types from all sentences
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
        
        if settings_updated:
            save_settings(self.settings)
            
            # Update popup options
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
        
        line_height = self.font.get_height() + 8
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
                y += 10
                line_tokens = []
                line_width = 0
            
            for tok_idx, token_text in enumerate(sentence):
                if not token_text:
                    global_idx += 1
                    continue
                
                token_width = self.font.size(token_text)[0] + 4
                
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
        
        save_history(self.undo_stack, self.redo_stack)
    
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
        
        relation_info = {
            "source": src_entity,
            "target": tgt_entity,
            "type": rel_type,
            "color": self.relation_colors.get(rel_type, (120, 120, 120)),
            "src_center_x": src_center_x,
            "src_center_y": src_center_y,
            "tgt_center_x": tgt_center_x,
            "tgt_center_y": tgt_center_y
        }
        
        self.rendered_relations.append(relation_info)
        
        # Add label
        label_x = (src_center_x + tgt_center_x) // 2
        label_y = min(self.get_entity_top(src_entity), 
                     self.get_entity_top(tgt_entity)) - 15
        
        label_info = {
            "text": rel_type,
            "x": label_x,
            "y": label_y,
            "color": self.relation_colors.get(rel_type, (120, 120, 120))
        }
        
        self.rendered_labels.append(label_info)
    
    def draw(self):
        """Draw the application"""
        self.screen.fill((240, 240, 240))
        
        # Toolbar
        toolbar_rect = pygame.Rect(0, 0, self.width, 160)
        pygame.draw.rect(self.screen, (220, 220, 220), toolbar_rect)
        pygame.draw.line(self.screen, (200, 200, 200), (0, 160), (self.width, 160), 2)
        
        # Title
        title_text = self.bold_font.render("Entity Annotator", True, (50, 50, 50))
        self.screen.blit(title_text, (10, 10))
        
        # Status
        status_surf = self.font.render(self.status_message[:100], True, (100, 100, 100))
        self.screen.blit(status_surf, (self.width - status_surf.get_width() - 10, 15))
        
        # Draw buttons
        self.undo_button.draw(self.screen)
        self.redo_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.open_file_button.draw(self.screen)
        self.add_entity_type_button.draw(self.screen)
        self.add_relation_type_button.draw(self.screen)
        self.prev_doc_button.draw(self.screen)
        self.next_doc_button.draw(self.screen)
        
        # Navigation bar
        if self.document_collection:
            self.navigation_bar.draw(self.screen, self.current_doc_index, 
                                    len(self.document_collection))
        
        # Save status
        current_time = pygame.time.get_ticks()
        if self.save_status and current_time - self.save_status_time < 3000:
            save_surf = self.font.render(self.save_status, True, (0, 150, 0))
            self.screen.blit(save_surf, (self.width - save_surf.get_width() - 10, 45))
        
        # Document container
        pygame.draw.rect(self.screen, (255, 255, 255), self.doc_container)
        pygame.draw.rect(self.screen, (200, 200, 200), self.doc_container, 1)
        
        # Draw document content
        original_clip = self.screen.get_clip()
        self.screen.set_clip(self.doc_container)
        self.draw_document_content()
        self.screen.set_clip(original_clip)
        
        # Scrollbar
        if self.max_scroll_y > 0:
            scrollbar_height = max(30, min(self.doc_container.height,
                self.doc_container.height * self.doc_container.height / 
                (self.doc_container.height + self.max_scroll_y)))
            scrollbar_pos = self.doc_container.y + (self.doc_container.height - scrollbar_height) * \
                           (self.doc_scroll_y / self.max_scroll_y)
            
            scrollbar_rect = pygame.Rect(self.doc_container.right - 10, scrollbar_pos, 
                                        10, scrollbar_height)
            pygame.draw.rect(self.screen, (200, 200, 200), scrollbar_rect, border_radius=5)
        
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
        """Draw document tokens, entities, and relations"""
        # Draw tokens
        for token in self.rendered_tokens:
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
        
        # Draw entities
        for entity in self.rendered_entities:
            self.draw_entity_background(entity)
        
        # Draw relations (only for hovered entity)
        if self.hovered_entity_key:
            # Collect relations connected to the hovered entity
            connected_relations = []
            for relation in self.rendered_relations:
                src_key = f"{relation['source']['start']}-{relation['source']['end']}"
                tgt_key = f"{relation['target']['start']}-{relation['target']['end']}"
                
                if src_key == self.hovered_entity_key or tgt_key == self.hovered_entity_key:
                    connected_relations.append(relation)
                    self.draw_relation_arrow(relation)
            
            # Draw labels only for the connected relations
            for relation in connected_relations:
                src_center_x = relation["src_center_x"]
                tgt_center_x = relation["tgt_center_x"]
                expected_label_x = (src_center_x + tgt_center_x) // 2
                relation_type = relation["type"]
                
                # Find the label that matches this specific relation
                for label in self.rendered_labels:
                    if label["text"] == relation_type:
                        # Check if label position is close to this relation's expected position
                        if abs(label["x"] - expected_label_x) < 100:
                            self.draw_relation_label(label)
                            break
        
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
        """Draw entity background rectangle"""
        entity_type = normalize_type(entity_info["type"])
        bg_color = self.entity_colors.get(entity_type, (200, 200, 200))
        bg_color_alpha = (bg_color[0], bg_color[1], bg_color[2], 100)
        
        rects = [entity_info["rect"]] if isinstance(entity_info["rect"], pygame.Rect) else entity_info["rect"]["rects"]
        
        for rect in (rects if isinstance(entity_info["rect"], dict) and entity_info["rect"].get("multi_line") else [entity_info["rect"]]):
            entity_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(entity_surface, bg_color_alpha, (0, 0, rect.width, rect.height), border_radius=3)
            self.screen.blit(entity_surface, rect)
            
            border_width = 2 if (entity_info["hovered"] or entity_info["selected"]) else 1
            pygame.draw.rect(self.screen, bg_color, rect, border_width, border_radius=3)
    
    def draw_relation_arrow(self, relation):
        """Draw relation arrow"""
        src_x, src_y = relation["src_center_x"], relation["src_center_y"]
        tgt_x, tgt_y = relation["tgt_center_x"], relation["tgt_center_y"]
        
        distance = math.sqrt((tgt_x - src_x)**2 + (tgt_y - src_y)**2)
        height_factor = min(100, distance / 4)
        
        if abs(tgt_y - src_y) < 50:
            ctrl_x1 = src_x + (tgt_x - src_x) * 0.25
            ctrl_y1 = src_y - height_factor
            ctrl_x2 = src_x + (tgt_x - src_x) * 0.75
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
        """Draw relation label"""
        if self.doc_container.y < label["y"] < self.doc_container.bottom:
            text_surf = self.small_font.render(label["text"], True, label["color"])
            text_rect = text_surf.get_rect(center=(label["x"], label["y"]))
            
            bg_rect = text_rect.copy()
            bg_rect.inflate_ip(6, 6)
            
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surf.fill((255, 255, 255))
            bg_surf.set_alpha(220)
            self.screen.blit(bg_surf, bg_rect)
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
                self.save_annotations()
                save_settings(self.settings)
                save_history(self.undo_stack, self.redo_stack)
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
                self.doc_scroll_y = max(0, min(self.max_scroll_y, 
                                     self.doc_scroll_y - scroll_dir * 30))
                self.render_document()
            return
        
        # Handle button clicks
        if self.undo_button.click(pos) and not self.undo_button.is_disabled:
            self.undo()
        elif self.redo_button.click(pos) and not self.redo_button.is_disabled:
            self.redo()
        elif self.save_button.click(pos):
            self.save_annotations()
        elif self.open_file_button.click(pos):
            self.file_browser.show(self.current_file_path if self.current_file_path else None)
        elif self.prev_doc_button.click(pos) and not self.prev_doc_button.is_disabled:
            self.load_document(self.current_doc_index - 1)
        elif self.next_doc_button.click(pos) and not self.next_doc_button.is_disabled:
            self.load_document(self.current_doc_index + 1)
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
        
        # Handle token selection
        if self.is_selecting and self.selection_start_token:
            token = self.check_token_hover(pos)
            if token:
                start_idx = min(self.selection_start_token["global_idx"], token["global_idx"])
                end_idx = max(self.selection_start_token["global_idx"], token["global_idx"])
                self.selected_tokens = list(range(start_idx, end_idx + 1))
                self.render_document()
        
        # Update entity hover states
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
            
            if entity["hovered"] and not was_hovered:
                self.hovered_entity_key = f"{entity['start']}-{entity['end']}"
            elif was_hovered and not entity["hovered"]:
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
            result = self.navigation_bar.handle_key(event, len(self.document_collection))
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
            if mods & pygame.KMOD_CTRL:
                new_idx = max(0, self.current_doc_index - 10)
                self.load_document(new_idx)
            else:
                if not self.prev_doc_button.is_disabled:
                    self.load_document(self.current_doc_index - 1)
        
        elif event.key == pygame.K_RIGHT:
            if mods & pygame.KMOD_CTRL:
                new_idx = min(len(self.document_collection) - 1, self.current_doc_index + 10)
                self.load_document(new_idx)
            else:
                if not self.next_doc_button.is_disabled:
                    self.load_document(self.current_doc_index + 1)
        
        # Home/End - First/Last document
        elif event.key == pygame.K_HOME:
            self.load_document(0)
        
        elif event.key == pygame.K_END:
            self.load_document(len(self.document_collection) - 1)
        
        # Page Up/Down - Scroll
        elif event.key == pygame.K_PAGEUP:
            self.doc_scroll_y = max(0, self.doc_scroll_y - 100)
            self.render_document()
        
        elif event.key == pygame.K_PAGEDOWN:
            self.doc_scroll_y = min(self.max_scroll_y, self.doc_scroll_y + 100)
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
        
        save_settings(self.settings)
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
        
        save_settings(self.settings)
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
        """Main application loop"""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

