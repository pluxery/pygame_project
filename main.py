import pygame
import os
import random
import csv

pygame.init()

WIDTH = 1280
HEIGHT = 720
SIZE = (WIDTH, HEIGHT)

screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption('Clash of soldier')
clock = pygame.time.Clock()
# Константы игры
FPS = 60
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLUMNS = 150
TILE_SIZE = HEIGHT // ROWS
TILE_TYPES = 21

RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

screen_scroll = 0
scroll_background = 0
start_game = False

# Флаги игрока
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False
# загрузка картинок кнопок
start_img = pygame.image.load('img/buttons/start.png').convert_alpha()
exit_img = pygame.image.load('img/buttons/exit.png').convert_alpha()
restart_img = pygame.image.load('img/buttons/restart.png').convert_alpha()
# загрузка картинок Задний фон для мени и уровня
menu_img = pygame.image.load('img/background/menu.png').convert_alpha()
world_img = pygame.image.load('img/background/world.png').convert_alpha()

# Загрузка всех видов плиток в список
tile_types = []
for i in range(TILE_TYPES):
    img = pygame.image.load(f'img/Tile/{i}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    tile_types.append(img)
# загрузка картинок пуль
scale_img = 1.35
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
bullet_x = int(bullet_img.get_width() * scale_img)
bullet_y = int(bullet_img.get_height() * scale_img)
bullet_img = pygame.transform.scale(bullet_img, (bullet_x, bullet_y))
# загрузка картинок гранат
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
grenade_img = pygame.transform.scale(grenade_img, (
    int(grenade_img.get_width() * scale_img), int(grenade_img.get_height() * scale_img)))
# загрузка картинок - бонусные ящики
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {'Health': health_box_img,
              'Ammo': ammo_box_img,
              'Grenade': grenade_box_img}

font = pygame.font.SysFont('Futura', 30)


def draw_text(text, font, text_col, x, y):
    font_img = font.render(text, True, text_col)
    screen.blit(font_img, (x, y))


def reset_lvl():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    empty_world_data = []
    for row in range(ROWS):
        empty = [-1] * COLUMNS
        empty_world_data.append(empty)

    return empty_world_data


class Button:
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        action = False

        mouse_pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(mouse_pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action


class Soldier(pygame.sprite.Sprite):
    def __init__(self, character_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.character_type = character_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.velocity_y = 0
        self.is_jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # Атрибуты для ai
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

        # Загружаем в массив все состояния для анимации персонажей
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            action_list = []
            # получаем число картинок в каждой папке
            num_of_frames = len(os.listdir(f'img/{self.character_type}/{animation}'))
            for i in range(num_of_frames):
                # маштабируем кадры (картинки) и добавляем в список анимации и так для каждого состояния
                img = pygame.image.load(f'img/{self.character_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                action_list.append(img)
            self.animation_list.append(action_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, left_move, right_move):
        scroll_screen = 0
        dx = 0
        dy = 0

        if left_move:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if right_move:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # Прыжок
        if self.is_jump and not self.in_air:
            self.velocity_y = -12
            self.is_jump = False
            self.in_air = True

        self.velocity_y += GRAVITY
        if self.velocity_y > 11:
            self.velocity_y
        dy += self.velocity_y

        # Проверяем столкновения с персонажа с объектами
        for tile in world_lvl.obstacle_list:
            # по оси X
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                # Если ai столкнулся со стеной то разворачиваем его
                if self.character_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            # по оси Y
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):

                if self.velocity_y < 0:
                    self.velocity_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

            # Столкновение с водой
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        if pygame.sprite.spritecollide(self, exit_group, False):
            self.health = 0

            # Падение вниз
        if self.rect.bottom > HEIGHT:
            self.health = 0

        # проверка не ушел ли игрок за границы экрана
        if self.character_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > WIDTH:
                dx = 0

        # обновляем координаты персонажа
        self.rect.x += dx
        self.rect.y += dy

        # обновляем скролл в зависимости от позиции игрока
        if self.character_type == 'player':
            if (self.rect.right > WIDTH - SCROLL_THRESH and scroll_background <
                (world_lvl.lvl_len * TILE_SIZE) - WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and scroll_background > abs(dx)):
                self.rect.x -= dx
                scroll_screen = -dx

        return scroll_screen

    # стрельба
    def shoot(self):
        # если есть патроны создаем пули
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            x_bullet = 0.75 * self.rect.size[0] * self.direction
            y_bullet = self.rect.centery
            bullet = Bullet(self.rect.centerx + x_bullet, y_bullet, self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1

    # Поведение ботов (enemy)
    # ai - artificial intelligence
    def ai(self):
        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)  # 0 - анимация когда персонаж стоит на месте
                self.idling = True
                self.idling_counter = 50
            # если бот увидел игрока то остонавливаемся и стреляем
            if self.vision.colliderect(player.rect):
                self.update_action(0)
                self.shoot()
            else:
                # если двигаемся
                if not self.idling:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False

                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # 1 - анимация бега
                    self.move_counter += 1
                    # Обновление поля зрения для бота
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        self.rect.x += screen_scroll

    def update_animation(self):
        ANIMATION_SPEED = 100
        # обновляем картинку в зависимости от текущего кадра
        self.image = self.animation_list[self.action][self.frame_index]
        # проверяем прошло ли достаточно времени с последнего обновления
        if pygame.time.get_ticks() - self.update_time > ANIMATION_SPEED:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        # Если анимация закончилась, начинаем сначала
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    # обновление состояния
    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    # проверка жив ли персонаж
    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)  # death

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class World():
    def __init__(self):
        # список плиток-препятствий уровня
        self.obstacle_list = []

    def load_world_data(self, data):
        self.lvl_len = len(data[0])
        # перебираем каждое значение уровня
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    # элемент tile содержит в себе картинку плиты и ее координаты
                    img_tile = tile_types[tile]
                    img_tile_rect = img_tile.get_rect()
                    img_tile_rect.x = x * TILE_SIZE
                    img_tile_rect.y = y * TILE_SIZE
                    tile_data = (img_tile, img_tile_rect)
                    # диапазон значений говорит о типе плитки
                    if 0 <= tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10:
                        water = WaterTile(img_tile, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif 11 <= tile <= 14:
                        decoration = DecorationTile(img_tile, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:  # cоздаем персонажа
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 2, 5, 15, 5)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # создаем бота
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 2, 2, 99, 0)
                        enemy_group.add(enemy)
                    elif tile == 17:  # создаем бокс с патронами
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:  # создаем бокс с гранатами
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:  # создаем аптечку
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:  # создаем финиш уровня
                        exit = ExitTile(img_tile, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


# плитки урашалки
class DecorationTile(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


# плитки воды
class WaterTile(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


# плитка завершения уровня
class ExitTile(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


# бонусные элементы (атечка, патроны...)
class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
        #  поднял ли игрок бонус-бокс
        if pygame.sprite.collide_rect(self, player):
            # узнаем ее тип и в соответсвии плюсуем к атрибуту игрока
            if self.item_type == 'Health':
                player.health += 25
                # чтобы полное здоровье больше не пополнялось
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            # удаляем использованный бонус-бокс
            self.kill()


# отображение жизней в левом верхнем углц
class HealthBar:
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        self.health = health
        # считаем коэффициент здоровья
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


# Пули
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # Движение пули
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # если пуля ушла за экран - удаляем ее
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()
        # проверяем не влетела ли пуля в текстуры (плитки-препядствия)
        for tile in world_lvl.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # проверяем не попала ли пуля в персонажей
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()


# Гранаты
class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.velocity_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.velocity_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.velocity_y

        # проверяем не попали ли в текстуры (плитки-препядствия)
        for tile in world_lvl.obstacle_list:
            # проверка коснулась ли граната стены
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1  # меняем направление
                dx = self.direction * self.speed
            # если уже открекашетили то останавливаем гранату
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # В воздухе ли граната
                if self.velocity_y < 0:
                    self.velocity_y = 0
                    dy = tile[1].bottom - self.rect.top
                # падение
                elif self.velocity_y >= 0:
                    self.velocity_y = 0
                    dy = tile[1].top - self.rect.bottom

        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        self.timer -= 1
        # Если таймер <=0 создаем взрыв
        if self.timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 0.5)
            explosion_group.add(explosion)
            # нанести урон всем, кто находится поблизости
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                        abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50


# Взрыв
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        # Добаляем все кадры в список для анимации
        self.animation_images = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.animation_images.append(img)
        self.frame_index = 0
        self.image = self.animation_images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        self.rect.x += screen_scroll

        EXPLOSION_SPEED = 4
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # если анимация завершена, удаляем взрыв
            if self.frame_index >= len(self.animation_images):
                self.kill()
            else:
                self.image = self.animation_images[self.frame_index]


# Ссоздаем спрайты
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

start_btn = Button(WIDTH // 2 - 130, HEIGHT // 2 - 150, start_img, 1)
exit_btn = Button(WIDTH // 2 - 110, HEIGHT // 2 + 50, exit_img, 1)
restart_btn = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, restart_img, 2)

# создаем список плиток мира
world_data = []
for row in range(ROWS):
    r = [-1] * COLUMNS
    world_data.append(r)

# Загружаем данные для отображения уровня в массив
with open('level_1.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for i, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[i][y] = int(tile)

world_lvl = World()
player, health_bar = world_lvl.load_world_data(world_data)

launched = True
while launched:

    clock.tick(FPS)
    if not start_game:

        screen.blit(menu_img, (0, 0))

        if start_btn.draw(screen):
            start_game = True

        if exit_btn.draw(screen):
            launched = False

    else:
        # Рисуем мир, статус бар с жизнями патронами и гранатами
        screen.blit(world_img, (0, 0))
        world_lvl.draw()
        health_bar.draw(player.health)

        draw_text('AMMO: ', font, WHITE, 10, 35)
        for i in range(player.ammo):
            screen.blit(bullet_img, (90 + (i * 10), 40))

        draw_text('GRENADES: ', font, WHITE, 10, 60)
        for i in range(player.grenades):
            screen.blit(grenade_img, (135 + (i * 15), 60))

        # рисуем игрока
        player.update()
        player.draw()

        # Рисуем ботов
        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # обновляем все спрайты
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()

        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # обновляем состояние игрока
        if player.alive:

            if shoot:
                player.shoot()

            elif grenade and not grenade_thrown and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), player.rect.top,
                                  player.direction)
                grenade_group.add(grenade)
                player.grenades -= 1
                grenade_thrown = True

            if player.in_air:
                player.update_action(2)  # 2: jump

            elif moving_left or moving_right:
                player.update_action(1)  # 1: run

            else:
                player.update_action(0)  # 0: stay

            screen_scroll = player.move(moving_left, moving_right)
            scroll_background -= screen_scroll

        else:
            screen_scroll = 0
            if restart_btn.draw(screen):
                scroll_background = 0
                world_data = reset_lvl()

                with open('level_1.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for i, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[i][y] = int(tile)

                world_lvl = World()
                player, health_bar = world_lvl.load_world_data(world_data)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            launched = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_q:
                grenade = True
            if event.key == pygame.K_w and player.alive:
                player.is_jump = True
            if event.key == pygame.K_ESCAPE:
                launched = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False

    pygame.display.update()

pygame.quit()
