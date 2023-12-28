import math
from random import random

import pygame
from pygame import mouse

# Window variables
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "agar.io"
DEBUG_TEXT = True
FONT_PATH = "Ubuntu-Bold.ttf"
FONT_SIZE = 16

# Camera variables
deltaTime = 0
FPS = 60
CAMERA_ZOOM_START = 0.2
CAMERA_ZOOM_INCREMENT = 0.2
CAMERA_ZOOM_DEADBAND = 0.01

# Map variables
MAP_DIMENSIONS = 3000
MAP_SPACE = 50
MAP_LINE_WIDTH = 1

# Player variables
PLAYER_SIZE_MIN = 1000
PLAYER_SIZE_MAX = 5000000
PLAYER_SPEED = 4
PLAYER_ACCELERATION = 0.5
PLAYER_DEADBAND = 40
PLAYER_RADIUS_INCREMENT = 0.05
PLAYER_EJECT_SIZE_MIN = 3000
PLAYER_SPLIT_SPEED = 24
PLAYER_SPLIT_DECELERATION = 1.04
PLAYER_SPLIT_DECELERATION_DEADBAND = 0.1
PLAYER_SPLIT_SIZE_MIN = 6000
PLAYER_PUSH_DEADBAND = 0.05
PLAYER_MERGE_TIME = 60
PLAYER_MERGE_SPEED = 0.5
PLAYER_MERGE_DEADBAND = 10

# Cell variables
CELLS_SIZE = 400
CELLS_MAX = 1000
CELLS_SPAWN_FREQUENCY = 20
CELLS_EJECT_SIZE = 1600
CELLS_EJECT_SPEED = 12
CELLS_EJECT_DECELERATION = 0.97
CELLS_EJECT_DECELERATION_DEADBAND = 0.1

