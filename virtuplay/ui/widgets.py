"""Buttons, legends, tooltips and other drawing helpers."""

import pygame


class WidgetsMixin:
    def setup_ui_elements(self):
        self.button_width = 80
        self.button_height = 30
        self.button_spacing = 10

        self.record_button_rect = pygame.Rect(10, 70, self.button_width, self.button_height)
        self.show_button_rect = pygame.Rect(10, 70 + self.button_height + self.button_spacing, self.button_width, self.button_height)
        self.settings_button_rect = pygame.Rect(
            10, 70 + 2 * (self.button_height + self.button_spacing), 100, self.button_height
        )
        self.syllable_button_rect = pygame.Rect(
            10, 70 + 3 * (self.button_height + self.button_spacing), 150, self.button_height
        )

        self.close_button_rect = pygame.Rect(self.screen_width - 60, self.screen_height - 60, 100, 40)
        self.animation_button_rect = pygame.Rect(
            10, 70 + 4 * (self.button_height + self.button_spacing), 120, self.button_height
        )

    def create_gradient_surface(self, width, height, top_color, bottom_color):
        # Create a surface with per-pixel alpha
        gradient = pygame.Surface((width, max(height, 1)), pygame.SRCALPHA)  # Ensure height is at least 1
        
        # Draw the gradient onto the surface
        for y in range(int(height)):
            ratio = y / height if height > 0 else 0
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))
        
        gradient.set_alpha(180)  # Adjust transparency if needed
        return gradient

    def draw_rounded_rect(self, surface, color, rect, radius=10):
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def draw_button_with_shadow(self, surface, rect, text, font, active=False):
        shadow_offset = 4  # Offset for shadow
        shadow_color = (100, 100, 100)  # Shadow color

        # Draw shadow
        shadow_rect = rect.move(shadow_offset, shadow_offset)
        self.draw_rounded_rect(surface, shadow_color, shadow_rect, radius=15)

        # Determine color based on active state
        if active:
            button_color = (200, 230, 255)  # Light blue
            text_color = (0, 102, 204)
        else:
            button_color = (230, 240, 250)  # Soft blue gradient
            text_color = (50, 50, 50)

        # Draw button background with rounded corners
        self.draw_rounded_rect(surface, button_color, rect, radius=15)

        # Draw button text
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def draw_tooltip(self, surface, text, x, y):
        """Draw a tooltip box with given text at the specified (x, y) position."""
        padding = 5
        font = self.font_note
        text_surface = font.render(text, True, (0, 0, 0))
        w = text_surface.get_width() + padding * 2
        h = text_surface.get_height() + padding * 2

        # Position tooltip slightly offset from the mouse pointer
        tooltip_x = x + 20
        tooltip_y = y + 20

        # Draw background and border
        pygame.draw.rect(surface, (255, 255, 225), (tooltip_x, tooltip_y, w, h))
        pygame.draw.rect(surface, (0, 0, 0), (tooltip_x, tooltip_y, w, h), 1)

        # Draw text
        surface.blit(text_surface, (tooltip_x + padding, tooltip_y + padding))

    def draw_legends(self):
        legend_height = 30
        legend_width = 220
        start_y = 20
        start_x = self.screen_width - legend_width - 10
        circle_radius = 8  # Circle radius
        padding = 8  # Padding inside the box
        spacing = 4  # Spacing between legends

        # Update legends with current time tolerance
        self.legends[4] = (f"Time tolerance: {self.time_tolerance:.2f}s", (150, 150, 150))

        # Calculate the height of the box
        total_height = len(self.legends) * legend_height + (len(self.legends) - 1) * spacing + padding * 2

        # Draw box background
        pygame.draw.rect(
            self.screen, 
            (220, 220, 220),  # Light gray background
            pygame.Rect(start_x - padding, start_y - padding, legend_width + padding * 2, total_height),
            border_radius=10  # Rounded corners
        )

        for i, (label, color) in enumerate(self.legends):
            y = start_y + i * (legend_height + spacing)
            
            # Draw circle
            circle_center = (start_x + circle_radius, y + circle_radius)  # Circle center position
            pygame.draw.circle(self.screen, color, circle_center, circle_radius)
            
            # Render and draw text
            text = self.legend_font.render(label, True, (0, 0, 0))
            self.screen.blit(text, (start_x + circle_radius * 2 + 10, y + 2.5))  # Slightly adjust text position
