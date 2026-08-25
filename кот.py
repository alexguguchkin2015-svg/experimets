#!/usr/bin/env python3
"""
Silksong-inspired Battle Game
Play as a cute cat in a narrow yellow cape with a cat-like head, huge circular black eyes with highlights.
Features detailed walking animation and a boss battle against a mechanical spider.
"""

import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Silksong Battle: Cat vs Mechanical Spider")

# Colors
YELLOW = (255, 220, 0)
DARK_YELLOW = (200, 170, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
METAL = (150, 150, 160)
DARK_METAL = (80, 80, 90)
RED = (200, 50, 50)
BLUE = (50, 100, 200)
BACKGROUND = (30, 30, 40)
FLOOR_COLOR = (60, 60, 70)

# Clock
clock = pygame.time.Clock()
FPS = 60

class Cat:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 80
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.is_jumping = False
        self.facing_right = True
        self.health = 100
        self.max_health = 100
        self.attack_damage = 25
        self.attack_cooldown = 0
        self.is_attacking = False
        self.attack_rect = None

        # Animation
        self.anim_frame = 0
        self.anim_speed = 0.15
        self.walk_cycle = 0

    def update(self, platforms):
        # Apply gravity
        self.vel_y += self.gravity
        if self.vel_y > 15:
            self.vel_y = 15

        # Move horizontally
        self.x += self.vel_x

        # Check horizontal collisions
        for platform in platforms:
            if self.get_rect().colliderect(platform):
                if self.vel_x > 0:
                    self.x = platform.left - self.width
                elif self.vel_x < 0:
                    self.x = platform.right

        # Move vertically
        self.y += self.vel_y

        # Check vertical collisions
        on_ground = False
        for platform in platforms:
            if self.get_rect().colliderect(platform):
                if self.vel_y > 0:
                    self.y = platform.top - self.height
                    self.vel_y = 0
                    self.is_jumping = False
                    on_ground = True
                elif self.vel_y < 0:
                    self.y = platform.bottom
                    self.vel_y = 0

        # Attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_cooldown == 0:
            self.is_attacking = False
            self.attack_rect = None

        # Update animation
        if abs(self.vel_x) > 0.5:
            self.walk_cycle += self.anim_speed
            self.anim_frame = math.sin(self.walk_cycle) * 0.3
        else:
            self.walk_cycle = 0
            self.anim_frame = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def jump(self):
        if not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True

    def attack(self):
        if self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_cooldown = 30
            if self.facing_right:
                self.attack_rect = pygame.Rect(self.x + self.width, self.y + 20, 40, 40)
            else:
                self.attack_rect = pygame.Rect(self.x - 40, self.y + 20, 40, 40)

    def draw(self, surface):
        # Draw the cat with detailed animation

        # Body tilt based on movement
        tilt = self.anim_frame * 0.1

        # Save current transform
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # Draw cape (narrow yellow cloak) - flows with animation
        cape_points = []
        cape_flow = math.sin(self.walk_cycle * 2) * 5
        if self.facing_right:
            cape_offset = -15
        else:
            cape_offset = 15

        cape_points.append((center_x + cape_offset, self.y + 30))
        cape_points.append((center_x + cape_offset - 10, self.y + 50 + cape_flow))
        cape_points.append((center_x + cape_offset + 10, self.y + 50 + cape_flow))

        pygame.draw.polygon(surface, YELLOW, cape_points)
        pygame.draw.polygon(surface, DARK_YELLOW, cape_points, 2)

        # Draw body (small, compact)
        body_rect = pygame.Rect(center_x - 15, self.y + 30, 30, 35)
        pygame.draw.ellipse(surface, GRAY, body_rect)
        pygame.draw.ellipse(surface, BLACK, body_rect, 2)

        # Draw legs with walking animation
        leg_offset = math.sin(self.walk_cycle) * 8
        leg_thickness = 6

        # Back legs
        back_leg_l = (center_x - 10 + leg_offset * 0.5, self.y + 60,
                      center_x - 10 - leg_offset * 0.3, self.y + 75)
        back_leg_r = (center_x + 10 - leg_offset * 0.5, self.y + 60,
                      center_x + 10 + leg_offset * 0.3, self.y + 75)

        pygame.draw.line(surface, DARK_GRAY, back_leg_l[0:2], back_leg_l[2:4], leg_thickness)
        pygame.draw.line(surface, DARK_GRAY, back_leg_r[0:2], back_leg_r[2:4], leg_thickness)

        # Front legs (more animated)
        front_leg_l = (center_x - 8 - leg_offset * 0.5, self.y + 55,
                       center_x - 8 + leg_offset * 0.7, self.y + 75)
        front_leg_r = (center_x + 8 + leg_offset * 0.5, self.y + 55,
                       center_x + 8 - leg_offset * 0.7, self.y + 75)

        pygame.draw.line(surface, GRAY, front_leg_l[0:2], front_leg_l[2:4], leg_thickness + 1)
        pygame.draw.line(surface, GRAY, front_leg_r[0:2], front_leg_r[2:4], leg_thickness + 1)

        # Draw tail with animation
        tail_curve = math.sin(self.walk_cycle * 1.5) * 15
        tail_points = [
            (center_x, self.y + 60),
            (center_x - 20 + tail_curve, self.y + 55),
            (center_x - 35 + tail_curve * 1.5, self.y + 45 + tail_curve * 0.5)
        ]
        pygame.draw.lines(surface, GRAY, False, tail_points, 5)

        # Draw head (cat-like, round)
        head_radius = 25
        head_center = (center_x, self.y + 25)
        pygame.draw.circle(surface, GRAY, head_center, head_radius)
        pygame.draw.circle(surface, BLACK, head_center, head_radius, 2)

        # Draw ears
        ear_size = 12
        left_ear = [(head_center[0] - 15, head_center[1] - 15),
                    (head_center[0] - 22, head_center[1] - 30),
                    (head_center[0] - 8, head_center[1] - 25)]
        right_ear = [(head_center[0] + 15, head_center[1] - 15),
                     (head_center[0] + 22, head_center[1] - 30),
                     (head_center[0] + 8, head_center[1] - 25)]
        pygame.draw.polygon(surface, GRAY, left_ear)
        pygame.draw.polygon(surface, GRAY, right_ear)
        pygame.draw.polygon(surface, BLACK, left_ear, 2)
        pygame.draw.polygon(surface, BLACK, right_ear, 2)

        # Draw HUGE circular black eyes with highlights
        eye_radius = 10
        eye_offset = 8
        left_eye_pos = (head_center[0] - eye_offset, head_center[1] - 2)
        right_eye_pos = (head_center[0] + eye_offset, head_center[1] - 2)

        # White part of eye
        pygame.draw.circle(surface, WHITE, left_eye_pos, eye_radius)
        pygame.draw.circle(surface, WHITE, right_eye_pos, eye_radius)

        # Huge black pupils (circular)
        pupil_radius = 7
        pygame.draw.circle(surface, BLACK, left_eye_pos, pupil_radius)
        pygame.draw.circle(surface, BLACK, right_eye_pos, pupil_radius)

        # Highlights (white dots in eyes)
        highlight_radius = 3
        left_highlight = (left_eye_pos[0] + 3, left_eye_pos[1] - 3)
        right_highlight = (right_eye_pos[0] + 3, right_eye_pos[1] - 3)
        pygame.draw.circle(surface, WHITE, left_highlight, highlight_radius)
        pygame.draw.circle(surface, WHITE, right_highlight, highlight_radius)

        # Draw nose
        nose_pos = (head_center[0], head_center[1] + 8)
        pygame.draw.circle(surface, BLACK, nose_pos, 3)

        # Draw whiskers
        whisker_length = 15
        whisker_y_offsets = [-2, 2, 6]
        for offset in whisker_y_offsets:
            # Left whiskers
            pygame.draw.line(surface, BLACK,
                           (head_center[0] - 10, head_center[1] + offset),
                           (head_center[0] - 10 - whisker_length, head_center[1] + offset), 2)
            # Right whiskers
            pygame.draw.line(surface, BLACK,
                           (head_center[0] + 10, head_center[1] + offset),
                           (head_center[0] + 10 + whisker_length, head_center[1] + offset), 2)

        # Draw attack effect
        if self.is_attacking and self.attack_rect:
            attack_color = (255, 200, 100)
            pygame.draw.rect(surface, attack_color, self.attack_rect, 0, 5)
            pygame.draw.rect(surface, YELLOW, self.attack_rect, 2, 5)


class MechanicalSpider:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 100
        self.height = 70
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 3
        self.health = 200
        self.max_health = 200
        self.attack_damage = 20
        self.attack_cooldown = 0
        self.is_attacking = False
        self.state = "idle"  # idle, chase, attack, jump
        self.state_timer = 0
        self.facing_right = False
        self.leg_anim = 0

        # Projectile
        self.projectile = None
        self.projectile_vel = (0, 0)

    def update(self, player, platforms):
        # Simple AI
        self.state_timer -= 1

        if self.state_timer <= 0:
            self.choose_state(player)

        distance_to_player = player.x - self.x

        if self.state == "chase":
            # Move towards player
            if abs(distance_to_player) > 100:
                if distance_to_player > 0:
                    self.vel_x = self.speed
                    self.facing_right = True
                else:
                    self.vel_x = -self.speed
                    self.facing_right = False
            else:
                self.vel_x = 0

            # Jump occasionally
            if random.random() < 0.02 and not self.is_on_ground(platforms):
                self.vel_y = -12

        elif self.state == "attack":
            self.vel_x = 0
            if self.attack_cooldown == 0:
                self.is_attacking = True
                self.attack_cooldown = 60
                # Shoot projectile
                if abs(distance_to_player) > 0:
                    dir_x = 1 if distance_to_player > 0 else -1
                    self.projectile = (self.x + self.width//2, self.y + self.height//2)
                    self.projectile_vel = (dir_x * 8, -3)

        elif self.state == "jump":
            if self.is_on_ground(platforms):
                self.vel_y = -15
                if distance_to_player > 0:
                    self.vel_x = self.speed * 1.5
                    self.facing_right = True
                else:
                    self.vel_x = -self.speed * 1.5
                    self.facing_right = False
            self.state_timer = 30

        # Apply gravity
        self.vel_y += 0.6
        if self.vel_y > 15:
            self.vel_y = 15

        # Move
        self.x += self.vel_x
        self.y += self.vel_y

        # Platform collision
        for platform in platforms:
            if self.get_rect().colliderect(platform):
                if self.vel_y > 0:
                    self.y = platform.top - self.height
                    self.vel_y = 0

        # Cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attack_cooldown == 0:
            self.is_attacking = False

        # Update projectile
        if self.projectile:
            self.projectile = (
                self.projectile[0] + self.projectile_vel[0],
                self.projectile[1] + self.projectile_vel[1]
            )
            # Remove if off screen
            if (self.projectile[0] < 0 or self.projectile[0] > SCREEN_WIDTH or
                self.projectile[1] < 0 or self.projectile[1] > SCREEN_HEIGHT):
                self.projectile = None

        # Leg animation
        self.leg_anim += 0.2

    def choose_state(self, player):
        rand = random.random()
        distance = abs(player.x - self.x)

        if distance < 150 and rand < 0.4:
            self.state = "attack"
            self.state_timer = 90
        elif rand < 0.3:
            self.state = "jump"
            self.state_timer = 60
        else:
            self.state = "chase"
            self.state_timer = 60

    def is_on_ground(self, platforms):
        test_rect = pygame.Rect(self.x, self.y + 5, self.width, self.height)
        for platform in platforms:
            if test_rect.colliderect(platform):
                return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def draw(self, surface):
        # Draw mechanical spider boss

        # Body segments
        body_center = (self.x + self.width//2, self.y + self.height//2)

        # Main body (metallic sphere)
        main_body_radius = 30
        pygame.draw.circle(surface, METAL, body_center, main_body_radius)
        pygame.draw.circle(surface, DARK_METAL, body_center, main_body_radius, 3)

        # Mechanical details on body
        pygame.draw.circle(surface, DARK_METAL, body_center, 15)
        pygame.draw.circle(surface, RED, body_center, 8)

        # Glowing red eye
        eye_pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 5 + 5
        pygame.draw.circle(surface, RED, (body_center[0], body_center[1] - 5), int(eye_pulse))

        # Legs (8 legs with mechanical joints)
        leg_base_positions = [
            (body_center[0] - 20, body_center[1] - 10),
            (body_center[0] + 20, body_center[1] - 10),
            (body_center[0] - 25, body_center[1]),
            (body_center[0] + 25, body_center[1]),
            (body_center[0] - 20, body_center[1] + 10),
            (body_center[0] + 20, body_center[1] + 10),
            (body_center[0] - 15, body_center[1] + 20),
            (body_center[0] + 15, body_center[1] + 20)
        ]

        leg_anim_offset = math.sin(self.leg_anim) * 10

        for i, base_pos in enumerate(leg_base_positions):
            # Alternate leg movement
            if i % 2 == 0:
                anim_mult = 1
            else:
                anim_mult = -1

            # Leg segments
            knee_x = base_pos[0] + (anim_mult * leg_anim_offset)
            knee_y = base_pos[1] + 20

            foot_x = base_pos[0] + (anim_mult * leg_anim_offset * 1.5)
            foot_y = self.y + self.height - 5

            # Draw leg segments
            pygame.draw.line(surface, DARK_METAL, base_pos, (knee_x, knee_y), 6)
            pygame.draw.line(surface, METAL, (knee_x, knee_y), (foot_x, foot_y), 5)

            # Joint circles
            pygame.draw.circle(surface, DARK_METAL, (int(knee_x), int(knee_y)), 5)
            pygame.draw.circle(surface, METAL, (int(foot_x), int(foot_y)), 4)

        # Draw attack indicator
        if self.is_attacking:
            glow_radius = 40 + abs(math.sin(pygame.time.get_ticks() * 0.02)) * 10
            pygame.draw.circle(surface, (255, 100, 100), body_center, int(glow_radius), 3)

        # Draw projectile
        if self.projectile:
            proj_radius = 10
            pygame.draw.circle(surface, RED, (int(self.projectile[0]), int(self.projectile[1])), proj_radius)
            pygame.draw.circle(surface, (255, 200, 0), (int(self.projectile[0]), int(self.projectile[1])), proj_radius - 3)


def create_platforms():
    platforms = []

    # Floor
    floor = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
    platforms.append(floor)

    # Some platforms for jumping
    plat1 = pygame.Rect(200, SCREEN_HEIGHT - 150, 200, 20)
    plat2 = pygame.Rect(500, SCREEN_HEIGHT - 220, 200, 20)
    plat3 = pygame.Rect(100, SCREEN_HEIGHT - 300, 150, 20)
    plat4 = pygame.Rect(700, SCREEN_HEIGHT - 300, 150, 20)

    platforms.extend([plat1, plat2, plat3, plat4])

    return platforms


def draw_health_bar(surface, x, y, health, max_health, width, height, color):
    ratio = health / max_health
    pygame.draw.rect(surface, (100, 0, 0), (x, y, width, height))
    pygame.draw.rect(surface, color, (x, y, int(width * ratio), height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)


def draw_background(surface):
    surface.fill(BACKGROUND)

    # Draw some atmospheric background elements
    # Distant pillars/arches (Silksong style)
    for i in range(0, SCREEN_WIDTH, 150):
        arch_x = i
        arch_width = 40
        arch_height = SCREEN_HEIGHT - 100

        # Left pillar
        pygame.draw.rect(surface, (40, 40, 50), (arch_x, 0, arch_width, arch_height))
        # Right pillar
        pygame.draw.rect(surface, (40, 40, 50), (arch_x + 110, 0, arch_width, arch_height))
        # Arch top
        pygame.draw.arc(surface, (40, 40, 50),
                       (arch_x, 0, 150, 80), 0, math.pi, 5)

    # Floor detail
    pygame.draw.rect(surface, FLOOR_COLOR, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
    pygame.draw.line(surface, (80, 80, 90), (0, SCREEN_HEIGHT - 50),
                    (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 3)


def main():
    # Create game objects
    cat = Cat(100, SCREEN_HEIGHT - 150)
    spider_boss = MechanicalSpider(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150)
    platforms = create_platforms()

    # Game state
    game_over = False
    victory = False

    # Font
    font = pygame.font.Font(None, 36)
    large_font = pygame.font.Font(None, 72)

    running = True
    while running:
        clock.tick(FPS)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over or victory:
                        # Restart game
                        cat = Cat(100, SCREEN_HEIGHT - 150)
                        spider_boss = MechanicalSpider(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150)
                        game_over = False
                        victory = False
                elif not game_over and not victory:
                    if event.key == pygame.K_z:
                        cat.jump()
                    if event.key == pygame.K_x:
                        cat.attack()

        if not game_over and not victory:
            # Player input
            keys = pygame.key.get_pressed()
            cat.vel_x = 0
            if keys[pygame.K_LEFT]:
                cat.vel_x = -cat.speed
                cat.facing_right = False
            if keys[pygame.K_RIGHT]:
                cat.vel_x = cat.speed
                cat.facing_right = True

            # Update
            cat.update(platforms)
            spider_boss.update(cat, platforms)

            # Check attack hit
            if cat.is_attacking and cat.attack_rect:
                if cat.attack_rect.colliderect(spider_boss.get_rect()):
                    if spider_boss.take_damage(cat.attack_damage):
                        victory = True

            # Check projectile hit
            if spider_boss.projectile:
                proj_rect = pygame.Rect(spider_boss.projectile[0] - 10,
                                       spider_boss.projectile[1] - 10, 20, 20)
                if proj_rect.colliderect(cat.get_rect()):
                    cat.health -= spider_boss.attack_damage
                    spider_boss.projectile = None
                    if cat.health <= 0:
                        cat.health = 0
                        game_over = True

            # Check collision with boss
            if cat.get_rect().colliderect(spider_boss.get_rect()):
                cat.health -= 1
                if cat.health <= 0:
                    cat.health = 0
                    game_over = True

        # Draw
        draw_background(screen)

        # Draw platforms
        for platform in platforms:
            pygame.draw.rect(screen, DARK_GRAY, platform)
            pygame.draw.rect(screen, GRAY, platform, 3)

        # Draw characters
        cat.draw(screen)
        spider_boss.draw(screen)

        # Draw UI
        draw_health_bar(screen, 20, 20, cat.health, cat.max_health, 200, 20, BLUE)
        draw_health_bar(screen, SCREEN_WIDTH - 220, 20, spider_boss.health,
                       spider_boss.max_health, 200, 20, RED)

        # Health text
        cat_health_text = font.render(f"Cat: {cat.health}/{cat.max_health}", True, WHITE)
        spider_health_text = font.render(f"Spider: {spider_boss.health}/{spider_boss.max_health}", True, WHITE)
        screen.blit(cat_health_text, (20, 45))
        screen.blit(spider_health_text, (SCREEN_WIDTH - 220, 45))

        # Game over / Victory screen
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            game_over_text = large_font.render("GAME OVER", True, RED)
            restart_text = font.render("Press SPACE to restart", True, WHITE)
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2,
                                        SCREEN_HEIGHT//2 - 50))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2,
                                      SCREEN_HEIGHT//2 + 20))

        if victory:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            victory_text = large_font.render("VICTORY!", True, YELLOW)
            restart_text = font.render("Press SPACE to restart", True, WHITE)
            screen.blit(victory_text, (SCREEN_WIDTH//2 - victory_text.get_width()//2,
                                      SCREEN_HEIGHT//2 - 50))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2,
                                      SCREEN_HEIGHT//2 + 20))

        # Controls hint
        if not game_over and not victory:
            controls_text = font.render("Arrow Keys: Move | Z: Jump | X: Attack", True, WHITE)
            screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2,
                                       SCREEN_HEIGHT - 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()