import math
import socket
import threading
from _thread import *
import _pickle as pickle
from random import random

import pygame

import constants
from objects import Cell, PlayerCell, Virus

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

PORT = 4926

HOST_NAME = socket.gethostname()
IP = "192.168.0.103"

try:
    s.bind((IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

s.listen()

print(f"[SERVER] Server started with local IP {IP}")

# Variables
global clock
global playerList
global cellsList
global virusList

connections = 0
_id = 0
time = 0


def generate_cell():
    return Cell(pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS)),
                (int(random() * 200) + 50,
                 int(random() * 200) + 50,
                 int(random() * 200) + 50), False)


def generate_virus():
    return Virus(
        pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS)))


def reset_map():
    global clock, playerList, cellsList, virusList

    clock = pygame.time.Clock()
    playerList = {}
    cellsList = []
    virusList = []

    for c in range(constants.CELLS_MAX):
        cellsList.append(generate_cell())

    for v in range(constants.VIRUS_MAX):
        virusList.append(generate_virus())


def threaded_client(connection, id):
    global connections, playerList, cellsList, virusList

    current_id = id

    data = connection.recv(16)
    name = data.decode("utf-8")
    print("[LOG]", name, "connected to server")

    playerList[current_id] = [PlayerCell(pygame.math.Vector2(
        pygame.math.Vector2(int(random() * constants.MAP_DIMENSIONS), int(random() * constants.MAP_DIMENSIONS))),
                                         constants.PLAYER_SIZE_START,
                                         (int(random() * 200) + 50, int(random() * 200) + 50, int(random() * 200) + 50),
                                         name)]

    connection.send(str.encode(str(current_id)))

    while True:
        try:
            data = connection.recv(32)

            if not data:
                break

            data = data.decode("utf-8")
            command = data.split(" ")[0]

            if command == "move":
                split_data = data.split(" ")

                for p in playerList[current_id]:
                    p.follow(pygame.math.Vector2(float(split_data[1]), float(split_data[2])))

            elif command == "emove":
                split_data = data.split(" ")

                for p in playerList[current_id]:
                    if p.size > constants.PLAYER_EJECT_SIZE_MIN:
                        p.change_size(-constants.PLAYER_EJECT_SIZE_LOSS)
                        ejectedCell = Cell(pygame.math.Vector2(p.pos.x, p.pos.y), p.color, True)
                        ejectedCell.eject(p, pygame.math.Vector2(float(split_data[1]), float(split_data[2])))
                        cellsList.append(ejectedCell)

                    p.follow(pygame.math.Vector2(float(split_data[1]), float(split_data[2])))

            elif command == "smove":
                split_data = data.split(" ")

                splitCellsList = []
                for p in playerList[current_id]:
                    playerSize = p.size
                    if playerSize > constants.PLAYER_SPLIT_SIZE_MIN and len(playerList) + len(
                            splitCellsList) < constants.PLAYER_SPLIT_MAX:
                        p.change_size(-playerSize / 2)
                        p.split_timer = 0
                        splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), playerSize / 2, p.color, p.name)
                        splitCell.split(p, pygame.math.Vector2(float(split_data[1]), float(split_data[2])))
                        splitCell.split_timer = 0
                        splitCellsList.append(splitCell)

                    p.follow(pygame.math.Vector2(float(split_data[1]), float(split_data[2])))

                playerList[current_id] += splitCellsList

            playerDict = {}
            for i in range(len(playerList)):
                playerDict[i] = []
                for j in range(len(playerList[i])):
                    playerDict[i].append(playerList[i][j].as_dict())

            cellsDict = {}
            for i in range(len(cellsList)):
                cellsDict[i] = cellsList[i].as_dict()

            virusDict = {}
            for i in range(len(virusList)):
                virusDict[i] = virusList[i].as_dict()

            send_data = pickle.dumps((playerDict, cellsDict, virusDict))
            connection.send(send_data)

        except Exception as e:
            print(e)
            break

    print("[DISCONNECT] Name:", name, ", Client ID:", current_id, "disconnected")

    connections -= 1
    # del playerList[current_id]
    playerList[current_id] = []
    connection.close()


