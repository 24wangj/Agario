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
CAMERA_POS_FACTOR = 0.3
CAMERA_ZOOM_START = 0.2
CAMERA_ZOOM_FACTOR = 0.01
CAMERA_ZOOM_DEADBAND = 0.01

# Map variables
MAP_DIMENSIONS = 3000
MAP_SPACE = 50
MAP_LINE_WIDTH = 1

# Player variables
PLAYER_SIZE_START = 100000
PLAYER_SIZE_MIN = 1000
PLAYER_SIZE_MAX = 5000000
PLAYER_SPEED = 4
PLAYER_ACCELERATION = 0.5
PLAYER_DEADBAND = 40
PLAYER_RADIUS_FACTOR = 0.1
PLAYER_EJECT_SIZE_MIN = 3000
PLAYER_SPLIT_SPEED = 30
PLAYER_SPLIT_DECELERATION = 1.04
PLAYER_SPLIT_DECELERATION_DEADBAND = 0.1
PLAYER_SPLIT_SIZE_MIN = 6000
PLAYER_SPLIT_MAX = 16
PLAYER_PUSH_DEADBAND = 0.05
PLAYER_MERGE_TIME = FPS * 10
PLAYER_MERGE_SPEED = 0.4
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

# Game objects
global window
global clock
global playerList
global camera
global cellsList


def get_scaled_size(size):
    return int(size * camera.zoom)


class Camera:
    def __init__(self, pos):
        self.pos_target = pos
        self.pos = pos
        self.zoom_target = CAMERA_ZOOM_START
        self.zoom = CAMERA_ZOOM_START

    def update_zoom(self):
        vector = (self.zoom_target - self.zoom) * CAMERA_ZOOM_FACTOR
        self.zoom += vector

    def update_pos(self):
        vector = (self.pos_target - self.pos) * CAMERA_POS_FACTOR
        self.pos += vector


class PlayerCell:
    def __init__(self, pos, size, color):
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.split_vel = pygame.math.Vector2(0, 0)
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.radius_drawn = self.radius
        self.color = color
        self.split_timer = None

    def follow(self, mouse_pos):
        deltaPos = (mouse_pos - self.pos).normalize()
        deltaPos.scale_to_length(PLAYER_ACCELERATION)
        self.acc.x = deltaPos.x
        self.acc.y = deltaPos.y

    def move(self):
        self.vel += self.acc
        self.pos += self.vel + self.split_vel
        # Gradually decreases velocity after splitting
        self.split_vel = self.split_vel / PLAYER_SPLIT_DECELERATION if \
            self.split_vel.length() > PLAYER_SPLIT_DECELERATION_DEADBAND else pygame.math.Vector2(0, 0)

        # Caps velocity to maximum speed
        if self.vel.length() > PLAYER_SPEED:
            velVector = self.vel.normalize()
            velVector.scale_to_length(PLAYER_SPEED)
            self.vel = velVector

        # Prevents player from leaving the map
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > MAP_DIMENSIONS:
            self.pos.x = MAP_DIMENSIONS
        if self.pos.y < 0:
            self.pos.y = 0
        elif self.pos.y > MAP_DIMENSIONS:
            self.pos.y = MAP_DIMENSIONS

    def overlaps(self, pos, r):
        distSq = int((self.pos - pos).length())
        if distSq + r < self.radius:
            return True
        return False

    def change_size(self, size):
        self.size += size
        if self.size < PLAYER_SIZE_MIN:
            self.size = PLAYER_SIZE_MIN
        elif self.size > PLAYER_SIZE_MAX:
            self.size = PLAYER_SIZE_MAX
        self.radius = math.sqrt(self.size / math.pi)

    def split(self, player_cell, mouse_pos):
        deltaPos = mouse_pos - self.pos
        hypotenuse = deltaPos.length()
        # Prevents division by zero
        speedMod = hypotenuse and PLAYER_SPLIT_SPEED / hypotenuse or 0

        self.split_vel = deltaPos * speedMod + player_cell.vel

        angle = math.atan2(player_cell.pos.y - mouse_pos.y, player_cell.pos.x - mouse_pos.x) - math.pi
        self.pos.x = (player_cell.radius * math.cos(angle)) + player_cell.pos.x
        self.pos.y = (player_cell.radius * math.sin(angle)) + player_cell.pos.y

    def is_colliding(self, player_cell):
        return (pow(player_cell.pos.x - self.pos.x, 2) + pow(player_cell.pos.y - self.pos.y, 2)
                <= pow(self.radius + player_cell.radius, 2))

    def draw(self):
        vector = (self.radius - self.radius_drawn) * PLAYER_RADIUS_FACTOR
        self.radius_drawn += vector

        pygame.draw.circle(window, self.color,
                           (get_scaled_size(self.pos.x) - camera.pos.x, get_scaled_size(self.pos.y) - camera.pos.y),
                           get_scaled_size(self.radius_drawn))


