"""Particle systems for smoke and fire effects."""

import random


class FireParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-15, 15)  # Slight horizontal spread
        self.y = y + random.uniform(0, 1)   # Start slightly below the combo position
        self.radius = random.uniform(1, 6)
        self.color = (255, random.randint(100, 150), 0, 255)  # Orange to yellow colors
        self.velocity_x = random.uniform(-0.5, 0.5)
        self.velocity_y = random.uniform(-1.5, -3.0)  # Upward movement
        self.alpha_decay = random.uniform(2, 5)
        self.radius_decay = random.uniform(0.05, 0.1)
        self.lifespan = random.randint(30, 60)

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += 0.05  # Gravity effect
        new_alpha = max(0, self.color[3] - self.alpha_decay)
        self.color = (
            self.color[0],
            self.color[1],
            self.color[2],
            new_alpha
        )
        self.radius = max(0, self.radius - self.radius_decay)
        self.lifespan -= 1

    def is_alive(self):
        return self.lifespan > 0 and self.color[3] > 0 and self.radius > 0





class TargetLineParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Smaller radius range for more subtle effect
        self.radius = random.uniform(1, 2.5)
        
        # Lighter gray with higher transparency for subtle smoke
        self.color = (150, 150, 150, 100)
        
        # Slower horizontal movement
        self.velocity_x = random.uniform(-0.15, 0.15)
        
        # Slower upward movement with lower height
        self.velocity_y = random.uniform(-0.6, -0.3)
        
        # Slower fade for longer-lasting effect
        self.alpha_decay = random.uniform(0.3, 0.8)
        
        # Slower size reduction
        self.radius_decay = 0.02
        
        # Longer lifespan to compensate for slower movement
        self.lifespan = random.randint(90, 150)

    def update(self):
        # Slower movement
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Very slight gravity effect
        self.velocity_y += 0.002
        
        # Gradual fade
        new_alpha = max(0, self.color[3] - self.alpha_decay)
        self.color = (
            self.color[0],
            self.color[1],
            self.color[2],
            new_alpha
        )
        
        # Gradual size reduction
        self.radius = max(0.5, self.radius - self.radius_decay)
        
        # Decrease lifespan
        self.lifespan -= 1

    def is_alive(self):
        return self.color[3] > 0 and self.radius > 0.5 and self.lifespan > 0


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.uniform(2, 5)  # More precise control over size
        self.color = (105, 105, 105, 200)  # Dark gray with higher transparency for smoke
        self.velocity_x = random.uniform(-0.3, 0.3)  # Slight horizontal movement
        self.velocity_y = random.uniform(-1.5, -0.8)  # Faster upward movement
        self.alpha_decay = random.uniform(0.5, 1.5)  # Smooth fading
        self.radius_decay = 0.05  # Slight radius reduction
        self.lifespan = random.randint(60, 120)  # Frames before the particle disappears

    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        # Apply a slight gravity effect to slow upward movement over time
        self.velocity_y += 0.005
        # Fade the particle
        new_alpha = max(0, self.color[3] - self.alpha_decay)
        self.color = (
            self.color[0],
            self.color[1],
            self.color[2],
            new_alpha
        )
        # Reduce the radius to simulate dissipation
        self.radius = max(1, self.radius - self.radius_decay)
        # Decrease lifespan
        self.lifespan -= 1

    def is_alive(self):
        return self.color[3] > 0 and self.radius > 1 and self.lifespan > 0

