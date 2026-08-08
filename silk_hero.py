import pygame
import sys
import math

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (20, 30, 60)  # Тёмно-синий для города в стиле Hollow Knight City of Tears
LIGHTER_BLUE = (40, 60, 100)  # Чуть светлее для города
WATER_BLUE = (60, 100, 160)  # Цвет воды
SILK_COLOR = (200, 200, 220)  # Цвет шёлка
RED = (255, 0, 0)
GRAY = (100, 100, 100)

# Настройки игрока
PLAYER_SPEED = 5
JUMP_STRENGTH = -12
GRAVITY = 0.6
MAX_SILK = 100
SILK_REGEN = 0.5
SILK_COST_MULTI_JUMP = 10
DASH_COOLDOWN = 0.2  # секунды
DASH_SPEED = 15
DASH_DURATION = 0.15

# Настройки шёлковой нити
SILK_THREAD_DAMAGE = 25
SILK_THREAD_DURATION = 3  # секунды

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.radius = 20  # Исправление ошибки: добавлен радиус
        self.image = pygame.Surface((self.radius * 2, self.radius * 2 + 15), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        # Позиция и скорость
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        
        # Характеристики
        self.max_hp = 100
        self.hp = self.max_hp
        self.max_silk = MAX_SILK
        self.silk = self.max_silk
        
        # Кулдауны и состояния
        self.dash_cooldown_timer = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.jump_count = 0
        self.max_jumps = 5  # Мультипрыжок ограничен шёлком
        
        # Направление
        self.facing_right = True
        
        # Шёлковая нить
        self.silk_thread_active = False
        self.silk_thread_start = None
        self.silk_thread_end = None
        self.silk_thread_timer = 0
        
        self.draw_player()
    
    def draw_player(self):
        """Рисует персонажа: белая круглая голова, рожки, чёрные глаза, тёмно-синяя накидка"""
        self.image.fill((0, 0, 0, 0))
        
        # Тёмно-синяя накидка (очень узкая)
        cloak_width = 12
        cloak_height = 35
        cloak_x = self.radius - cloak_width // 2
        cloak_y = self.radius
        pygame.draw.rect(self.image, DARK_BLUE, (cloak_x, cloak_y, cloak_width, cloak_height))
        
        # Белая круглая голова
        head_center = (self.radius, self.radius)
        pygame.draw.circle(self.image, WHITE, head_center, self.radius)
        
        # Белые рожки (без разделения с головой, загибаются как у козла)
        horn_length = 18
        horn_thickness = 5
        
        # Левый рог
        left_horn_start = (self.radius - 8, self.radius - 15)
        left_horn_points = [
            left_horn_start,
            (left_horn_start[0] - 5, left_horn_start[1] - 10),
            (left_horn_start[0] - 8, left_horn_start[1] - 5),
        ]
        pygame.draw.polygon(self.image, WHITE, left_horn_points)
        
        # Правый рог
        right_horn_start = (self.radius + 8, self.radius - 15)
        right_horn_points = [
            right_horn_start,
            (right_horn_start[0] + 5, right_horn_start[1] - 10),
            (right_horn_start[0] + 8, right_horn_start[1] - 5),
        ]
        pygame.draw.polygon(self.image, WHITE, right_horn_points)
        
        # Чёрные глаза (как провалы в пустоту)
        eye_size = 6
        left_eye_pos = (self.radius - 7, self.radius - 2)
        right_eye_pos = (self.radius + 7, self.radius - 2)
        pygame.draw.circle(self.image, BLACK, left_eye_pos, eye_size)
        pygame.draw.circle(self.image, BLACK, right_eye_pos, eye_size)
    
    def update(self, platforms, water_rect, dt):
        # Обновление таймеров
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing = False
        
        if self.silk_thread_active:
            self.silk_thread_timer -= dt
            if self.silk_thread_timer <= 0:
                self.silk_thread_active = False
                self.silk_thread_start = None
                self.silk_thread_end = None
        
        # Регенерация шёлка
        if self.silk < self.max_silk and not self.silk_thread_active:
            self.silk += SILK_REGEN
            if self.silk > self.max_silk:
                self.silk = self.max_silk
        
        # Гравитация
        if not self.is_dashing:
            self.vel_y += GRAVITY
        
        # Движение по X
        keys = pygame.key.get_pressed()
        if not self.is_dashing:
            self.vel_x = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -PLAYER_SPEED
                self.facing_right = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = PLAYER_SPEED
                self.facing_right = True
        
        # Применение скорости
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)
        
        # Коллизия с платформами
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                # Проверка сверху
                if self.vel_y > 0 and self.rect.bottom <= platform.top + 10:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0
                # Проверка снизу
                elif self.vel_y < 0 and self.rect.top >= platform.bottom - 10:
                    self.rect.top = platform.bottom
                    self.vel_y = 0
        
        # Ограничение по воде (можно плавать)
        if self.rect.colliderect(water_rect):
            # В воде гравитация меньше
            if self.vel_y > 0:
                self.vel_y *= 0.95
            # Можно двигаться вверх в воде
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.vel_y = -3
        
        # Ограничение по экрану
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.vel_y = 0
            self.on_ground = True
            self.jump_count = 0
    
    def jump(self):
        """Прыжок с расходом шёлка для мультипрыжка"""
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            self.jump_count = 1
        else:
            # Мультипрыжок в воздухе тратит шёлк
            if self.silk >= SILK_COST_MULTI_JUMP and self.jump_count < self.max_jumps:
                self.vel_y = JUMP_STRENGTH
                self.silk -= SILK_COST_MULTI_JUMP
                self.jump_count += 1
    
    def dash(self):
        """Шёлковый рывок"""
        if self.dash_cooldown_timer <= 0 and self.silk >= 5:
            self.is_dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            self.silk -= 5
            
            # Рывок в направлении движения
            if self.facing_right:
                self.vel_x = DASH_SPEED
            else:
                self.vel_x = -DASH_SPEED
            self.vel_y = 0
    
    def shoot_silk_thread(self, screen_width):
        """Атака шёлковой нитью поперёк локации"""
        if not self.silk_thread_active and self.on_ground and self.silk >= 15:
            self.silk_thread_active = True
            self.silk_thread_timer = SILK_THREAD_DURATION
            self.silk -= 15
            
            # Нить натягивается поперёк всей локации
            thread_y = self.rect.centery
            self.silk_thread_start = (0, thread_y)
            self.silk_thread_end = (screen_width, thread_y)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
    
    def draw(self, surface):
        # Отрисовка персонажа
        surface.blit(self.image, self.rect)
        
        # Отрисовка шёлковой нити
        if self.silk_thread_active and self.silk_thread_start and self.silk_thread_end:
            pygame.draw.line(surface, SILK_COLOR, self.silk_thread_start, self.silk_thread_end, 3)


