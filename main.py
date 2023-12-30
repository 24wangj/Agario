import math
import numpy
from random import random

import pygame
from pygame import mouse

# Window variables
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_TITLE = "agar.io"
DEBUG_TEXT = True
DEBUG_TEXT_PADDING = 10
FONT_PATH = "Ubuntu-Bold.ttf"
FONT_DEBUG_SIZE = 16
FONT_CELLS_SIZE = 100
FONT_ANTI_ALIAS = True

# Camera variables
deltaTimeCell = 0
deltaTimeVirus = 0
FPS = 60
CAMERA_POS_FACTOR = 0.3
CAMERA_ZOOM_START = 0.2
CAMERA_ZOOM_FACTOR = 0.04
CAMERA_ZOOM_DEADBAND = 0.01

# Map variables
MAP_DIMENSIONS = 4000
MAP_SPACE = 50
MAP_LINE_WIDTH = 1
MAP_COLOR = (242, 251, 255)
MAP_GRID_COLOR = (182, 188, 190)

# Player variables
PLAYER_NAME = "John Cena"
PLAYER_SIZE_START = 100000
PLAYER_SIZE_MIN = 4000
PLAYER_SIZE_MAX = 5000000
PLAYER_SPEED = 4
PLAYER_ACCELERATION = 0.5
PLAYER_DEADBAND = 40
PLAYER_RADIUS_FACTOR = 0.1
PLAYER_EJECT_SIZE_MIN = 3000
PLAYER_EJECT_SIZE_LOSS = 2000
PLAYER_SPLIT_SPEED = 40.0
PLAYER_SPLIT_DECELERATION = 1.04
PLAYER_SPLIT_DECELERATION_DEADBAND = 0.1
PLAYER_SPLIT_SIZE_MIN = 6000
PLAYER_SPLIT_MAX = 16
PLAYER_PUSH_DEADBAND = 0.05
PLAYER_MERGE_TIME = FPS * 10
PLAYER_MERGE_SPEED = 0.4
PLAYER_MERGE_DEADBAND = 10
PLAYER_DECAY_RATE = 0.00001

# Cell variables
CELLS_SIZE = 400
CELLS_MAX = 2000
CELLS_SPAWN_FREQUENCY = 20
CELLS_EJECT_SIZE = 0.9 * PLAYER_EJECT_SIZE_LOSS
CELLS_EJECT_SPEED = 12
CELLS_EJECT_DECELERATION = 0.97
CELLS_EJECT_DECELERATION_DEADBAND = 0.1

# Virus variables
VIRUS_SIZE = 40000
VIRUS_MAX = 10
VIRUS_SPAWN_FREQUENCY = 0.01
VIRUS_SPLIT_SIZE = 8000
VIRUS_COLOR = (0, 255, 0)
VIRUS_OUTLINE_COLOR = (0, 234, 0)

BLACK = (0, 0, 0)

