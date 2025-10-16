"""
UI Components for Entity Annotator
Basic reusable UI elements: buttons, popups, dialogs
"""
import pygame
from typing import List, Dict, Tuple, Optional, Union


class Button:
    """Modern button with hover effects"""
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
        color = self.disabled_color if self.is_disabled else (
            self.hover_color if self.is_hovered else self.active_color
        )
        
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1, border_radius=5)
        
        text_surf = self.font.render(self.text, True, 
            (255, 255, 255) if not self.is_disabled else (100, 100, 100))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos: Tuple[int, int]) -> bool:
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(pos) and not self.is_disabled
        return self.is_hovered != was_hovered
    
    def click(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos) and not self.is_disabled


class Popup:
    """Scrollable popup for selecting options"""
    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = False
        self.options = []
        self.selected_option = None
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        
        # Scrolling
        self.scroll_y = 0
        self.max_scroll_y = 0
        self.option_height = 30
        self.visible_options_height = height - 90
        
        # Buttons
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
    
    def set_options(self, options: List[Dict[str, Union[str, Tuple[int, int, int]]]]):
        self.options = options
        self.selected_option = None
        self.scroll_y = 0
        options_container_height = len(options) * self.option_height
        self.max_scroll_y = max(0, options_container_height - self.visible_options_height)
    
    def draw(self, surface: pygame.Surface):
        if not self.visible:
            return
        
        # Background
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
        
        # Title
        title_surf = self.title_font.render(self.title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        
        pygame.draw.line(surface, (200, 200, 200), 
                        (self.rect.x, self.rect.y + 40), 
                        (self.rect.x + self.rect.width, self.rect.y + 40))
        
        # Options area with clipping
        options_rect = pygame.Rect(
            self.rect.x, self.rect.y + 50, 
            self.rect.width, self.visible_options_height
        )
        original_clip = surface.get_clip()
        surface.set_clip(options_rect)
        
        # Draw visible options
        start_idx = max(0, int(self.scroll_y / self.option_height))
        end_idx = min(len(self.options), 
                     start_idx + int(self.visible_options_height / self.option_height) + 2)
        
        for i in range(start_idx, end_idx):
            option = self.options[i]
            y_pos = self.rect.y + 50 + i * self.option_height - self.scroll_y
            option_rect = pygame.Rect(self.rect.x + 10, y_pos, 
                                     self.rect.width - 20, self.option_height)
            
            if self.selected_option == option["value"]:
                pygame.draw.rect(surface, (230, 240, 255), option_rect, border_radius=3)
            
            text_color = option.get("color", (0, 0, 0))
            text_surf = self.font.render(option["text"], True, text_color)
            surface.blit(text_surf, (option_rect.x + 10, option_rect.y + 5))
        
        surface.set_clip(original_clip)
        
        # Scrollbar
        if self.max_scroll_y > 0:
            scrollbar_width = 8
            scrollbar_height = max(30, min(self.visible_options_height, 
                self.visible_options_height * self.visible_options_height / 
                (self.visible_options_height + self.max_scroll_y)))
            scrollbar_x = self.rect.x + self.rect.width - scrollbar_width - 5
            scrollbar_y = self.rect.y + 50 + (self.visible_options_height - scrollbar_height) * \
                         (self.scroll_y / self.max_scroll_y)
            
            scrollbar_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            pygame.draw.rect(surface, (200, 200, 200), scrollbar_rect, border_radius=4)
        
        # Buttons
        self.cancel_button.draw(surface)
        self.save_button.draw(surface)
    
    def handle_scroll(self, scroll_amount: int):
        if not self.visible or self.max_scroll_y <= 0:
            return
        self.scroll_y = max(0, min(self.max_scroll_y, self.scroll_y - scroll_amount * 30))
    
    def check_hover(self, pos: Tuple[int, int]):
        if not self.visible:
            return None
        
        self.cancel_button.check_hover(pos)
        self.save_button.check_hover(pos)
        
        options_rect = pygame.Rect(
            self.rect.x + 10, self.rect.y + 50, 
            self.rect.width - 20, self.visible_options_height
        )
        
        if options_rect.collidepoint(pos):
            option_idx = int((pos[1] - (self.rect.y + 50) + self.scroll_y) / self.option_height)
            if 0 <= option_idx < len(self.options):
                return "option:" + self.options[option_idx]["value"]
        
        return None
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        if not self.visible:
            return None
        
        if self.cancel_button.click(pos):
            return "cancel"
        
        if self.save_button.click(pos):
            return "save"
        
        options_rect = pygame.Rect(
            self.rect.x + 10, self.rect.y + 50, 
            self.rect.width - 20, self.visible_options_height
        )
        
        if options_rect.collidepoint(pos):
            option_idx = int((pos[1] - (self.rect.y + 50) + self.scroll_y) / self.option_height)
            if 0 <= option_idx < len(self.options):
                self.selected_option = self.options[option_idx]["value"]
                return "option:" + self.selected_option
        
        return None
    
    def show(self, x: Optional[int] = None, y: Optional[int] = None):
        self.visible = True
        self.scroll_y = 0
        
        if x is not None and y is not None:
            screen_width = pygame.display.get_surface().get_width()
            screen_height = pygame.display.get_surface().get_height()
            
            self.rect.x = min(max(x, 0), screen_width - self.rect.width)
            self.rect.y = min(max(y, 0), screen_height - self.rect.height)
            
            button_width = 80
            button_height = 30
            button_margin = 10
            
            self.cancel_button.rect.x = self.rect.x + self.rect.width - 2 * button_width - button_margin
            self.cancel_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
            
            self.save_button.rect.x = self.rect.x + self.rect.width - button_width - button_margin
            self.save_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
    
    def hide(self):
        self.visible = False
        self.selected_option = None


class InputDialog:
    """Text input dialog for adding custom types"""
    def __init__(self, x: int, y: int, width: int, height: int, title: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.visible = False
        self.text_input = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 18, bold=True)
        
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
        
        # Background
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
        
        # Title
        title_surf = self.title_font.render(self.title, True, (0, 0, 0))
        surface.blit(title_surf, (self.rect.x + 10, self.rect.y + 10))
        
        pygame.draw.line(surface, (200, 200, 200), 
                        (self.rect.x, self.rect.y + 40), 
                        (self.rect.x + self.rect.width, self.rect.y + 40))
        
        # Input box
        input_rect = pygame.Rect(self.rect.x + 20, self.rect.y + 60, 
                               self.rect.width - 40, 35)
        pygame.draw.rect(surface, (240, 240, 240), input_rect, border_radius=5)
        pygame.draw.rect(surface, (100, 150, 255), input_rect, 2, border_radius=5)
        
        # Input text
        text_surf = self.font.render(self.text_input, True, (0, 0, 0))
        surface.blit(text_surf, (input_rect.x + 8, input_rect.y + 8))
        
        # Cursor
        if self.cursor_visible:
            text_width = self.font.size(self.text_input)[0]
            cursor_x = input_rect.x + 8 + text_width
            pygame.draw.line(surface, (0, 0, 0), 
                            (cursor_x, input_rect.y + 8), 
                            (cursor_x, input_rect.y + 27), 2)
        
        # Cursor blink
        current_time = pygame.time.get_ticks()
        if current_time - self.cursor_timer > 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = current_time
        
        # Buttons
        self.cancel_button.draw(surface)
        self.save_button.draw(surface)
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        if not self.visible:
            return None
        
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
            if self.text_input.strip():
                return "save"
        elif event.key == pygame.K_ESCAPE:
            return "cancel"
        else:
            if len(self.text_input) < 30:
                self.text_input += event.unicode
        
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        return None
    
    def show(self, x: Optional[int] = None, y: Optional[int] = None):
        self.visible = True
        self.text_input = ""
        if x is not None and y is not None:
            screen_width = pygame.display.get_surface().get_width()
            screen_height = pygame.display.get_surface().get_height()
            
            self.rect.x = min(max(x, 0), screen_width - self.rect.width)
            self.rect.y = min(max(y, 0), screen_height - self.rect.height)
            
            button_width = 80
            button_height = 30
            button_margin = 10
            
            self.cancel_button.rect.x = self.rect.x + self.rect.width - 2 * button_width - button_margin
            self.cancel_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
            
            self.save_button.rect.x = self.rect.x + self.rect.width - button_width - button_margin
            self.save_button.rect.y = self.rect.y + self.rect.height - button_height - button_margin
    
    def hide(self):
        self.visible = False


