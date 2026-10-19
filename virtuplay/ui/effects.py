"""Particle effects, the astronaut GIF and the combo counter."""

import random
import time

import imageio
import pygame
from PIL import Image

from .particles import FireParticle, Particle, TargetLineParticle


class EffectsMixin:
    def load_and_resize_gif(self, gif_path, desired_width):
        """
        Load a GIF, resize each frame to the desired width, and return the frames and their durations.
        """
        gif = imageio.mimread(gif_path, memtest=False)
        gif_reader = imageio.get_reader(gif_path)
        gif_meta = gif_reader.get_meta_data()

        # Ensure gif_durations is a list
        gif_duration = gif_meta.get('duration', 100)  # Default duration: 100ms
        gif_durations = [gif_duration] * len(gif) if isinstance(gif_duration, int) else gif_duration

        # Adjust the frame durations to make the GIF play faster
        speed_factor = 1  # Increase this value to make the GIF faster
        adjusted_gif_durations = [max(1, int(duration / speed_factor)) for duration in gif_durations]

        resized_frames = []
        for frame in gif:
            # Convert frame to a PIL image for better compatibility
            pil_frame = Image.fromarray(frame).convert("RGBA")
            scaling_factor = desired_width / pil_frame.width
            new_width = int(pil_frame.width * scaling_factor)
            new_height = int(pil_frame.height * scaling_factor)

            # Resize the frame
            resized_pil_frame = pil_frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert back to a Pygame surface
            frame_surface = pygame.image.fromstring(resized_pil_frame.tobytes(), resized_pil_frame.size, "RGBA")
            resized_frames.append(frame_surface)

        return resized_frames, adjusted_gif_durations

    def generate_fire_particles(self):
        if self.current_combo >= 10:
            x, y = self.combo_position
            # Generate multiple particles per frame for a denser effect
            for _ in range(2):
                self.fire_particles.append(FireParticle(x, y + 20))  # Slightly adjust y if needed

    def update_and_draw_fire_particles(self):
        for particle in self.fire_particles[:]:
            particle.update()
            if particle.is_alive():
                # Create a surface for each particle with per-pixel alpha
                particle_surface = pygame.Surface((particle.radius * 2, particle.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surface,
                    particle.color,
                    (particle.radius, particle.radius),
                    int(particle.radius)
                )
                # Blit the particle onto the main screen
                self.screen.blit(
                    particle_surface,
                    (particle.x - particle.radius, particle.y - particle.radius),
                    special_flags=pygame.BLEND_ADD
                )
            else:
                self.fire_particles.remove(particle)
        # Limit the total number of particles to prevent performance issues
        MAX_FIRE_PARTICLES = 500
        if len(self.fire_particles) > MAX_FIRE_PARTICLES:
            self.fire_particles = self.fire_particles[-MAX_FIRE_PARTICLES:]

    def draw_gif(self):
        """
        Draw the current frame of the GIF and update the frame based on timing.
        The GIF is stuck at the first frame when combo is under 15, and animates when combo is 15 or more.
        """
        if self.current_combo < 10:
            # Combo is less than 15, show the first frame only
            frame_to_display = self.gif_frames[161]
        else:
            # Combo is 15 or greater, animate the GIF
            current_time = pygame.time.get_ticks()
            if current_time - self.gif_last_update > self.gif_durations[self.current_frame_index]:
                self.current_frame_index = (self.current_frame_index + 1) % len(self.gif_frames)
                self.gif_last_update = current_time
            frame_to_display = self.gif_frames[self.current_frame_index]

        # Draw the frame at the desired position
        self.screen.blit(frame_to_display, self.gif_position)

    def draw_smoke_effect(self, x, y, key_width):
        """
        Generate smoke effect evenly across the key's width.
        """
        # Increase particle generation rate for continuous smoke effect
        for _ in range(12):  # Increased from 8 to 12 for denser smoke
            # Randomly position particles across the entire width of the key
            particle_x = x + random.uniform(0, key_width)
            # Add some vertical variation for a more natural effect
            particle_y = y - 10 + random.uniform(-5, 5)
            self.particles.append(Particle(particle_x, particle_y))

    def draw_combo(self):
        combo_text = f"{self.current_combo}"
        x, y = self.combo_position

        # 基礎字體大小與最大字體大小
        base_font_size = 30
        max_font_size = 100  # 定義最大字體大小

        # 根據 combo 數值調整字體大小
        if self.current_combo > 10:
            # 超過 10 後字體隨 combo 增大
            dynamic_font_size = min(base_font_size + (self.current_combo - 10) * 2, max_font_size)
        else:
            # combo ≤ 10 使用基礎字體大小
            dynamic_font_size = base_font_size

        # 動態縮放效果
        if self.combo_last_increase_time is not None:
            elapsed_time = time.time() - self.combo_last_increase_time
            shrink_duration = 0.15  # 縮放效果的持續時間
            if elapsed_time < shrink_duration:
                # 計算縮放比例，基於 ease-out 動畫效果
                t = elapsed_time / shrink_duration
                scale = 0.8 + 0.2 * t * (2 - t)  # Ease-out quadratic
                font_size = int(dynamic_font_size * scale)
            else:
                font_size = dynamic_font_size
        else:
            font_size = dynamic_font_size

        # 主字體
        main_font = pygame.font.SysFont("Verdana", font_size, bold=True)

        # 設定字體顏色
        if self.current_combo < 10:
            main_color = (138, 212, 250)  # 淺藍色
        else:
            main_color = (246, 201, 162)  # 淺橘色

        glow_color = (255, 0, 0)  # 紅色發光效果

        # 創建發光效果
        glow_layers = 15
        for i in range(glow_layers, 0, -1):
            glow_font_size = font_size + i * 2
            glow_font = pygame.font.SysFont("Terminal", int(glow_font_size), bold=True)
            glow_surface = glow_font.render(combo_text, True, glow_color)

            alpha = int(50 / i)
            glow_surface.set_alpha(alpha)

            glow_rect = glow_surface.get_rect(center=(x, y))
            self.screen.blit(glow_surface, glow_rect)

        # 繪製主字體
        main_surface = main_font.render(combo_text, True, main_color)
        main_rect = main_surface.get_rect(center=(x, y))
        self.screen.blit(main_surface, main_rect)

    def draw_smoke_layer(self):
        """
        Draw a semi-transparent smoke layer that fades out over time.
        """
        smoke_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        smoke_surface.fill((50, 50, 50, 30))  # Dark gray with low opacity
        self.screen.blit(smoke_surface, (0, 0))

    def update_smoke_particles(self):
        """
        Update and render smoke particles with improved visual effects.
        """
        for particle in self.particles[:]:
            particle.update()
            if particle.is_alive():
                # Create a surface for each particle with per-pixel alpha
                particle_surface = pygame.Surface((particle.radius * 2, particle.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surface,
                    particle.color,
                    (particle.radius, particle.radius),
                    int(particle.radius)
                )
                # Blit the particle onto the main screen with additive blending for a glowing effect
                self.screen.blit(
                    particle_surface,
                    (particle.x - particle.radius, particle.y - particle.radius),
                    special_flags=pygame.BLEND_ADD
                )
            else:
                self.particles.remove(particle)
        
        # Limit the total number of particles to prevent performance issues
        MAX_PARTICLES = 500
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

    def draw_target_line_smoke_effect(self):
        """
        Generate a continuous, subtle smoking effect along the target line.
        """
        # Fewer particles for a lighter effect
        for _ in range(8):
            particle_x = random.uniform(0, self.screen_width)
            # Lower vertical variation
            particle_y = self.target_line_y + random.uniform(-2, 20)
            self.particles.append(TargetLineParticle(particle_x, particle_y))