# Game objects
global window
global clock
global camera
global playerList
global cellsList
global virusList


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
    def __init__(self, pos, size, color, name):
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.split_vel = pygame.math.Vector2(0, 0)
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.radius_drawn = self.radius
        self.color = color
        self.outline_color = numpy.subtract(self.color, 20)
        self.name = name
        self.split_timer = None

    def follow(self, mouse_pos):
        deltaPos = (mouse_pos - self.pos)
        deltaPos.scale_to_length(PLAYER_ACCELERATION)
        self.acc.x = deltaPos.x
        self.acc.y = deltaPos.y

    def move(self):
        self.vel += self.acc
        self.pos += self.vel + self.split_vel
        # Gradually decreases velocity after splitting
        self.split_vel = self.split_vel / PLAYER_SPLIT_DECELERATION if self.split_vel.length() > PLAYER_SPLIT_DECELERATION_DEADBAND else pygame.math.Vector2(
            0, 0)

        # Caps velocity to maximum speed
        if self.vel.length() > PLAYER_SPEED:
            self.vel.scale_to_length(PLAYER_SPEED)

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
        direction = mouse_pos - player_cell.pos

        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1)

        self.split_vel = PLAYER_SPLIT_SPEED * direction.normalize()
        direction.scale_to_length(player_cell.radius)
        self.pos = direction + player_cell.pos

    def is_colliding(self, player_cell):
        return (pow(player_cell.pos.x - self.pos.x, 2) + pow(player_cell.pos.y - self.pos.y, 2)
                <= pow(self.radius + player_cell.radius, 2))

    def draw(self, font):
        vector = (self.radius - self.radius_drawn) * PLAYER_RADIUS_FACTOR
        self.radius_drawn += vector

        scaled_pos = self.pos * camera.zoom - camera.pos
        pygame.draw.circle(window, self.outline_color, scaled_pos, get_scaled_size(self.radius_drawn + 8))
        pygame.draw.circle(window, self.color, scaled_pos, get_scaled_size(self.radius_drawn))

        textSurface = font.render(self.name, FONT_ANTI_ALIAS, MAP_COLOR, None)
        heightWidthRatio = textSurface.get_height() / textSurface.get_width()
        if heightWidthRatio < 0.4:
            scaledSurface = pygame.transform.scale(textSurface, (
                self.radius_drawn * camera.zoom * 1.8, self.radius_drawn * camera.zoom * 1.8 * heightWidthRatio))
        else:
            scaledSurface = pygame.transform.scale(textSurface, (
                self.radius_drawn * camera.zoom * 0.75 / heightWidthRatio, self.radius_drawn * camera.zoom * 0.75))
        window.blit(scaledSurface,
                    scaled_pos - pygame.math.Vector2(scaledSurface.get_width(), scaledSurface.get_height()) / 2)


class Cell:
    def __init__(self, pos, size, color):
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        self.size = size
        self.radius = math.sqrt(self.size / math.pi)
        self.color = color

    def eject(self, player_cell, mouse_pos):
        direction = mouse_pos - player_cell.pos

        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1)

        self.vel = CELLS_EJECT_SPEED * direction.normalize()
        direction.scale_to_length(player_cell.radius)
        self.pos = direction + player_cell.pos

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
        pygame.draw.circle(window, self.color, self.pos * camera.zoom - camera.pos, get_scaled_size(self.radius))


class Virus:
    def __init__(self, pos):
        self.pos = pos
        self.size = VIRUS_SIZE
        self.radius = math.sqrt(self.size / math.pi)
        self.color = VIRUS_COLOR
        self.outline_color = VIRUS_OUTLINE_COLOR

    def draw(self):
        pygame.draw.circle(window, self.outline_color, self.pos * camera.zoom - camera.pos,
                           get_scaled_size(self.radius + 8))
        pygame.draw.circle(window, self.color, self.pos * camera.zoom - camera.pos, get_scaled_size(self.radius))


def generate_cell():
    return Cell(pygame.math.Vector2(int(random() * MAP_DIMENSIONS), int(random() * MAP_DIMENSIONS)), CELLS_SIZE,
                (int(random() * 200) + 50,
                 int(random() * 200) + 50,
                 int(random() * 200) + 50))


def generate_virus():
    return Virus(pygame.math.Vector2(int(random() * MAP_DIMENSIONS), int(random() * MAP_DIMENSIONS)))


def reset_map():
    global window, clock, camera, playerList, cellsList, virusList

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    playerList = [PlayerCell(
        pygame.math.Vector2(pygame.math.Vector2(int(random() * MAP_DIMENSIONS), int(random() * MAP_DIMENSIONS))),
        PLAYER_SIZE_START, (int(random() * 200) + 50, int(random() * 200) + 50, int(random() * 200) + 50), PLAYER_NAME)]
    camera = Camera(pygame.math.Vector2(playerList[0].pos.x, playerList[0].pos.y))
    cellsList = []
    virusList = []

    for c in range(CELLS_MAX):
        cellsList.append(generate_cell())

    for v in range(VIRUS_MAX):
        virusList.append(generate_virus())


def draw_text(text, font, text_color, bg_color, pos):
    textSurface = font.render(text, FONT_ANTI_ALIAS, text_color, bg_color)
    window.blit(textSurface, pos)


