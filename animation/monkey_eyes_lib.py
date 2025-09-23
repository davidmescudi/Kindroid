import math
import multiprocessing
import queue
import random
import os
import pygame
import signal

"""
Annalisa Comin
https://github.com/Annalisa11/monkey/tree/master
https://github.com/Annalisa11/monkey/blob/master/robot-eyes/monkey_eyes_lib.py
Monkey Eyes Animation System - Library Version

Classes:
- Eye: Represents a single eye with drawing and transformation methods.
- EyePair: Manages and draws a pair of eyes.
- AnimationState: Enumeration of possible animation states.
- AnimationManager: Controls different animation states and transitions.
- MonkeyEyeApp: Main application class (runs in a separate process).
- EyesController: Interface for controlling the MonkeyEyeApp externally.
"""

class Eye:
    """
    Represents a single eye with position, size, and rendering logic.

    Args:
        x (int): X (left) position of the eye.
        y (int): Y (top) position of the eye.
        width (int): Width of the eye.
        height (int): Height of the eye.
        radius (int): Border radius for rounded corners.
        color (tuple): RGB color of the eye.
    """
    def __init__(self, x, y, width, height, radius=30, color=(0, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.original_rect = pygame.Rect(x, y, width, height)
        self.radius = radius
        self.color = color
        self.original_color = color

    def draw(self, screen):
        """Draws the eye as a rounded rectangle."""
        pygame.draw.rect(screen, self.color, self.rect, border_radius=self.radius)

    def grow(self, width, height):
        """Inflates (or shrinks) the eye by width and height."""
        self.rect.inflate_ip(width, height)

    def move(self, x, y):
        """Moves the eye position by the given x and y offsets."""
        self.rect.move_ip(x, y)

    def reset_position(self):
        """Resets the eye to its original position."""
        self.rect.x = self.original_rect.x
        self.rect.y = self.original_rect.y

    def reset_size(self):
        """Resets the eye to its original width and height."""
        self.rect.width = self.original_rect.width
        self.rect.height = self.original_rect.height

    def reset(self):
        """Resets both position and size of the eye."""
        self.reset_position()
        self.reset_size()

    def get_center(self):
        """Returns the (x, y) center of the eye."""
        return (self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2)

    def draw_circular(self, screen, background_color, vertical_offset=0, overlay_circle_offset=150):
        """
        Draws the eye as a circular laughing/smiling representation.
        """
        center_x, center_y = self.get_center()
        center_y += vertical_offset
        radius = self.rect.height // 2
        
        pygame.draw.circle(screen, self.color, (center_x, center_y), radius)
        pygame.draw.circle(screen, background_color, (center_x, center_y + overlay_circle_offset), radius + 60)

    def draw_star(self, screen, color=(255, 255, 0), scale=1.0):
        """
        Draws a star shape within the eye area.
        """
        cx, cy = self.get_center()
        radius = min(self.rect.width, self.rect.height) // 2 * scale
        inner_radius = radius * 0.4
        
        points = []
        for i in range(10):
            angle = math.pi * 2 * i / 10 - math.pi / 2
            current_radius = radius if i % 2 == 0 else inner_radius
            x = cx + current_radius * math.cos(angle)
            y = cy + current_radius * math.sin(angle)
            points.append((x, y))
        
        if len(points) > 2:
            pygame.draw.polygon(screen, color, points)

    def draw_loader(self, screen, angle, color=(255, 255, 255), width=15):
        """
        Draws a spinning loader arc inside the eye.
        """
        center = self.get_center()
        radius = min(self.rect.width, self.rect.height) // 3
        
        # Draw the background of the eye
        self.draw(screen)

        # Define the rectangle for the arc
        arc_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
        
        # Calculate start and end angles for the arc
        start_angle = math.radians(angle)
        end_angle = math.radians(angle + 270) # Draw a 270-degree arc
        
        # Draw the arc
        pygame.draw.arc(screen, color, arc_rect, start_angle, end_angle, width)

    def draw_error(self, screen, eye_color=(255, 0, 0), x_color=(255, 255, 255), x_width=20):
        """
        Draws the eye with a red background and a white X.
        """
        # Zeichne den roten Hintergrund
        pygame.draw.rect(screen, eye_color, self.rect, border_radius=self.radius)

        # Berechne die Punkte für das X
        center_x, center_y = self.get_center()
        size = self.rect.width // 4 # Größe des X basierend auf der Augengröße

        # Zeichne die beiden Linien für das X
        start_pos1 = (center_x - size, center_y - size)
        end_pos1 = (center_x + size, center_y + size)
        pygame.draw.line(screen, x_color, start_pos1, end_pos1, x_width)

        start_pos2 = (center_x + size, center_y - size)
        end_pos2 = (center_x - size, center_y + size)
        pygame.draw.line(screen, x_color, start_pos2, end_pos2, x_width)

class EyePair:
    """
    Manages a pair of eyes and their expressions.
    """
    def __init__(self, left_x, right_x, y, width, height, distance, radius=30, color=(0, 0, 0), background_color=(255,255, 255), star_color=(255, 255, 0), loader_color=(255, 255, 0)):
        self.left_eye = Eye(left_x, y, width, height, radius, color)
        self.right_eye = Eye(right_x, y, width, height, radius, color)
        self.distance = distance
        self.background_color = background_color
        self.star_color = star_color
        self.loader_color = loader_color

    def draw_normal(self, screen):
        self.left_eye.draw(screen)
        self.right_eye.draw(screen)

    def draw_laughing(self, screen, vertical_offset=0):
        self.left_eye.draw_circular(screen, self.background_color, vertical_offset)
        self.right_eye.draw_circular(screen, self.background_color, vertical_offset)
    
    def draw_smiling(self, screen):
        self.left_eye.draw_circular(screen, self.background_color, 10) 
        self.right_eye.draw_circular(screen, self.background_color, 10)

    def draw_stars(self, screen, scale=1.0):
        self.left_eye.draw_star(screen, self.star_color, scale)
        self.right_eye.draw_star(screen, self.star_color, scale)
    
    def draw_loading(self, screen, angle):
        """Draws the loading animation on both eyes."""
        self.left_eye.draw_loader(screen, angle, self.loader_color)
        self.right_eye.draw_loader(screen, angle, self.loader_color)

    def draw_error(self, screen):
        """Draws the error animation on both eyes."""
        error_eye_color = (200, 0, 0)
        x_color = (255, 255, 255)
        self.left_eye.draw_error(screen, error_eye_color, x_color)
        self.right_eye.draw_error(screen, error_eye_color, x_color)

    def reset(self):
        self.left_eye.reset()
        self.right_eye.reset()


class AnimationState:
    IDLE = "idle"
    BLINKING = "blinking"
    LAUGHING = "laughing"
    SMILING = "smiling"
    STAR = "star"
    MOVING = "moving"
    CONCENTRATING = "concentrating"
    LOADING = "loading"
    ERROR = "error"
    LISTENING = "listening"


class AnimationManager:
    def __init__(self, eye_pair):
        self.eye_pair = eye_pair
        self.current_state = AnimationState.IDLE
        self.previous_state = AnimationState.IDLE
        
        self.current_time = 0 
        self.animation_start_time = 0
        
        # Blinking 
        self.shrinking = True
        self.blink_speed = 20
        self.last_blink_time = 0 
        self.blink_interval = random.uniform(2000, 4000)
        self.blink_type = "single"  # "single" or "double", single as default
        self.current_blink_count = 0
        self.target_blink_count = 1
        self.blink_pause_start_time = 0
        self.blink_paused = False
        self.blink_pause_duration = 150  
        
        # Laughing 
        self.laugh_up = True
        self.laugh_speed = 2
        self.laugh_offset = 0
        self.max_laugh_offset = 20
        self.laugh_cycle_count = 0
        
        # Smiling 
        self.smile_start_time = 0
        self.smile_duration = 2000 
        
        # Star 
        self.star_start_time = 0
        self.star_duration = 3000 
        self.star_growing = True
        self.star_scale = 0.0
        self.star_speed = 0.05
        
        # Movement 
        self.move_speed = 10
        self.max_move_distance = 200
        self.squinting_degree = 5
        self.last_look_time = 0 
        self.look_interval = random.uniform(10000, 20000)
        self.looking_direction = 1
        self.moving_away = True
        self.look_paused = False
        self.look_pause_start_time = 0

        # Concentrate
        self.concentrate_duration = 2000 
        self.concentrate_start_time = 0
        self.concentrate_indefinite = False

        # Loading
        self.loader_angle = 0
        self.loader_speed = 5 # Degrees per frame

        # Error
        self.error_start_time = 0
        self.error_duration = 3000
        self.error_indefinite = False

        # Listening
        self.listening_color = (0,255,150)
        self.listening_dark_color = (0, 150, 90)
        self.listening_start_time = 0
        self.listening_pulse_speed = 1.5
        self.listening_size_amplitude = 25

        # Not Listening
        self.not_listening_active = False
        self.not_listening_color = (255, 0, 0)

    def update(self, current_time_ticks):
        self.current_time = current_time_ticks
        
        if self.current_state == AnimationState.IDLE:
            if self.current_time - self.last_blink_time > self.blink_interval:
                self.trigger_blinking()
            # elif self.current_time - self.last_look_time > self.look_interval:
                # self.trigger_look()
        
        if self.current_state == AnimationState.LAUGHING:
            self._animate_laugh()
        elif self.current_state == AnimationState.SMILING:
            if self._check_timed_animation_completed(self.smile_start_time, self.smile_duration):
                self.set_state(AnimationState.IDLE)
        elif self.current_state == AnimationState.STAR:
            self._animate_star()
        elif self.current_state == AnimationState.MOVING:
            self._animate_sideways_look(self.looking_direction)
        elif self.current_state == AnimationState.CONCENTRATING:
            self._animate_concentrate()
        elif self.current_state == AnimationState.BLINKING:
            self._animate_blink()
        elif self.current_state == AnimationState.LOADING:
            self._animate_loading()
        elif self.current_state == AnimationState.ERROR:
            self._animate_error()
        elif self.current_state == AnimationState.LISTENING:
            self._animate_listening()

        if self.not_listening_active:
            self.eye_pair.left_eye.color = self.not_listening_color
            self.eye_pair.right_eye.color = self.not_listening_color

    def set_state(self, new_state):
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.animation_start_time = self.current_time
            
            # TODO: Besprechen ob korrekt
            if self.previous_state != AnimationState.IDLE and new_state == AnimationState.IDLE:
                 # Reset only when transitioning to IDLE from a non-IDLE state,
                 # and not from another active animation to IDLE (which might manage its own reset)
                self.eye_pair.reset()
            elif self.previous_state != AnimationState.IDLE and self.previous_state != new_state:
                 # Reset if switching between two different active animations
                self.eye_pair.reset()

    
    def _check_timed_animation_completed(self, start_time, duration):
        if self.current_state == AnimationState.CONCENTRATING and self.concentrate_indefinite:
            return False
        return self.current_time - start_time > duration
    
    def trigger_laugh(self):
        self.set_state(AnimationState.LAUGHING)
        self.laugh_up = True
        self.laugh_cycle_count = 0
        self.laugh_offset = 0
    
    def trigger_smile(self, duration=None):
        self.set_state(AnimationState.SMILING)
        self.smile_start_time = self.current_time
        self.smile_duration = duration if duration is not None else 2000

    def trigger_concentrate(self, duration=None, indefinite=False):
        self.set_state(AnimationState.CONCENTRATING)
        self.concentrate_start_time = self.current_time
        self.concentrate_indefinite = indefinite
        self.shrinking = True 
        self.concentrate_duration = duration if duration is not None and not indefinite else 2000
    
    def stop_concentrate(self):
        if self.current_state == AnimationState.CONCENTRATING: 
            if self.concentrate_indefinite:
                self.concentrate_indefinite = False
                # Force completion by setting start time such that duration is exceeded
                self.concentrate_start_time = self.current_time - (self.concentrate_duration + 1)
            else: 
                self.concentrate_start_time = self.current_time - (self.concentrate_duration + 1)

    def trigger_star(self, duration=None):
        self.set_state(AnimationState.STAR)
        self.star_start_time = self.current_time
        self.star_growing = True
        self.star_scale = 0.0
        self.star_duration = duration if duration is not None else 3000
    
    def trigger_blinking(self):
        if self.current_state == AnimationState.IDLE:
            self.set_state(AnimationState.BLINKING)
            self.shrinking = True
            self.last_blink_time = self.current_time 
            self.blink_interval = random.uniform(3000, 8000)
            
            self.blink_type = random.choices(["single", "double"], weights=[3, 1])[0]
            self.target_blink_count = 1 if self.blink_type == "single" else 2
            self.current_blink_count = 0
            self.blink_paused = False

    def trigger_look(self):
        if self.current_state == AnimationState.IDLE:
            self.set_state(AnimationState.MOVING)
            self.moving_away = True
            self.looking_direction = random.choice([1, -1])
            self.look_paused = False
            self.last_look_time = self.current_time 
            self.look_interval = random.uniform(10000, 20000)

    def trigger_loading(self):
        self.set_state(AnimationState.LOADING)
        self.loader_angle = 0

    def stop_loading(self):
        if self.current_state == AnimationState.LOADING:
            self.set_state(AnimationState.IDLE)

    def trigger_error(self, duration=None, indefinite=False):
        self.set_state(AnimationState.ERROR)
        self.error_start_time = self.current_time
        self.error_indefinite = indefinite
        self.error_duration = duration if duration is not None and not indefinite else 3000

    def stop_error(self):
        if self.current_state == AnimationState.ERROR:
            self.set_state(AnimationState.IDLE)

    def trigger_listening(self):
        if self.current_state != AnimationState.LISTENING:
            self.eye_pair.left_eye.original_color = self.eye_pair.left_eye.color
            self.eye_pair.right_eye.original_color = self.eye_pair.right_eye.color
            
            self.set_state(AnimationState.LISTENING)
            
            self.eye_pair.left_eye.color = self.listening_color
            self.eye_pair.right_eye.color = self.listening_color

    def stop_listening(self):
        if self.current_state == AnimationState.LISTENING:
            self.eye_pair.reset()
            self.eye_pair.left_eye.color = self.eye_pair.left_eye.original_color
            self.eye_pair.right_eye.color = self.eye_pair.right_eye.original_color
            self.set_state(AnimationState.IDLE)

    def start_not_listening(self):
        self.not_listening_active = True
    
    def stop_not_listening(self):
        self.not_listening_active = False
        self.eye_pair.reset()
        self.eye_pair.left_eye.color = self.eye_pair.left_eye.original_color
        self.eye_pair.right_eye.color = self.eye_pair.right_eye.original_color

    def _animate_blink(self):
        if self.blink_paused:
            if self.current_time - self.blink_pause_start_time > self.blink_pause_duration:
                self.blink_paused = False
                self.shrinking = True 
            return
        
        if self.shrinking:
            self.eye_pair.left_eye.grow(0, -self.blink_speed)
            self.eye_pair.right_eye.grow(0, -self.blink_speed)
            if self.eye_pair.left_eye.rect.height <= 10:
                self.shrinking = False
        else:
            self.eye_pair.left_eye.grow(0, self.blink_speed)
            self.eye_pair.right_eye.grow(0, self.blink_speed)
            if self.eye_pair.left_eye.rect.height >= self.eye_pair.left_eye.original_rect.height:
                self.current_blink_count += 1
                
                if self.current_blink_count < self.target_blink_count:
                    self.eye_pair.reset()
                    self.blink_paused = True
                    self.blink_pause_start_time = self.current_time
                else:
                    self.eye_pair.reset() 
                    self.set_state(AnimationState.IDLE)
    
    def _animate_concentrate(self):
        if self.shrinking:
            self.eye_pair.left_eye.grow(0, -self.blink_speed) 
            self.eye_pair.right_eye.grow(0, -self.blink_speed)
            if self.eye_pair.left_eye.rect.height <= 60: 
                self.shrinking = False 
        else: # Not shrinking: either holding or expanding
            is_timed_out = self._check_timed_animation_completed(self.concentrate_start_time, self.concentrate_duration)
            
            if not self.concentrate_indefinite and is_timed_out:
                # Time to expand and finish
                self.eye_pair.left_eye.grow(0, self.blink_speed)
                self.eye_pair.right_eye.grow(0, self.blink_speed)
                if self.eye_pair.left_eye.rect.height >= self.eye_pair.left_eye.original_rect.height:
                    self.eye_pair.reset()
                    self.set_state(AnimationState.IDLE)
            elif self.concentrate_indefinite:
                # Holding indefinitely, do nothing until stop_concentrate is called
                pass
            # Else, it's timed but not yet timed out, so still holding.

    def _animate_laugh(self):
        if self.laugh_up:
            self.laugh_offset += self.laugh_speed
            if self.laugh_offset >= self.max_laugh_offset:
                self.laugh_up = False
        else:
            self.laugh_offset -= self.laugh_speed
            if self.laugh_offset <= 0:
                self.laugh_up = True
                self.laugh_cycle_count += 1
                if self.laugh_cycle_count >= 4: 
                    self.set_state(AnimationState.IDLE)
    
    def _animate_star(self):
        time_elapsed = self.current_time - self.star_start_time
        
        if self.star_growing and time_elapsed > self.star_duration / 2.0 :
            self.star_growing = False 

        if self.star_growing:
            self.star_scale += self.star_speed
            if self.star_scale >= 1.0:
                self.star_scale = 1.0
        else: 
            self.star_scale -= self.star_speed
            if self.star_scale <= 0.0:
                self.star_scale = 0.0
                self.set_state(AnimationState.IDLE) 

    def _animate_loading(self):
        self.loader_angle = (self.loader_angle + self.loader_speed) % 360
    
    def _animate_error(self):
        if not self.error_indefinite:
            if self.current_time - self.error_start_time > self.error_duration:
                self.set_state(AnimationState.IDLE)
    
    def _animate_listening(self):
        elapsed_time = (self.current_time - self.listening_start_time) / 1000.0
        
        # Sinus-Welle für eine sanfte Oszillation (Wertebereich -1 bis 1)
        # (pulse + 1) / 2 skaliert den Bereich auf 0.0 bis 1.0
        pulse_factor = (math.sin(elapsed_time * self.listening_pulse_speed) + 1) / 2.0
        
        # Berechne Farbänderung
        new_color_components = []
        for start_comp, end_comp in zip(self.listening_color, self.listening_dark_color):
            comp = start_comp + (end_comp - start_comp) * pulse_factor
            new_color_components.append(int(comp))
    
        new_color = tuple(new_color_components)
        
        for eye in [self.eye_pair.left_eye, self.eye_pair.right_eye]:
            size_offset = self.listening_size_amplitude * pulse_factor
            new_width = eye.original_rect.width + int(size_offset)
            new_height = eye.original_rect.height + int(size_offset)
            
            eye.rect = pygame.Rect(0, 0, new_width, new_height)
            
            eye.rect.center = eye.original_rect.center
            
            eye.color = new_color
    
    def _animate_sideways_look(self, direction):
        left_eye = self.eye_pair.left_eye
        right_eye = self.eye_pair.right_eye
        original_left_x = left_eye.original_rect.x
        original_height = left_eye.original_rect.height
        
        if self.look_paused:
            if self.current_time - self.look_pause_start_time > 1000:
                self.look_paused = False
            return 

        if self.moving_away:
            left_eye.move(self.move_speed * direction, 0)
            right_eye.move(self.move_speed * direction, 0)
            
            current_distance = abs(left_eye.rect.x - original_left_x)
            if current_distance < 100:
                if left_eye.rect.height > original_height - 40:
                    left_eye.grow(0, -self.squinting_degree)
                    right_eye.grow(0, -self.squinting_degree)
            else:
                if left_eye.rect.height < original_height:
                    left_eye.grow(0, self.squinting_degree)
                    right_eye.grow(0, self.squinting_degree)
                if direction > 0: right_eye.grow(4, 4)
                else: left_eye.grow(4, 4)
            
            if current_distance >= self.max_move_distance: 
                self.moving_away = False
                self.look_pause_start_time = self.current_time
                self.look_paused = True
        else: 
            move_back_direction = -1 if left_eye.rect.x > original_left_x else 1
            
            dist_to_origin = abs(left_eye.rect.x - original_left_x)
            if dist_to_origin < self.move_speed:
                 left_eye.rect.x = original_left_x
                 right_eye.rect.x = right_eye.original_rect.x 
            else:
                left_eye.move(self.move_speed * move_back_direction, 0)
                right_eye.move(self.move_speed * move_back_direction, 0)
            
            if left_eye.rect.height < original_height: left_eye.grow(0, self.squinting_degree)
            if right_eye.rect.height < original_height: right_eye.grow(0, self.squinting_degree)
            
            if direction > 0 and right_eye.rect.width > right_eye.original_rect.width: right_eye.grow(-2, -2)
            elif direction < 0 and left_eye.rect.width > left_eye.original_rect.width: left_eye.grow(-2, -2)
            
            if abs(left_eye.rect.x - original_left_x) < self.move_speed : 
                self.eye_pair.reset()
                self.set_state(AnimationState.IDLE)


class MonkeyEyeApp:
    def __init__(self, command_queue):
        self.command_queue = command_queue
        self.screen = None
        self.clock = None
        self.background_color = (0, 0, 0)
        self.eyes = None
        self.animation = None
        
        self.screen_width = 1280
        self.screen_height = 720
        self.eye_width = 250
        self.eye_height = 250
        self.eye_distance = 300
        self.eye_radius = 30
        self.eye_color = (133, 242, 239)
        self.star_color = self.eye_color

        self.eye_y_offset = 100
        self.eye_x_offset = 70

    def _initialize_pygame_and_eyes(self):
        os.environ['DISPLAY'] = ':0'
        pygame.init()
        infoObject = pygame.display.Info()
        # Get Resolution from display
        self.screen_width = infoObject.current_w
        self.screen_height = infoObject.current_h

        #Hide mouse cursor
        pygame.mouse.set_visible(False)
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        #self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Monkey Eyes Animation")
        self.clock = pygame.time.Clock()
        
        center_x = self.screen_width // 2
        eye_y = self.screen_height // 2 - self.eye_height // 2 - self.eye_y_offset
        eye_left_x = center_x - self.eye_width - (self.eye_distance // 2) + self.eye_x_offset
        eye_right_x = center_x + (self.eye_distance // 2) - self.eye_x_offset
        
        self.eyes = EyePair(
            eye_left_x, eye_right_x, eye_y, 
            self.eye_width, self.eye_height, self.eye_distance, 
            self.eye_radius, self.eye_color, self.background_color, self.star_color
        )
        self.animation = AnimationManager(self.eyes)
        
        current_ticks = pygame.time.get_ticks()
        self.animation.last_blink_time = current_ticks
        self.animation.last_look_time = current_ticks

    def _process_command(self, command_str):
        parts = command_str.split(':')
        cmd = parts[0]
        args = parts[1:]

        if cmd == "laugh": self.animation.trigger_laugh()
        elif cmd == "smile":
            duration = int(args[0]) if args and args[0].isdigit() else None
            self.animation.trigger_smile(duration=duration)
        elif cmd == "star":
            duration = int(args[0]) if args and args[0].isdigit() else None
            self.animation.trigger_star(duration=duration)
        elif cmd == "concentrate":
            if args and args[0] == "indefinite":
                self.animation.trigger_concentrate(indefinite=True)
            else:
                duration = int(args[0]) if args and args[0].isdigit() else None
                self.animation.trigger_concentrate(duration=duration, indefinite=False)
        elif cmd == "stop_concentrate": self.animation.stop_concentrate()
        elif cmd == "loading": self.animation.trigger_loading()
        elif cmd == "stop_loading": self.animation.stop_loading()
        elif cmd == "error":
            if args and args[0] == "indefinite":
                self.animation.trigger_error(indefinite=True)
            else:
                duration = int(args[0]) if args and args[0].isdigit() else None
                self.animation.trigger_error(duration=duration, indefinite=False)
        elif cmd == "stop_error": self.animation.stop_error()
        elif cmd == "listening": self.animation.trigger_listening()
        elif cmd == "stop_listening": self.animation.stop_listening()
        elif cmd == "start_not_listening": self.animation.start_not_listening()
        elif cmd == "stop_not_listening": self.animation.stop_not_listening()
        else: print(f"EyeApp: Unknown command: {command_str}")

    def run_app_loop(self):
        self._initialize_pygame_and_eyes()
        running = True
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while running:
            current_ticks = pygame.time.get_ticks()
            try:
                while not self.command_queue.empty():
                    command_str = self.command_queue.get_nowait()
                    if command_str == "quit": running = False; break
                    self._process_command(command_str)
            except queue.Empty: pass
            if not running: break

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
            if not running: break

            self.animation.update(current_ticks)
            
            self.screen.fill(self.background_color)
            current_state = self.animation.current_state
            if current_state == AnimationState.LAUGHING:
                self.eyes.draw_laughing(self.screen, self.animation.laugh_offset)
            elif current_state == AnimationState.SMILING:
                self.eyes.draw_smiling(self.screen)
            elif current_state == AnimationState.STAR:
                self.eyes.draw_stars(self.screen, self.animation.star_scale)
            elif current_state == AnimationState.LOADING:
                self.eyes.draw_loading(self.screen, self.animation.loader_angle)
            elif current_state == AnimationState.ERROR:
                self.eyes.draw_error(self.screen)
            else: 
                self.eyes.draw_normal(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

class EyesController:
    """
    Manages and controls the Monkey Eyes animation program, which runs in a
    separate process.

    This controller provides a simple interface to start, stop, and trigger
    various emotional animations (like laughing, smiling, concentrating, etc.)
    for a pair of "monkey eyes" displayed in a dedicated Pygame window.

    Example:
        >>> controller = EyesController()
        >>> controller.start_eyes()
        >>> # Eyes window appears
        >>> controller.trigger_smile(duration_ms=3000)
        >>> # Eyes smile for 3 seconds
        >>> controller.stop_eyes()
        >>> # Eyes window closes
    """
    def __init__(self):
        self.command_queue = None
        self.eye_process = None

    def start_eyes(self):
        """
        Starts the Monkey Eyes animation program in a separate process.

        A new window will be created to display the eye animations. If the
        eye animation program is already running, this method will print a
        message and do nothing.

        The eye process is started as a daemon, meaning it will automatically
        terminate if the main program exits.
        """
        if self.eye_process and self.eye_process.is_alive():
            print("EyesController: Eyes are already running.")
            return
        self.command_queue = multiprocessing.Queue()
        app_instance = MonkeyEyeApp(self.command_queue)
        self.eye_process = multiprocessing.Process(target=app_instance.run_app_loop)
        self.eye_process.daemon = True 
        self.eye_process.start()
        print("EyesController: Monkey Eyes program started.")

    def stop_eyes(self):
        """
        Stops the Monkey Eyes animation program and closes its window.

        This method sends a 'quit' command to the eye animation process
        and waits for it to terminate. If the process does not stop
        gracefully within a short timeout, it will be forcibly terminated.

        If the eye program is not running, this method will print a message
        and do nothing.
        """
        if not self.eye_process or not self.eye_process.is_alive():
            print("EyesController: Eyes are not running or already stopped.")
            return
        if self.command_queue:
            try: self.command_queue.put("quit")
            except Exception as e: print(f"EyesController: Error sending quit command: {e}")
        if self.eye_process:
            self.eye_process.join(timeout=3) 
            if self.eye_process.is_alive():
                print("EyesController: Eye process did not terminate gracefully, attempting to terminate.")
                self.eye_process.terminate()
                self.eye_process.join(timeout=1) 
        self.eye_process = None
        self.command_queue = None
        print("EyesController: Monkey Eyes program stopped.")

    def _send_command(self, command_str):
        if not self.command_queue or (self.eye_process and not self.eye_process.is_alive()):
            print(f"EyesController: Cannot send '{command_str}'. Eyes not running or queue unavailable.")
            return
        try: self.command_queue.put(command_str)
        except Exception as e: print(f"EyesController: Error sending '{command_str}': {e}")

    def trigger_laugh(self):
        """
        Triggers the laughing animation.

        The eyes will laugh for a predefined number of cycles.
        """ 
        self._send_command("laugh")
    def trigger_smile(self, duration_ms=None):
        """
        Triggers the smiling animation.

        The animation lasts for a specified duration, after which the eyes
        return to their idle state.

        Args:
            duration_ms (int, optional): The duration of the smile animation
                in milliseconds. If None, a default duration (e.g., 2000ms)
                defined within the animation logic will be used.
        """
        cmd = f"smile:{duration_ms}" if duration_ms is not None else "smile"
        self._send_command(cmd)
    def trigger_star(self, duration_ms=None):
        """
        Triggers the star-eyes animation in the Monkey Eyes program.

        The entire animation (grow and shrink) lasts for the specified duration.

        Args:
            duration_ms (int, optional): The total duration of the star
                animation in milliseconds. If None, a default duration
                (e.g., 3000ms) defined within the animation logic will be used.
        """
        cmd = f"star:{duration_ms}" if duration_ms is not None else "star"
        self._send_command(cmd)
    def trigger_concentrate(self, duration_ms=None, indefinite=False):
        """
        Triggers the concentrating (squinting) animation in the Monkey Eyes program.

        The animation can be set for a specific duration or indefinitely until stopped.

        Args:
            duration_ms (int, optional): The duration of the concentrate
                animation in milliseconds. This parameter is ignored if
                `indefinite` is True. If None and `indefinite` is False,
                a default duration (e.g., 2000ms) will be used.
            indefinite (bool, optional): If True, the eyes will remain in the
                concentrated state until `stop_concentrate()` is called.
                Defaults to False.
        """
        if indefinite: cmd = "concentrate:indefinite"
        elif duration_ms is not None: cmd = f"concentrate:{duration_ms}"
        else: cmd = "concentrate"
        self._send_command(cmd)
    def stop_concentrate(self): 
        """
        Stops an ongoing 'concentrate' animation.

        If the concentration animation was triggered with `indefinite=True`,
        this method will cause the eyes to return to their normal idle state.
        If it was a timed concentration, this will end it prematurely.
        """
        self._send_command("stop_concentrate")

    def trigger_loading(self):
        """
        Triggers the loading (spinning circle) animation.

        The animation will continue indefinitely until `stop_loading()` is called.
        """
        self._send_command("loading")

    def stop_loading(self):
        """
        Stops the loading animation and returns the eyes to the idle state.
        """
        self._send_command("stop_loading")

    def trigger_error(self, duration_ms=None, indefinite=False):
        """
        Triggers the error (red eyes with an X) animation.

        The animation can be set for a specific duration or indefinitely until stopped.

        Args:
            duration_ms (int, optional): The duration of the error animation
                in milliseconds. Ignored if `indefinite` is True. Defaults to 3000ms.
            indefinite (bool, optional): If True, the eyes remain in the error
                state until `stop_error()` is called. Defaults to False.
        """
        if indefinite:
            cmd = "error:indefinite"
        elif duration_ms is not None:
            cmd = f"error:{duration_ms}"
        else:
            cmd = "error"
        self._send_command(cmd)

    def stop_error(self):
        """
        Stops an ongoing 'error' animation.
        """
        self._send_command("stop_error")
    
    def trigger_listening(self):
        """
        Triggers the listening animation, where the eyes pulse and change color.

        The animation will continue indefinitely until `stop_listening()` is called.
        """
        self._send_command("listening")

    def stop_listening(self):
        """
        Stops the listening animation and returns the eyes to their idle state.
        """
        self._send_command("stop_listening")

    def start_not_listening(self):
        """
        Triggers the not listening animation, where the eyes turn red.

        The animation will continue indefinitely until `stop_not_listening()` is called.
        """
        self._send_command("start_not_listening")
    
    def stop_not_listening(self):
        """
        Stops the not listening animation and returns the eyes to their idle state.
        """
        self._send_command("stop_not_listening")