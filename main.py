import math
from random import random

import pygame
from pygame import mouse

import constants
from objects import Camera
from objects import PlayerCell
from objects import Cell
from objects import Virus

DEBUG_TEXT = True

# Game objects
global window
global clock
global camera
global playerList
global cellsList
global virusList

time = 0


def get_scaled_size(size):
    return int(size * camera.zoom)


def generate_cell():
    return Cell(pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS)),
                (int(random() * 200) + 50,
                 int(random() * 200) + 50,
                 int(random() * 200) + 50), False)


def generate_virus():
    return Virus(pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS)))


def reset_map():
    global clock, camera, playerList, cellsList, virusList

    clock = pygame.time.Clock()
    playerList = [PlayerCell(
        pygame.math.Vector2(pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS))),
        constants.PLAYER_SIZE_START, (int(random() * 200) + 50, int(random() * 200) + 50, int(random() * 200) + 50), constants.PLAYER_NAME)]
    camera = Camera(pygame.math.Vector2(playerList[0].pos.x, playerList[0].pos.y))
    cellsList = []
    virusList = []

    for c in range(constants.CELLS_MAX):
        cellsList.append(generate_cell())

    for v in range(constants.VIRUS_MAX):
        virusList.append(generate_virus())


def draw_text(text, font, text_color, bg_color, pos):
    textSurface = font.render(text, constants.FONT_ANTI_ALIAS, text_color, bg_color)
    window.blit(textSurface, pos)


def draw_window(font_debug, font_cells):
    window.fill(constants.MAP_COLOR)

    for m in range(0, constants.MAP_DIMENSIONS + constants.MAP_SPACE, constants.MAP_SPACE):
        pygame.draw.line(window, constants.MAP_GRID_COLOR,
                         (get_scaled_size(m) - camera.pos.x, -camera.pos.y),
                         (get_scaled_size(m) - camera.pos.x, get_scaled_size(constants.MAP_DIMENSIONS) - camera.pos.y),
                         constants.MAP_LINE_WIDTH)
        pygame.draw.line(window, constants.MAP_GRID_COLOR,
                         (get_scaled_size(constants.MAP_DIMENSIONS) - camera.pos.x, get_scaled_size(m) - camera.pos.y),
                         (-camera.pos.x, get_scaled_size(m) - camera.pos.y), constants.MAP_LINE_WIDTH)

    averagePlayerPos = pygame.math.Vector2(0, 0)
    totalPlayerSize = 0

    combinedList = cellsList + virusList + playerList
    combinedList.sort(key=lambda x: x.size, reverse=False)

    for x in combinedList:
        if isinstance(x, PlayerCell):
            averagePlayerPos += x.pos
            totalPlayerSize += x.size
            x.draw(window, camera, font_cells)
        else:
            x.draw(window, camera)

    averagePlayerPos /= len(playerList)

    if DEBUG_TEXT:
        draw_text("FPS: " + str(int(clock.get_fps())), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING))
        draw_text("(x, y): (" + str(int(averagePlayerPos.x)) + ", " + str(int(averagePlayerPos.y)) + ")", font_debug,
                  constants.BLACK, constants.MAP_COLOR, (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + constants.FONT_DEBUG_SIZE + 2))
        draw_text("Size: " + str(int(totalPlayerSize)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 2 * constants.FONT_DEBUG_SIZE + 4))
        draw_text("# Player Cells: " + str(len(playerList)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 3 * constants.FONT_DEBUG_SIZE + 6))
        draw_text("# Cells: " + str(len(cellsList)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 4 * constants.FONT_DEBUG_SIZE + 8))
        draw_text("# Viruses: " + str(len(virusList)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 5 * constants.FONT_DEBUG_SIZE + 10))
        draw_text("Zoom: " + str(camera.zoom), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 6 * constants.FONT_DEBUG_SIZE + 12))

    pygame.display.update()