# Colors
COLOR_WHITE = (242, 251, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRID = (182, 188, 190)
COLOR_PLAYER = (255, 0, 0)

# Game objects
global window
global clock
global playerList
global camera
global cellsList


def get_scaled_size(size):
    return int(size * camera.zoom)


class Camera:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.zoom_target = CAMERA_ZOOM_START
        self.zoom = CAMERA_ZOOM_START

    def update_zoom(self):
        if self.zoom < self.zoom_target - CAMERA_ZOOM_DEADBAND:
            self.zoom += CAMERA_ZOOM_INCREMENT * (pow(self.zoom - self.zoom_target, 2))
        elif self.zoom > self.zoom_target + CAMERA_ZOOM_DEADBAND:
            self.zoom -= CAMERA_ZOOM_INCREMENT * (pow(self.zoom - self.zoom_target, 2))


class PlayerCell:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.prevRadius = self.radius
        self.color = color
        self.xVel = 0
        self.yVel = 0
        self.xAcc = 0
        self.yAcc = 0
        self.xSplitVel = 0
        self.ySplitVel = 0
        self.splitTimer = None

    def distance_to(self, x, y):
        return math.sqrt(pow(x - self.x, 2) + pow(y - self.y, 2))

    def follow(self, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and PLAYER_ACCELERATION / hypotenuse or 0

        if math.fabs(hypotenuse) < PLAYER_DEADBAND:
            self.xAcc = (deltaX * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
            self.yAcc = (deltaY * ((hypotenuse / PLAYER_DEADBAND) * speedMod))
        else:
            self.xAcc = (deltaX * speedMod)
            self.yAcc = (deltaY * speedMod)

    def move(self):
        self.xVel += self.xAcc
        self.yVel += self.yAcc

        self.x += self.xVel + self.xSplitVel
        self.y += self.yVel + self.ySplitVel

        # Gradually decreases velocity after splitting
        self.xSplitVel = self.xSplitVel / PLAYER_SPLIT_DECELERATION if (math.fabs(self.xSplitVel) >
                                                                        PLAYER_SPLIT_DECELERATION_DEADBAND) else 0
        self.ySplitVel = self.ySplitVel / PLAYER_SPLIT_DECELERATION if (math.fabs(self.ySplitVel) >
                                                                        PLAYER_SPLIT_DECELERATION_DEADBAND) else 0

        # Caps velocity to maximum speed
        if math.sqrt(pow(self.xVel, 2) + pow(self.yVel, 2)) > PLAYER_SPEED:
            velVector = pygame.math.Vector2(self.xVel, self.yVel).normalize()
            velVector.scale_to_length(PLAYER_SPEED)
            self.xVel = velVector.x
            self.yVel = velVector.y

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
        if distSq + r < self.radius:
            return True
        return False

    def change_size(self, size):
        nextSize = self.size + size

        if nextSize < PLAYER_SIZE_MIN:
            nextSize = PLAYER_SIZE_MIN
        elif nextSize > PLAYER_SIZE_MAX:
            nextSize = PLAYER_SIZE_MAX
        self.size = nextSize

        self.radius = math.sqrt(self.size / math.pi)

    def split(self, player_cell, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and PLAYER_SPLIT_SPEED / hypotenuse or 0

        self.xSplitVel = int(deltaX * speedMod) + player_cell.xVel
        self.ySplitVel = int(deltaY * speedMod) + player_cell.yVel

        angle = math.atan2(player_cell.y - mouse_y, player_cell.x - mouse_x) - math.pi
        self.x = (player_cell.radius * math.cos(angle)) + player_cell.x
        self.y = (player_cell.radius * math.sin(angle)) + player_cell.y

    def is_colliding(self, player_cell):
        return (pow(player_cell.x - self.x, 2) + pow(player_cell.y - self.y, 2)
                <= pow(self.radius + player_cell.radius, 2))

    def draw(self):
        # if self.prevRadius < self.radius - PLAYER_RADIUS_INCREMENT:
        #     self.prevRadius += PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - self.radius, 2)))
        # elif self.prevRadius > self.radius + PLAYER_RADIUS_INCREMENT:
        #     self.prevRadius -= PLAYER_RADIUS_INCREMENT * (math.fabs(pow(self.prevRadius - self.radius, 2)))
        #
        # self.prevRadius = min(self.prevRadius, math.sqrt(PLAYER_SIZE_MAX / math.pi))

        pygame.draw.circle(window, self.color, (get_scaled_size(self.x) - camera.x, get_scaled_size(self.y) - camera.y),
                           get_scaled_size(self.radius))


class Cell:

    def __init__(self, x, y, size, color):
        self.yVel = 0
        self.xVel = 0
        self.x = x
        self.y = y
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.color = color

    def eject(self, player_cell, mouse_x, mouse_y):
        deltaX = mouse_x - self.x
        deltaY = mouse_y - self.y
        hypotenuse = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        # Prevents division by zero
        speedMod = hypotenuse and CELLS_EJECT_SPEED / hypotenuse or 0

        self.xVel = int(deltaX * speedMod) + player_cell.xVel
        self.yVel = int(deltaY * speedMod) + player_cell.yVel

        angle = math.atan2(player_cell.y - mouse_y, player_cell.x - mouse_x) - math.pi
        self.x = (player_cell.radius * math.cos(angle)) + player_cell.x
        self.y = (player_cell.radius * math.sin(angle)) + player_cell.y

    def move(self):
        self.x += self.xVel
        self.y += self.yVel

        self.xVel = self.xVel * CELLS_EJECT_DECELERATION if (
                math.fabs(self.xVel) > CELLS_EJECT_DECELERATION_DEADBAND) else 0
        self.yVel = self.yVel * CELLS_EJECT_DECELERATION if (
                math.fabs(self.yVel) > CELLS_EJECT_DECELERATION_DEADBAND) else 0

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
                           get_scaled_size(self.radius))


def generate_cell():
    return Cell(int(random() * MAP_DIMENSIONS),
                int(random() * MAP_DIMENSIONS), CELLS_SIZE,
                (int(random() * 200) + 50,
                 int(random() * 200) + 50,
                 int(random() * 200) + 50))


def reset_map():
    global window, clock, playerList, camera, cellsList

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    playerList = [PlayerCell(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, PLAYER_SIZE_MIN, COLOR_PLAYER)]
    camera = Camera(playerList[0].x, playerList[0].y)
    cellsList = []

    for c in range(CELLS_MAX):
        cellsList.append(generate_cell())


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
        textSurface = font.render("FPS: " + str(int(clock.get_fps())), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 10))
        textSurface = font.render("(x, y)[0]: (" + str(int(playerList[0].x)) + ", " + str(int(playerList[0].y)) + ")",
                                  False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 12 + FONT_SIZE))
        textSurface = font.render("Size[0]: " + str(int(playerList[0].size)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 14 + 2 * FONT_SIZE))
        textSurface = font.render("# Player Cells: " + str(len(playerList)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 16 + 3 * FONT_SIZE))
        textSurface = font.render("# Cells: " + str(len(cellsList)), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 18 + 4 * FONT_SIZE))
        textSurface = font.render("Zoom: " + str(camera.zoom), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 20 + 5 * FONT_SIZE))

    pygame.display.update()


