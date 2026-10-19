"""Falling-note practice view: keyboard, target line and countdown."""

import time

import pygame


class PracticeViewMixin:
    def draw_piano_keyboard(self):
        # Piano dimensions
        keyboard_height = 200
        keyboard_y = self.screen_height - keyboard_height

        # Calculate key widths
        self.white_key_width = self.screen_width / 52
        self.black_key_width = self.white_key_width * 0.7
        self.black_key_height = keyboard_height * 0.6

        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)

        # Prepare key positions
        self.key_x_positions = {}

        white_key_x = 0
        midi_note = self.min_pitch

        while midi_note <= self.max_pitch:
            is_white = self.is_white_key(midi_note)

            if is_white:
                # Draw white key
                pygame.draw.rect(self.screen, WHITE,
                                (white_key_x, keyboard_y, self.white_key_width - 1, keyboard_height))
                pygame.draw.rect(self.screen, BLACK,
                                (white_key_x, keyboard_y, self.white_key_width - 1, keyboard_height), 1)

                # Record x position
                self.key_x_positions[midi_note] = white_key_x

                # Label the C notes
                if midi_note % 12 == 0:  # Check if the note is C
                    octave = (midi_note // 12) - 1
                    label = f"C{octave}"
                    text_surface = self.font_note.render(label, True, (0, 0, 0))
                    text_x = white_key_x + (self.white_key_width - text_surface.get_width()) / 2
                    text_y = keyboard_y + keyboard_height - text_surface.get_height() - 5
                    self.screen.blit(text_surface, (text_x, text_y))

                white_key_x += self.white_key_width
                midi_note += 1
            else:
                # Black key
                black_x = white_key_x - self.white_key_width * 0.7

                # Draw black key
                pygame.draw.rect(self.screen, BLACK,
                                (black_x, keyboard_y, self.black_key_width, self.black_key_height))

                # Record x position
                self.key_x_positions[midi_note] = black_x

                midi_note += 1

        

        # Define a larger duration tolerance
        duration_tolerance = 5.0  # 您可以根据需要调整这个值

        # Get current time in performance
        if self.falling_notes_start_time is not None:
            current_time = time.time() - self.falling_notes_start_time
        else:
            current_time = 0

        # Initialize the incorrect note detection flag
        incorrect_note_detected = False

        # Highlight active notes
        for note_number in self.active_notes:
            x = self.key_x_positions.get(note_number)
            if x is not None:
                is_white = self.is_white_key(note_number)
                if is_white:
                    key_width = self.white_key_width - 1
                    key_height = keyboard_height
                    key_y = keyboard_y
                else:
                    key_width = self.black_key_width
                    key_height = self.black_key_height
                    key_y = keyboard_y

                # Determine correctness dynamically based on current time and note duration
                correctness = False
                for ref_pitch, ref_start, ref_end, ref_velocity in self.ref_notes:
                    if ref_pitch == note_number:
                        # Allow the note to be held longer without being incorrect
                        if (ref_start - self.time_tolerance) <= current_time <= (ref_end + duration_tolerance):
                            correctness = True
                            break  # Found a matching note, no need to check further

                # Set key color based on dynamic correctness
                if correctness:
                    key_color = (0, 255, 0)  # Green
                else:
                    key_color = (255, 0, 0)  # Red
                    incorrect_note_detected = True  # An incorrect note is being pressed

                # Draw the key with the highlight color
                s = pygame.Surface((key_width, key_height), pygame.SRCALPHA)
                s.fill((*key_color, 100))  # Semi-transparent
                self.screen.blit(s, (x, key_y))

        # After processing all active notes, reset combo if incorrect note is detected
        if incorrect_note_detected:
            self.current_combo = 0
            self.combo_last_increase_time = None  # Reset combo increase time

    def is_note_at_target_line(self, note_number):
        """
        檢查指定音符是否在目標線上，並且正在被按下
        """
        if self.falling_notes_start_time is None:
            return False
            
        current_time = time.time() - self.falling_notes_start_time
        # 擴大容差範圍以確保更好的檢測
        target_tolerance = 0.1  # 容差範圍（秒）
        
        # 檢查音符是否存在於 active_notes 中（表示正在被按下）
        is_note_active = note_number in self.active_notes and self.active_notes[note_number]['velocity'] > 0
        
        if not is_note_active:
            return False
        
        # 檢查是否有對應的參考音符在目標線上
        for pitch, start, end, velocity in self.ref_notes:
            if pitch == note_number:
                # 計算音符與目標線的距離
                time_until_hit = start - current_time
                
                # 檢查音符是否在目標線範圍內
                if abs(time_until_hit) <= target_tolerance:
                    return True
                    
        return False

    def draw_visualization(self):
        """
        Visualize falling notes, highlight active notes, and add continuous smoke effect to the target line.
        """
        # Add continuous smoke effect to the target line
        self.draw_target_line_smoke_effect()

        # Update and draw smoke particles
        self.update_smoke_particles()
        
        self.note_speed = 150  # Pixels per second
        if self.falling_notes_start_time is not None:
            current_time = time.time() - self.falling_notes_start_time
        else:
            current_time = 0

        # Draw reference notes
        for pitch, start, end, velocity in self.ref_notes:
            if pitch < self.min_pitch or pitch > self.max_pitch:
                continue

            time_until_hit = start - current_time
            y = self.target_line_y - (time_until_hit * self.note_speed)
            duration = end - start
            height = int(duration * self.note_speed)

            rect_bottom = y
            rect_top = y - height

            if rect_top >= self.target_line_y:
                continue

            x = self.key_x_positions.get(pitch)
            if x is not None:
                is_white = self.is_white_key(pitch)
                key_width = self.white_key_width if is_white else self.black_key_width

                # Check if smoke effect should be generated for individual notes
                if pitch in self.active_notes and pitch in self.should_smoke:
                    note_data = self.active_notes[pitch]
                    if note_data['velocity'] > 0 and abs(rect_bottom - self.target_line_y) <= self.note_speed * 0.1:
                        self.draw_smoke_effect(x, self.target_line_y, key_width)

                # Draw gradient surface for the note with rounded corners
                if rect_bottom > self.target_line_y:
                    height -= rect_bottom - self.target_line_y
                    rect_bottom = self.target_line_y
                rect_top = rect_bottom - height

                if rect_bottom < 0 or rect_top > self.screen_height:
                    continue

                # Create a gradient surface with rounded corners
                top_color = (0, 200, 255)
                bottom_color = (0, 100, 255)
                note_surface = self.create_gradient_surface(int(key_width), int(height), top_color, bottom_color)
                
                # Clip the surface to fit rounded corners
                rounded_note_surface = pygame.Surface((int(key_width), int(height)), pygame.SRCALPHA)
                pygame.draw.rect(rounded_note_surface, (0, 0, 0, 0), rounded_note_surface.get_rect(), border_radius=5)
                rounded_note_surface.blit(note_surface, (0, 0))
                
                self.screen.blit(rounded_note_surface, (x, rect_top))

                if self.show_syllables and is_white:
                    # Calculate the syllable for the note based on pitch class
                    pitch_class = pitch % 12
                    syllable = self.pitch_class_to_syllable.get(pitch_class, '')

                    if syllable:
                        syllable_text = self.font_note.render(syllable, True, (255, 255, 255))
                        syllable_x = x + key_width // 2 - syllable_text.get_width() // 2
                        syllable_y = rect_bottom - syllable_text.get_height() - 5
                        self.screen.blit(syllable_text, (syllable_x, syllable_y))

    def is_white_key(self, midi_note_number):
        # Returns True if the note is a white key
        return midi_note_number % 12 in [0, 2, 4, 5, 7, 9, 11]

    def draw_dynamic_line(self):
        """Draw the target line where notes should be hit."""
        pygame.draw.line(self.screen, (255, 255, 255), (0, self.target_line_y), (self.screen_width, self.target_line_y), 2)

    def show_countdown(self, dots_left):
        # Define position, size of dots, and colors
        outer_radius = 10
        spacing = 30  # Space between dots
        start_x = 250
        y = 30 # Adjust y-coordinate as needed

        # Clear the entire area before drawing
        self.hide_countdown()

        # Draw each dot with a filled "vanishing" effect
        for i in range(4):  # Always draw the four outer circles
            x = start_x + i * (outer_radius * 2 + spacing)
            pygame.draw.circle(self.screen, (105,105, 105), (x, y), outer_radius)  # Black outer circle
            
            # If the dot should remain partially filled, draw the inner part in the background color
            if i >= dots_left:
                pygame.draw.circle(self.screen, (190, 190, 190), (x, y), outer_radius - 3)  # Vanished middle part

        pygame.display.flip()  # Update display to show the dots

    def hide_countdown(self):
        # Clear the area where dots are displayed
        outer_radius = 10
        spacing = 30
        start_x = 250
        y = 30  # Same y-coordinate as used in show_countdown

        # Calculate total width of dots area
        total_width = (outer_radius * 2 + spacing) * 4 - spacing  # 4 dots and spaces between them

        # Fill with background color to clear
        self.screen.fill((30, 30, 30), (start_x - outer_radius, y - outer_radius, total_width, outer_radius * 2))
