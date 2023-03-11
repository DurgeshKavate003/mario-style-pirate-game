import pygame, sys

from pygame.math import Vector2 as vector
from pygame.image import load

from settings import *
from support import *

from editor import Editor
from level import Level

class Main:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display_surface = pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.imports()

        self.editor_active = True
        self.transition = Transition(self.toogle)

        self.editor = Editor(self.land_tiles, self.switch)
        # self.level = Level()

        # Cursor
        surf = load('../graphics/cursors/mouse.png').convert_alpha()
        cursor = pygame.cursors.Cursor((0, 0), surf)
        pygame.mouse.set_cursor(cursor)

    def imports(self):
        self.land_tiles = import_folder_dict('../graphics/terrain/land')

    def toogle(self):
         self.editor_active = not self.editor_active

    def switch(self, grid = None):
         self.transition.active = True
         if grid:
                self.level = Level(grid, self.switch)

    def run(self):
        while True:
            dt = self.clock.tick() / 1000

            if self.editor_active:
                self.editor.run(dt)

            else:
                self.level.run(dt)

            self.transition.display(dt)
            
            pygame.display.update()


class Transition:
    def __init__(self, toogle):
          self.display_surface = pygame.display.get_surface()
          self.toogle = toogle
          self.active = False

          self.border_width = 0
          self.direction = 1
          self.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
          self.radius = vector(self.center).magnitude()
          self.threshold = self.radius + 100

    def display(self, dt):
         if self.active:
            self.border_width += 500 * dt * self.direction

            if self.border_width >= self.threshold:
                 self.direction = -1
                 self.toogle()

            if self.border_width < 0:
                self.active = False
                self.border_width = 0
                self.direction = 1

            pygame.draw.circle(self.display_surface, 'black', self.center, self.radius, int(self.border_width))



if __name__ == '__main__':
	main = Main()
	main.run() 
