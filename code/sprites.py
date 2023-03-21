import pygame
from pygame.math import Vector2 as vector

from timer_ import Timer

from settings import *

from random import choice, randint

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, group, z = LEVEL_LAYERS['main']):
		super().__init__(group)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = z

class Block(Generic):
	def __init__(self, pos, size, group):
		surf = pygame.Surface(size)
		super().__init__(pos, surf, group)

class Cloud(Generic):
	def __init__(self, pos, surf, group, left_limit):
		self.left_limit = left_limit
		super().__init__(pos, surf, group, LEVEL_LAYERS['clouds'])

		# movement
		self.pos = vector(self.rect.topleft)
		self.speed = randint(20, 30)

	def update(self, dt):
		self.pos.x -= self.speed * dt
		self.rect.x = round(self.pos.x)

		if self.rect.x <= self.left_limit:
			self.kill()

# Simple animated objects
class Animated(Generic):
	def __init__(self, assets, pos, group, z = LEVEL_LAYERS['main']):
		self.animation_frames = assets
		self.frame_index = 0

		super().__init__(pos, self.animation_frames[self.frame_index], group, z)

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(self.animation_frames) else self.frame_index
		self.image = self.animation_frames[int(self.frame_index)]

	def update(self, dt):
		self.animate(dt)

class Particle(Animated):
	def __init__(self, assets, pos, group):
		super().__init__(assets, pos, group)

		self.rect = self.image.get_rect(center = pos)

	def animate(self, dt):
		self.frame_index += ANIMATION_SPEED * dt

		if self.frame_index < len(self.animation_frames):
			self.image = self.animation_frames[int(self.frame_index)]

		else:
			self.kill()

class Coin(Animated):
	def __init__(self, coin_type, assets, pos, group):
		super().__init__(assets, pos, group)

		self.rect = self.image.get_rect(center = pos)
		self.coin_type = coin_type

# Enemeies
class Spikes(Generic):
	def __init__(self, surf, pos, group):
		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

class Tooth(Generic):
	def __init__(self, assets, pos, group, collision_sprites):

		# General setup
		self.animation_frames = assets
		self.frame_index = 0

		self.orientation = 'right'

		surf = self.animation_frames[f'run_{self.orientation}'][self.frame_index]

		super().__init__(pos, surf, group)
		self.rect.bottom = self.rect.top + TILE_SIZE

		self.mask = pygame.mask.from_surface(self.image)

		# Movement
		self.direction = vector(choice((-1, 1)), 0)
		self.orientation = 'left' if self.direction.x < 0 else 'right'
		self.pos = vector(self.rect.topleft)
		self.speed = 120
		self.collision_sprites = collision_sprites

		if not [sprite for sprite in collision_sprites if sprite.rect.collidepoint(self.rect.midbottom + vector(0, 10))]:
			self.kill()

	def animate(self, dt):
		current_animation = self.animation_frames[f'run_{self.orientation}']
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(current_animation) else self.frame_index
		self.image = current_animation[int(self.frame_index)]
		self.mask = pygame.mask.from_surface(self.image)

	def move(self, dt):
		right_gap = self.rect.bottomright + vector(1, 1)
		right_block = self.rect.midright + vector(1, 0)
		left_gap = self.rect.bottomleft + vector(-1, 1)
		left_block = self.rect.midleft + vector(-1, 0)

		if self.direction.x > 0:
			floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(right_gap)]
			wall_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(right_block)]

			if wall_sprites or not floor_sprites:
				self.direction *= -1
				self.orientation = 'left'

		if self.direction.x < 0:
			if not [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(left_gap)] \
				or [sprite for sprite in self.collision_sprites if sprite.rect.collidepoint(left_block)]:
				self.direction *= -1
				self.orientation = 'right'

		self.pos.x += self.direction.x * self.speed * dt
		self.rect.x = round(self.pos.x)

	def update(self, dt):
		self.animate(dt)
		self.move(dt)
 
class Shell(Generic):
	def __init__(self, orientation, assets, pos, group, pearl_surf, damage_sprites):
		self.orientation = orientation
		self.animations_frames = assets.copy()

		if orientation == 'right':
			for key, value in self.animations_frames.items():
				self.animations_frames[key] = [pygame.transform.flip(surf, True, False) for surf in value]

		self.frame_index = 0
		self.status = 'idle'
		super().__init__(pos, self.animations_frames[self.status][self.frame_index], group)
		self.rect.bottom = self.rect.top + TILE_SIZE

		# Pearl
		self.pearl_surf = pearl_surf
		self.has_shot = False
		self.attack_countdown = Timer(2000)
		self.damage_sprites = damage_sprites

	def animate(self, dt):
		current_animation = self.animations_frames[self.status]
		self.frame_index += ANIMATION_SPEED * dt
		if self.frame_index >= len(current_animation):
			self.frame_index = 0
			if self.has_shot:
				self.attack_countdown.activate()
				self.has_shot = False

		self.image = current_animation[int(self.frame_index)]

		if int(self.frame_index) == 2 and self.status == 'attack' and not self.has_shot:
			pearl_direction = vector(-1, 0) if self.orientation == 'left' else vector(1, 0)
			offset = (pearl_direction * 50) + vector(0, -10) if self.orientation == 'left' else (pearl_direction * 20) + vector(0, -10)
			Pearl(self.rect.center + offset, pearl_direction, self.pearl_surf, [self.groups()[0], self.damage_sprites])
			self.has_shot = True

	def get_status(self):
		if vector(self.player.rect.center).distance_to(vector(self.rect.center)) < 500 and not self.attack_countdown.active:
			self.status = 'attack'
		else:
			self.status = 'idle'

	def update(self, dt):
		self.get_status()
		self.animate(dt)
		self.attack_countdown.update()