class Enemy(pygame.sprite.Sprite):
    """Жучок на платформе"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        
        # Рисуем жучка
        pygame.draw.ellipse(self.image, (80, 60, 40), (0, 0, 30, 20))
        # Глаза жучка
        pygame.draw.circle(self.image, WHITE, (8, 8), 3)
        pygame.draw.circle(self.image, WHITE, (22, 8), 3)
        
        self.direction = 1
        self.speed = 1
        self.patrol_range = 100
        self.start_x = x
    
    def update(self):
        self.rect.x += self.speed * self.direction
        
        if abs(self.rect.x - self.start_x) > self.patrol_range:
            self.direction *= -1


class Platform(pygame.Rect):
    pass


def draw_ui(surface, player):
    """Отрисовка интерфейса: HP бар, шёлк, кулдаун рывка"""
    font = pygame.font.Font(None, 24)
    
    # HP бар
    hp_bar_width = 200
    hp_bar_height = 20
    hp_bar_x = 20
    hp_bar_y = 20
    hp_ratio = player.hp / player.max_hp
    
    pygame.draw.rect(surface, GRAY, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
    pygame.draw.rect(surface, RED, (hp_bar_x, hp_bar_y, int(hp_bar_width * hp_ratio), hp_bar_height))
    pygame.draw.rect(surface, WHITE, (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height), 2)
    
    hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
    surface.blit(hp_text, (hp_bar_x + 5, hp_bar_y + 2))
    
    # Шёлк бар
    silk_bar_width = 200
    silk_bar_height = 20
    silk_bar_x = 20
    silk_bar_y = 50
    silk_ratio = player.silk / player.max_silk
    
    pygame.draw.rect(surface, GRAY, (silk_bar_x, silk_bar_y, silk_bar_width, silk_bar_height))
    pygame.draw.rect(surface, SILK_COLOR, (silk_bar_x, silk_bar_y, int(silk_bar_width * silk_ratio), silk_bar_height))
    pygame.draw.rect(surface, WHITE, (silk_bar_x, silk_bar_y, silk_bar_width, silk_bar_height), 2)
    
    silk_text = font.render(f"Шёлк: {int(player.silk)}/{player.max_silk}", True, WHITE)
    surface.blit(silk_text, (silk_bar_x + 5, silk_bar_y + 2))
    
    # Кулдаун рывка
    dash_y = 80
    if player.dash_cooldown_timer > 0:
        cooldown_ratio = player.dash_cooldown_timer / DASH_COOLDOWN
        dash_width = int(200 * cooldown_ratio)
        pygame.draw.rect(surface, GRAY, (20, dash_y, 200, 20))
        pygame.draw.rect(surface, (150, 150, 150), (20, dash_y, dash_width, 20))
        pygame.draw.rect(surface, WHITE, (20, dash_y, 200, 20), 2)
        dash_text = font.render("Рывок: перезарядка", True, WHITE)
    else:
        pygame.draw.rect(surface, GRAY, (20, dash_y, 200, 20))
        pygame.draw.rect(surface, (0, 200, 0), (20, dash_y, 200, 20))
        pygame.draw.rect(surface, WHITE, (20, dash_y, 200, 20), 2)
        dash_text = font.render("Рывок: готов", True, WHITE)
    
    surface.blit(dash_text, (25, dash_y + 2))


def cutscene(screen, player_start_pos):
    """Катсцена: сбрасывание из лаборатории в колбе"""
    clock = pygame.time.Clock()
    
    # Начальная позиция колбы
    capsule_x = SCREEN_WIDTH // 2
    capsule_y = -100
    capsule_speed = 8
    
    # Состояния катсцены
    state = "falling"  # falling, breaking, fade_out
    timer = 0
    break_particles = []
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.fill(DARK_BLUE)
        
        if state == "falling":
            capsule_y += capsule_speed
            capsule_speed += 0.3  # Ускорение падения
            
            # Рисуем колбу
            pygame.draw.ellipse(screen, (150, 200, 255), (capsule_x - 30, capsule_y - 40, 60, 80))
            pygame.draw.ellipse(screen, WHITE, (capsule_x - 30, capsule_y - 40, 60, 80), 2)
            
            # Игрок внутри колбы
            pygame.draw.circle(screen, WHITE, (capsule_x, capsule_y), 15)
            
            # Проверка удара о землю
            if capsule_y >= SCREEN_HEIGHT - 150:
                state = "breaking"
                timer = 0
                # Создаём осколки
                for i in range(20):
                    break_particles.append({
                        'x': capsule_x,
                        'y': capsule_y,
                        'vx': (i - 10) * 2,
                        'vy': -5 - i * 0.5,
                        'life': 1.0
                    })
        
        elif state == "breaking":
            timer += dt
            
            # Рисуем осколки
            for particle in break_particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] += 0.3  # Гравитация
                particle['life'] -= dt
                
                if particle['life'] > 0:
                    alpha = int(255 * particle['life'])
                    color = (150, 200, 255, alpha)
                    pygame.draw.circle(screen, (150, 200, 255), (int(particle['x']), int(particle['y'])), 3)
                else:
                    break_particles.remove(particle)
            
            # Игрок появляется после разбивания
            if timer > 0.5:
                state = "fade_out"
                timer = 0
        
        elif state == "fade_out":
            timer += dt
            # Игрок на земле
            pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150), 20)
            
            if timer > 1.0:
                running = False
        
        pygame.display.flip()
    
    return player_start_pos


def main():
    # Создание окна
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Silk Hero - City of Tears")
    
    # Установка иконки (создаём простую иконку программно)
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, WHITE, (16, 16), 14)
    pygame.draw.circle(icon, BLACK, (12, 14), 4)
    pygame.draw.circle(icon, BLACK, (20, 14), 4)
    pygame.display.set_icon(icon)
    
    clock = pygame.time.Clock()
    
    # Начальная позиция игрока
    player_start_x = SCREEN_WIDTH // 2
    player_start_y = SCREEN_HEIGHT - 150
    
    # Запуск катсцены
    cutscene(screen, (player_start_x, player_start_y))
    
    # Создание игрока
    player = Player(player_start_x, player_start_y)
    player_group = pygame.sprite.Group(player)
    
    # Создание платформы посередине
    platform_width = 400
    platform_height = 20
    platform_x = (SCREEN_WIDTH - platform_width) // 2
    platform_y = SCREEN_HEIGHT - 100
    platform = Platform(platform_x, platform_y, platform_width, platform_height)
    platforms = [platform]
    
    # Жучок на платформе
    enemy = Enemy(SCREEN_WIDTH // 2, platform_y - 15)
    enemy_group = pygame.sprite.Group(enemy)
    
    # Вода по краям и внизу
    water_rect = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
    
    # Флаг полного экрана
    fullscreen = True
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    # Переключение полного экрана
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                
                if event.key == pygame.K_z:
                    player.jump()
                
                if event.key == pygame.K_x:
                    player.shoot_silk_thread(SCREEN_WIDTH)
                
                if event.key == pygame.K_c:
                    player.dash()
                
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Обновление
        player.update(platforms, water_rect, dt)
        enemy_group.update()
        
        # Проверка попадания в шёлковую нить
        if player.silk_thread_active and player.silk_thread_start and player.silk_thread_end:
            thread_y = player.silk_thread_start[1]
            thread_rect = pygame.Rect(0, thread_y - 5, SCREEN_WIDTH, 10)
            
            for enemy in enemy_group:
                if thread_rect.colliderect(enemy.rect):
                    enemy.take_damage(SILK_THREAD_DAMAGE) if hasattr(enemy, 'take_damage') else None
                    # Визуальный эффект попадания
                    player.silk_thread_active = False
        
        # Отрисовка
        screen.fill(LIGHTER_BLUE)  # Город чуть светлее в стиле City of Tears
        
        # Рисуем воду
        pygame.draw.rect(screen, WATER_BLUE, water_rect)
        
        # Рисуем платформы
        for plat in platforms:
            pygame.draw.rect(screen, GRAY, plat)
        
        # Отрисовка врагов
        enemy_group.draw(screen)
        
        # Отрисовка игрока
        player_group.draw(screen)
        player.draw(screen)
        
        # Отрисовка UI
        draw_ui(screen, player)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
