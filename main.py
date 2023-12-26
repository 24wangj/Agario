import math
from random import random

import pygame
from pygame import mouse

# Window constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "agar.io"
DEBUG_TEXT = True
FONT_PATH = "Ubuntu-Bold.ttf"
FONT_SIZE = 16

# Camera constants
FPS = 60
CAMERA_ZOOM_START = 0.2
CAMERA_ZOOM_INCREMENT = 0.1

# Map constants
MAP_DIMENSIONS = 3000
MAP_SPACE = 50
MAP_LINE_WIDTH = 1

# Player constants
PLAYER_SIZE_MIN = 1000
PLAYER_SIZE_MAX = 5000000
PLAYER_SPEED = 4
PLAYER_DEADBAND = 40
PLAYER_RADIUS_INCREMENT = 0.05
PLAYER_EJECT_SIZE_MIN = 3000

# Cell constants
CELLS_SIZE = 400
CELLS_MAX = 1000
CELLS_EJECT_SIZE = CELLS_SIZE * 4
CELLS_EJECT_SPEED = PLAYER_SPEED * 4
CELLS_EJECT_DECELERATION = 0.97

# Colors
COLOR_WHITE = (242, 251, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRID = (182, 188, 190)
COLOR_PLAYER = (255, 0, 0)


def get_scaled_size(size):
    return int(size * camera.zoom)


class Camera:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.zoom = CAMERA_ZOOM_START


class PlayerCell:
    def __init__(self, x, y, size, color):
        self.yVel = None
        self.xVel = None
        self.x = x
        self.y = y
        self.size = size
        self.prevRadius = self.get_radius()
        self.color = color

    def get_radius(self):
        return math.sqrt(self.size / math.pi)

    def follow(self, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and PLAYER_SPEED / hypotenuse or 0

        if math.fabs(hypotenuse) < PLAYER_DEADBAND:
            self.xVel = (deltaX * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
            self.yVel = (deltaY * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
        else:
            self.xVel = (deltaX * speedMod)
            self.yVel = (deltaY * speedMod)

    def move(self):
        self.x += self.xVel
        self.y += self.yVel

        # Prevents player from leaving the map
        if self.x < 0:
            self.x = 0
        elif self.x > MAP_DIMENSIONS:
            self.x = MAP_DIMENSIONS
        if self.y < 0:
            self.y = 0
        elif self.y > MAP_DIMENSIONS:
            self.y = MAP_DIMENSIONS

    def overlaps(self, x, y, r):
        distSq = int(math.sqrt(pow(self.x - x, 2) + pow(self.y - y, 2)))
        if distSq + r < self.get_radius():
            return True
        return False

    def change_size(self, size):
        nextSize = self.size + size
        if nextSize < PLAYER_SIZE_MIN:
            nextSize = PLAYER_SIZE_MIN
        elif nextSize > PLAYER_SIZE_MAX:
            nextSize = PLAYER_SIZE_MAX
        self.size = nextSize

    def draw(self):
        radius = self.get_radius()

        if self.prevRadius < radius - PLAYER_RADIUS_INCREMENT:
            self.prevRadius += PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - radius, 2)))
        elif self.prevRadius > radius + PLAYER_RADIUS_INCREMENT:
            self.prevRadius -= PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - radius, 2)))

        self.prevRadius = min(self.prevRadius, math.sqrt(PLAYER_SIZE_MAX / math.pi))

        pygame.draw.circle(window, self.color, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2),
                           get_scaled_size(self.prevRadius))


