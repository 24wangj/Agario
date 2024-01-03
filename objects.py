import math

import numpy
import pygame

import constants


class Camera:
    def __init__(self, pos):
        self.pos_target = pos
        self.pos = pos
        self.zoom_target = constants.CAMERA_ZOOM_START
        self.zoom = constants.CAMERA_ZOOM_START

    def update_zoom(self):
        vector = (self.zoom_target - self.zoom) * constants.CAMERA_ZOOM_FACTOR
        self.zoom += vector

    def update_pos(self):
        vector = (self.pos_target - self.pos) * constants.CAMERA_POS_FACTOR
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
        deltaPos.scale_to_length(constants.PLAYER_ACCELERATION)
        self.acc.x = deltaPos.x
        self.acc.y = deltaPos.y

    def move(self):
        self.vel += self.acc
        self.pos += self.vel + self.split_vel
        # Gradually decreases velocity after splitting
        self.split_vel = self.split_vel / constants.PLAYER_SPLIT_DECELERATION if self.split_vel.length() > constants.PLAYER_SPLIT_DECELERATION_DEADBAND else pygame.math.Vector2(
            0, 0)

        # Caps velocity to maximum speed
        if self.vel.length() > constants.PLAYER_SPEED:
            self.vel.scale_to_length(constants.PLAYER_SPEED)

        # Prevents player from leaving the map
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > constants.MAP_DIMENSIONS:
            self.pos.x = constants.MAP_DIMENSIONS
        if self.pos.y < 0:
            self.pos.y = 0
        elif self.pos.y > constants.MAP_DIMENSIONS:
            self.pos.y = constants.MAP_DIMENSIONS

        self.radius_drawn += (self.radius - self.radius_drawn) * constants.PLAYER_RADIUS_FACTOR

    def overlaps(self, pos, r):
        distSq = int((self.pos - pos).length())
        if distSq + r < self.radius:
            return True
        return False

    def change_size(self, size):
        self.size += size
        if self.size < constants.PLAYER_SIZE_MIN:
            self.size = constants.PLAYER_SIZE_MIN
        elif self.size > constants.PLAYER_SIZE_MAX:
            self.size = constants.PLAYER_SIZE_MAX
        self.radius = math.sqrt(self.size / math.pi)

    def split(self, player_cell, mouse_pos):
        direction = mouse_pos - player_cell.pos

        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1)

        self.split_vel = constants.PLAYER_SPLIT_SPEED * direction.normalize()
        direction.scale_to_length(player_cell.radius)
        self.pos = direction + player_cell.pos

    def is_colliding(self, player_cell):
        return (pow(player_cell.pos.x - self.pos.x, 2) + pow(player_cell.pos.y - self.pos.y, 2)
                <= pow(self.radius + player_cell.radius, 2))

    def draw(self, window, camera, font):
        scaled_pos = self.pos * camera.zoom - camera.pos
        pygame.draw.circle(window, self.outline_color, scaled_pos, camera.zoom * (self.radius_drawn + 8))
        pygame.draw.circle(window, self.color, scaled_pos, camera.zoom * self.radius_drawn)

        textSurface = font.render(self.name, constants.FONT_ANTI_ALIAS, constants.MAP_COLOR, None)
        heightWidthRatio = textSurface.get_height() / textSurface.get_width()
        if heightWidthRatio < 0.4:
            scaledSurface = pygame.transform.scale(textSurface, (
                self.radius_drawn * camera.zoom * 1.8, self.radius_drawn * camera.zoom * 1.8 * heightWidthRatio))
        else:
            scaledSurface = pygame.transform.scale(textSurface, (
                self.radius_drawn * camera.zoom * 0.75 / heightWidthRatio, self.radius_drawn * camera.zoom * 0.75))
        window.blit(scaledSurface,
                    scaled_pos - pygame.math.Vector2(scaledSurface.get_width(), scaledSurface.get_height()) / 2)

    def as_dict(self):
        return {"x": int(self.pos.x), "y": int(self.pos.y), "radius": int(self.radius_drawn), "color": self.color, "outline_color": self.outline_color, "name": self.name}



class Cell:
    def __init__(self, pos, color, ejected):
        self.pos = pos
        self.vel = pygame.math.Vector2(0, 0)
        if ejected:
            self.size = constants.CELLS_EJECT_SIZE
            self.radius = constants.CELLS_EJECT_RADIUS
        else:
            self.size = constants.CELLS_SIZE
            self.radius = constants.CELLS_RADIUS
        self.color = color
        self.ejected = ejected

    def eject(self, player_cell, mouse_pos):
        direction = mouse_pos - player_cell.pos

        if direction.length() == 0:
            direction = pygame.math.Vector2(0, 1)

        self.vel = constants.CELLS_EJECT_SPEED * direction.normalize()
        direction.scale_to_length(player_cell.radius)
        self.pos = direction + player_cell.pos

    def move(self):
        self.pos += self.vel
        self.vel = self.vel * constants.CELLS_EJECT_DECELERATION if self.vel.length() > constants.CELLS_EJECT_DECELERATION_DEADBAND else pygame.math.Vector2(
            0, 0)

        # Prevents cell from leaving the map
        if self.pos.x < 0:
            self.pos.x = 0
        elif self.pos.x > constants.MAP_DIMENSIONS:
            self.pos.x = constants.MAP_DIMENSIONS
        if self.pos.y < 0:
            self.pos.y = 0
        elif self.pos.y > constants.MAP_DIMENSIONS:
            self.pos.y = constants.MAP_DIMENSIONS

    def draw(self, window, camera):
        pygame.draw.circle(window, self.color, self.pos * camera.zoom - camera.pos, camera.zoom * self.radius)

    def as_dict(self):
        return {"x": int(self.pos.x), "y": int(self.pos.y), "color": self.color, "ejected": self.ejected}


class Virus:
    def __init__(self, pos):
        self.pos = pos
        self.size = constants.VIRUS_SIZE
        self.radius = constants.VIRUS_RADIUS
        self.color = constants.VIRUS_COLOR
        self.outline_color = constants.VIRUS_OUTLINE_COLOR

    def draw(self, window, camera):
        pygame.draw.circle(window, self.outline_color, self.pos * camera.zoom - camera.pos, camera.zoom * (self.radius + 8))
        pygame.draw.circle(window, self.color, self.pos * camera.zoom - camera.pos, camera.zoom * self.radius)

    def as_dict(self):
        return {"x": int(self.pos.x), "y": int(self.pos.y)}