class Cell:

    def __init__(self, pos, size, color):
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.color = color

    def eject(self, player_cell, mouse_pos):
        deltaPos = mouse_pos - self.pos
        hypotenuse = deltaPos.length()
        # Prevents division by zero
        speedMod = hypotenuse and CELLS_EJECT_SPEED / hypotenuse or 0

        self.vel = deltaPos * speedMod + player_cell.vel

        angle = math.atan2(player_cell.pos.y - mouse_pos.y, player_cell.pos.x - mouse_pos.x) - math.pi
        self.pos.x = (player_cell.radius * math.cos(angle)) + player_cell.pos.x
        self.pos.y = (player_cell.radius * math.sin(angle)) + player_cell.pos.y

    def move(self):
        self.pos += self.vel
        self.vel = self.vel * CELLS_EJECT_DECELERATION if self.vel.length() > CELLS_EJECT_DECELERATION_DEADBAND else pygame.math.Vector2(
            0, 0)

        # Prevents cell from leaving the map
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > MAP_DIMENSIONS:
            self.pos.x = MAP_DIMENSIONS
        if self.pos.y < 0:
            self.pos.y = 0
        elif self.pos.y > MAP_DIMENSIONS:
            self.pos.y = MAP_DIMENSIONS

    def draw(self):
        pygame.draw.circle(window, self.color,
                           (get_scaled_size(self.pos.x) - camera.pos.x, get_scaled_size(self.pos.y) - camera.pos.y),
                           get_scaled_size(self.radius))


def generate_cell():
    return Cell(pygame.math.Vector2(int(random() * MAP_DIMENSIONS),
                                    int(random() * MAP_DIMENSIONS)), CELLS_SIZE,
                (int(random() * 200) + 50,
                 int(random() * 200) + 50,
                 int(random() * 200) + 50))


def reset_map():
    global window, clock, playerList, camera, cellsList

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    playerList = [PlayerCell(
        pygame.math.Vector2(pygame.math.Vector2(int(random() * MAP_DIMENSIONS), int(random() * MAP_DIMENSIONS))),
        PLAYER_SIZE_START, (int(random() * 200) + 50, int(random() * 200) + 50, int(random() * 200) + 50))]
    camera = Camera(pygame.math.Vector2(playerList[0].pos.x, playerList[0].pos.y))
    cellsList = []

    for c in range(CELLS_MAX):
        cellsList.append(generate_cell())


