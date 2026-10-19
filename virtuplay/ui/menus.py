"""Settings menus and text input handling."""

import pygame


class MenusMixin:
    def draw_animation_menu(self):
        """繪製動畫設定菜單"""
        # 菜單背景
        menu_width = 300
        menu_height = 150
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(self.screen, (240, 240, 240), menu_rect, border_radius=10)

        # 顯示 combo 選項
        combo_checkbox_rect = pygame.Rect(menu_x + 20, menu_y + 30, 20, 20)
        pygame.draw.rect(self.screen, (255, 255, 255), combo_checkbox_rect)
        if self.show_combo:
            # 計算圓心位置和半徑
            center_x = combo_checkbox_rect.left + combo_checkbox_rect.width // 2
            center_y = combo_checkbox_rect.top + combo_checkbox_rect.height // 2
            radius = combo_checkbox_rect.width // 4  # 圓點的半徑，設為框寬度的四分之一

            # 繪製圓點
            pygame.draw.circle(self.screen, (0, 0, 0), (center_x, center_y), radius)

        combo_label = self.font_title.render("Show Combo", True, (0, 0, 0))
        self.screen.blit(combo_label, (combo_checkbox_rect.right + 10, combo_checkbox_rect.top))

        gif_checkbox_rect = pygame.Rect(menu_x + 20, menu_y + 70, 20, 20)
        pygame.draw.rect(self.screen, (255, 255, 255), gif_checkbox_rect)  # 繪製方框

        # 顯示 gif 選項
        if self.show_gif:
            # 計算圓心和半徑
            center_x = gif_checkbox_rect.left + gif_checkbox_rect.width // 2
            center_y = gif_checkbox_rect.top + gif_checkbox_rect.height // 2
            radius = gif_checkbox_rect.width // 4  # 圓點的半徑，設為框寬度的四分之一

            # 繪製圓點
            pygame.draw.circle(self.screen, (0, 0, 0), (center_x, center_y), radius)

        gif_label = self.font_title.render("Show Astronout", True, (0, 0, 0))
        self.screen.blit(gif_label, (gif_checkbox_rect.right + 10, gif_checkbox_rect.top))


        # OK 按鈕
        ok_button_rect = pygame.Rect(menu_x + 100, menu_y + 110, 80, 30)
        pygame.draw.rect(self.screen, (200, 200, 200), ok_button_rect, border_radius=5)
        ok_text = self.font_title.render("OK", True, (0, 0, 0))
        self.screen.blit(ok_text, (ok_button_rect.x + 20, ok_button_rect.y + 5))

        # 處理點擊事件
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        if mouse_click[0]:  # 檢查左鍵按下
            if combo_checkbox_rect.collidepoint(mouse_pos):
                self.show_combo = not self.show_combo
            elif gif_checkbox_rect.collidepoint(mouse_pos):
                self.show_gif = not self.show_gif
            elif ok_button_rect.collidepoint(mouse_pos):
                self.animation_menu_active = False

    def draw_settings_menu(self):
        # Semi-transparent background
        s = pygame.Surface((self.screen_width, self.screen_height))
        s.set_alpha(150)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        # Settings menu box
        menu_width = 300
        menu_height = 200
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(self.screen, (240, 240, 240), menu_rect, border_radius=10)

        # BPM input
        bpm_label = self.font_title.render("BPM:", True, (0, 0, 0))
        self.screen.blit(bpm_label, (menu_x + 20, menu_y + 30))
        bpm_input_rect = pygame.Rect(menu_x + 100, menu_y + 25, 150, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), bpm_input_rect, border_radius=5)
        bpm_text_surface = self.font_title.render(self.bpm_text, True, (0, 0, 0))
        self.screen.blit(bpm_text_surface, (bpm_input_rect.x + 5, bpm_input_rect.y + 5))

        # Time tolerance input
        tolerance_label = self.font_title.render("Time Tol:", True, (0, 0, 0))
        self.screen.blit(tolerance_label, (menu_x + 20, menu_y + 80))
        tolerance_input_rect = pygame.Rect(menu_x + 100, menu_y + 75, 150, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), tolerance_input_rect, border_radius=5)
        tolerance_text_surface = self.font_title.render(self.time_tolerance_text, True, (0, 0, 0))
        self.screen.blit(tolerance_text_surface, (tolerance_input_rect.x + 5, tolerance_input_rect.y + 5))
        
        # OK button
        ok_button_rect = pygame.Rect(menu_x + 50, menu_y + 130, 80, 30)
        cancel_button_rect = pygame.Rect(menu_x + 170, menu_y + 130, 80, 30)

        mouse_pos = pygame.mouse.get_pos()

        # OK Button
        if ok_button_rect.collidepoint(mouse_pos):
            ok_color = (173, 216, 230)
        else:
            ok_color = (200, 200, 200)
        pygame.draw.rect(self.screen, ok_color, ok_button_rect, border_radius=5)
        ok_text = self.font_title.render("OK", True, (0, 0, 0))
        self.screen.blit(ok_text, (ok_button_rect.x + 20, ok_button_rect.y + 5))

        # Cancel Button
        if cancel_button_rect.collidepoint(mouse_pos):
            cancel_color = (173, 216, 230)
        else:
            cancel_color = (200, 200, 200)
        pygame.draw.rect(self.screen, cancel_color, cancel_button_rect, border_radius=5)
        cancel_text = self.font_title.render("Cancel", True, (0, 0, 0))
        self.screen.blit(cancel_text, (cancel_button_rect.x + 5, cancel_button_rect.y + 5))

        self.bpm_input_rect = bpm_input_rect
        self.tolerance_input_rect = tolerance_input_rect
        self.ok_button_rect = ok_button_rect
        self.cancel_button_rect = cancel_button_rect

    def draw_report_settings_menu(self):
        # Semi-transparent background
        s = pygame.Surface((self.screen_width, self.screen_height))
        s.set_alpha(150)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        # Settings menu box
        menu_width = 300
        menu_height = 200
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(self.screen, (240, 240, 240), menu_rect, border_radius=10)

        # Time tolerance input
        tolerance_label = self.font_title.render("Time Tol:", True, (0, 0, 0))
        self.screen.blit(tolerance_label, (menu_x + 20, menu_y + 30))
        tolerance_input_rect = pygame.Rect(menu_x + 100, menu_y + 25, 150, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), tolerance_input_rect, border_radius=5)
        tolerance_text_surface = self.font_title.render(self.report_time_tolerance_text, True, (0, 0, 0))
        self.screen.blit(tolerance_text_surface, (tolerance_input_rect.x + 5, tolerance_input_rect.y + 5))

        # Velocity Tolerance input
        velocity_tolerance_label = self.font_title.render("Velo Tol:", True, (0, 0, 0))
        self.screen.blit(velocity_tolerance_label, (menu_x + 20, menu_y + 80))
        velocity_tolerance_input_rect = pygame.Rect(menu_x + 100, menu_y + 75, 150, 30)
        pygame.draw.rect(self.screen, (255, 255, 255), velocity_tolerance_input_rect, border_radius=5)
        velocity_tolerance_text_surface = self.font_title.render(self.report_velocity_tolerance_text, True, (0, 0, 0))
        self.screen.blit(velocity_tolerance_text_surface, (velocity_tolerance_input_rect.x + 5, velocity_tolerance_input_rect.y + 5))

        # OK button
        ok_button_rect = pygame.Rect(menu_x + 50, menu_y + 130, 80, 30)
        cancel_button_rect = pygame.Rect(menu_x + 170, menu_y + 130, 80, 30)

        mouse_pos = pygame.mouse.get_pos()

        # OK Button
        if ok_button_rect.collidepoint(mouse_pos):
            ok_color = (173, 216, 230)
        else:
            ok_color = (200, 200, 200)
        pygame.draw.rect(self.screen, ok_color, ok_button_rect, border_radius=5)
        ok_text = self.font_title.render("OK", True, (0, 0, 0))
        self.screen.blit(ok_text, (ok_button_rect.x + 20, ok_button_rect.y + 5))

        # Cancel Button
        if cancel_button_rect.collidepoint(mouse_pos):
            cancel_color = (173, 216, 230)
        else:
            cancel_color = (200, 200, 200)
        pygame.draw.rect(self.screen, cancel_color, cancel_button_rect, border_radius=5)
        cancel_text = self.font_title.render("Cancel", True, (0, 0, 0))
        self.screen.blit(cancel_text, (cancel_button_rect.x + 5, cancel_button_rect.y + 5))

        self.report_time_tolerance_input_rect = tolerance_input_rect
        self.report_velocity_tolerance_input_rect = velocity_tolerance_input_rect
        self.report_ok_button_rect = ok_button_rect
        self.report_cancel_button_rect = cancel_button_rect

    def update_bpm_and_tolerance(self, new_bpm, new_time_tolerance):
        self.BPM = new_bpm
        self.time_tolerance = new_time_tolerance
        self.ticks_per_second = (self.ticks_per_beat * self.BPM) / 60
        # Reload reference MIDI with new BPM
        self.ref_notes, self.ref_control = self.load_reference_midi(self.reference_path)
        # Recalculate total duration
        self.total_duration = max([end for _, _, end, _ in self.ref_notes])
        # Update beat sound
        self.beat_sound = self.generate_beat_sound(duration=self.metronome_duration)
        # Clear previous data
        self.note_list.clear()
        self.pedal_list.clear()
        self.student_control_pressed_time = -1
        self.student_notes.clear()
        self.bar_scores.clear()
        self.overall_score = {'pitch': 0, 'velocity': 0, 'timing': 0, 'count': 0, 'note_count': 0, 'duration': 0}
        self.performance_report = ""
        self.bpm_text = ''  # Clear the BPM text input
        self.time_tolerance_text = ''  # Clear the time tolerance input

    def report_settings_update_both_tolerance(self, new_time_tolerance, new_velocity_tolerance): # to change time and velocity tolerance value
        self.time_tolerance = new_time_tolerance
        self.velocity_tolerance = new_velocity_tolerance

    def handle_text_input(self, event, target):
        if event.key == pygame.K_RETURN:
            if target == "bpm":
                self.bpm_input_active = False
            elif target == "time_tolerance":
                self.time_tolerance_input_active = False
            elif target == "report_settings_time_tolerance":
                self.report_time_tolerance_input_active = False
            elif target == "report_settings_velocity_tolerance":
                self.report_velocity_tolerance_input_active = False

        elif event.key == pygame.K_BACKSPACE:
            if target == "bpm":
                self.bpm_text = self.bpm_text[:-1]
            elif target == "time_tolerance":
                self.time_tolerance_text = self.time_tolerance_text[:-1]
            elif target == "report_settings_time_tolerance":
                self.report_time_tolerance_text = self.report_time_tolerance_text[:-1]
            elif target == "report_settings_velocity_tolerance":
                self.report_velocity_tolerance_text = self.report_velocity_tolerance_text[:-1]
        else:
            if target == "bpm":
                self.bpm_text += event.unicode
            elif target == "time_tolerance":
                self.time_tolerance_text += event.unicode
            elif target == "report_settings_time_tolerance":
                self.report_time_tolerance_text += event.unicode
            elif target == "report_settings_velocity_tolerance":
                self.report_velocity_tolerance_text += event.unicode
