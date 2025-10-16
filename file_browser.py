"""
File Browser Component
Modern file browser for loading JSONL files with folder navigation
"""
import pygame
import os
import json
from typing import Optional, Tuple

# Handle both relative and absolute imports
try:
    from .ui_components import Button
except ImportError:
    from ui_components import Button


class FileBrowser:
    """Modern file browser dialog for loading annotation files"""
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.visible = False
        self.current_path = os.getcwd()
        self.selected_file = None
        self.scroll_y = 0
        self.max_scroll_y = 0
        
        # UI elements
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        self.path_font = pygame.font.SysFont('Arial', 12)
        
        # File lists
        self.files = []
        self.folders = []
        self.hovered_index = -1
        
        # Recent files
        self.recent_files = self.load_recent_files()
        
        # Buttons (positions will be updated in draw)
        self.load_button = Button(0, 0, 120, 35, "Load File", color=(76, 175, 80))
        self.cancel_button = Button(0, 0, 120, 35, "Cancel", color=(244, 67, 54))
        self.home_button = Button(0, 0, 80, 30, "Home", color=(100, 100, 100))
        self.up_button = Button(0, 0, 80, 30, "Up", color=(100, 100, 100))
        
        self.refresh_file_list()
    
    def load_recent_files(self):
        """Load recent files from settings"""
        try:
            recent_path = 'incep/recent_files.json'
            if os.path.exists(recent_path):
                with open(recent_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_recent_files(self):
        """Save recent files to settings"""
        try:
            os.makedirs('incep', exist_ok=True)
            with open('incep/recent_files.json', 'w') as f:
                json.dump(self.recent_files[:10], f)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def add_recent_file(self, filepath):
        """Add file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self.save_recent_files()
    
    def refresh_file_list(self):
        """Refresh the file and folder list"""
        self.files = []
        self.folders = []
        
        try:
            items = os.listdir(self.current_path)
            
            for item in items:
                full_path = os.path.join(self.current_path, item)
                if os.path.isdir(full_path):
                    self.folders.append(item)
                elif item.endswith('.jsonl') or item.endswith('.json'):
                    self.files.append(item)
            
            self.folders.sort()
            self.files.sort()
            
        except Exception as e:
            print(f"Error reading directory: {e}")
        
        self.scroll_y = 0
        self.calculate_max_scroll()
    
    def calculate_max_scroll(self):
        """Calculate maximum scroll based on content"""
        item_height = 35
        recent_height = (len(self.recent_files[:5]) + 2) * item_height if self.recent_files else 0
        total_items = len(self.folders) + len(self.files)
        content_height = recent_height + total_items * item_height
        visible_height = self.height - 200
        self.max_scroll_y = max(0, content_height - visible_height)
    
    def navigate_to(self, path):
        """Navigate to a specific path"""
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = path
            self.refresh_file_list()
    
    def navigate_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.navigate_to(parent)
    
    def format_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def draw(self, surface):
        if not self.visible:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Calculate centered position
        x = (surface.get_width() - self.width) // 2
        y = (surface.get_height() - self.height) // 2
        
        # Main dialog background
        dialog_rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(surface, (255, 255, 255), dialog_rect, border_radius=10)
        pygame.draw.rect(surface, (180, 180, 180), dialog_rect, 2, border_radius=10)
        
        # Title
        title_text = self.title_font.render("Load Annotation File", True, (50, 50, 50))
        surface.blit(title_text, (x + 20, y + 15))
        
        # Current path
        path_text = self.path_font.render(self.current_path[:80], True, (100, 100, 100))
        surface.blit(path_text, (x + 20, y + 95))
        
        # Navigation buttons
        self.home_button.rect = pygame.Rect(x + 20, y + 60, 80, 30)
        self.home_button.draw(surface)
        
        self.up_button.rect = pygame.Rect(x + 110, y + 60, 80, 30)
        self.up_button.draw(surface)
        
        # Separator
        pygame.draw.line(surface, (220, 220, 220), 
                        (x + 20, y + 120), (x + self.width - 20, y + 120), 1)
        
        # File list area
        list_rect = pygame.Rect(x + 20, y + 130, self.width - 40, self.height - 200)
        pygame.draw.rect(surface, (250, 250, 250), list_rect, border_radius=5)
        
        # Set clipping for file list
        original_clip = surface.get_clip()
        surface.set_clip(list_rect)
        
        current_y = list_rect.y + 10 - self.scroll_y
        
        # Draw recent files
        if self.recent_files:
            recent_label = self.font.render("Recent Files:", True, (100, 100, 100))
            surface.blit(recent_label, (list_rect.x + 10, current_y))
            current_y += 30
            
            for i, recent_file in enumerate(self.recent_files[:5]):
                if current_y > list_rect.bottom or current_y + 35 < list_rect.top:
                    current_y += 35
                    continue
                
                item_rect = pygame.Rect(list_rect.x + 10, current_y, list_rect.width - 20, 30)
                
                if self.hovered_index == -(i + 1):
                    pygame.draw.rect(surface, (230, 240, 255), item_rect, border_radius=3)
                
                icon_text = self.font.render("📄", True, (100, 150, 255))
                surface.blit(icon_text, (item_rect.x + 5, item_rect.y + 5))
                
                file_name = os.path.basename(recent_file)
                name_text = self.font.render(file_name[:50], True, (60, 60, 60))
                surface.blit(name_text, (item_rect.x + 30, item_rect.y + 7))
                
                current_y += 35
            
            current_y += 10
            pygame.draw.line(surface, (220, 220, 220),
                           (list_rect.x + 10, current_y),
                           (list_rect.x + list_rect.width - 10, current_y), 1)
            current_y += 20
        
        # Draw folders
        for i, folder in enumerate(self.folders):
            if current_y > list_rect.bottom or current_y + 35 < list_rect.top:
                current_y += 35
                continue
            
            item_rect = pygame.Rect(list_rect.x + 10, current_y, list_rect.width - 20, 30)
            
            if self.hovered_index == i:
                pygame.draw.rect(surface, (240, 240, 240), item_rect, border_radius=3)
            
            icon_text = self.font.render("📁", True, (255, 200, 100))
            surface.blit(icon_text, (item_rect.x + 5, item_rect.y + 5))
            
            name_text = self.font.render(folder[:50], True, (60, 60, 60))
            surface.blit(name_text, (item_rect.x + 30, item_rect.y + 7))
            
            current_y += 35
        
        # Draw files
        for i, file in enumerate(self.files):
            if current_y > list_rect.bottom or current_y + 35 < list_rect.top:
                current_y += 35
                continue
            
            item_rect = pygame.Rect(list_rect.x + 10, current_y, list_rect.width - 20, 30)
            file_index = len(self.folders) + i
            
            if self.hovered_index == file_index:
                pygame.draw.rect(surface, (230, 240, 255), item_rect, border_radius=3)
            elif self.selected_file == file:
                pygame.draw.rect(surface, (200, 220, 255), item_rect, border_radius=3)
            
            icon_text = self.font.render("📄", True, (100, 150, 255))
            surface.blit(icon_text, (item_rect.x + 5, item_rect.y + 5))
            
            name_text = self.font.render(file[:50], True, (60, 60, 60))
            surface.blit(name_text, (item_rect.x + 30, item_rect.y + 7))
            
            # File size
            try:
                file_path = os.path.join(self.current_path, file)
                size = os.path.getsize(file_path)
                size_text = self.format_size(size)
                size_surf = self.path_font.render(size_text, True, (120, 120, 120))
                surface.blit(size_surf, (item_rect.right - size_surf.get_width() - 10, item_rect.y + 8))
            except:
                pass
            
            current_y += 35
        
        surface.set_clip(original_clip)
        
        # Scrollbar
        if self.max_scroll_y > 0:
            total_height = list_rect.height + self.max_scroll_y
            scrollbar_height = max(30, list_rect.height * list_rect.height / total_height)
            scrollbar_y = list_rect.y + (list_rect.height - scrollbar_height) * (self.scroll_y / self.max_scroll_y)
            
            scrollbar_rect = pygame.Rect(list_rect.right - 8, scrollbar_y, 6, scrollbar_height)
            pygame.draw.rect(surface, (180, 180, 180), scrollbar_rect, border_radius=3)
        
        # Action buttons
        self.load_button.rect = pygame.Rect(x + self.width - 280, y + self.height - 50, 120, 35)
        self.load_button.is_disabled = self.selected_file is None
        self.load_button.draw(surface)
        
        self.cancel_button.rect = pygame.Rect(x + self.width - 150, y + self.height - 50, 120, 35)
        self.cancel_button.draw(surface)
    
    def handle_click(self, pos, screen_offset):
        """Handle mouse clicks"""
        x, y = screen_offset
        
        if self.home_button.click(pos):
            self.navigate_to(os.path.expanduser("~"))
            return None
        
        if self.up_button.click(pos):
            self.navigate_up()
            return None
        
        if self.cancel_button.click(pos):
            return "cancel"
        
        if self.load_button.click(pos) and self.selected_file:
            file_path = os.path.join(self.current_path, self.selected_file)
            self.add_recent_file(file_path)
            return file_path
        
        # Check file list clicks
        list_rect = pygame.Rect(x + 20, y + 130, self.width - 40, self.height - 200)
        if list_rect.collidepoint(pos):
            relative_y = pos[1] - list_rect.y + self.scroll_y - 10
            
            # Check recent files
            if self.recent_files:
                recent_section_height = (len(self.recent_files[:5]) + 2) * 35
                if relative_y < recent_section_height:
                    index = int((relative_y - 30) / 35)
                    if 0 <= index < len(self.recent_files[:5]):
                        file_path = self.recent_files[index]
                        if os.path.exists(file_path):
                            self.add_recent_file(file_path)
                            return file_path
                    return None
                relative_y -= recent_section_height
            
            item_index = int(relative_y / 35)
            
            if item_index < len(self.folders):
                folder_name = self.folders[item_index]
                new_path = os.path.join(self.current_path, folder_name)
                self.navigate_to(new_path)
            elif item_index < len(self.folders) + len(self.files):
                file_index = item_index - len(self.folders)
                self.selected_file = self.files[file_index]
        
        return None
    
    def handle_hover(self, pos, screen_offset):
        """Handle mouse hover"""
        x, y = screen_offset
        
        self.home_button.check_hover(pos)
        self.up_button.check_hover(pos)
        self.load_button.check_hover(pos)
        self.cancel_button.check_hover(pos)
        
        list_rect = pygame.Rect(x + 20, y + 130, self.width - 40, self.height - 200)
        if list_rect.collidepoint(pos):
            relative_y = pos[1] - list_rect.y + self.scroll_y - 10
            
            if self.recent_files:
                recent_section_height = (len(self.recent_files[:5]) + 2) * 35
                if relative_y < recent_section_height:
                    index = int((relative_y - 30) / 35)
                    if 0 <= index < len(self.recent_files[:5]):
                        self.hovered_index = -(index + 1)
                        return
                relative_y -= recent_section_height
            
            item_index = int(relative_y / 35)
            if 0 <= item_index < len(self.folders) + len(self.files):
                self.hovered_index = item_index
            else:
                self.hovered_index = -1
        else:
            self.hovered_index = -1
    
    def handle_scroll(self, amount, screen_offset):
        """Handle scroll wheel"""
        mouse_pos = pygame.mouse.get_pos()
        x, y = screen_offset
        list_rect = pygame.Rect(x + 20, y + 130, self.width - 40, self.height - 200)
        
        if list_rect.collidepoint(mouse_pos):
            self.scroll_y = max(0, min(self.max_scroll_y, self.scroll_y - amount * 30))
    
    def show(self, initial_path=None):
        """Show the file browser"""
        self.visible = True
        if initial_path and os.path.exists(initial_path):
            if os.path.isfile(initial_path):
                self.navigate_to(os.path.dirname(initial_path))
                self.selected_file = os.path.basename(initial_path)
            else:
                self.navigate_to(initial_path)
        self.refresh_file_list()
    
    def hide(self):
        """Hide the file browser"""
        self.visible = False
        self.selected_file = None

