import math
import socket
import _pickle as pickle

import pygame
from pygame import mouse

import constants
from objects import Camera

DEBUG_TEXT = True

# Game objects
global current_id
global window
global clock
global camera
global playerList
global cellsList
global virusList


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "192.168.0.103"
        self.port = 4926
        self.address = (self.host, self.port)

    def connect(self, name):
        self.client.connect(self.address)
        self.client.send(str.encode(name))
        value = self.client.recv(8)
        return int(value.decode())

    def disconnect(self):
        self.client.close()

    def send(self, data, pick=False):
        try:
            if pick:
                self.client.send(pickle.dumps(data))
            else:
                self.client.send(str.encode(data))
            reply = self.client.recv(2048 * 500)
            try:
                reply = pickle.loads(reply)
            except Exception as e:
                print(e)

            return reply
        except socket.error as e:
            print(e)


def reset():
    global clock, camera, playerList, cellsList, virusList

    clock = pygame.time.Clock()

    camera = Camera(pygame.math.Vector2(0, 0))
    playerList = {}
    cellsList = []
    virusList = []


def draw_text(text, font, text_color, bg_color, pos):
    textSurface = font.render(text, constants.FONT_ANTI_ALIAS, text_color, bg_color)
    window.blit(textSurface, pos)


def draw_window(font_debug, font_cells):
    window.fill(constants.MAP_COLOR)

    for m in range(0, constants.MAP_DIMENSIONS + constants.MAP_SPACE, constants.MAP_SPACE):
        pygame.draw.line(window, constants.MAP_GRID_COLOR,
                         (camera.zoom * m - camera.pos.x, -camera.pos.y),
                         (camera.zoom * m - camera.pos.x, camera.zoom * constants.MAP_DIMENSIONS - camera.pos.y),
                         constants.MAP_LINE_WIDTH)
        pygame.draw.line(window, constants.MAP_GRID_COLOR,
                         (camera.zoom * constants.MAP_DIMENSIONS - camera.pos.x, camera.zoom * m - camera.pos.y),
                         (-camera.pos.x, camera.zoom * m - camera.pos.y), constants.MAP_LINE_WIDTH)

    for i in range(len(cellsList)):
        if cellsList[i]["ejected"]:
            pygame.draw.circle(window, cellsList[i]["color"],
                               pygame.math.Vector2(cellsList[i]["x"], cellsList[i]["y"]) * camera.zoom - camera.pos,
                               camera.zoom * constants.CELLS_EJECT_RADIUS)
        else:
            pygame.draw.circle(window, cellsList[i]["color"],
                           pygame.math.Vector2(cellsList[i]["x"], cellsList[i]["y"]) * camera.zoom - camera.pos,
                           camera.zoom * constants.CELLS_RADIUS)

    for i in range(len(virusList)):
        pygame.draw.circle(window, constants.VIRUS_OUTLINE_COLOR,
                           pygame.math.Vector2(virusList[i]["x"], virusList[i]["y"]) * camera.zoom - camera.pos,
                           camera.zoom * (constants.VIRUS_RADIUS + constants.OUTLINE_WIDTH))
        pygame.draw.circle(window, constants.VIRUS_COLOR,
                           pygame.math.Vector2(virusList[i]["x"], virusList[i]["y"]) * camera.zoom - camera.pos,
                           camera.zoom * constants.VIRUS_RADIUS)

    averagePlayerPos = pygame.math.Vector2(0, 0)
    totalPlayerSize = 0

    for i in range(len(playerList)):
        for j in range(len(playerList[i])):
            averagePlayerPos += pygame.math.Vector2(playerList[i][j]["x"], playerList[i][j]["y"])
            totalPlayerSize += int(pow(playerList[i][j]["radius"], 2) * math.pi)

            scaled_pos = pygame.math.Vector2(playerList[i][j]["x"], playerList[i][j]["y"]) * camera.zoom - camera.pos
            pygame.draw.circle(window, playerList[i][j]["outline_color"], scaled_pos,
                               camera.zoom * (playerList[i][j]["radius"] + constants.OUTLINE_WIDTH))
            pygame.draw.circle(window, playerList[i][j]["color"], scaled_pos, camera.zoom * playerList[i][j]["radius"])

            textSurface = font_cells.render(playerList[i][j]["name"], constants.FONT_ANTI_ALIAS, constants.MAP_COLOR,
                                            None)
            heightWidthRatio = textSurface.get_height() / textSurface.get_width()
            if heightWidthRatio < 0.4:
                scaledSurface = pygame.transform.scale(textSurface, (
                    playerList[i][j]["radius"] * camera.zoom * 1.8,
                    playerList[i][j]["radius"] * camera.zoom * 1.8 * heightWidthRatio))
            else:
                scaledSurface = pygame.transform.scale(textSurface, (
                    playerList[i][j]["radius"] * camera.zoom * 0.75 / heightWidthRatio,
                    playerList[i][j]["radius"] * camera.zoom * 0.75))
            window.blit(scaledSurface,
                        scaled_pos - pygame.math.Vector2(scaledSurface.get_width(), scaledSurface.get_height()) / 2)

    if DEBUG_TEXT:
        draw_text("FPS: " + str(int(clock.get_fps())), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING))
        draw_text("(x, y): (" + str(int(averagePlayerPos.x)) + ", " + str(int(averagePlayerPos.y)) + ")", font_debug,
                  constants.BLACK, constants.MAP_COLOR, (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + constants.FONT_DEBUG_SIZE + 2))
        draw_text("Size: " + str(int(totalPlayerSize)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 2 * constants.FONT_DEBUG_SIZE + 4))
        draw_text("# Player Cells: " + str(len(playerList[current_id])), font_debug, constants.BLACK,
                  constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 3 * constants.FONT_DEBUG_SIZE + 6))
        draw_text("# Cells: " + str(len(cellsList)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 4 * constants.FONT_DEBUG_SIZE + 8))
        draw_text("# Viruses: " + str(len(virusList)), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 5 * constants.FONT_DEBUG_SIZE + 10))
        draw_text("Zoom: " + str(camera.zoom), font_debug, constants.BLACK, constants.MAP_COLOR,
                  (constants.DEBUG_TEXT_PADDING, constants.DEBUG_TEXT_PADDING + 6 * constants.FONT_DEBUG_SIZE + 12))

    pygame.display.update()