def draw_window(font_debug, font_cells):
    window.fill(MAP_COLOR)

    for m in range(0, MAP_DIMENSIONS + MAP_SPACE, MAP_SPACE):
        pygame.draw.line(window, MAP_GRID_COLOR,
                         (get_scaled_size(m) - camera.pos.x, -camera.pos.y),
                         (get_scaled_size(m) - camera.pos.x, get_scaled_size(MAP_DIMENSIONS) - camera.pos.y),
                         MAP_LINE_WIDTH)
        pygame.draw.line(window, MAP_GRID_COLOR,
                         (get_scaled_size(MAP_DIMENSIONS) - camera.pos.x, get_scaled_size(m) - camera.pos.y),
                         (-camera.pos.x, get_scaled_size(m) - camera.pos.y), MAP_LINE_WIDTH)

    for c in cellsList:
        c.draw()

    for v in virusList:
        v.draw()

    averagePlayerPos = pygame.math.Vector2(0, 0)
    totalPlayerSize = 0

    for p in reversed(playerList):
        averagePlayerPos += p.pos
        totalPlayerSize += p.size
        p.draw(font_cells)

    averagePlayerPos /= len(playerList)

    if DEBUG_TEXT:
        draw_text("FPS: " + str(int(clock.get_fps())), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING))
        draw_text("(x, y): (" + str(int(averagePlayerPos.x)) + ", " + str(int(averagePlayerPos.y)) + ")", font_debug,
                  BLACK, MAP_COLOR, (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + FONT_DEBUG_SIZE + 2))
        draw_text("Size: " + str(int(totalPlayerSize)), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + 2 * FONT_DEBUG_SIZE + 4))
        draw_text("# Player Cells: " + str(len(playerList)), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + 3 * FONT_DEBUG_SIZE + 6))
        draw_text("# Cells: " + str(len(cellsList)), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + 4 * FONT_DEBUG_SIZE + 8))
        draw_text("# Viruses: " + str(len(virusList)), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + 5 * FONT_DEBUG_SIZE + 10))
        draw_text("Zoom: " + str(camera.zoom), font_debug, BLACK, MAP_COLOR,
                  (DEBUG_TEXT_PADDING, DEBUG_TEXT_PADDING + 6 * FONT_DEBUG_SIZE + 12))

    pygame.display.update()


