""""""

import threading
from collections import defaultdict

import pygame
import pygame.font
import pygame.midi

from .config import DEFAULT_BPM, DEFAULT_REFERENCE, GIF_PATH, LOGO_PATH
from .evaluation import EvaluationMixin
from .recording import RecordingMixin
from .ui.effects import EffectsMixin
from .ui.menus import MenusMixin
from .ui.practice_view import PracticeViewMixin
from .ui.report_view import ReportViewMixin
from .ui.widgets import WidgetsMixin


class DynamicMusicSheet(
    EvaluationMixin,
    RecordingMixin,
    PracticeViewMixin,
    ReportViewMixin,
    MenusMixin,
    EffectsMixin,
    WidgetsMixin,
):
    """Main application: practice view, live scoring and the performance report."""

    def __init__(self, reference_path=DEFAULT_REFERENCE, bpm=DEFAULT_BPM):
        # Screen Info Initialization
        pygame.init()
        pygame.font.init()
        screen_info = pygame.display.Info()
        self.screen_width, self.screen_height = screen_info.current_w, screen_info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Dynamic Music Sheet - Real-time Visualization")
        
        # Load the logo image
        self.logo = pygame.image.load(str(LOGO_PATH))

        # Get the original dimensions of the logo
        original_width, original_height = self.logo.get_size()

        # Define the desired width or height, maintaining aspect ratio
        desired_width = 225  # Set your desired width
        scaling_factor = desired_width / original_width
        new_width = int(original_width * scaling_factor)
        new_height = int(original_height * scaling_factor)

        # Resize the logo while keeping its shape
        self.logo = pygame.transform.smoothscale(self.logo, (new_width, new_height))


        
        self.particles = []  # List to hold active particles
        self.should_smoke = {}  # 新增：追踪哪些音符應該產生煙霧效果

        
        # Tolerance Param Initialization
        self.time_tolerance = 0.2
        self.velocity_tolerance = 20
        self.pedal_tolerance = 0.2
        self.pedal_start_tolerance = 2  # New tolerance for pedal start time
        self.pedal_duration_tolerance = 0.2

        # Scoring-related initialization
        self.bar_scores = defaultdict(lambda: {'pitch': 0, 'velocity': 0, 'timing': 0, 'count': 0, 'duration': 0})
        self.overall_score = {'pitch': 0, 'velocity': 0, 'timing': 0, 'count': 0, 'note_count': 0}
        # note count is the amount of all notes, 
        # count is the amount of correct notes
        
        self.performance_report = ""
        
        # Add a new attribute for the close button
        self.close_button_rect = None
        self.showing_report = False
        
        # Midi Input Info Initialization
        pygame.midi.init()
        try:
            self.midi_input = pygame.midi.Input(pygame.midi.get_default_input_id())
        except pygame.midi.MidiException:
            print("No MIDI input device found!")
            self.midi_input = None
        
        # Modified MIDI recording attributes
        self.recorded_events = []
        self.recording_start_timestamp = None
        self.active_notes = {}  # Track currently active notes
        self.released_notes = []  # Track recently released notes for visualization
        
        # Midi Details Initialization
        self.BPM = bpm
        self.ticks_per_beat = 480
        self.ticks_per_second = (self.ticks_per_beat * self.BPM) / 60
        self.student_notes = {}
        self.student_control_pressed_time = -1
        self.note_list = []
        self.pedal_list = []
        self.midi_thread = None
        self.start_time = None
        self.is_recording = threading.Event()
        
        # Reference Midi File Initialization
        self.reference_path = str(reference_path)

        self.ref_notes, self.ref_control = self.load_reference_midi(self.reference_path)
        self.total_duration = max([end for _, _, end, _ in self.ref_notes])

        # Set fixed keyboard range from A0 to C8 (MIDI notes 21 to 108)
        self.min_pitch = 21  # A0
        self.max_pitch = 108  # C8
        self.total_keys = self.max_pitch - self.min_pitch + 1  # 88 keys

        # Attempt to use system font
        self.font_title = pygame.font.SysFont("Verdana", 15, bold = True)
        self.font_report_title = pygame.font.SysFont("Verdana", 30, bold = True) # changed 1204
        self.font_note = pygame.font.SysFont("Verdana", 13)
        self.font_report = pygame.font.SysFont("Verdana", 18)#1218
        self.legend_font = pygame.font.SysFont(None, 22)

        # Test font availability
        if not pygame.font.match_font("Verdana"):
            print("Verdana font not found, using default font.")
            self.font_title = pygame.font.Font(None, 20)
            self.font_report_title = pygame.font.Font(None, 56)
            self.font_note = pygame.font.Font(None, 7)
            self.font_report = pygame.font.Font(None, 7)
        
        self.setup_ui_elements()
        
        # Metronome Initialization
        self.metronome_duration = 0.1
        self.beat_sound = self.generate_beat_sound(duration=self.metronome_duration)
        self.is_playing_metronome = False
        self.metronome_thread = None
        self.bpm_text = ''
        self.time_tolerance_text = ''
        self.bpm_input_active = False  # To track if BPM input is active
        self.time_tolerance_input_active = False  # To track if time tolerance input is active
        self.show_settings_menu = False  # To track if settings menu is open

        # Notes Colors Initialization
        self.colors = {
            'correct': (144, 238, 144),  # light green
            'incorrect': (255, 0, 0),    # red
            'too_hard': (255, 255, 0),   # yellow
            'too_light': (0, 255, 255)   # cyan
        }

        # Notes Legend Initialization
        self.legends = [
            ("Correct", self.colors['correct']),
            ("Incorrect", self.colors['incorrect']),
            ("Too hard", self.colors['too_hard']),
            ("Too light", self.colors['too_light']),
            (f"Time tolerance: {self.time_tolerance:.2f}s", (150, 150, 150)),
            (f"Velocity tolerance: {self.velocity_tolerance}", (150, 150, 150)),
            (f"Pedal tolerance: {self.pedal_start_tolerance:.2f}s", (150, 150, 150))
        ]

        # Overall Comment Initialization
        self.student_midi_file = None
        self.overall_comment = ""

        # Initialize falling notes start time
        self.falling_notes_start_time = None
        
        self.erased_notes = {}  # Tracks notes being erased (key: note_number, value: True)
        
        self.reference_pitch = 60  # MIDI pitch for C4 (middle C)
        self.show_syllables = True
        # Add this in the __init__ method of DynamicMusicSheet
        self.pitch_class_to_syllable = {
            0: 'Do',   # C
            2: 'Re',   # D
            4: 'Mi',   # E
            5: 'Fa',   # F
            7: 'So',   # G
            9: 'La',   # A
            11: 'Si'   # B
        }

        
        #target line
        self.target_line_y = self.screen_height - 200
        
        self.control_y_diff = (self.screen_height / 4) + (self.screen_height / 12)

        

        # Load and prepare GIF
        self.gif_path = str(GIF_PATH)
        self.gif_frames, self.gif_durations = self.load_and_resize_gif(self.gif_path, desired_width=180)
        self.current_frame_index = 0
        self.gif_last_update = pygame.time.get_ticks()
        self.gif_display_width = 180
        self.gif_position = (self.screen_width - self.gif_display_width - 10, 220)  # Right side, near the top

        self.clock = pygame.time.Clock()
        
        self.current_combo = 0  # Tracks the current combo
        self.max_combo = 0      # Tracks the maximum combo achieved
        self.combo_position = (self.screen_width - self.gif_display_width+76, 210)  # Position for the combo display
        self.font_combo = pygame.font.SysFont("Terminal", 18, bold = True)  # Font for the combo display
        #self.combo_position = (self.screen_width - self.gif_display_width // 2 - 10, 240)
        
        self.combo_last_increase_time = None
        self.fire_particles = []  # List to hold fire particles
        
        self.show_combo = True  # 是否顯示 combo 數字
        self.show_gif = True  # 是否顯示 GIF 動畫
        self.animation_menu_active = False  # 是否顯示動畫設定菜單
        ...
        self.animation_button_rect = pygame.Rect(
            10, 70 + 4 * (self.button_height + self.button_spacing), 120, self.button_height
        )

        # variables for scrollable report
        self.scroll_y = 0
        self.surface_height = 0
        self.scroll_speed = 0
        self.print_button_rect = None
        self.report_surface = None
        self.emulate_close_button_rect = None
        self.emulate_print_button_rect = None
        self.y_intercept = self.screen_height/2
        self.x_intercept = self.screen_width/10
        self.scaling_factor = 1.3 * 1000 // (self.screen_width/self.BPM)
        self.showing_report_settings_menu = False  # To track if settings menu is open
        self.report_time_tolerance_text = ''
        self.report_velocity_tolerance_text = ''
        self.report_time_tolerance_input_active = False  # To track if BPM input is active
        self.report_velocity_tolerance_input_active = False  # To track if time tolerance input is active
        self.scroll_x = 0 #for the horizontal scrollable report notes

        #1212: making the ar_vl_plot
        self.ar_vl_path = None

        #fixing duration score
        self.ref_duration_list = []

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            self.screen_width, self.screen_height = pygame.display.get_surface().get_size()

            self.target_line_y = self.screen_height - 200

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    if self.record_button_rect.collidepoint(mouse_pos) and not self.show_settings_menu and not self.animation_menu_active:
                        self.toggle_recording()
                        if not self.is_recording.is_set():
                            self.showing_report = True
                            #self.re_adjust_note_list() # moved to stop_recording()
                            self.report_compare_with_tolerance(self.time_tolerance, self.velocity_tolerance) #compare note_list with tolerance to get new color

                    elif self.showing_report and not self.showing_report_settings_menu:#main/report #draw_report
                        if self.emulate_close_button_rect.collidepoint(mouse_pos): #close button
                            self.showing_report = False
                            self.reset_for_new_session()

                        elif self.emulate_print_button_rect.collidepoint(mouse_pos): #print button
                            print("clicked")
                            self.save_content_to_pdf(self.report_surface)

                        elif self.emulate_report_settings_button_rect.collidepoint(mouse_pos): # settings button
                            self.showing_report_settings_menu = True
                            self.report_time_tolerance_input_active = False
                            self.report_velocity_tolerance_input_active = False
                            self.report_time_tolerance_text = str(self.time_tolerance)
                            self.report_velocity_tolerance_text = str(self.velocity_tolerance)
                            

                    elif self.showing_report and self.showing_report_settings_menu: #main/report/settings #draw_report_settings
                        if self.report_time_tolerance_input_rect.collidepoint(mouse_pos): #main/report/settings/timetolerance
                            self.report_time_tolerance_input_active = True
                            self.report_velocity_tolerance_input_active = False

                        elif self.report_velocity_tolerance_input_rect.collidepoint(mouse_pos): #main/report/settings/timetolerance
                            self.report_time_tolerance_input_active = False
                            self.report_velocity_tolerance_input_active = True

                        elif self.report_ok_button_rect.collidepoint(mouse_pos):
                            try:
                                new_time_tolerance = float(self.report_time_tolerance_text)
                                new_velocity_tolerance = float(self.report_velocity_tolerance_text)
                                #self.update_bpm_and_tolerance(new_bpm, new_time_tolerance)
                                self.report_settings_update_both_tolerance(new_time_tolerance, new_velocity_tolerance)
                                self.report_compare_with_tolerance(self.time_tolerance, self.velocity_tolerance) #compare note_list with new tolerance to get new color
                            except ValueError:
                                print("Invalid input for BPM or time tolerance.")
                            self.showing_report_settings_menu = False

                        elif self.report_cancel_button_rect.collidepoint(mouse_pos):
                            self.showing_report_settings_menu = False
                            self.report_time_tolerance_input_active = False
                            self.report_velocity_tolerance_input_active = False

                    elif self.show_button_rect.collidepoint(mouse_pos) and not self.show_settings_menu and not self.animation_menu_active:
                        self.showing_report = not self.showing_report
                    elif self.settings_button_rect.collidepoint(mouse_pos) and not self.show_settings_menu and not self.animation_menu_active:
                        self.show_settings_menu = True
                        self.bpm_input_active = False
                        self.time_tolerance_input_active = False
                        self.bpm_text = str(self.BPM)
                        self.time_tolerance_text = str(self.time_tolerance)
                    elif self.syllable_button_rect.collidepoint(mouse_pos) and not self.animation_menu_active:
                        self.show_syllables = not self.show_syllables
                    elif self.animation_button_rect.collidepoint(mouse_pos):
                        self.animation_menu_active = True
                    elif self.show_settings_menu:
                        if self.bpm_input_rect.collidepoint(mouse_pos):
                            self.bpm_input_active = True
                            self.time_tolerance_input_active = False
                        elif self.tolerance_input_rect.collidepoint(mouse_pos):
                            self.time_tolerance_input_active = True
                            self.bpm_input_active = False
                        elif self.ok_button_rect.collidepoint(mouse_pos):
                            try:
                                new_bpm = int(self.bpm_text)
                                new_time_tolerance = float(self.time_tolerance_text)
                                self.update_bpm_and_tolerance(new_bpm, new_time_tolerance)
                            except ValueError:
                                print("Invalid input for BPM or time tolerance.")
                            self.show_settings_menu = False
                        elif self.cancel_button_rect.collidepoint(mouse_pos):
                            self.show_settings_menu = False
                            self.bpm_input_active = False
                            self.time_tolerance_input_active = False
                elif event.type == pygame.KEYDOWN:
                    if self.show_settings_menu:
                        if self.bpm_input_active:
                            self.handle_text_input(event, target="bpm")
                        elif self.time_tolerance_input_active:
                            self.handle_text_input(event, target="time_tolerance")
                    elif self.showing_report and self.showing_report_settings_menu:
                        if self.report_time_tolerance_input_active:
                            self.handle_text_input(event, target="report_settings_time_tolerance")
                        elif self.report_velocity_tolerance_input_active:
                            self.handle_text_input(event, target="report_settings_velocity_tolerance")

                elif event.type == pygame.MOUSEWHEEL:
                    mouse_pos = pygame.mouse.get_pos()
                    #horizontal_scroll_surface_mouse_pos_rect
                    if self.showing_report:
                        if self.horizontal_scroll_surface_mouse_pos_rect.collidepoint(mouse_pos):
                            self.scroll_x -= event.y * self.horizontal_scroll_speed
                            self.scroll_x = max(0, min(self.scroll_x, self.horizontal_scroll_surface_width - self.screen_width))  # Keep scroll within bounds
                        else:
                            self.scroll_y -= event.y * self.scroll_speed
                            self.scroll_y = max(0, min(self.scroll_y, self.surface_height - self.screen_height))  # Keep scroll within bounds

            # 清空畫面
            self.screen.fill((0, 0, 0))
            
            # Display the logo in the top-left corner
            self.screen.blit(self.logo, (0, 0))  # Coordinates (10, 10) for some padding from the edges
            
            # 更新和繪製火焰粒子
            if self.show_combo:
                self.update_and_draw_fire_particles()

            # 繪製鋼琴鍵盤和其他視覺效果
            self.draw_piano_keyboard()
            self.draw_visualization()
            self.draw_dynamic_line()
            
            # 繪製 GIF
            if self.show_gif:
                self.draw_gif()

            # 繪製 combo 數字
            if self.show_combo:
                self.generate_fire_particles()
                self.draw_combo()

            # 顯示按鈕
            mouse_pos = pygame.mouse.get_pos()
            record_text = "Stop" if self.is_recording.is_set() else "Start"
            record_active = self.record_button_rect.collidepoint(mouse_pos)
            self.draw_button_with_shadow(self.screen, self.record_button_rect, record_text, self.font_title, active=record_active)

            show_text = "Show" if not self.showing_report else "UnShow"
            show_active = self.show_button_rect.collidepoint(mouse_pos)
            self.draw_button_with_shadow(self.screen, self.show_button_rect, show_text, self.font_title, active=show_active)

            settings_active = self.settings_button_rect.collidepoint(mouse_pos)
            self.draw_button_with_shadow(self.screen, self.settings_button_rect, "Settings", self.font_title, active=settings_active)

            syllable_text = "Hide Syllables" if self.show_syllables else "Show Syllables"
            syllable_active = self.syllable_button_rect.collidepoint(mouse_pos)
            self.draw_button_with_shadow(self.screen, self.syllable_button_rect, syllable_text, self.font_title, active=syllable_active)

            animation_active = self.animation_button_rect.collidepoint(mouse_pos)
            self.draw_button_with_shadow(self.screen, self.animation_button_rect, "Animation", self.font_title, active=animation_active)
            
            # Draw BPM and Time Tolerance labels
            bpm_label = self.font_title.render(f"BPM: {self.BPM}", True, (255, 255, 255))
            self.screen.blit(bpm_label, (self.settings_button_rect.left + 10, self.settings_button_rect.bottom + 90))

            tolerance_label = self.font_title.render(f"Time Tolerance: {self.time_tolerance:.2f} sec", True, (255, 255, 255))
            self.screen.blit(tolerance_label, (self.settings_button_rect.left + 10, self.settings_button_rect.bottom + 110))

            # 顯示動畫選單
            if self.animation_menu_active:
                self.draw_animation_menu()

            # 畫出設定和報告
            if self.showing_report:
                self.draw_report()
                if self.showing_report_settings_menu:
                    self.draw_report_settings_menu()
            if self.show_settings_menu:
                self.draw_settings_menu()

            pygame.display.flip()
            clock.tick(60)

        self.stop_recording()
        if self.midi_input:
            self.midi_input.close()
        pygame.quit()

    def reset_for_new_session(self):
        self.bar_scores.clear()
        self.overall_score = {'pitch': 0, 'velocity': 0, 'timing': 0, 'count': 0, 'note_count': 0, 'duration': 0}
        self.note_list.clear()
        self.pedal_list.clear()
        self.student_control_pressed_time = -1
        self.falling_notes_start_time = None
