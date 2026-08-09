#!/usr/bin/env python3
"""
Hollow Knight-inspired game with a silk-based character
Run as: python main.py
Or compile to exe with: pyinstaller --onefile --windowed --icon=icon.ico main.py
"""

import pygame
import sys
import math
import random
import os

# Initialize Pygame
pygame.init()
# Try to initialize mixer, but continue if it fails (for headless systems)
try:
    pygame.mixer.init()
except:
    pass

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FULLSCREEN = False

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Silk Knight")
clock = pygame.time.Clock()

# Colors (City of Tears inspired palette)
DARK_BLUE = (20, 30, 60)
MEDIUM_BLUE = (40, 60, 100)
LIGHT_BLUE = (80, 120, 160)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SILK_COLOR = (200, 200, 220)
CAPE_COLOR = (10, 20, 50)
WATER_COLOR = (60, 100, 140)
HP_BAR_BG = (60, 20, 20)
HP_BAR_FG = (200, 50, 50)
COOLDOWN_BG = (40, 40, 60)
COOLDOWN_FG = (100, 200, 255)
SILK_BAR_BG = (40, 60, 40)
SILK_BAR_FG = (200, 220, 255)
GLASS_COLOR = (180, 200, 220)
BENCH_COLOR = (139, 90, 43)

# Game constants
GRAVITY = 0.6
PLAYER_SPEED = 5
JUMP_FORCE = -12
MAX_SILK = 100
SILK_JUMP_COST = 15
DASH_COOLDOWN = 200  # milliseconds
DASH_SPEED = 15
DASH_DURATION = 150  # milliseconds

# Animation paths
ANIM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "animations")


