import math
import numpy as np


class ExitException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


class Vertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Game_Object:
    orientation = ""
    x: int
    y: int
    width: int
    height: int
    children: list
    type: str

    def __init__(self, x, y, width, height, sprite, type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.sprite = sprite
        self.children = []
        self.type = type


class Agent(Game_Object):
    def __init__(self, x, y, width, height, sprite, type, rot):
        Game_Object.__init__(self, x, y, width, height, sprite, type)
        self._rot = rot
        self._target_rot = rot
        self.image = None
        self._last_room = 0


class Room(Game_Object):
    vertex1 = Vertex(0, 0)
    vertex2 = Vertex(0, 0)
    vertex3 = Vertex(0, 0)
    vertex4 = Vertex(0, 0)
    door = Game_Object(0, 0, 0, 0, 0, "door")

    def __init__(self, x, y, width, height, index, sprite, type):
        Game_Object.__init__(self, x, y, width, height, sprite, type)
        self.index = index


def check_line_line_collision(line1, line2):
    x1 = line1[0]
    y1 = line1[1]
    x2 = line1[2]
    y2 = line1[3]
    x3 = line2[0]
    y3 = line2[1]
    x4 = line2[2]
    y4 = line2[3]
    try:
        uA = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    except ZeroDivisionError:
        uA = 2
    try:
        uB = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
    except ZeroDivisionError:
        uB = 2
    if 0 <= uA <= 1 and 0 <= uB <= 1:
        return int(x1 + (uA * (x2 - x1))), int(y1 + (uA * (y2 - y1)))
    else:
        return None


class Check_Collisions:
    def __init__(self):
        pass

    def check_line_rect_collision(self, line, rect):
        intersection_points = []
        eye_point = (line[0], line[1])
        point1 = check_line_line_collision(line, (rect.x, rect.y, rect.x, rect.y + rect.height))  # West
        point2 = check_line_line_collision(line, (
            rect.x, rect.y + rect.height, rect.x + rect.width, rect.y + rect.height))  # North
        point3 = check_line_line_collision(line, (
            rect.x + rect.width, rect.y + rect.height, rect.x + rect.width, rect.y))  # Est
        point4 = check_line_line_collision(line, (rect.x, rect.y, rect.x + rect.width, rect.y))  # South
        if point1 is not None:
            intersection_points.append(point1)
        if point2 is not None:
            intersection_points.append(point2)
        if point3 is not None:
            intersection_points.append(point3)
        if point4 is not None:
            intersection_points.append(point4)
        intersection_points_distances = []
        for point in intersection_points:
            intersection_points_distances.append(self.point_point_distance(eye_point, point))
        if len(intersection_points) > 0:
            return intersection_points[np.argmin(intersection_points_distances)]
        else:
            return None

    def check_line_room_collision(self, line, room):
        intersection_points = []
        eye_point = (line[0], line[1])
        rect = room.sprite.rect
        point1 = check_line_line_collision(line, (rect.x, rect.y, rect.x, rect.y + rect.height))  # West
        point2 = check_line_line_collision(line, (
            rect.x, rect.y + rect.height, rect.x + rect.width, rect.y + rect.height))  # North
        point3 = check_line_line_collision(line, (
            rect.x + rect.width, rect.y + rect.height, rect.x + rect.width, rect.y))  # Est
        point4 = check_line_line_collision(line, (rect.x, rect.y, rect.x + rect.width, rect.y))  # South
        if point1 is not None:
            if not room.door.sprite.rect.collidepoint(point1):
                intersection_points.append(point1)
        if point2 is not None:
            if not room.door.sprite.rect.collidepoint(point2):
                intersection_points.append(point2)
        if point3 is not None:
            if not room.door.sprite.rect.collidepoint(point3):
                intersection_points.append(point3)
        if point4 is not None:
            if not room.door.sprite.rect.collidepoint(point4):
                intersection_points.append(point4)
        intersection_points_distances = []
        for point in intersection_points:
            intersection_points_distances.append(self.point_point_distance(eye_point, point))
        if len(intersection_points) > 0:
            return intersection_points[np.argmin(intersection_points_distances)]
        else:
            return None

    def point_point_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def check_rect_contains_point(self, rect, point):
        return rect.x <= point[0] <= rect.x + rect.width and rect.y <= point[1] <= rect.y + rect.height