class Pearl(Generic):
	def __init__(self, pos, direction, surf, group):
		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

		# Movement
		self.pos = vector(self.rect.topleft)
		self.direction = direction
		self.speed = 150

		# Self Destruct
		self.timer = Timer(6000)
		self.timer.activate()

	def update(self, dt):
		# Movement
		self.pos.x += self.direction.x * self.speed * dt
		self.rect.x = round(self.pos.x)

		# Timer
		self.timer.update()
		if not self.timer.active:
			self.kill()

class Player(Generic):
	def __init__(self, pos, assets, group, collision_sprites):
		# Animation
		self.animation_frames = assets
		self.frame_index = 0
		self.status = 'idle'
		self.orientation = 'right'

		surf = self.animation_frames[f'{self.status}_{self.orientation}'][self.frame_index]

		super().__init__(pos, surf, group)
		self.mask = pygame.mask.from_surface(self.image)

		# movement
		self.direction = vector()
		self.pos = vector(self.rect.center)
		self.speed = 300

		self.gravity = 4
		self.on_floor = False

		# collision
		self.collision_sprites = collision_sprites
		self.hitbox = self.rect.inflate(-50, 0)

		# timer
		self.invul_timer = Timer(200)

	def damage(self):
		if not self.invul_timer.active:
			self.invul_timer.activate()
			self.direction.y -= 1.5

	def get_status(self):
		if self.direction.y < 0:
			self.status = 'jump'
		
		elif self.direction.y > 1:
			self.status = 'fall'

		else:
			self.status = 'run' if self.direction.x != 0 else 'idle'

	def animate(self, dt):
		current_animation = self.animation_frames[f'{self.status}_{self.orientation}']
		self.frame_index += ANIMATION_SPEED * dt
		self.frame_index = 0 if self.frame_index >= len(current_animation) else self.frame_index
		self.image = current_animation[int(self.frame_index)]
		self.mask = pygame.mask.from_surface(self.image)

		if self.invul_timer.active:
			surf = self.mask.to_surface()
			surf.set_colorkey('black')
			self.image = surf

	def input(self):
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RIGHT]:
			self.direction.x = 1
			self.orientation = 'right'
		elif keys[pygame.K_LEFT]:
			self.direction.x = -1
			self.orientation = 'left'
		else:
			self.direction.x = 0

		if keys[pygame.K_SPACE] and self.on_floor:
			self.direction.y = -2

		# if keys[pygame.K_DOWN]:
		# 	self.direction.y = 1
		# elif keys[pygame.K_UP]:
		# 	self.direction.y = -1
		# else:
		# 	self.direction.y = 0

	def move(self, dt):
		# Horizontal Movement
		self.pos.x += self.direction.x * self.speed * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collision('horizontal')

		# Vertical Movement
		self.pos.y += self.direction.y * self.speed * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collision('vertical')

	def apply_gravity(self, dt):
		self.direction.y += self.gravity * dt
		self.rect.y += self.direction.y

	def check_of_floor(self):
		floor_rect = pygame.Rect(self.hitbox.bottomleft, (self.hitbox.width, 2))
		floor_sprites = [sprite for sprite in self.collision_sprites if sprite.rect.colliderect(floor_rect)]

		self.on_floor = True if floor_sprites else False

	def collision(self, direction):
		for sprite in self.collision_sprites:
			if sprite.rect.colliderect(self.hitbox):
				if direction == 'horizontal':
					self.hitbox.right = sprite.rect.left if self.direction.x > 0 else self.hitbox.right
					self.hitbox.left = sprite.rect.right if self.direction.x < 0 else self.hitbox.left
						
					self.rect.centerx, self.pos.x= self.hitbox.centerx, self.hitbox.centerx
				else:
					self.hitbox.top = sprite.rect.bottom if self.direction.y < 0 else self.hitbox.top
					self.hitbox.bottom = sprite.rect.top if self.direction.y > 0 else self.hitbox.bottom

					self.rect.centery, self.pos.y = self.hitbox.centery, self.hitbox.centery

					self.direction.y = 0

	def update(self, dt):
		self.input()
		self.apply_gravity(dt)
		self.move(dt)
		self.check_of_floor()

		self.invul_timer.update()

		self.get_status()
		self.animate(dt)