def load_animation_frames(anim_name):
    """Load animation frames from files or return None if not found"""
    frames = []
    if anim_name == "walk":
        for i in range(1, 5):
            filename = os.path.join(ANIM_DIR, f"walk{i}.png")
            if os.path.exists(filename):
                try:
                    frame = pygame.image.load(filename).convert_alpha()
                    frames.append(frame)
                except:
                    pass
    else:
        filename = os.path.join(ANIM_DIR, f"{anim_name}.png")
        if os.path.exists(filename):
            try:
                frame = pygame.image.load(filename).convert_alpha()
                frames.append(frame)
            except:
                pass
    return frames if frames else None


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 60
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.hp = 100
        self.max_hp = 100
        self.silk = MAX_SILK
        self.facing_right = True
        self.radius = 20  # Head radius - FIXES THE ERROR
        self.horn_length = 15
        self.cape_width = 8
        self.in_water = False
        self.jump_count = 0
        self.max_jumps = 1
        
        # Dash
        self.dash_cooldown_timer = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_direction = 1
        
        # Silk thread attack
        self.silk_thread_active = False
        self.silk_thread_x = 0
        self.silk_thread_y = 0
        self.silk_thread_width = 0
        self.silk_thread_duration = 0
        
        # Animation
        self.anim_frame = 0
        self.anim_timer = 0
        self.current_anim = "stand"
        self.is_sitting = False
        self.sitting_timer = 0
        
        # Load animations
        self.animations = {
            "sit": load_animation_frames("sit"),
            "stand": load_animation_frames("stand"),
            "walk": load_animation_frames("walk")
        }
    
    def get_rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2, 
                          self.width, self.height)
    
    def draw(self, surface):
        # If sitting on bench, use sit animation or draw sitting pose
        if self.is_sitting:
            if self.animations["sit"]:
                frame = self.animations["sit"][0]
                surface.blit(frame, (self.x - frame.get_width()//2, self.y - frame.get_height()//2))
            else:
                # Draw sitting pose manually
                self._draw_sitting(surface)
            return
        
        # Use loaded animations if available
        if self.current_anim == "walk" and self.animations["walk"]:
            frame_idx = self.anim_frame % len(self.animations["walk"])
            frame = self.animations["walk"][frame_idx]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.x - frame.get_width()//2, self.y - frame.get_height()//2))
            return
        elif self.current_anim == "stand" and self.animations["stand"]:
            frame = self.animations["stand"][0]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.x - frame.get_width()//2, self.y - frame.get_height()//2))
            return
        
        # Default procedural drawing if no animations loaded
        self._draw_procedural(surface)
    
    def _draw_sitting(self, surface):
        # Draw cape (very narrow dark blue)
        cape_x = self.x - (5 if self.facing_right else -5)
        cape_rect = pygame.Rect(cape_x - self.cape_width//2, self.y - 5, 
                               self.cape_width, self.height - 25)
        pygame.draw.rect(surface, CAPE_COLOR, cape_rect)
        
        # Draw body (white, connected to head) - sitting position
        body_rect = pygame.Rect(self.x - 15, self.y - 5, 30, 25)
        pygame.draw.ellipse(surface, WHITE, body_rect)
        
        # Draw head (white circle)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y - 20)), self.radius)
        
        # Draw horns (white, curved like goat horns, no separation from head)
        horn_color = WHITE
        left_horn_points = [
            (self.x - 12, self.y - 30),
            (self.x - 18, self.y - 40),
            (self.x - 14, self.y - 45),
            (self.x - 8, self.y - 35)
        ]
        pygame.draw.polygon(surface, horn_color, left_horn_points)
        
        right_horn_points = [
            (self.x + 12, self.y - 30),
            (self.x + 18, self.y - 40),
            (self.x + 14, self.y - 45),
            (self.x + 8, self.y - 35)
        ]
        pygame.draw.polygon(surface, horn_color, right_horn_points)
        
        # Draw eyes (black voids)
        eye_offset = 5 if self.facing_right else -5
        pygame.draw.circle(surface, BLACK, (int(self.x - 6 + eye_offset), int(self.y - 17)), 4)
        pygame.draw.circle(surface, BLACK, (int(self.x + 6 + eye_offset), int(self.y - 17)), 4)
    
    def _draw_procedural(self, surface):
        # Draw cape (very narrow dark blue)
        cape_x = self.x - (5 if self.facing_right else -5)
        cape_rect = pygame.Rect(cape_x - self.cape_width//2, self.y - 10, 
                               self.cape_width, self.height - 20)
        pygame.draw.rect(surface, CAPE_COLOR, cape_rect)
        
        # Draw body (white, connected to head)
        body_rect = pygame.Rect(self.x - 15, self.y - 10, 30, 35)
        pygame.draw.ellipse(surface, WHITE, body_rect)
        
        # Draw head (white circle)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y - 25)), self.radius)
        
        # Draw horns (white, curved like goat horns, no separation from head)
        horn_color = WHITE
        # Left horn
        left_horn_points = [
            (self.x - 12, self.y - 35),
            (self.x - 18, self.y - 45),
            (self.x - 14, self.y - 50),
            (self.x - 8, self.y - 40)
        ]
        pygame.draw.polygon(surface, horn_color, left_horn_points)
        
        # Right horn
        right_horn_points = [
            (self.x + 12, self.y - 35),
            (self.x + 18, self.y - 45),
            (self.x + 14, self.y - 50),
            (self.x + 8, self.y - 40)
        ]
        pygame.draw.polygon(surface, horn_color, right_horn_points)
        
        # Draw eyes (black voids)
        eye_offset = 5 if self.facing_right else -5
        pygame.draw.circle(surface, BLACK, (int(self.x - 6 + eye_offset), int(self.y - 22)), 4)
        pygame.draw.circle(surface, BLACK, (int(self.x + 6 + eye_offset), int(self.y - 22)), 4)
        
        # Draw silk thread if active
        if self.silk_thread_active:
            pygame.draw.line(surface, SILK_COLOR, 
                           (self.silk_thread_x, self.silk_thread_y),
                           (self.silk_thread_x + self.silk_thread_width, self.silk_thread_y), 3)
    
    def update(self, keys, platforms, water_rect, bench_rect=None):
        # Handle sitting on bench
        if self.is_sitting:
            self.sitting_timer -= clock.get_time()
            if self.sitting_timer <= 0:
                self.is_sitting = False
            # Regenerate HP while sitting
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + 0.5)
            return
        
        # Check if near bench and press UP to sit
        if bench_rect:
            player_rect = self.get_rect()
            if player_rect.colliderect(bench_rect.inflate(20, 10)) and keys[pygame.K_UP]:
                if self.on_ground or player_rect.bottom >= bench_rect.top - 5:
                    self.is_sitting = True
                    self.sitting_timer = 5000  # Sit for 5 seconds max
                    self.x = bench_rect.centerx
                    self.y = bench_rect.top - self.height // 2
                    self.vel_x = 0
                    self.vel_y = 0
                    return
        
        # Update animation state
        if not self.on_ground:
            self.current_anim = "stand"
        elif abs(self.vel_x) > 0.5:
            self.current_anim = "walk"
            self.anim_timer += clock.get_time()
            if self.anim_timer > 100:  # Change frame every 100ms
                self.anim_frame += 1
                self.anim_timer = 0
        else:
            self.current_anim = "stand"
        
        # Handle dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= clock.get_time()
        if self.is_dashing:
            self.dash_timer -= clock.get_time()
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vel_x = 0
        
        # Handle silk thread duration
        if self.silk_thread_active:
            self.silk_thread_duration -= clock.get_time()
            if self.silk_thread_duration <= 0:
                self.silk_thread_active = False
        
        # Horizontal movement
        if not self.is_dashing:
            self.vel_x = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -PLAYER_SPEED
                self.facing_right = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = PLAYER_SPEED
                self.facing_right = True
        
        # Apply gravity (unless in water)
        if self.in_water:
            self.vel_y *= 0.95  # Water resistance
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y -= 0.5
        else:
            self.vel_y += GRAVITY
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Check water collision
        player_rect = self.get_rect()
        self.in_water = player_rect.colliderect(water_rect) and player_rect.centery > water_rect.top + 10
        
        # Platform collision
        self.on_ground = False
        if not self.in_water:
            for platform in platforms:
                plat_rect = pygame.Rect(platform[0], platform[1], platform[2], platform[3])
                if player_rect.colliderect(plat_rect):
                    # Landing on top
                    if self.vel_y > 0 and player_rect.bottom - self.vel_y <= plat_rect.top + 10:
                        self.y = plat_rect.top - self.height//2
                        self.vel_y = 0
                        self.on_ground = True
                        self.jump_count = 0
        
        # Screen bounds
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
    
    def jump(self):
        if self.in_water:
            self.vel_y = JUMP_FORCE * 0.7
            return True
        
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.jump_count = 1
            return True
        elif self.silk >= SILK_JUMP_COST:
            # Air jump costs silk
            self.vel_y = JUMP_FORCE
            self.jump_count += 1
            self.silk -= SILK_JUMP_COST
            return True
        return False
    
    def dash(self):
        if self.dash_cooldown_timer <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            self.dash_direction = 1 if self.facing_right else -1
            self.vel_x = self.dash_direction * DASH_SPEED
            return True
        return False
    
    def use_silk_attack(self):
        if not self.silk_thread_active and not self.in_water and self.on_ground:
            self.silk_thread_active = True
            self.silk_thread_x = 0 if self.facing_right else SCREEN_WIDTH
            self.silk_thread_y = self.y
            self.silk_thread_width = SCREEN_WIDTH
            self.silk_thread_duration = 1000
            return True
        return False
    
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            return True
        return False


class BugEnemy:
    def __init__(self, x, platform_y):
        self.x = x
        self.y = platform_y - 20
        self.platform_y = platform_y
        self.width = 30
        self.height = 25
        self.direction = 1
        self.speed = 1
        self.patrol_range = 100
        self.start_x = x
        
    def get_rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height//2,
                          self.width, self.height)
    
    def update(self):
        self.x += self.speed * self.direction
        if abs(self.x - self.start_x) > self.patrol_range:
            self.direction *= -1
    
    def draw(self, surface):
        # Body
        body_rect = pygame.Rect(self.x - 15, self.y - 10, 30, 20)
        pygame.draw.ellipse(surface, (100, 80, 60), body_rect)
        
        # Shell
        shell_rect = pygame.Rect(self.x - 12, self.y - 15, 24, 12)
        pygame.draw.ellipse(surface, (80, 60, 40), shell_rect)
        
        # Legs
        for i in range(3):
            leg_x = self.x - 8 + i * 8
            pygame.draw.line(surface, (60, 40, 30), 
                           (leg_x, self.y), (leg_x - 3, self.y + 8), 2)
            pygame.draw.line(surface, (60, 40, 30),
                           (leg_x, self.y), (leg_x + 3, self.y + 8), 2)
        
        # Antennae
        pygame.draw.line(surface, (60, 40, 30),
                        (self.x - 5, self.y - 15), (self.x - 10, self.y - 22), 2)
        pygame.draw.line(surface, (60, 40, 30),
                        (self.x + 5, self.y - 15), (self.x + 10, self.y - 22), 2)


