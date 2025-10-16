"""
Navigation and Help Components
Navigation bar with progress tracking and keyboard shortcut help overlay
"""
import pygame
from typing import Optional


class NavigationBar:
    """Enhanced navigation with progress bar and jump to document"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.SysFont('Arial', 14)
        self.bold_font = pygame.font.SysFont('Arial', 14, bold=True)
        
        self.jump_input = ""
        self.jump_active = False
        self.jump_rect = pygame.Rect(x + width - 200, y + 5, 80, height - 10)
    
    def draw(self, surface, current_doc, total_docs):
        # Background
        pygame.draw.rect(surface, (245, 245, 245), self.rect, border_radius=5)
        pygame.draw.rect(surface, (220, 220, 220), self.rect, 1, border_radius=5)
        
        # Update jump_rect position based on current rect (in case of resize)
        # Moved further right to avoid overlap
        self.jump_rect = pygame.Rect(
            self.rect.x + self.rect.width - 130, 
            self.rect.y + 5, 
            80, 
            self.rect.height - 10
        )
        
        # Progress bar - made narrower to give more space for counter and jump box
        progress_width = self.rect.width - 270
        progress_rect = pygame.Rect(
            self.rect.x + 10, 
            self.rect.y + self.rect.height // 2 - 5,
            progress_width, 10
        )
        pygame.draw.rect(surface, (230, 230, 230), progress_rect, border_radius=5)
        
        if total_docs > 0:
            filled_width = int(((current_doc + 1) / total_docs) * progress_width)
            filled_rect = pygame.Rect(progress_rect.x, progress_rect.y, filled_width, 10)
            pygame.draw.rect(surface, (100, 180, 100), filled_rect, border_radius=5)
        
        # Document counter - with more spacing from progress bar
        counter_text = f"{current_doc + 1} / {total_docs}"
        counter_surf = self.bold_font.render(counter_text, True, (60, 60, 60))
        surface.blit(counter_surf, (progress_rect.x + progress_width + 20, 
                                   self.rect.y + self.rect.height // 2 - 7))
        
        # Jump to label - with more spacing from counter
        jump_label = self.font.render("Go to:", True, (100, 100, 100))
        surface.blit(jump_label, (self.jump_rect.x - 50, self.rect.y + self.rect.height // 2 - 7))
        
        # Jump input box
        input_bg_color = (255, 255, 255) if self.jump_active else (245, 245, 245)
        pygame.draw.rect(surface, input_bg_color, self.jump_rect, border_radius=3)
        border_color = (100, 150, 255) if self.jump_active else (200, 200, 200)
        pygame.draw.rect(surface, border_color, self.jump_rect, 2, border_radius=3)
        
        # Jump input text - centered vertically in the box
        input_text = self.jump_input if self.jump_input else str(current_doc + 1)
        text_color = (0, 0, 0) if self.jump_input else (150, 150, 150)
        text_surf = self.font.render(input_text, True, text_color)
        # Center text vertically in the input box
        text_y = self.jump_rect.y + (self.jump_rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (self.jump_rect.x + 8, text_y))
    
    def handle_click(self, pos):
        """Handle clicks on navigation bar"""
        if self.jump_rect.collidepoint(pos):
            self.jump_active = True
            self.jump_input = ""
            return "activate_jump"
        else:
            self.jump_active = False
        return None
    
    def handle_key(self, event, total_docs):
        """Handle keyboard input for jump to document"""
        if not self.jump_active:
            return None
        
        if event.key == pygame.K_RETURN:
            try:
                doc_num = int(self.jump_input)
                if 1 <= doc_num <= total_docs:
                    self.jump_active = False
                    self.jump_input = ""
                    return doc_num - 1  # Convert to 0-indexed
            except ValueError:
                pass
            return None
        
        elif event.key == pygame.K_ESCAPE:
            self.jump_active = False
            self.jump_input = ""
            return None
        
        elif event.key == pygame.K_BACKSPACE:
            self.jump_input = self.jump_input[:-1]
        
        elif event.unicode.isdigit() and len(self.jump_input) < 6:
            self.jump_input += event.unicode
        
        return None


class ShortcutHelp:
    """Keyboard shortcut help overlay"""
    def __init__(self):
        self.visible = False
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        self.section_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        self.shortcuts = {
            "General": [
                ("Ctrl + O", "Open file"),
                ("Ctrl + S", "Save annotations"),
                ("Ctrl + Z", "Undo"),
                ("Ctrl + Y", "Redo"),
                ("F1 or ?", "Show/hide this help"),
                ("Esc", "Close dialogs"),
            ],
            "Navigation": [
                ("Left/Right Arrow", "Previous/Next document"),
                ("Ctrl + Left/Right", "Jump 10 documents"),
                ("Home/End", "First/Last document"),
                ("Ctrl + G", "Go to document number"),
                ("Page Up/Down", "Scroll document"),
            ],
            "Annotation": [
                ("Click + Drag", "Select tokens"),
                ("E + Hover", "Quick entity highlight"),
                ("Right Click Entity", "Create relation"),
                ("D", "Delete selected entity"),
                ("Left Click Entity", "Select entity"),
            ],
        }
    
    def draw(self, surface):
        if not self.visible:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface(surface.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        # Calculate dialog size
        width = 700
        height = 500
        x = (surface.get_width() - width) // 2
        y = (surface.get_height() - height) // 2
        
        # Dialog background
        dialog_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (255, 255, 255), dialog_rect, border_radius=10)
        pygame.draw.rect(surface, (180, 180, 180), dialog_rect, 2, border_radius=10)
        
        # Title
        title_text = self.title_font.render("Keyboard Shortcuts", True, (50, 50, 50))
        surface.blit(title_text, (x + 30, y + 20))
        
        # Close instruction
        close_text = self.font.render("Press Esc or F1 to close", True, (120, 120, 120))
        surface.blit(close_text, (x + width - close_text.get_width() - 30, y + 25))
        
        # Draw shortcuts in columns
        current_x = x + 30
        current_y = y + 70
        column_width = (width - 60) // 2
        
        sections = list(self.shortcuts.items())
        mid_point = (len(sections) + 1) // 2
        
        for col in range(2):
            col_x = current_x + col * column_width
            col_y = current_y
            
            start_idx = col * mid_point
            end_idx = start_idx + mid_point
            
            for section, shortcuts in sections[start_idx:end_idx]:
                # Section title
                section_surf = self.section_font.render(section, True, (80, 80, 80))
                surface.blit(section_surf, (col_x, col_y))
                col_y += 30
                
                # Shortcuts
                for key, description in shortcuts:
                    # Key
                    key_surf = self.font.render(key, True, (100, 150, 255))
                    surface.blit(key_surf, (col_x + 10, col_y))
                    
                    # Description
                    desc_surf = self.font.render(description, True, (60, 60, 60))
                    surface.blit(desc_surf, (col_x + 160, col_y))
                    
                    col_y += 25
                
                col_y += 15
    
    def toggle(self):
        """Toggle visibility"""
        self.visible = not self.visible

