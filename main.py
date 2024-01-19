import pygame

pygame.init()

debug = False

display_size = [900, 600]
display = pygame.display.set_mode(display_size)
pygame.display.set_caption('Platformer')

clock = pygame.time.Clock()
FPS = 60

background = pygame.image.load('dist/img/sky.png')
background = pygame.transform.scale(background, display_size)

block_size = 50
gravity = 1


def draw_grid():
    for i in range(display_size[0] // block_size):
        pygame.draw.line(display,
                         pygame.color.Color('black'),
                         (i * block_size, 0),
                         (i * block_size, display_size[1]))

    for i in range(display_size[0] // block_size):
        pygame.draw.line(display,
                         pygame.color.Color('black'),
                         (0, i * block_size),
                         (display_size[0], i * block_size))


def load_map(lvl):
    f = open(f'dist/map{lvl}.txt', 'r')
    data = f.read()
    f.close()

    game_map = data.split('\n')
    return game_map


class Player():
    def __init__(self, left, bottom):
        self.images_right = []
        self.images_left = []

        for i in range(1, 5):
            img_right = pygame.image.load(f'dist/img/guy{i}.png')
            k = img_right.get_width() / (block_size - 10)
            img_right = pygame.transform.scale(img_right,
                                               (img_right.get_width() // k,
                                                img_right.get_height() // k))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)

        self.ghostImg = pygame.image.load('dist/img/ghost.png')
        self.index = 0
        self.image = self.images_right[self.index]

        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        self.jump = True
        self.jump_force = -12
        self.speed_x = 5
        self.speed_y = gravity
        self.move_x = 0
        self.move_y = 0
        self.direction = 0

        self.score = 0

        self.walk_time = 0
        self.walk_cooldown = 5

        self.sound_coin = pygame.mixer.Sound('dist/sound/coin.wav')
        self.sound_game_over = pygame.mixer.Sound('dist/sound/game_over.wav')
        self.sound_jump = pygame.mixer.Sound('dist/sound/jump.wav')

        self.alive = True

    def draw(self):
        display.blit(self.image, self.rect)

    def update(self, world):
        key = pygame.key.get_pressed()

        if not self.alive:
            self.image = self.ghostImg
            if self.rect.y > 200:
                self.rect.y -= 5

            if key[pygame.K_SPACE] or key[pygame.K_UP]:
                world.next_level(restart=True)
                self.alive = True

            return

        self.move_x = 0

        if key[pygame.K_a] or key[pygame.K_LEFT]:
            self.move_x = -self.speed_x
            self.walk_time += 1

        if key[pygame.K_d] or key[pygame.K_RIGHT]:
            self.move_x = self.speed_x
            self.walk_time += 1

        if (key[pygame.K_SPACE] or key[pygame.K_UP]) and not self.jump:
            self.sound_jump.play()
            self.jump = True
            self.move_y = self.jump_force

        if self.walk_time == self.walk_cooldown:
            self.walk_time = 0
            self.index = (self.index + 1) % len(self.images_right)

        if self.move_x > 0:
            self.image = self.images_right[self.index]
            self.direction = 1
        elif self.move_x < 0:
            self.image = self.images_left[self.index]
            self.direction = -1
        else:
            self.index = 0
            if self.direction == -1:
                self.image = self.images_left[self.index]
            else:
                self.image = self.images_right[self.index]

        for exit_door in world.exits_group:
            if exit_door.rect.colliderect(self.rect):
                world.next_level()

        for coin in world.coin_group:
            if coin.rect.colliderect(self.rect):
                self.sound_coin.play()
                self.score += 1
                if self.score > world.high_score:
                    world.high_score = self.score
                world.coin_group.remove(coin)

        for enemy in world.enemy_group:
            if enemy.rect.colliderect(self.rect.x, self.rect.y,
                                     self.width, self.height):
                if self.move_y > 0 and self.rect.bottom < enemy.rect.center[1]:
                    world.enemy_group.remove(enemy)
                    self.jump = True
                    self.move_y = -5

        if pygame.sprite.spritecollide(self, world.enemy_group, False) or \
           pygame.sprite.spritecollide(self, world.lava_group, False):
            self.sound_game_over.play()

            self.alive = False
            self.score = 0

        for tile in world.tile_group:
            if tile.rect.colliderect(self.rect.x + self.move_x, self.rect.y,
                                     self.width, self.height):
                self.move_x = 0

            if tile.rect.colliderect(self.rect.x, self.rect.y + self.move_y,
                                  self.width, self.height):
                if self.move_y > 0:
                    self.jump = False
                    self.rect.y += tile.rect.top - self.rect.bottom
                else:
                    self.rect.y += tile.rect.bottom - self.rect.top
                self.move_y = 0

        self.rect.x += self.move_x
        self.rect.y += self.move_y
        self.move_y += self.speed_y


class Lava(pygame.sprite.Sprite):
    def __init__(self, left, bottom):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('dist/img/lava.png')

        self.image = pygame.transform.scale(img, (block_size, block_size // 2))
        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom


class Enemy(pygame.sprite.Sprite):
    def __init__(self, left, bottom):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('dist/img/blob.png')

        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom

        self.move_x = 0
        self.speed_x = 1
        self.direction = 1

    def update(self):
        self.rect.x += self.speed_x * self.direction
        self.move_x += self.speed_x
        if self.move_x == block_size:
            self.move_x = 0
            self.direction *= -1


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('dist/img/coin.png')

        self.image = pygame.transform.scale(img, (block_size // 2, block_size // 2))
        self.rect = self.image.get_rect()

        self.rect.x = x + (block_size - self.image.get_width()) // 2
        self.rect.y = y + (block_size - self.image.get_height()) // 2


class Tile(pygame.sprite.Sprite):
    def __init__(self, left, bottom, img):
        pygame.sprite.Sprite.__init__(self)
        self.image = img

        self.rect = self.image.get_rect()
        self.rect.left = left
        self.rect.bottom = bottom


class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('dist/img/exit.png')

        self.image = pygame.transform.scale(img, (block_size, block_size * 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class World():
    def __init__(self):
        self.end = False
        self.victory_sound = pygame.mixer.Sound('dist/sound/victory.mp3')

        self.font = pygame.font.Font('dist/04B_19.TTF', 32)
        self.large_font = pygame.font.Font('dist/04B_19.TTF', 64)
        self.grass_img = pygame.image.load('dist/img/grass.png')
        pygame.mixer.music.load('dist/sound/music.wav')
        pygame.mixer.music.play(-1)

        self.grass_img = pygame.transform.scale(self.grass_img, (block_size, block_size))

        self.lava_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.coin_group = pygame.sprite.Group()
        self.tile_group = pygame.sprite.Group()
        self.exits_group = pygame.sprite.Group()

        self.player = Player(0, 0)

        self.level = 1
        self.map = load_map(self.level)
        self.load_sprites()

        self.high_score = 0

    def load_sprites(self):
        self.tile_group.empty()
        self.coin_group.empty()
        self.exits_group.empty()
        self.enemy_group.empty()
        self.lava_group.empty()

        for i in range(len(self.map)):
            for j in range(len(self.map[i])):
                tile = self.map[i][j]

                if tile == '1':
                    tile = Tile(j * block_size, (i + 1) * block_size, self.grass_img)
                    self.tile_group.add(tile)

                elif tile == 'X':
                    exit_door = Exit(j * block_size, (i - 1) * block_size)
                    self.exits_group.add(exit_door)

                elif tile == 'P':
                    self.player.rect.left = j * block_size
                    self.player.rect.bottom = (i + 1) * block_size

                elif tile == 'L':
                    lava = Lava(j * block_size, (i + 1) * block_size)
                    self.lava_group.add(lava)

                elif tile == 'E':
                    enemy = Enemy(j * block_size, (i + 1) * block_size)
                    self.enemy_group.add(enemy)

                elif tile == 'C':
                    coin = Coin(j * block_size, i * block_size)
                    self.coin_group.add(coin)

    def draw(self):
        self.lava_group.draw(display)
        self.enemy_group.draw(display)
        self.coin_group.draw(display)
        self.tile_group.draw(display)
        self.exits_group.draw(display)

        self.player.draw()
        self.score_display()

    def score_display(self):
        text_score = self.font.render(f"Level: {self.level} Score: {self.player.score}",
                                      True,
                                      pygame.color.Color('white'))

        display.blit(text_score, (10, 10))

        if not self.player.alive:
            self.message_display(f'High Score: {self.high_score}',
                                 'Press space to restart')

    def message_display(self, string_1, string_2 = None):
        if string_2 is not None:
            surface_2 = self.large_font.render(str(string_2), True, (123, 123, 123))
            rect_2 = surface_2.get_rect(center=(display_size[0] / 2, display_size[1] / 2))
            display.blit(surface_2, rect_2)

        surface_1 = self.large_font.render(str(string_1), True, (100, 100, 100))
        rect_1 = surface_1.get_rect(center=(display_size[0] / 2, display_size[1] / 2 - 100))
        display.blit(surface_1, rect_1)

    def next_level(self, restart=False):
        self.lava_group.empty()
        self.enemy_group.empty()
        self.coin_group.empty()
        self.tile_group.empty()
        self.exits_group.empty()

        display.fill(pygame.color.Color('black'))
        pygame.display.flip()

        if restart:
            self.level = 1
        else:
            self.level += 1

        if self.level > 5:
            self.end = True
            self.victory_sound.play()
            display.fill(pygame.color.Color('white'))
        else:
            self.map = load_map(self.level)
            self.load_sprites()

    def update(self):
        if self.end:
            display.fill(pygame.color.Color('white'))
            self.message_display(f'Score: {self.player.score}', 'Congratulations!')

        self.player.update(self)
        self.enemy_group.update()


def start_screen(world):
    display.fill(pygame.color.Color('white'))
    world.message_display('Press any button')
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                return

            if event.type == pygame.KEYDOWN:
                return


def main():
    world = World()

    start_screen(world)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        display.blit(background, (0, 0))

        world.draw()
        world.update()

        if debug:
            draw_grid()

        pygame.display.update()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
