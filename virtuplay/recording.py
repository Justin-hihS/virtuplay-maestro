"""MIDI input capture, metronome and recording lifecycle."""

import threading
import time

import numpy as np
import pygame

from .config import OUTPUT_DIR
from .midi_io import events_to_midi


class RecordingMixin:
    def save_recorded_midi(self, filename):
        """Write the recorded events to ``filename`` and return the mido.MidiFile."""
        if not self.recorded_events:
            print("No MIDI events recorded")
            return None
        midi_file = events_to_midi(self.recorded_events, self.BPM)
        try:
            midi_file.save(filename)
            print(f"Recording saved as {filename} ({len(self.recorded_events)} events, BPM {self.BPM})")
        except Exception as e:
            print(f"Error saving MIDI file: {e}")
        return midi_file

    def setup_midi_recording(self):
        """Initialize MIDI recording"""
        self.recorded_events = []
        self.active_notes = {}
        self.released_notes = []
        self.recording_start_timestamp = time.time()

    def generate_beat_sound(self, frequency=450, duration=0.05, volume=0.5):
        """
        Generate a shorter, crisper metronome sound
        """
        sample_rate = 44100
        num_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        
        # Use a sharper attack and decay for better timing precision
        sine_wave = np.sin(2 * np.pi * frequency * t)
        
        # Create shorter fade in/out for crisper sound
        fade_samples = int(sample_rate * 0.01)  # 10ms fade
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        envelope = np.ones_like(sine_wave)
        envelope[:len(fade_in)] = fade_in
        envelope[-len(fade_out):] = fade_out
        
        smooth_wave = sine_wave * envelope
        
        stereo_wave = np.column_stack((smooth_wave, smooth_wave)) * volume * 32767
        stereo_wave = stereo_wave.astype(np.int16)
        
        return pygame.sndarray.make_sound(stereo_wave)

    def play_metronome(self):
        """
        Improved metronome timing using time-based correction
        """
        beat_interval = 60.0 / self.BPM
        next_beat_time = time.time()
        
        while self.is_playing_metronome:
            current_time = time.time()
            
            if current_time >= next_beat_time:
                self.beat_sound.play()
                # Calculate next beat time based on the original start time
                next_beat_time += beat_interval
                
                # If we're running behind, reset the next beat time
                if current_time > next_beat_time + beat_interval:
                    next_beat_time = current_time + beat_interval
            
            # Shorter sleep interval for more precise timing
            time.sleep(0.001)

    def start_metronome(self):
        if not self.is_playing_metronome:
            self.is_playing_metronome = True
            self.metronome_thread = threading.Thread(target=self.play_metronome)
            self.metronome_thread.daemon = True
            self.metronome_thread.start()

    def stop_metronome(self):
        if self.is_playing_metronome:
            self.is_playing_metronome = False
            if self.metronome_thread.is_alive():
                self.metronome_thread.join()

    def process_midi_input(self):
        if not self.midi_input:
            return
        
        self.start_time = time.time()
        while self.is_recording.is_set():
            if self.midi_input.poll():
                midi_events = self.midi_input.read(10)
                for event in midi_events:
                    status = event[0][0]
                    note_number = event[0][1]
                    velocity = event[0][2]
                    current_time = time.time()
                    timestamp = current_time - self.recording_start_timestamp
                    
                    # 詳細 MIDI 事件結構
                    midi_event = {
                        'type': 'note_on' if status == 144 and velocity > 0 else
                                'note_off' if (status == 128 or (status == 144 and velocity == 0)) else
                                'control_change' if status == 176 else 'other',
                        'note': note_number,
                        'velocity': velocity,
                        'timestamp': timestamp,
                        'status': status
                    }
                    self.recorded_events.append(midi_event)
                    
                    # Note ON 事件
                    if status == 144 and velocity > 0:
                        note_start_time = current_time - self.start_time
                        student_note = (note_number, note_start_time, note_start_time, velocity) # anything related to start, start or start_time, start_time
                        color = self.compare_and_visualize(student_note, self.time_tolerance, self.velocity_tolerance)
                        
                        # 更新 active_notes
                        self.active_notes[note_number] = {
                            'start_time': note_start_time,
                            'velocity': velocity,
                            'correct': color == self.colors['correct']
                        }
                        
                        # 檢查是否應該產生煙霧效果
                        if self.is_note_at_target_line(note_number):
                            self.should_smoke[note_number] = True
                        
                    # Note OFF 事件
                    elif status == 128 or (status == 144 and velocity == 0):
                        if note_number in self.active_notes:
                            self.active_notes.pop(note_number)
                            if note_number in self.should_smoke:
                                del self.should_smoke[note_number]
                    
                    # Control Change 事件 #changelog1127 : added back control changes
                    elif status == 176 and velocity >= 0:
                         if note_number == 64:  # Pedal
                            if velocity > 0:  # Pedal pressed
                                self.student_control_pressed_time = timestamp
                            elif velocity == 0:  # Pedal released
                                control_end_time = timestamp
                                control_start_time = self.student_control_pressed_time
                                if self.student_control_pressed_time >= 0:
                                    self.compare_pedal_and_visulaize((control_start_time, control_end_time))
                        
            time.sleep(0.001)

    def toggle_recording(self):
        if self.is_recording.is_set():
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Start recording with proper initialization"""
        
        self.current_combo = 0
        self.max_combo = 0
        
        self.note_list.clear()
        self.pedal_list.clear()
        self.should_smoke = {}  # 重置煙霧效果追踪
        self.student_control_pressed_time = -1
        self.student_notes.clear()
        self.bar_scores.clear()
        self.overall_score = {'pitch': 0, 'velocity': 0, 'timing': 0, 'count': 0, 'note_count': 0, 'duration': 0}
        self.performance_report = ""
        self.is_recording.set()
        
        # Initialize MIDI recording
        self.setup_midi_recording()
        
        # Play countdown beats
        countdown_start = time.time()
        beat_interval = 60.0 / self.BPM
        
        for i in range(4, -1, -1):  # Countdown from 4 to 1
            self.show_countdown(i)  # Show dots for the countdown
            while time.time() < countdown_start + ((4 - i) * beat_interval):
                time.sleep(0.001)
            self.beat_sound.play()
            self.hide_countdown()  # Hide previous dots after each beat

        # Start recording time and threads
        self.recording_start_time = pygame.time.get_ticks()
        self.recording_start_timestamp = time.time()
        
        # **Initialize falling notes start time**
        self.falling_notes_start_time = time.time()
        
        self.start_metronome()
        
        # Start MIDI processing thread
        self.midi_thread = threading.Thread(target=self.process_midi_input)
        self.midi_thread.daemon = True
        self.midi_thread.start()

    def stop_recording(self):
        """Stop recording and save MIDI file"""
        self.is_recording.clear()
        self.stop_metronome()
        
        # **Reset falling notes start time**
        self.falling_notes_start_time = None
        
        # Wait for threads to finish
        if self.midi_thread:
            self.midi_thread.join()
            self.midi_thread = None
            
        # Save the recorded MIDI file
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        filename = str(OUTPUT_DIR / f"performance_{timestamp}.mid")
        self.student_midi_file = self.save_recorded_midi(filename)
        
        # Generate performance report
        self.re_adjust_note_list()
        self.generate_performance_report()
        self.generate_overall_comment()
        if self.student_midi_file is not None:
            self.ar_vl_path = self.generate_ar_vl_path()
        else:
            print("ERROR: Student performance did not write to file")
        print(self.performance_report)

    def find_note_segment_off(self, note_pitch, note_time):#pitch, start
        temp_segment = [x for x in self.recorded_events if x["timestamp"] > note_time and x["type"] == "note_off" and x["note"] == note_pitch]
        if(len(temp_segment)==0):
            return None
        minObject = min(temp_segment, key=lambda x:x["timestamp"])
        return minObject

    def re_adjust_note_list(self):
        temp_note_list = []
        for note in self.note_list:
            pitch, start, end, correct, color, velocity = note
            temp = self.find_note_segment_off(pitch, start)
            if temp != None:
                new_end = temp["timestamp"]
            else:
                new_end = end
            temp_note_list.append((pitch, start, new_end, correct, color, velocity))
        self.note_list = temp_note_list