def main():
    global playerList, deltaTimeCell, deltaTimeVirus, DEBUG_TEXT

    reset_map()
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(WINDOW_TITLE)
    font_debug = pygame.font.Font(FONT_PATH, FONT_DEBUG_SIZE)
    font_cells = pygame.font.Font(FONT_PATH, FONT_CELLS_SIZE)
    running = True

    while running:
        clock.tick(FPS)
        deltaTimeCell += 1
        deltaTimeVirus += 1

        mouseX, mouseY = mouse.get_pos()
        mousePos = pygame.math.Vector2((mouseX + camera.pos.x) / camera.zoom, (mouseY + camera.pos.y) / camera.zoom)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    splitCellsList = []
                    for p in playerList:
                        playerSize = p.size
                        if playerSize > PLAYER_SPLIT_SIZE_MIN and len(playerList) + len(
                                splitCellsList) < PLAYER_SPLIT_MAX:
                            p.change_size(-playerSize / 2)
                            p.split_timer = 0
                            splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), playerSize / 2, p.color,
                                                   p.name)
                            splitCell.split(p, mousePos)
                            splitCell.split_timer = 0
                            splitCellsList.append(splitCell)
                    playerList += splitCellsList

                elif event.key == pygame.K_r:
                    reset_map()

                elif event.key == pygame.K_e:
                    DEBUG_TEXT = not DEBUG_TEXT

                elif event.key == pygame.K_q:
                    running = False

            if event.type == pygame.QUIT:
                running = False

        key = pygame.key.get_pressed()

        if key[pygame.K_w]:
            for p in playerList:
                if p.size > PLAYER_EJECT_SIZE_MIN:
                    p.change_size(-PLAYER_EJECT_SIZE_LOSS)
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

        for c in cellsList:
            c.move()
            for p in playerList:
                if p.overlaps(c.pos, c.radius):
                    p.change_size(c.size)
                    if cellsList.__contains__(c):
                        cellsList.remove(c)

        splitCellsList = []
        for v in virusList:
            for p in playerList:
                if p.overlaps(v.pos, v.radius):
                    virusList.remove(v)
                    if len(playerList) >= PLAYER_SPLIT_MAX:
                        p.change_size(v.size)
                    else:
                        maxSplits = int(min((p.size - PLAYER_SIZE_MIN) / VIRUS_SPLIT_SIZE, PLAYER_SPLIT_MAX - (len(playerList) + len(splitCellsList))))
                        p.change_size(-maxSplits * VIRUS_SPLIT_SIZE)
                        p.split_timer = 0
                        for m in range(maxSplits):
                            splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), VIRUS_SPLIT_SIZE, p.color, p.name)
                            angle = random() * 2.0 * math.pi
                            vector = pygame.math.Vector2((math.cos(angle) * p.pos.x + camera.pos.x) / camera.zoom,
                                                         (math.sin(angle) * p.pos.y + camera.pos.y) / camera.zoom)
                            splitCell.split(p, vector)
                            splitCell.split_timer = 0
                            splitCellsList.append(splitCell)

        playerList += splitCellsList

        averagePlayerPos = pygame.math.Vector2(0, 0)
        totalPlayerRadius = 0
        playerListLength = len(playerList)

        playerList.sort(key=lambda x: x.size, reverse=True)

        for index, p in enumerate(playerList):

            # Player cell decays over time proportional to its size
            p.change_size(-int(p.size * PLAYER_DECAY_RATE))

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
                            vector.scale_to_length(PLAYER_MERGE_SPEED)

                        p.pos += vector
                        playerList[nextIndex].pos -= vector

                    # if ((playerList[nextIndex].overlaps(p.pos, p.radius) or
                    #      (playerList[nextIndex].pos.x - PLAYER_MERGE_DEADBAND < p.pos.x <
                    #       playerList[nextIndex].pos.x + PLAYER_MERGE_DEADBAND and
                    #       playerList[nextIndex].pos.y - PLAYER_MERGE_DEADBAND <
                    #       p.pos.y < playerList[nextIndex].pos.y + PLAYER_MERGE_DEADBAND))):
                    #     playerList[nextIndex].change_size(p.size)
                    #     if playerList.__contains__(p):
                    #         playerList.remove(p)
                    #         playerListLength -= 1
                    if (p.overlaps(playerList[nextIndex].pos, playerList[nextIndex].radius) or
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
                            vector.scale_to_length(((p.radius + playerList[nextIndex].radius) -
                                                    playerList[nextIndex].pos.distance_to(p.pos)) / 2)

                        p.pos = p.pos - vector if vector.length() > PLAYER_PUSH_DEADBAND else p.pos
                        playerList[nextIndex].pos = playerList[nextIndex].pos + vector if \
                            vector.length() > PLAYER_PUSH_DEADBAND else playerList[nextIndex].pos

                nextIndex += 1

        # Generates new cells and viruses
        cellsListLength = len(cellsList)
        if cellsListLength < CELLS_MAX and deltaTimeCell % (int((cellsListLength + CELLS_SPAWN_FREQUENCY) / CELLS_SPAWN_FREQUENCY)) == 0:
            deltaTimeCell = 0
            cellsList.append(generate_cell())

        virusListLength = len(virusList)
        if virusListLength < VIRUS_MAX and deltaTimeVirus % (int((virusListLength + VIRUS_SPAWN_FREQUENCY) / VIRUS_SPAWN_FREQUENCY)) == 0:
            deltaTimeVirus = 0
            virusList.append(generate_virus())

        # Smooth camera zoom
        averagePlayerPos /= playerListLength

        camera.zoom_target = pow(100 / totalPlayerRadius, 0.5)
        camera.pos_target = pygame.math.Vector2(averagePlayerPos.x * camera.zoom - WINDOW_WIDTH / 2,
                                                averagePlayerPos.y * camera.zoom - WINDOW_HEIGHT / 2)
        camera.update_zoom()
        camera.update_pos()

        # camera.pos.x = averagePlayerPos.x * camera.zoom - WINDOW_WIDTH / 2
        # camera.pos.y = averagePlayerPos.y * camera.zoom - WINDOW_HEIGHT / 2

        draw_window(font_debug, font_cells)

    pygame.quit()


if __name__ == "__main__":
    main()
