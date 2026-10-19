"""Scrollable performance report and PDF export."""

import os
import time

import pygame
from fpdf import FPDF
from PIL import Image

from ..config import OUTPUT_DIR


class ReportViewMixin:
    def create_file_if_not_exist(self, path):
        # Extract the directory from the path
        directory = os.path.dirname(path)

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Create the file (if it doesn't exist)
        if not os.path.exists(path):
            with open(path, 'w') as file:
                file.write("")  # Create an empty file

    def save_content_to_pdf(self, surface):
        # Create a PDF
        pdf = FPDF()
        pdf_width_setup = 794
        pdf_height_setup = 1122
        screenshot_to_pdf_page_ratio = pdf_width_setup / self.screen_width
        # Number of pages required to cover the content height
        page_surface_y = pdf_height_setup / screenshot_to_pdf_page_ratio
        #num_pages = int((self.surface_height + self.screen_height - 1) // page_surface_y + 1)
        num_pages = int((self.surface_height) // page_surface_y + 1)

        for page_num in range(num_pages):
            # Define the area of content to capture
            page_surface = pygame.Surface((self.screen_width, page_surface_y))
            page_surface.blit(surface, (0, 0), (0, page_num * page_surface_y, self.screen_width, page_surface_y))# x * ratio = 1122

            # Save the page image temporarily
            page_image_path = str(OUTPUT_DIR / "pdf_pages" / f"page_{page_num}.png")
            self.create_file_if_not_exist(page_image_path)
            pygame.image.save(page_surface, page_image_path)
            
            # Open the saved image and get dimensions
            image = Image.open(page_image_path)
            image = image.resize((pdf_width_setup, pdf_height_setup))
            width, height = image.size
            # Convert pixel dimensions to mm for PDF (assuming 96 dpi)
            pdf_width, pdf_height = width * 0.2645, height * 0.2645  # pixels to mm

            # Add a new page to the PDF and insert the image
            pdf.add_page()
            pdf.image(page_image_path, 0, 0, pdf_width, pdf_height)

        # Output the final PDF
        pdf_path = str(OUTPUT_DIR / f"report_{time.strftime('%Y%m%d-%H%M%S')}.pdf")
        self.create_file_if_not_exist(pdf_path)
        pdf.output(pdf_path)
        print("PDF has been output")

    def draw_all_bar_markers(self, surface, bar_duration, scaling_factor, x_intercept, surface_height):
        """
        Draw vertical markers for every bar in the report.
        """
        current_time = 0
        bar_number = 1
        bar_marker_color = (200, 200, 200)  # Light gray for bar lines
        bar_label_color = (0, 0, 0)  # Black for bar labels

        while current_time <= self.total_duration:
            x = x_intercept + current_time * scaling_factor

            # Draw vertical line for the bar marker
            pygame.draw.line(surface, bar_marker_color, (x, 0), (x, surface_height), 1)

            # Add bar number label above the line
            label_surface = self.font_note.render(f"Bar {bar_number}", True, bar_label_color)
            label_x = x - label_surface.get_width() // 2
            label_y = 5  # Position slightly above the bar marker
            surface.blit(label_surface, (label_x, label_y))

            # Move to the next bar
            current_time += bar_duration
            bar_number += 1

    def draw_report(self):
        self.y_intercept = self.screen_height * 1 / 4
        self.x_intercept = self.screen_width / 10

        # 設定放大係數
        bar_scale_factor = 1.5
        horizontal_length_factor = 2

        # 根據 bar_scale_factor 放大音高線距
        self.pitch_y_diff = (self.screen_height / 120) * bar_scale_factor

        # 設定 note 厚度 (原為8，這裡放大)
        note_thickness = int(8 * bar_scale_factor)

        # 給予更多底部空間，使 boundary line 往下
        extra_vertical_padding = 200

        # 計算報表需要的總高度
        ref_midi_end_time = self.get_ref_midi_end_time()
        bar_duration = (240 / self.BPM)
        amount_of_bars = int(ref_midi_end_time // bar_duration) + 1
        amount_of_lines = (amount_of_bars // 4) + 1
        self.surface_height = self.y_intercept + self.screen_height * 2 / 3 * (amount_of_lines + 1)

        self.report_surface = pygame.Surface((self.screen_width, self.surface_height))
        self.report_surface.fill((255, 255, 255))  # 白底
        self.scroll_speed = self.screen_height * 2 / 8

        # 報表文字(Performance Metrics等)繪製
        report_lines = self.performance_report.split('\n')
        line_height = 22
        header_y = 20
        for i, line in enumerate(report_lines):
            if line.strip() in ["Performance Metrics", "AI Comments", "Color Representation"]:
                text_surface = self.font_report_title.render(line, True, (0, 0, 0))
            else:
                text_surface = self.font_report.render(line, True, (0, 0, 0))
            self.report_surface.blit(text_surface, (20, header_y + i * line_height))

        #1212: draw ar_vl_plot on the report ui
        if self.ar_vl_path is not None:
            self.ar_vl_plot_loc_x = self.screen_width / 2 + self.screen_width / 32
            self.ar_vl_plot_loc_y = header_y
            self.ar_vl_plot_width = self.screen_width * 0.4
            ar_vl_text_surface = self.font_report_title.render("The Arousal-Valence Model", True, (0, 0, 0))
            self.report_surface.blit(ar_vl_text_surface, (self.ar_vl_plot_loc_x, self.ar_vl_plot_loc_y))

            # Load the ar_vl plot image
        
            self.ar_vl = pygame.image.load(self.ar_vl_path)

            # Get the original dimensions of the logo
            original_width, original_height = self.ar_vl.get_size()

            # Define the desired width or height, maintaining aspect ratio
            desired_width = self.ar_vl_plot_width  # Set your desired width
            scaling_factor = desired_width / original_width
            new_width = int(original_width * scaling_factor)
            new_height = int(original_height * scaling_factor)

            # Resize the ar_vl plot while keeping its shape
            self.ar_vl = pygame.transform.smoothscale(self.ar_vl, (new_width, new_height))
            self.report_surface.blit(self.ar_vl, (self.ar_vl_plot_loc_x, self.ar_vl_plot_loc_y + 40))  # Coordinates (self.screen_width / 2, 10) for some padding from the edges


        # After drawing the report text, we start drawing the notes lower down
        # Move the music visualization down after the report text
        visualize_offset_y = header_y + (len(report_lines) * line_height) + 40
        # Adjust the intercept so that notes start below the report text
        base_y_intercept = self.y_intercept + visualize_offset_y

        mouse_pos = pygame.mouse.get_pos()
        mouse_x, mouse_y = mouse_pos
        mouse_y_adjusted = mouse_y + self.scroll_y  # Adjust for scrolling

        # 將水平滾動區域高度加大一些，讓底部 boundary line 更往下
        self.horizontal_scroll_surface_width = self.screen_width * amount_of_lines * horizontal_length_factor
        self.horizontal_scroll_surface_height = (self.screen_height * 2 / 3 * bar_scale_factor) - 180
        self.horizontal_scroll_surface = pygame.Surface((int(self.horizontal_scroll_surface_width), int(self.horizontal_scroll_surface_height)))
        self.horizontal_scroll_surface.fill((255, 255, 255))  # 白底
        self.horizontal_scroll_speed = self.screen_width * 2 / 8
        self.horizontal_scroll_surface_mouse_pos_rect = pygame.Rect(
            0, visualize_offset_y - self.scroll_y, 
            self.screen_width, (self.screen_height * 2 / 3)
        )

        note_rects = []
        ref_syllables_to_draw = []

        # 繪製 reference notes (灰色) 並放大水平長度
        for pitch, start, end, velocity in self.ref_notes:
            y = (self.screen_height * 2 / 9) - (pitch - 71) * self.pitch_y_diff
            x = self.x_intercept + start * self.scaling_factor * horizontal_length_factor
            width = (end - start) * self.scaling_factor * horizontal_length_factor
            ref_rect = pygame.Rect(x, y, width, note_thickness)
            pygame.draw.rect(self.horizontal_scroll_surface, (210, 210, 210), ref_rect)

            # 預先計算 syllable，稍後最後再畫
            pitch_class = pitch % 12
            syllable = self.pitch_class_to_syllable.get(pitch_class, '')
            if syllable:
                syllable_text_surface = self.font_note.render(syllable, True, (0,0,0))
                # 將文字放在 bar 左側(略向右 2 px)，並垂直置中
                text_x = x + 2
                text_y = y + (note_thickness - syllable_text_surface.get_height()) / 2
                ref_syllables_to_draw.append((syllable_text_surface, text_x, text_y))

        # 繪製 student notes，同樣水平延伸
        for note in self.note_list:
            pitch, start, end, correct, color, velocity = note
            y = (self.screen_height * 2 / 9) - (pitch - 71) * self.pitch_y_diff
            x = self.x_intercept + start * self.scaling_factor * horizontal_length_factor
            width = (end - start) * self.scaling_factor * horizontal_length_factor
            stu_rect = pygame.Rect(x, y, width, note_thickness)
            pygame.draw.rect(self.horizontal_scroll_surface, color, stu_rect)
            note_rects.append((stu_rect, pitch, velocity))

        # 繪製 reference pedal，水平與notes同樣延伸
        # 並將 Y 座標下移 (透過 bar_scale_factor 放大 control_y_diff)
        pedal_y_offset = (self.screen_height * 1 / 9) + (self.control_y_diff * bar_scale_factor)
        first_control = True
        last_control = -1
        pedal_pressed_time = 0
        for number, value, event_time in self.ref_control:
            if number == 64:
                if value == 0: # release
                    if first_control:
                        y1 = pedal_y_offset
                        y2 = y1 + 10
                        x1 = self.x_intercept
                        x2 = self.x_intercept + event_time * self.scaling_factor * horizontal_length_factor
                        points = [(x1, y2), (x2, y2), (x2, y1)]
                        pygame.draw.lines(self.horizontal_scroll_surface, (190, 190, 190), False, points, width=3)
                        first_control = False
                    else:
                        y1 = pedal_y_offset
                        y2 = y1 + 10
                        x1 = self.x_intercept + pedal_pressed_time * self.scaling_factor * horizontal_length_factor
                        x2 = self.x_intercept + event_time * self.scaling_factor * horizontal_length_factor
                        points = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
                        pygame.draw.lines(self.horizontal_scroll_surface, (190, 190, 190), False, points, width=3)
                elif value > 0: # pressed
                    pedal_pressed_time = event_time
                    if first_control:
                        first_control = False
                last_control = value
            else:
                continue

        if last_control > 0: # pedal pressed and unreleased
            y1 = pedal_y_offset
            y2 = y1 + 10
            x1 = self.x_intercept + pedal_pressed_time * self.scaling_factor * horizontal_length_factor
            x2 = self.x_intercept + (bar_duration * 4) * amount_of_lines * self.scaling_factor * horizontal_length_factor
            points = [(x1, y1), (x1, y2), (x2, y2)]
            pygame.draw.lines(self.horizontal_scroll_surface, (190, 190, 190), False, points, width=3)
            
        # Calculate bar duration in seconds (8 beats at 108 BPM)
        bar_duration = 8 * 60 / self.BPM  # 4.444 seconds per bar

        # Draw all bar markers in the horizontal scroll surface
        self.draw_all_bar_markers(
            self.horizontal_scroll_surface,
            bar_duration=bar_duration,
            scaling_factor=self.scaling_factor * horizontal_length_factor,
            x_intercept=self.x_intercept,
            surface_height=self.horizontal_scroll_surface_height
        )

        # Student pedal 同樣延伸與下移
        for pedal in self.pedal_list:
            pedal_start_time, pedal_end_time, correctness, color = pedal
            y1 = pedal_y_offset   # 再略往下移動，和reference pedal有區隔
            y2 = y1 + 10
            x1 = self.x_intercept + pedal_start_time * self.scaling_factor * horizontal_length_factor
            x2 = self.x_intercept + pedal_end_time * self.scaling_factor * horizontal_length_factor
            points = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
            pygame.draw.lines(self.horizontal_scroll_surface, color, False, points, width=3)

        # 繪製 close, print, settings 按鈕
        close_button_x = (self.screen_width - 100) // 4
        close_button_y = self.surface_height - 100
        self.close_button_rect = pygame.Rect(close_button_x, close_button_y, 100, 40)

        print_button_x = (self.screen_width - 100) * 2 // 4
        print_button_y = self.surface_height - 100
        self.print_button_rect = pygame.Rect(print_button_x, print_button_y, 100, 40)

        settings_button_x = (self.screen_width - 100) * 3 // 4
        settings_button_y = self.surface_height - 100
        self.report_settings_button_rect = pygame.Rect(settings_button_x, settings_button_y, 100, 40)

        self.emulate_close_button_rect = pygame.Rect(close_button_x, close_button_y - self.scroll_y, 100, 40)
        self.emulate_print_button_rect = pygame.Rect(print_button_x, print_button_y - self.scroll_y, 100, 40)
        self.emulate_report_settings_button_rect = pygame.Rect(settings_button_x, settings_button_y - self.scroll_y, 100, 40)

        mouse_pos = pygame.mouse.get_pos()
        if self.emulate_close_button_rect.collidepoint(mouse_pos):
            close_color = (173, 216, 230)
        else:
            close_color = (200, 200, 200)

        if self.emulate_print_button_rect.collidepoint(mouse_pos):
            print_color = (173, 216, 230)
        else:
            print_color = (200, 200, 200)

        if self.emulate_report_settings_button_rect.collidepoint(mouse_pos):
            settings_color = (173, 216, 230)
        else:
            settings_color = (200, 200, 200)

        self.draw_button_with_shadow(self.report_surface, self.close_button_rect, "Close", self.font_title, active=False)
        self.draw_button_with_shadow(self.report_surface, self.print_button_rect, "Print", self.font_title, active=False)
        self.draw_button_with_shadow(self.report_surface, self.report_settings_button_rect, "Settings", self.font_title, active=False)

        # 判定滑鼠 hover 在 note 上的 tooltip
        for rect, pitch, velocity in note_rects:
            adjusted_rect = pygame.Rect(rect.x - self.scroll_x, rect.y + visualize_offset_y - self.scroll_y, rect.width, rect.height)
            if adjusted_rect.collidepoint(mouse_pos):
                pitch_class = pitch % 12
                syllable = self.pitch_class_to_syllable.get(pitch_class, '')
                tooltip_text = f"P{pitch} V{velocity} {syllable}"
                self.draw_tooltip(self.horizontal_scroll_surface, tooltip_text, mouse_x + self.scroll_x, mouse_y - visualize_offset_y + self.scroll_y)
                break

        # 最後繪製 reference syllables，確保不被學生音符遮擋
        for syllable_surface, sx, sy in ref_syllables_to_draw:
            self.horizontal_scroll_surface.blit(syllable_surface, (sx, sy))

        #boundary of horizontal scroll surface 調整後下邊界
        testing = True
        if testing:
            pygame.draw.line(self.horizontal_scroll_surface, (0, 0, 0), (0, 0), (self.horizontal_scroll_surface_width, 0), 3)
            pygame.draw.line(
                self.horizontal_scroll_surface, (0, 0, 0),
                (0, self.horizontal_scroll_surface_height - 1),
                (self.horizontal_scroll_surface_width, self.horizontal_scroll_surface_height - 1),
                3
            )

        self.screen.blit(self.report_surface, (0, -self.scroll_y))
        self.screen.blit(self.horizontal_scroll_surface, (-self.scroll_x, visualize_offset_y - self.scroll_y))
