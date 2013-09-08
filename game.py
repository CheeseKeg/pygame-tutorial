#/usr/bin/python2

import pygame
import tmx

class Background(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super(Background, self).__init__(*groups)
        self.image = pygame.image.load('images/background.png')
        self.rect = pygame.rect.Rect((0, 0), self.image.get_size())

class Player(pygame.sprite.Sprite):
    def __init__(self, start_position, *groups):
        super(Player, self).__init__(*groups)
        self.image = pygame.image.load('images/player_right.png')
        self.right_image = self.image
        self.left_image = pygame.image.load('images/player_left.png')
        self.rect = pygame.rect.Rect(start_position, self.image.get_size())

        self.resting = False
        self.dy = 0
        self.direction = 1
        self.gun_cooldown = 0

        self.is_dead = False

    def update(self, dt, game):
        last = self.rect.copy()

        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.image = self.left_image
            self.direction = -1
            self.rect.x -= 300*dt
        if key[pygame.K_RIGHT]:
            self.image = self.right_image
            self.direction = 1
            self.rect.x += 300*dt

        if key[pygame.K_LSHIFT] and not self.gun_cooldown:
            if self.direction > 0:
                Bullet(self.rect.midright, 1, game.sprites)
            else:
                Bullet(self.rect.midleft, -1, game.sprites)
            self.gun_cooldown = 0.2
            game.sounds['shoot'].play()

        self.gun_cooldown = max(0, self.gun_cooldown - dt)

        if self.resting and key[pygame.K_SPACE]:
            self.dy = -500
            game.sounds['jump'].play()
        self.dy = min(700, self.dy + 40)

        self.rect.y += self.dy*dt

        new = self.rect

        old_resting = self.resting
        self.resting = False
        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            blockers = cell['blockers']

            if 'l' in blockers and new.right > cell.left and last.right <= cell.left:
                new.right = cell.left
            if 'r' in blockers and new.left < cell.right and last.left >= cell.right:
                new.left = cell.right
            if 't' in blockers and new.bottom > cell.top and last.bottom <= cell.top:
                new.bottom = cell.top
                if not old_resting:
                    game.sounds['land'].play()
                self.resting = True
                self.dy = 0
            if 'b' in blockers and new.top < cell.bottom and last.top >= cell.bottom:
                new.top = cell.bottom
                self.dy = 0

        game.camera_position = (new.x, new.y)

class Enemy(pygame.sprite.Sprite):
    image = pygame.image.load('images/enemy.png')
    def __init__(self, location, *groups):
        super(Enemy, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.direction = 1

    def update(self, dt, game):
        self.rect.x += self.direction*100*dt
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.rect.right = cell.left
            else:
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect):
            game.player.is_dead = True

class Bullet(pygame.sprite.Sprite):
    image = pygame.image.load('images/bullet.png')
    def __init__(self, location, direction, *groups):
        super(Bullet, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.direction = direction
        self.lifespan = 1

    def update(self, dt, game):
        self.lifespan += dt
        if self.lifespan <= 0:
            self.kill()
            return
        self.rect.x += self.direction*400*dt

        if pygame.sprite.spritecollide(self, game.enemies, True) or not self.rect.colliderect(game.tilemap.viewport):
            self.kill()

class Game(object):
    def main(self, screen):
        clock = pygame.time.Clock()

        self.background = pygame.sprite.Group()
        Background(self.background)

        self.sounds = {}
        for sound in ['jump', 'land', 'shoot']:
            self.sounds[sound] = pygame.mixer.Sound('sounds/' + sound + '.wav')

        self.tilemap = tmx.load('map.tmx', screen.get_size())

        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        start_position = (start_cell.px, start_cell.py)

        self.sprites = tmx.SpriteLayer()
        self.player = Player(start_position, self.sprites)
        self.tilemap.layers.append(self.sprites)

        self.enemies = tmx.SpriteLayer()
        for enemy in self.tilemap.layers['triggers'].find('enemy'):
            Enemy((enemy.px, enemy.py), self.enemies)
        self.tilemap.layers.append(self.enemies)


        self.tilemap.set_focus(start_position[0], start_position[1])
        
        while 1:
            dt = clock.tick(30)/1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            #screen.blit(background, (0, 0))
            self.tilemap.update(dt, self)
            self.tilemap.set_focus(
                self.tilemap.fx + (self.player.rect.x - self.tilemap.fx)/6.0,
                self.tilemap.fy + (self.player.rect.y - self.tilemap.fy)/6.0
            )
            self.background.draw(screen)
            self.tilemap.draw(screen)

            pygame.display.flip()

            if self.player.is_dead:
                print 'YOU DIED'
                return

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    Game().main(screen)