class Cell:

    def __init__(self, x, y, size, color):
        self.yVel = 0
        self.xVel = 0
        self.x = x
        self.y = y
        self.size = size
        self.color = color

    def get_radius(self):
        return math.sqrt(self.size / math.pi)

    def eject(self, player_cell, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and CELLS_EJECT_SPEED / hypotenuse or 0

        self.xVel = int(deltaX * speedMod) + player_cell.xVel
        self.yVel = int(deltaY * speedMod) + player_cell.yVel

        angle = math.atan2(player.y - mouse_y, player.x - mouse_x) - math.pi
        self.x = (player.get_radius() * math.cos(angle)) + player.x
        self.y = (player.get_radius() * math.sin(angle)) + player.y

    def move(self):
        self.x += self.xVel
        self.y += self.yVel

        self.xVel *= CELLS_EJECT_DECELERATION
        self.yVel *= CELLS_EJECT_DECELERATION

        # Prevents cell from leaving the map
        if self.x < 0:
            self.x = 0
        elif self.x > MAP_DIMENSIONS:
            self.x = MAP_DIMENSIONS
        if self.y < 0:
            self.y = 0
        elif self.y > MAP_DIMENSIONS:
            self.y = MAP_DIMENSIONS

    def draw(self):
        pygame.draw.circle(window, self.color, (get_scaled_size(self.x) - camera.x, get_scaled_size(self.y) - camera.y),
                           get_scaled_size(self.get_radius()))


# Game objects
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
player = PlayerCell(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, PLAYER_SIZE_MIN, COLOR_PLAYER)
camera = Camera(player.x, player.y)
cellsList = []
for a in range(CELLS_MAX):
    cellsList.append(Cell(int(random() * MAP_DIMENSIONS),
                          int(random() * MAP_DIMENSIONS), CELLS_SIZE,
                          (int(random() * 250), int(random() * 250),
                           int(random() * 250))))


def draw_window(font):
    window.fill(COLOR_WHITE)

    for m in range(0, MAP_DIMENSIONS + MAP_SPACE, MAP_SPACE):
        pygame.draw.line(window, COLOR_GRID,
                         (get_scaled_size(m) - camera.x, -camera.y),
                         (get_scaled_size(m) - camera.x, get_scaled_size(MAP_DIMENSIONS) - camera.y),
                         MAP_LINE_WIDTH)
        pygame.draw.line(window, COLOR_GRID,
                         (get_scaled_size(MAP_DIMENSIONS) - camera.x, get_scaled_size(m) - camera.y),
                         (-camera.x, get_scaled_size(m) - camera.y), MAP_LINE_WIDTH)

    for c in cellsList:
        c.draw()

    player.draw()

    if DEBUG_TEXT:
        textSurface = font.render("(x, y): (" + str(int(player.x)) + ", " + str(int(player.y)) + ")", False,
                                  COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 10))
        textSurface = font.render("Size: " + str(int(player.size)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 12 + FONT_SIZE))
        textSurface = font.render("# Cells: " + str(len(cellsList)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 14 + 2 * FONT_SIZE))
        textSurface = font.render("Zoom: " + str(camera.zoom), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 16 + 3 * FONT_SIZE))

    pygame.display.update()


def main():
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(FONT_PATH, FONT_SIZE)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouseX, mouseY = mouse.get_pos()

        key = pygame.key.get_pressed()
        if key[pygame.K_w]:
            if player.size > PLAYER_EJECT_SIZE_MIN:
                player.change_size(-CELLS_EJECT_SIZE)
                ejectedCell = Cell(player.x, player.y, CELLS_EJECT_SIZE, player.color)
                ejectedCell.eject(player, mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                                  mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
                cellsList.append(ejectedCell)
        elif key[pygame.K_MINUS]:
            camera.zoom *= .95
        elif key[pygame.K_EQUALS]:
            camera.zoom *= 1.05
        elif key[pygame.K_LEFTBRACKET]:
            player.change_size(-20 * player.get_radius())
        elif key[pygame.K_RIGHTBRACKET]:
            player.change_size(20 * player.get_radius())
        elif key[pygame.K_q]:
            running = False

        # Smooth camera zoom
        camera.target = pow(100 / player.get_radius(), 0.5)
        if camera.zoom < camera.target - CAMERA_ZOOM_INCREMENT:
            camera.zoom += CAMERA_ZOOM_INCREMENT * (pow(camera.zoom - camera.target, 2))
        elif camera.zoom > camera.target + CAMERA_ZOOM_INCREMENT:
            camera.zoom -= CAMERA_ZOOM_INCREMENT * (pow(camera.zoom - camera.target, 2))

        camera.x = player.x * camera.zoom - WINDOW_WIDTH / 2
        camera.y = player.y * camera.zoom - WINDOW_HEIGHT / 2

        player.follow(mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                      mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
        player.move()

        for c in cellsList:
            c.move()
            if player.overlaps(c.x, c.y, c.get_radius()):
                player.change_size(c.size)
                cellsList.remove(c)

        # Generates new cells
        cellsListLength = len(cellsList)
        if cellsListLength < CELLS_MAX and clock.tick() % (cellsListLength / 4) == 0:
            cellsList.append(Cell(int(random() * MAP_DIMENSIONS),
                                  int(random() * MAP_DIMENSIONS), CELLS_SIZE,
                                  (int(random() * 250), int(random() * 250),
                                   int(random() * 250))))

        # print(clock.tick())

        draw_window(font)

    pygame.quit()


main()