def main():
    global current_id, window, DEBUG_TEXT, playerList, cellsList, virusList

    # while True:
    #     name = input("Please enter your name: ")
    #     if 0 < len(name) < 20:
    #         break
    #     else:
    #         print("Error, this name is not allowed (must be between 1 and 19 characters [inclusive])")

    reset()
    window = pygame.display.set_mode((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))

    server = Network()
    current_id = server.connect("Among Us")

    playerList, cellsList, virusList = server.send("get")

    pygame.init()
    pygame.font.init()
    pygame.display.set_caption(constants.WINDOW_TITLE)
    font_debug = pygame.font.Font(constants.FONT_PATH, constants.FONT_DEBUG_SIZE)
    font_cells = pygame.font.Font(constants.FONT_PATH, constants.FONT_CELLS_SIZE)
    running = True

    while running:
        clock.tick(constants.FPS)

        player = playerList[current_id]

        mouseX, mouseY = mouse.get_pos()
        mousePos = pygame.math.Vector2((mouseX + camera.pos.x) / camera.zoom, (mouseY + camera.pos.y) / camera.zoom)

        data = ""

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    data = "s"

                elif event.key == pygame.K_r:
                    reset()

                elif event.key == pygame.K_e:
                    DEBUG_TEXT = not DEBUG_TEXT

                elif event.key == pygame.K_q:
                    running = False

            if event.type == pygame.QUIT:
                running = False

        key = pygame.key.get_pressed()

        if key[pygame.K_w]:
            data = "e"

        data += "move " + str(mousePos.x) + " " + str(mousePos.y)
        playerList, cellsList, virusList = server.send(data)

        averagePlayerPos = pygame.math.Vector2(0, 0)
        totalPlayerRadius = 0
        playerListLength = len(player)

        for p in player:
            averagePlayerPos += pygame.math.Vector2(p["x"], p["y"])
            totalPlayerRadius += p["radius"]

        averagePlayerPos /= playerListLength

        camera.zoom_target = pow(100 / totalPlayerRadius, 0.5)
        camera.pos_target = pygame.math.Vector2(averagePlayerPos.x * camera.zoom - constants.WINDOW_WIDTH / 2,
                                                averagePlayerPos.y * camera.zoom - constants.WINDOW_HEIGHT / 2)
        camera.update_zoom()
        camera.update_pos()

        draw_window(font_debug, font_cells)

    server.disconnect()
    pygame.quit()


if __name__ == "__main__":
    main()