class RainDrop:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-100, 0)
        self.speed = random.randint(8, 15)
        self.length = random.randint(10, 25)
        
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.reset()
            
    def draw(self, surface):
        pygame.draw.line(surface, LIGHT_BLUE, 
                        (self.x, self.y), (self.x, self.y + self.length), 2)


class CutscenePlayer:
    """Player in capsule during cutscene"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_y = 0
        self.radius = 25
        self.landed = False
        
    def update(self):
        if not self.landed:
            self.vel_y += GRAVITY
            self.y += self.vel_y
            
            if self.y >= SCREEN_HEIGHT - 100:
                self.y = SCREEN_HEIGHT - 100
                self.vel_y = 0
                self.landed = True
                return True  # Capsule broken
        return False
    
    def draw(self, surface):
        # Draw glass capsule
        capsule_rect = pygame.Rect(self.x - 35, self.y - 45, 70, 90)
        pygame.draw.ellipse(surface, GLASS_COLOR, capsule_rect)
        pygame.draw.arc(surface, WHITE, capsule_rect, 0, 3.14, 2)
        
        # Draw player inside
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y - 10)), 20)
        # Horns
        pygame.draw.polygon(surface, WHITE, [
            (self.x - 12, self.y - 20),
            (self.x - 18, self.y - 30),
            (self.x - 14, self.y - 35),
            (self.x - 8, self.y - 25)
        ])
        pygame.draw.polygon(surface, WHITE, [
            (self.x + 12, self.y - 20),
            (self.x + 18, self.y - 30),
            (self.x + 14, self.y - 35),
            (self.x + 8, self.y - 25)
        ])
        # Eyes
        pygame.draw.circle(surface, BLACK, (int(self.x - 5), int(self.y - 8)), 3)
        pygame.draw.circle(surface, BLACK, (int(self.x + 5), int(self.y - 8)), 3)


def draw_ui(surface, player):
    # HP Bar
    hp_bar_width = 200
    hp_bar_height = 20
    hp_bar_x = 20
    hp_bar_y = 20
    pygame.draw.rect(surface, HP_BAR_BG, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
    hp_fill = int((player.hp / player.max_hp) * hp_bar_width)
    pygame.draw.rect(surface, HP_BAR_FG, (hp_bar_x, hp_bar_y, hp_fill, hp_bar_height))
    pygame.draw.rect(surface, WHITE, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 2)
    
    # Silk Bar
    silk_bar_width = 150
    silk_bar_height = 15
    silk_bar_x = 20
    silk_bar_y = 50
    pygame.draw.rect(surface, SILK_BAR_BG, (silk_bar_x, silk_bar_y, silk_bar_width, silk_bar_height))
    silk_fill = int((player.silk / MAX_SILK) * silk_bar_width)
    pygame.draw.rect(surface, SILK_BAR_FG, (silk_bar_x, silk_bar_y, silk_fill, silk_bar_height))
    pygame.draw.rect(surface, WHITE, (silk_bar_x, silk_bar_y, silk_bar_width, silk_bar_height), 2)
    
    # Dash Cooldown Indicator
    cooldown_x = 20
    cooldown_y = 80
    cooldown_size = 40
    pygame.draw.rect(surface, COOLDOWN_BG, (cooldown_x, cooldown_y, cooldown_size, cooldown_size))
    if player.dash_cooldown_timer <= 0:
        pygame.draw.rect(surface, COOLDOWN_FG, (cooldown_x + 5, cooldown_y + 5, cooldown_size - 10, cooldown_size - 10))
    else:
        cooldown_progress = 1 - (player.dash_cooldown_timer / DASH_COOLDOWN)
        fill_height = int(cooldown_size * cooldown_progress)
        pygame.draw.rect(surface, COOLDOWN_FG, 
                        (cooldown_x + 5, cooldown_y + cooldown_size - 5 - fill_height, cooldown_size - 10, fill_height))
    pygame.draw.rect(surface, WHITE, (cooldown_x, cooldown_y, cooldown_size, cooldown_size), 2)
    
    # Silk regeneration indicator
    if player.silk < MAX_SILK and player.on_ground:
        player.silk = min(MAX_SILK, player.silk + 0.3)


def draw_platforms(surface, platforms):
    for platform in platforms:
        rect = pygame.Rect(platform[0], platform[1], platform[2], platform[3])
        pygame.draw.rect(surface, MEDIUM_BLUE, rect)
        pygame.draw.rect(surface, LIGHT_BLUE, rect, 3)


def draw_ladder(surface, ladder_rect, show_hint):
    # Draw ladder rungs
    rung_spacing = 30
    for y in range(ladder_rect.top, ladder_rect.bottom, rung_spacing):
        pygame.draw.line(surface, LIGHT_BLUE, 
                        (ladder_rect.left + 5, y), 
                        (ladder_rect.right - 5, y), 4)
    # Side rails
    pygame.draw.line(surface, LIGHT_BLUE,
                    (ladder_rect.left + 10, ladder_rect.top),
                    (ladder_rect.left + 10, ladder_rect.bottom), 4)
    pygame.draw.line(surface, LIGHT_BLUE,
                    (ladder_rect.right - 10, ladder_rect.top),
                    (ladder_rect.right - 10, ladder_rect.bottom), 4)
    
    if show_hint:
        font = pygame.font.Font(None, 36)
        hint_text = font.render("Press UP to climb", True, WHITE)
        hint_rect = hint_text.get_rect(center=(ladder_rect.centerx, ladder_rect.top - 30))
        surface.blit(hint_text, hint_rect)


def main():
    global FULLSCREEN, screen
    
    # Create player
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
    
    # Platforms: (x, y, width, height)
    platforms = [
        (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50),  # Ground
        (200, SCREEN_HEIGHT - 150, 200, 20),  # Left platform
        (SCREEN_WIDTH - 400, SCREEN_HEIGHT - 250, 200, 20),  # Right platform
        (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 350, 300, 20),  # Middle platform (bug platform)
        (100, SCREEN_HEIGHT - 450, 150, 20),  # Upper left
        (SCREEN_WIDTH - 250, SCREEN_HEIGHT - 550, 150, 20),  # Upper right
    ]
    
    # Water area (around the middle platform)
    water_rect = pygame.Rect(0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, SCREEN_HEIGHT - (SCREEN_HEIGHT - 100))
    
    # Ladder
    ladder_rect = pygame.Rect(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 550, 40, 500)
    show_ladder_hint = False
    climbing = False
    
    # Bench for healing (near the starting area)
    bench_rect = pygame.Rect(100, SCREEN_HEIGHT - 90, 80, 40)
    show_bench_hint = False
    
    # Bug enemy on middle platform
    bug = BugEnemy(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 350)
    
    # Rain drops
    rain_drops = [RainDrop() for _ in range(100)]
    
    # Cutscene
    cutscene_player = CutscenePlayer(SCREEN_WIDTH // 2, -100)
    cutscene_active = True
    cutscene_timer = 0
    cutscene_duration = 3000  # 3 seconds
    
    # Game loop
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    FULLSCREEN = not FULLSCREEN
                    if FULLSCREEN:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if cutscene_active:
                    continue
                
                if event.key == pygame.K_z:
                    player.jump()
                
                if event.key == pygame.K_x:
                    player.use_silk_attack()
                
                if event.key == pygame.K_c:
                    player.dash()
                
                # Ladder climbing
                if event.key == pygame.K_UP and show_ladder_hint and not climbing:
                    climbing = True
                    player.x = ladder_rect.centerx
                    player.y = ladder_rect.bottom + 20
                    player.vel_y = 0
                
                # Sitting on bench handled in player.update()
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    climbing = False
        
        # Clear screen
        screen.fill(DARK_BLUE)
        
        # Cutscene handling
        if cutscene_active:
            cutscene_broken = cutscene_player.update()
            cutscene_player.draw(screen)
            
            # Draw rain during cutscene
            for drop in rain_drops:
                drop.update()
                drop.draw(screen)
            
            if cutscene_broken:
                cutscene_timer += dt
                # Show break effect
                for _ in range(10):
                    shard_x = cutscene_player.x + random.randint(-30, 30)
                    shard_y = cutscene_player.y + random.randint(-40, 40)
                    pygame.draw.polygon(screen, GLASS_COLOR, [
                        (shard_x, shard_y),
                        (shard_x + random.randint(5, 15), shard_y + random.randint(5, 15)),
                        (shard_x + random.randint(-10, 10), shard_y + random.randint(10, 20))
                    ])
                
                if cutscene_timer > cutscene_duration:
                    cutscene_active = False
                    # Spawn player at landing spot
                    player.x = cutscene_player.x
                    player.y = cutscene_player.y - 50
            clock.tick(60)
            pygame.display.flip()
            continue
        
        # Update player
        keys = pygame.key.get_pressed()
        
        # Check bench proximity for hint
        player_rect = player.get_rect()
        show_bench_hint = player_rect.colliderect(bench_rect.inflate(40, 20)) and not player.is_sitting
        
        # Ladder logic
        show_ladder_hint = player_rect.colliderect(ladder_rect) and not climbing and not player.is_sitting
        
        if climbing:
            player.x = ladder_rect.centerx
            if keys[pygame.K_UP]:
                player.y -= 3
            if keys[pygame.K_DOWN]:
                player.y += 3
            if player.y <= ladder_rect.top:
                climbing = False
        else:
            player.update(keys, platforms, water_rect, bench_rect)
        
        # Update bug
        bug.update()
        
        # Check silk thread collision with bug
        if player.silk_thread_active:
            thread_rect = pygame.Rect(min(player.silk_thread_x, player.silk_thread_x + player.silk_thread_width),
                                     player.silk_thread_y - 5,
                                     abs(player.silk_thread_width), 10)
            if thread_rect.colliderect(bug.get_rect()):
                bug.start_x = bug.x
                bug.x = random.randint(100, SCREEN_WIDTH - 100)
        
        # Draw water
        pygame.draw.rect(screen, WATER_COLOR, water_rect)
        
        # Draw platforms
        draw_platforms(screen, platforms)
        
        # Draw ladder
        draw_ladder(screen, ladder_rect, show_ladder_hint)
        
        # Draw bench
        pygame.draw.rect(screen, BENCH_COLOR, bench_rect)
        pygame.draw.rect(screen, (100, 70, 30), bench_rect, 3)
        # Bench legs
        pygame.draw.rect(screen, (100, 70, 30), (bench_rect.left + 10, bench_rect.bottom, 10, 20))
        pygame.draw.rect(screen, (100, 70, 30), (bench_rect.right - 20, bench_rect.bottom, 10, 20))
        
        # Draw bench hint
        if show_bench_hint and not player.is_sitting:
            font = pygame.font.Font(None, 36)
            bench_hint_text = font.render("Press UP to sit and heal", True, WHITE)
            bench_hint_rect = bench_hint_text.get_rect(center=(bench_rect.centerx, bench_rect.top - 30))
            screen.blit(bench_hint_text, bench_hint_rect)
        
        # Draw bug
        bug.draw(screen)
        
        # Draw player
        player.draw(screen)
        
        # Draw rain
        for drop in rain_drops:
            drop.update()
            drop.draw(screen)
        
        # Draw UI
        draw_ui(screen, player)
        
        # Check damage from bug (only if not sitting)
        if not player.is_sitting and player.get_rect().colliderect(bug.get_rect()):
            if player.take_damage(10):
                # Game over - respawn
                player.x = SCREEN_WIDTH // 2
                player.y = SCREEN_HEIGHT - 150
                player.hp = player.max_hp
                player.silk = MAX_SILK
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()