def main():
    global window, playerList, time, DEBUG_TEXT

    reset_map()
    window = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(constants.WINDOW_TITLE)
    font_debug = pygame.font.Font(constants.FONT_PATH, constants.FONT_DEBUG_SIZE)
    font_cells = pygame.font.Font(constants.FONT_PATH, constants.FONT_CELLS_SIZE)
    running = True

    while running:
        clock.tick(constants.FPS)
        time += 1

        mouseX, mouseY = mouse.get_pos()
        mousePos = pygame.math.Vector2((mouseX + camera.pos.x) / camera.zoom, (mouseY + camera.pos.y) / camera.zoom)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    splitCellsList = []
                    for p in playerList:
                        playerSize = p.size
                        if playerSize > constants.PLAYER_SPLIT_SIZE_MIN and len(playerList) + len(
                                splitCellsList) < constants.PLAYER_SPLIT_MAX:
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
                if p.size > constants.PLAYER_EJECT_SIZE_MIN:
                    p.change_size(-constants.PLAYER_EJECT_SIZE_LOSS)
                    ejectedCell = Cell(pygame.math.Vector2(p.pos.x, p.pos.y), p.color, True)
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
            if c.ejected:
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
                    playerListLength = len(playerList)
                    if playerListLength >= constants.PLAYER_SPLIT_MAX:
                        p.change_size(v.size)
                    else:
                        maxSplits = int(min((p.size - constants.PLAYER_SIZE_MIN) / constants.VIRUS_SPLIT_SIZE, constants.PLAYER_SPLIT_MAX - (playerListLength + len(splitCellsList))))
                        p.change_size(-maxSplits * constants.VIRUS_SPLIT_SIZE)
                        p.split_timer = 0
                        for m in range(maxSplits):
                            splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), constants.VIRUS_SPLIT_SIZE, p.color, p.name)
                            angle = random() * 2.0 * math.pi
                            vector = pygame.math.Vector2(math.cos(angle) + p.pos.x, math.sin(angle) + p.pos.y)
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
            p.change_size(-int(p.size * constants.PLAYER_DECAY_RATE))

            averagePlayerPos += p.pos
            totalPlayerRadius += p.radius_drawn

            p.follow(mousePos)
            p.move()

            p.split_timer = p.split_timer + 1 if p.split_timer is not None and p.split_timer < constants.PLAYER_MERGE_TIME else None
            nextIndex = index + 1

            # Collision between player cells
            while nextIndex < playerListLength:
                if p.split_timer is None and playerList[nextIndex].split_timer is None:
                    if p.is_colliding(playerList[nextIndex]):
                        vector = playerList[nextIndex].pos - p.pos

                        if vector.length() == 0:
                            vector = pygame.math.Vector2(0, 1)
                        else:
                            vector.scale_to_length(constants.PLAYER_MERGE_SPEED)

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
                          (playerList[nextIndex].pos.x - constants.PLAYER_MERGE_DEADBAND < p.pos.x <
                           playerList[nextIndex].pos.x + constants.PLAYER_MERGE_DEADBAND and
                           playerList[nextIndex].pos.y - constants.PLAYER_MERGE_DEADBAND <
                           p.pos.y < playerList[nextIndex].pos.y + constants.PLAYER_MERGE_DEADBAND)):
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

                        p.pos = p.pos - vector if vector.length() > constants.PLAYER_PUSH_DEADBAND else p.pos
                        playerList[nextIndex].pos = playerList[nextIndex].pos + vector if \
                            vector.length() > constants.PLAYER_PUSH_DEADBAND else playerList[nextIndex].pos

                nextIndex += 1

        # Generates new cells and viruses
        cellsListLength = len(cellsList)
        if cellsListLength < constants.CELLS_MAX and time % (int((cellsListLength + constants.CELLS_SPAWN_FREQUENCY) / constants.CELLS_SPAWN_FREQUENCY)) == 0:
            cellsList.append(generate_cell())

        virusListLength = len(virusList)
        if virusListLength < constants.VIRUS_MAX and time % (int((virusListLength + constants.VIRUS_SPAWN_FREQUENCY) / constants.VIRUS_SPAWN_FREQUENCY)) == 0:
            virusList.append(generate_virus())

        # Smooth camera zoom
        averagePlayerPos /= playerListLength

        camera.zoom_target = pow(100 / totalPlayerRadius, 0.5)
        camera.pos_target = pygame.math.Vector2(averagePlayerPos.x * camera.zoom - constants.WINDOW_WIDTH / 2,
                                                averagePlayerPos.y * camera.zoom - constants.WINDOW_HEIGHT / 2)
        camera.update_zoom()
        camera.update_pos()

        # camera.pos.x = averagePlayerPos.x * camera.zoom - WINDOW_WIDTH / 2
        # camera.pos.y = averagePlayerPos.y * camera.zoom - WINDOW_HEIGHT / 2

        draw_window(font_debug, font_cells)

    pygame.quit()


if __name__ == "__main__":
    main()