def draw_window(font):
    window.fill(COLOR_WHITE)

    for m in range(0, MAP_DIMENSIONS + MAP_SPACE, MAP_SPACE):
        pygame.draw.line(window, COLOR_GRID,
                         (get_scaled_size(m) - camera.pos.x, -camera.pos.y),
                         (get_scaled_size(m) - camera.pos.x, get_scaled_size(MAP_DIMENSIONS) - camera.pos.y),
                         MAP_LINE_WIDTH)
        pygame.draw.line(window, COLOR_GRID,
                         (get_scaled_size(MAP_DIMENSIONS) - camera.pos.x, get_scaled_size(m) - camera.pos.y),
                         (-camera.pos.x, get_scaled_size(m) - camera.pos.y), MAP_LINE_WIDTH)

    for c in cellsList:
        c.draw()

    for p in playerList:
        p.draw()

    if DEBUG_TEXT:
        textSurface = font.render("FPS: " + str(int(clock.get_fps())), False, COLOR_BLACK, COLOR_WHITE)
        window.blit(textSurface, (10, 10))
        textSurface = font.render(
            "(x, y)[0]: (" + str(int(playerList[0].pos.x)) + ", " + str(int(playerList[0].pos.y)) + ")",
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
        mousePos = pygame.math.Vector2((mouseX + camera.pos.x) / camera.zoom, (mouseY + camera.pos.y) / camera.zoom)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    splitCellsList = []
                    for p in playerList:
                        playerSize = p.size
                        if playerSize > PLAYER_SPLIT_SIZE_MIN and len(playerList) < PLAYER_SPLIT_MAX:
                            p.change_size(-playerSize / 2)
                            p.split_timer = 0
                            splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), playerSize / 2, p.color)
                            splitCell.split(p, mousePos)
                            splitCell.split_timer = 0
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
                    ejectedCell = Cell(pygame.math.Vector2(p.pos.x, p.pos.y), CELLS_EJECT_SIZE, p.color)
                    ejectedCell.eject(p, mousePos)
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

        averagePlayerPos = pygame.math.Vector2(0, 0)
        totalPlayerRadius = 0
        playerListLength = len(playerList)

        for index, p in enumerate(playerList):
            averagePlayerPos += p.pos
            totalPlayerRadius += p.radius

            p.follow(mousePos)
            p.move()

            p.split_timer = p.split_timer + 1 if p.split_timer is not None and p.split_timer < PLAYER_MERGE_TIME else None
            nextIndex = index + 1

            # Collision between player cells
            while nextIndex < playerListLength:
                if p.split_timer is None and playerList[nextIndex].split_timer is None:
                    if p.is_colliding(playerList[nextIndex]):
                        vector = playerList[nextIndex].pos - p.pos

                        if vector.length() == 0:
                            vector = pygame.math.Vector2(0, 1)
                        else:
                            vector.normalize()
                            vector.scale_to_length(PLAYER_MERGE_SPEED)

                        p.pos += vector
                        playerList[nextIndex].pos -= vector

                    if (playerList[nextIndex].radius > p.radius and
                            (playerList[nextIndex].overlaps(p.pos, p.radius) or
                             (playerList[nextIndex].pos.x - PLAYER_MERGE_DEADBAND < p.pos.x <
                              playerList[nextIndex].pos.x + PLAYER_MERGE_DEADBAND and
                              playerList[nextIndex].pos.y - PLAYER_MERGE_DEADBAND <
                              p.pos.y < playerList[nextIndex].pos.y + PLAYER_MERGE_DEADBAND))):
                        playerList[nextIndex].change_size(p.size)
                        if playerList.__contains__(p):
                            playerList.remove(p)
                            playerListLength -= 1
                    elif (p.overlaps(playerList[nextIndex].pos, playerList[nextIndex].radius) or
                          (playerList[nextIndex].pos.x - PLAYER_MERGE_DEADBAND < p.pos.x <
                           playerList[nextIndex].pos.x + PLAYER_MERGE_DEADBAND and
                           playerList[nextIndex].pos.y - PLAYER_MERGE_DEADBAND <
                           p.pos.y < playerList[nextIndex].pos.y + PLAYER_MERGE_DEADBAND)):
                        p.change_size(playerList[nextIndex].size)
                        playerList.remove(playerList[nextIndex])
                        playerListLength -= 1
                else:
                    if p.is_colliding(playerList[nextIndex]):
                        vector = playerList[nextIndex].pos - p.pos

                        if vector.length() == 0:
                            vector = pygame.math.Vector2(0, 1)
                        else:
                            vector.normalize()
                            vector.scale_to_length(((p.radius + playerList[nextIndex].radius) -
                                                    playerList[nextIndex].pos.distance_to(p.pos)) / 2)

                        p.pos = p.pos - vector if vector.length() > PLAYER_PUSH_DEADBAND else p.pos
                        playerList[nextIndex].pos = playerList[nextIndex].pos + vector if \
                            vector.length() > PLAYER_PUSH_DEADBAND else playerList[nextIndex].pos

                nextIndex += 1

        for c in cellsList:
            c.move()
            for p in playerList:
                if p.overlaps(c.pos, c.radius):
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
        averagePlayerPos /= playerListLength

        camera.zoom_target = pow(100 / totalPlayerRadius, 0.5)
        camera.pos_target = pygame.math.Vector2(averagePlayerPos.x * camera.zoom - WINDOW_WIDTH / 2,
                                                averagePlayerPos.y * camera.zoom - WINDOW_HEIGHT / 2)
        camera.update_zoom()
        camera.update_pos()

        # camera.pos.x = averagePlayerPos.x * camera.zoom - WINDOW_WIDTH / 2
        # camera.pos.y = averagePlayerPos.y * camera.zoom - WINDOW_HEIGHT / 2

        draw_window(font)

    pygame.quit()


main()