def background():
    global time

    running = True
    while running:
        clock.tick(constants.FPS)
        time += 1

        for c in cellsList:
            if c.ejected:
                c.move()
            for i in range(len(playerList)):
                for j in range(len(playerList[i])):
                    if playerList[i][j].overlaps(c.pos, c.radius):
                        playerList[i][j].change_size(c.size)
                        if cellsList.__contains__(c):
                            cellsList.remove(c)

        splitCellsList = []
        for v in virusList:
            for i in range(len(playerList)):
                for p in playerList[i]:
                    if p.overlaps(v.pos, v.radius):
                        virusList.remove(v)
                        playerListLength = len(playerList[i])
                        if playerListLength >= constants.PLAYER_SPLIT_MAX:
                            p.change_size(v.size)
                        else:
                            maxSplits = int(min((p.size - constants.PLAYER_SIZE_MIN) / constants.VIRUS_SPLIT_SIZE,
                                                constants.PLAYER_SPLIT_MAX - (playerListLength + len(splitCellsList))))
                            p.change_size(-maxSplits * constants.VIRUS_SPLIT_SIZE)
                            p.split_timer = 0
                            for m in range(maxSplits):
                                splitCell = PlayerCell(pygame.math.Vector2(p.pos.x, p.pos.y), constants.VIRUS_SPLIT_SIZE,
                                                       p.color, p.name)
                                angle = random() * 2.0 * math.pi
                                vector = pygame.math.Vector2(math.cos(angle) + p.pos.x, math.sin(angle) + p.pos.y)
                                splitCell.split(p, vector)
                                splitCell.split_timer = 0
                                splitCellsList.append(splitCell)

                playerList[i] += splitCellsList

        for i in range(len(playerList)):

            playerListLength = len(playerList[i])

            playerList[i].sort(key=lambda x: x.size, reverse=True)

            for index, p in enumerate(playerList[i]):

                # Player cell decays over time proportional to its size
                p.change_size(-int(p.size * constants.PLAYER_DECAY_RATE))

                p.move()

                p.split_timer = p.split_timer + 1 if p.split_timer is not None and p.split_timer < constants.PLAYER_MERGE_TIME else None
                nextIndex = index + 1

                # Collision between player cells
                while nextIndex < playerListLength:
                    if p.split_timer is None and playerList[i][nextIndex].split_timer is None:
                        if p.is_colliding(playerList[i][nextIndex]):
                            vector = playerList[i][nextIndex].pos - p.pos

                            if vector.length() == 0:
                                vector = pygame.math.Vector2(0, 1)
                            else:
                                vector.scale_to_length(constants.PLAYER_MERGE_SPEED)

                            p.pos += vector
                            playerList[i][nextIndex].pos -= vector

                        if (p.overlaps(playerList[i][nextIndex].pos, playerList[i][nextIndex].radius) or
                                (playerList[i][nextIndex].pos.x - constants.PLAYER_MERGE_DEADBAND < p.pos.x <
                                 playerList[i][nextIndex].pos.x + constants.PLAYER_MERGE_DEADBAND and
                                 playerList[i][nextIndex].pos.y - constants.PLAYER_MERGE_DEADBAND <
                                 p.pos.y < playerList[i][nextIndex].pos.y + constants.PLAYER_MERGE_DEADBAND)):
                            p.change_size(playerList[i][nextIndex].size)
                            playerList[i].remove(playerList[i][nextIndex])
                            playerListLength -= 1
                    else:
                        if p.is_colliding(playerList[i][nextIndex]):
                            vector = playerList[i][nextIndex].pos - p.pos

                            if vector.length() == 0:
                                vector = pygame.math.Vector2(0, 1)
                            else:
                                vector.scale_to_length(((p.radius + playerList[i][nextIndex].radius) -
                                                        playerList[i][nextIndex].pos.distance_to(p.pos)) / 2)

                            p.pos = p.pos - vector if vector.length() > constants.PLAYER_PUSH_DEADBAND else p.pos
                            playerList[i][nextIndex].pos = playerList[i][nextIndex].pos + vector if \
                                vector.length() > constants.PLAYER_PUSH_DEADBAND else playerList[i][nextIndex].pos

                    nextIndex += 1

        # Generates new cells and viruses
        cellsListLength = len(cellsList)
        if cellsListLength < constants.CELLS_MAX and time % (int((cellsListLength + constants.CELLS_SPAWN_FREQUENCY) / constants.CELLS_SPAWN_FREQUENCY)) == 0:
            cellsList.append(generate_cell())

        virusListLength = len(virusList)
        if virusListLength < constants.VIRUS_MAX and time % (int((virusListLength + constants.VIRUS_SPAWN_FREQUENCY) / constants.VIRUS_SPAWN_FREQUENCY)) == 0:
            virusList.append(generate_virus())


reset_map()

print("[GAME] Setting up level")
print("[SERVER] Waiting for connections")

bg = threading.Thread(name='background', target=background)
bg.start()

while True:
    host, address = s.accept()
    print("[CONNECTION] Connected to:", address)

    # if address[0] == IP:
    #     print("[STARTED] Game Started")

    connections += 1
    start_new_thread(threaded_client, (host, _id))
    _id += 1