def main():
    global playerList, deltaTime

    reset_map()
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(WINDOW_TITLE)
    font = pygame.font.Font(FONT_PATH, FONT_SIZE)
    running = True

    while running:
        clock.tick(FPS)
        deltaTime += 1
        mouseX, mouseY = mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    splitCellsList = []
                    for p in playerList:
                        playerSize = p.size
                        if playerSize > PLAYER_SPLIT_SIZE_MIN:
                            p.change_size(-playerSize / 2)
                            p.splitTimer = 0
                            splitCell = PlayerCell(p.x, p.y, playerSize / 2, p.color)
                            splitCell.splitTimer = 0
                            splitCell.split(p, mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                                            mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
                            splitCellsList.append(splitCell)
                    playerList += splitCellsList

                elif event.key == pygame.K_r:
                    reset_map()

                elif event.key == pygame.K_q:
                    running = False

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
                p.change_size(-20 * p.radius)
        elif key[pygame.K_RIGHTBRACKET]:
            for p in playerList:
                p.change_size(20 * p.radius)

        averagePlayerX = 0
        averagePlayerY = 0
        averagePlayerRadius = 0
        playerListLength = len(playerList)

        for index, p in enumerate(playerList):
            averagePlayerX += p.x
            averagePlayerY += p.y
            averagePlayerRadius += p.radius

            p.follow(mouseX + (camera.x + WINDOW_WIDTH / 2) / camera.zoom - WINDOW_WIDTH / 2,
                     mouseY + (camera.y + WINDOW_HEIGHT / 2) / camera.zoom - WINDOW_HEIGHT / 2)
            p.move()

            p.splitTimer = p.splitTimer + 1 if p.splitTimer is not None and p.splitTimer < PLAYER_MERGE_TIME else None
            nextIndex = index + 1

            # Collision between player cells
            while nextIndex < playerListLength:
                if p.splitTimer is None and playerList[nextIndex].splitTimer is None:
                    if p.is_colliding(playerList[nextIndex]):
                        vector = pygame.math.Vector2(playerList[nextIndex].x - p.x, playerList[nextIndex].y - p.y)

                        if vector.length() == 0:
                            vector = pygame.math.Vector2(0, 1)
                        else:
                            vector.normalize()
                            vector.scale_to_length(PLAYER_MERGE_SPEED)

                        p.x += vector.x
                        p.y += vector.y

                        playerList[nextIndex].x -= vector.x
                        playerList[nextIndex].y -= vector.y

                    if playerList[nextIndex].x - PLAYER_MERGE_DEADBAND < p.x < \
                            playerList[nextIndex].x + PLAYER_MERGE_DEADBAND and \
                            playerList[nextIndex].y - PLAYER_MERGE_DEADBAND < \
                            p.y < playerList[nextIndex].y + PLAYER_MERGE_DEADBAND:
                        p.change_size(p.size + playerList[nextIndex].size)
                        playerList.remove(playerList[nextIndex])
                        playerListLength -= 1
                else:
                    if p.is_colliding(playerList[nextIndex]):
                        vector = pygame.math.Vector2(playerList[nextIndex].x - p.x, playerList[nextIndex].y - p.y)

                        if vector.length() == 0:
                            vector = pygame.math.Vector2(0, 1)
                        else:
                            vector.normalize()
                            vector.scale_to_length(((p.radius + playerList[nextIndex].radius) - (
                                playerList[nextIndex].distance_to(p.x, p.y))) / 2)

                        p.x = p.x - vector.x if math.fabs(vector.x) > PLAYER_PUSH_DEADBAND else p.x
                        p.y = p.y - vector.y if math.fabs(vector.y) > PLAYER_PUSH_DEADBAND else p.y

                        playerList[nextIndex].x = playerList[nextIndex].x + vector.x if math.fabs(
                            vector.x) > PLAYER_PUSH_DEADBAND else playerList[nextIndex].x
                        playerList[nextIndex].y = playerList[nextIndex].y + vector.y if math.fabs(
                            vector.y) > PLAYER_PUSH_DEADBAND else playerList[nextIndex].y

                nextIndex += 1

        for c in cellsList:
            c.move()
            for p in playerList:
                if p.overlaps(c.x, c.y, c.radius):
                    p.change_size(c.size)
                    if cellsList.__contains__(c):
                        cellsList.remove(c)

        # Generates new cells
        cellsListLength = len(cellsList)
        if cellsListLength < CELLS_MAX and deltaTime % (
                int((cellsListLength + CELLS_SPAWN_FREQUENCY) / CELLS_SPAWN_FREQUENCY)) == 0:
            deltaTime = 0
            cellsList.append(generate_cell())

        # Smooth camera zoom
        averagePlayerX /= playerListLength
        averagePlayerY /= playerListLength
        # averagePlayerRadius /= playerListLength

        camera.zoom_target = pow(100 / averagePlayerRadius, 0.5)
        camera.update_zoom()

        camera.x = averagePlayerX * camera.zoom - WINDOW_WIDTH / 2
        camera.y = averagePlayerY * camera.zoom - WINDOW_HEIGHT / 2

        draw_window(font)

    pygame.quit()


main()
