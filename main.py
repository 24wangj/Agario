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
PLAYER_SPLIT_SPEED = PLAYER_SPEED * 5
PLAYER_SPLIT_DECELERATION = 0.97
PLAYER_SPLIT_SIZE_MIN = 5000
PLAYER_SPLIT_PUSH_SPEED = 2

# Cell constants
CELLS_SIZE = 400
CELLS_MAX = 1000
CELLS_EJECT_SIZE = CELLS_SIZE * 4
CELLS_EJECT_SPEED = PLAYER_SPEED * 3
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
        self.speed = PLAYER_SPEED

    def get_radius(self):
        return math.sqrt(self.size / math.pi)

    def follow(self, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and self.speed / hypotenuse or 0

        if math.fabs(hypotenuse) < PLAYER_DEADBAND:
            self.xVel = (deltaX * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
            self.yVel = (deltaY * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
        else:
            self.xVel = (deltaX * speedMod)
            self.yVel = (deltaY * speedMod)

    def move(self):
        self.x += self.xVel
        self.y += self.yVel
        if self.speed > PLAYER_SPEED:
            self.speed -= PLAYER_SPEED / self.speed

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

    def split(self, player_cell, mouse_x, mouse_y):
        self.speed = PLAYER_SPLIT_SPEED
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and self.speed / hypotenuse or 0

        self.xVel = int(deltaX * speedMod) + player_cell.xVel
        self.yVel = int(deltaY * speedMod) + player_cell.yVel

        angle = math.atan2(player_cell.y - mouse_y, player_cell.x - mouse_x) - math.pi
        self.x = (player_cell.get_radius() * math.cos(angle)) + player_cell.x
        self.y = (player_cell.get_radius() * math.sin(angle)) + player_cell.y

    def is_colliding(self, player_cell):
        return (pow(player_cell.x - self.x, 2) + pow(player_cell.y - self.y, 2)
                <= pow(self.get_radius() + player_cell.get_radius(), 2))

    def draw(self):
        radius = self.get_radius()

        if self.prevRadius < radius - PLAYER_RADIUS_INCREMENT:
            self.prevRadius += PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - radius, 2)))
        elif self.prevRadius > radius + PLAYER_RADIUS_INCREMENT:
            self.prevRadius -= PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - radius, 2)))

        self.prevRadius = min(self.prevRadius, math.sqrt(PLAYER_SIZE_MAX / math.pi))

        pygame.draw.circle(window, self.color, (get_scaled_size(self.x) - camera.x, get_scaled_size(self.y) - camera.y),
                           get_scaled_size(self.get_radius()))


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

        angle = math.atan2(player_cell.y - mouse_y, player_cell.x - mouse_x) - math.pi
        self.x = (player_cell.get_radius() * math.cos(angle)) + player_cell.x
        self.y = (player_cell.get_radius() * math.sin(angle)) + player_cell.y

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
playerList = [PlayerCell(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, PLAYER_SIZE_MIN, COLOR_PLAYER)]
camera = Camera(playerList[0].x, playerList[0].y)
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

    for p in playerList:
        p.draw()

    if DEBUG_TEXT:
        textSurface = font.render("(x, y): (" + str(int(playerList[0].x)) + ", " + str(int(playerList[0].y)) + ")",
                                  False,
                                  COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 10))
        textSurface = font.render("Size: " + str(int(playerList[0].size)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 12 + FONT_SIZE))
        textSurface = font.render("# Player Cells: " + str(len(playerList)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 14 + 2 * FONT_SIZE))
        textSurface = font.render("# Cells: " + str(len(cellsList)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 16 + 3 * FONT_SIZE))
        textSurface = font.render("Zoom: " + str(camera.zoom), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 18 + 4 * FONT_SIZE))

    pygame.display.update()


def main():
    global playerList
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(FONT_PATH, FONT_SIZE)
    running = True
    while running:
        clock.tick(FPS)

        mouseX, mouseY = mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    splitCellsList = []
                    for p in playerList:
                        playerSize = p.size
                        if playerSize > PLAYER_SPLIT_SIZE_MIN:
                            p.change_size(-playerSize / 2)
                            splitCell = PlayerCell(p.x, p.y, playerSize / 2, p.color)
                            splitCell.split(p, mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                                            mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
                            splitCellsList.append(splitCell)
                    playerList += splitCellsList
            if event.type == pygame.QUIT:
                running = False

        key = pygame.key.get_pressed()
        if key[pygame.K_w]:
            for p in playerList:
                if p.size > PLAYER_EJECT_SIZE_MIN:
                    p.change_size(-CELLS_EJECT_SIZE)
                    ejectedCell = Cell(p.x, p.y, CELLS_EJECT_SIZE, p.color)
                    ejectedCell.eject(p, mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                                      mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
                    cellsList.append(ejectedCell)

        if key[pygame.K_MINUS]:
            camera.zoom *= .95
        elif key[pygame.K_EQUALS]:
            camera.zoom *= 1.05

        if key[pygame.K_LEFTBRACKET]:
            for p in playerList:
                p.change_size(-20 * p.get_radius())
        elif key[pygame.K_RIGHTBRACKET]:
            for p in playerList:
                p.change_size(20 * p.get_radius())

        if key[pygame.K_q]:
            running = False

        averagePlayerX = 0
        averagePlayerY = 0
        averagePlayerRadius = 0
        playerListLength = len(playerList)
        for p in playerList:
            averagePlayerX += p.x
            averagePlayerY += p.y
            averagePlayerRadius += p.get_radius()

        averagePlayerX /= playerListLength
        averagePlayerY /= playerListLength
        averagePlayerRadius /= playerListLength

        # Smooth camera zoom
        camera.target = pow(100 / averagePlayerRadius, 0.5)
        if camera.zoom < camera.target - CAMERA_ZOOM_INCREMENT:
            camera.zoom += CAMERA_ZOOM_INCREMENT * (pow(camera.zoom - camera.target, 2))
        elif camera.zoom > camera.target + CAMERA_ZOOM_INCREMENT:
            camera.zoom -= CAMERA_ZOOM_INCREMENT * (pow(camera.zoom - camera.target, 2))

        camera.x = averagePlayerX * camera.zoom - WINDOW_WIDTH / 2
        camera.y = averagePlayerY * camera.zoom - WINDOW_HEIGHT / 2

        for index, p in enumerate(playerList):
            p.follow(mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                     mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
            p.move()
            nextIndex = index + 1
            while nextIndex < playerListLength:
                if p.is_colliding(playerList[nextIndex]):
                    vector = pygame.math.Vector2(playerList[nextIndex].x - p.x, playerList[nextIndex].y - p.y).normalize()
                    vector.scale_to_length(PLAYER_SPLIT_PUSH_SPEED)
                    if len(vector) == 0:
                        vector = pygame.math.Vector2(0, 1)

                    p.x -= vector.x
                    p.y -= vector.y

                    playerList[nextIndex].x += vector.x
                    playerList[nextIndex].y += vector.y

                nextIndex += 1

        for c in cellsList:
            c.move()
            for p in playerList:
                if p.overlaps(c.x, c.y, c.get_radius()):
                    p.change_size(c.size)
                    if cellsList.__contains__(c):
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
