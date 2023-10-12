from pyswip import *
import pygame
import random
import numpy as np
import math
import json
import datetime
from utils.utils import Check_Collisions, Agent, Vertex, Room, Game_Object


class Environment:
    """Class to generate and simulate the world environment"""

    def __init__(self, env_width, env_height, multiplier, fake_collision_mt, door_fake_collision_mt):
        self._type_to_sprite = None
        self._env_width = env_width * multiplier
        self._env_height = env_height * multiplier
        self._multiplier = multiplier
        self._checker = Check_Collisions()
        self._prolog = Prolog()
        self._fake_collision_mt = fake_collision_mt
        self._door_fake_collision_mt = door_fake_collision_mt
        self._floor = Game_Object(0, 0, 0, 0, 0, 'floor')
        self._agent = Agent(9999, 9999, 8, 8, 0, 'agent', 90)
        self._objective = Game_Object(9800, 9800, 15, 15, 0, 'objective')
        self._objective_position = []
        self._rooms = []
        self._screen = None
        prolog_query = "use_module(library(clpr))"

        for solution in self._prolog.query(prolog_query):
            print("CLPR loaded.")

    def generate_environment(self, bathroom_no, bedroom_no, kitchen_no, hall_no):
        floor_pos, door_pos_x, door_pos_y = random.random(), random.random(), random.random()
        self.generate_rooms_and_doors(bathroom_no, bedroom_no, kitchen_no, hall_no,
                                      floor_pos, door_pos_x, door_pos_y)
        for bathroom in self.get_rooms(flag='bathroom'):
            self.populate_bathroom(bathroom, random.randint(0, 1), random.randint(0, 1), random.randint(0, 1))
        for bedroom in self.get_rooms(flag='bedroom'):
            self.populate_bedroom(bedroom, random.randint(0, 2), random.randint(0, 2))
        for kitchen in self.get_rooms(flag='kitchen'):
            self.populate_kitchen(kitchen, random.randint(0, 3), random.randint(0, 1))
        for hall in self.get_rooms(flag='hall'):
            self.populate_hall(hall, random.randint(0, 1), random.randint(0, 2), random.randint(0, 2), 1.0)

    def draw_model(self):
        if len(self._rooms) > 1:
            self._screen.blit(self._floor.sprite.image, self._floor.sprite.rect)
            pygame.draw.rect(self._screen, (255, 255, 255), self._floor.sprite.rect, 2)
        self.draw_rooms()
        self.draw_agent_and_target()

    def draw_agent_and_target(self):
        if self._agent._target_rot - self._agent._rot != 0:
            self._agent.image = pygame.transform.rotate(self._agent.sprite.image, self._agent._target_rot - 90)
            old_center = self._agent.sprite.rect.center
            self._agent.sprite.rect = self._agent.image.get_rect()
            self._agent.sprite.rect.center = old_center
            self._agent._rot = self._agent._target_rot
        self._agent.sprite.rect.x = self._agent.x
        self._agent.sprite.rect.y = self._agent.y
        self._screen.blit(self._agent.image, self._agent.sprite.rect)
        self._screen.blit(self._objective.sprite.image, self._objective.sprite.rect)

    def draw_rooms(self):
        for room in self._rooms:
            self._screen.blit(room.sprite.image, room.sprite.rect)
            pygame.draw.rect(self._screen, (255, 255, 255), room.sprite.rect, 2)

            if room.door.width == 0:
                blitRect = pygame.Rect(room.door.x - 0.5 * self._multiplier, room.door.y, 1.0 * self._multiplier,
                                       room.door.height)
                self._screen.blit(room.door.sprite.image, blitRect)
                room.door.sprite.rect = blitRect
            else:
                blitRect = pygame.Rect(room.door.x, room.door.y - 0.5 * self._multiplier, room.door.width,
                                       1.0 * self._multiplier)
                self._screen.blit(room.door.sprite.image, blitRect)
                room.door.sprite.rect = blitRect

            for room_child in room.children:
                self._screen.blit(room_child.sprite.image, room_child.sprite.rect)
                for child in room_child.children:
                    self._screen.blit(child.sprite.image, child.sprite.rect)

    def display_environment(self, bathroom_no, bedroom_no, kitchen_no, hall_no,
                            mode='view'):
        running = True
        clock = pygame.time.Clock()
        pygame.init()
        pygame.display.set_caption("Environment Generator")
        frames = 1500
        score = 0
        f_once = mode == 'view'
        while running:
            if f_once:
                self._screen.fill((30, 30, 30))
                self.draw_model()
                f_once = False
            elif mode == "generate":
                self._screen.fill((30, 30, 30))
                self.draw_model()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    try:
                        pygame.display.quit()
                    except Exception as e:
                        print(e)
                    self.reset()
            if not running:
                break
            pressed = pygame.key.get_pressed()
            self.simple_react_to_keys(pressed, bathroom_no, bedroom_no, hall_no, kitchen_no, mode)
            if self._agent.sprite.rect.colliderect(self._objective.sprite.rect):
                self.reset_objective()
                score += 1
            pygame.display.update()
            clock.tick(100)
            frames -= 1
            if frames == 0:
                running = False
                print(f"score achieved: {str(score)}")
        pygame.display.quit()

    def simple_react_to_keys(self, pressed, bathroom_no, bedroom_no, hall_no, kitchen_no, mode):
        if pressed[pygame.K_s] and mode == "generate":
            self.save_generated_model()
            self.reset()
            self.generate_environment(bathroom_no, bedroom_no, kitchen_no, hall_no)
            self.draw_model()
        if pressed[pygame.K_n] and mode == "generate":
            self.reset()
            self.generate_environment(bathroom_no, bedroom_no, kitchen_no, hall_no)
            self.draw_model()

    def reset_objective(self):
        ridx = random.randint(0, len(self._rooms) - 1)
        self._objective.x = int(random.uniform(self._rooms[ridx].x * 1.15,
                                               (self._rooms[ridx].x + self._rooms[ridx].width * 0.85)))
        self._objective.y = int(random.uniform(self._rooms[ridx].y * 1.15,
                                               (self._rooms[ridx].y + self._rooms[ridx].height * 0.85)))
        self._objective.sprite.rect.x = self._objective.x
        self._objective.sprite.rect.y = self._objective.y

    def reset(self):
        self._env_width = 15.0 * self._multiplier
        self._env_height = 15.0 * self._multiplier
        self._floor = Game_Object(0, 0, 0, 0, 0, 'floor')
        self._rooms = []

    def generate_rooms_and_doors(self, bathroom_no, bedroom_no,
                                 kitchen_no, hall_no,
                                 floor_pos, door_pos_x, door_pos_y):
        room_number = bedroom_no + kitchen_no + bathroom_no + hall_no
        room_distance_threshold = 10.0 + 3 * room_number
        self._env_width = self._env_width + (8.0 * room_number * self._multiplier)
        self._env_height = self._env_height + (8.0 * room_number * self._multiplier)
        self._screen = pygame.display.set_mode((int(self._env_width), int(self._env_height)))
        self.makes_sprites()

        predicate_body, predicate_head, query, room_type = self.build_query(bathroom_no, bedroom_no, hall_no,
                                                                            kitchen_no, room_distance_threshold,
                                                                            room_number)
        self._prolog.assertz(predicate_head + predicate_body)
        query_out = self._prolog.query(query)
        self.make_rooms(room_number, room_type, query_out)
        self._prolog.retract(predicate_head + predicate_body)
        barycenter = self.make_barycenter()
        self.make_floor(barycenter, floor_pos)
        self.make_doors(barycenter)

    def make_doors(self, barycenter):
        for room in self._rooms:
            side1 = (room.vertex1, room.vertex4)
            side2 = (room.vertex1, room.vertex2)
            side3 = (room.vertex2, room.vertex3)
            side4 = (room.vertex3, room.vertex4)

            side_distance1 = math.sqrt((((side1[0].x + side1[1].x) / 2) - barycenter.x) ** 2 +
                                       (((side1[0].y + side1[1].y) / 2) - barycenter.y) ** 2)
            side_distance2 = math.sqrt((((side2[0].x + side2[1].x) / 2) - barycenter.x) ** 2 +
                                       (((side2[0].y + side2[1].y) / 2) - barycenter.y) ** 2)
            side_distance3 = math.sqrt((((side3[0].x + side3[1].x) / 2) - barycenter.x) ** 2 +
                                       (((side3[0].y + side3[1].y) / 2) - barycenter.y) ** 2)
            side_distance4 = math.sqrt((((side4[0].x + side4[1].x) / 2) - barycenter.x) ** 2 +
                                       (((side4[0].y + side4[1].y) / 2) - barycenter.y) ** 2)
            min_distance = min(side_distance1, side_distance2, side_distance3, side_distance4)

            if min_distance == side_distance1:
                constraints_satisfied = False
                door_y = 0
                while not constraints_satisfied:
                    door_y = random.random() * (room.height - 2.5 * self._multiplier) + room.y
                    if door_y >= self._floor.y and door_y + 2.5 * self._multiplier <= self._floor.y + self._floor.height:
                        constraints_satisfied = True
                door_sprite = pygame.sprite.Sprite()
                door_sprite.image = self._type_to_sprite['door']
                door_sprite.image = pygame.transform.scale(door_sprite.image,
                                                           (int(1.0 * self._multiplier),
                                                            int(2.5 * self._multiplier)))
                room.door = Game_Object(room.x, door_y, 0, 2.5 * self._multiplier, door_sprite, 'door')

            elif min_distance == side_distance2:
                constraints_satisfied = False
                door_x = 0
                while not constraints_satisfied:
                    door_x = random.random() * (room.width - 2.5 * self._multiplier) + room.x
                    if door_x >= self._floor.x and door_x + 2.5 * self._multiplier <= self._floor.x + self._floor.width:
                        constraints_satisfied = True
                door_sprite = pygame.sprite.Sprite()
                door_sprite.image = self._type_to_sprite['door']
                door_sprite.image = pygame.transform.rotate(door_sprite.image, 90)
                door_sprite.image = pygame.transform.scale(door_sprite.image,
                                                           (int(2.5 * self._multiplier),
                                                            int(1.0 * self._multiplier)))
                room.door = Game_Object(door_x, room.y + room.height, 2.5 * self._multiplier, 0, door_sprite, 'door')

            elif min_distance == side_distance3:
                constraints_satisfied = False
                door_y = 0
                while not constraints_satisfied:
                    door_y = random.random() * (room.height - 2.5 * self._multiplier) + room.y
                    if door_y >= self._floor.y and door_y + 2.5 * self._multiplier <= self._floor.y + self._floor.height:
                        constraints_satisfied = True

                door_sprite = pygame.sprite.Sprite()
                door_sprite.image = self._type_to_sprite['door']
                door_sprite.image = pygame.transform.scale(door_sprite.image,
                                                           (int(1.0 * self._multiplier),
                                                            int(2.5 * self._multiplier)))
                room.door = Game_Object(room.x + room.width, door_y, 0, 2.5 * self._multiplier, door_sprite, 'door')
            else:
                constraints_satisfied = False
                door_x = 0
                while not constraints_satisfied:
                    door_x = random.random() * (room.width - 2.5 * self._multiplier) + room.x
                    if door_x >= self._floor.x and door_x + 2.5 * self._multiplier <= self._floor.x + self._floor.width:
                        constraints_satisfied = True
                door_sprite = pygame.sprite.Sprite()
                door_sprite.image = self._type_to_sprite['door']
                door_sprite.image = pygame.transform.rotate(door_sprite.image, 90)
                door_sprite.image = pygame.transform.scale(door_sprite.image,
                                                           (int(2.5 * self._multiplier),
                                                            int(1.0 * self._multiplier)))
                room.door = Game_Object(door_x, room.y, 2.5 * self._multiplier, 0, door_sprite, 'door')

    def make_floor(self, barycenter, floor_pos):
        vertexes_xs = []
        vertexes_ys = []
        for room in self._rooms:
            vertex1_distance = math.sqrt(
                (room.vertex1.x - barycenter.x) ** 2 + (room.vertex1.y - barycenter.y) ** 2)
            vertex2_distance = math.sqrt(
                (room.vertex2.x - barycenter.x) ** 2 + (room.vertex2.y - barycenter.y) ** 2)
            vertex3_distance = math.sqrt(
                (room.vertex3.x - barycenter.x) ** 2 + (room.vertex3.y - barycenter.y) ** 2)
            vertex4_distance = math.sqrt(
                (room.vertex4.x - barycenter.x) ** 2 + (room.vertex4.y - barycenter.y) ** 2)

            min_distance = min(vertex1_distance, vertex2_distance, vertex3_distance, vertex4_distance)

            if min_distance == vertex1_distance:
                vertexes_xs.append(room.vertex1.x)
                vertexes_ys.append(room.vertex1.y)
            elif min_distance == vertex2_distance:
                vertexes_xs.append(room.vertex2.x)
                vertexes_ys.append(room.vertex2.y)
            elif min_distance == vertex3_distance:
                vertexes_xs.append(room.vertex3.x)
                vertexes_ys.append(room.vertex3.y)
            else:
                vertexes_xs.append(room.vertex4.x)
                vertexes_ys.append(room.vertex4.y)
        space_multiplier = (floor_pos * 3 + 3) * self._multiplier
        floor_sprite = pygame.sprite.Sprite()
        floor_sprite.image = self._type_to_sprite['floor']
        floor_sprite.image = pygame.transform.scale(floor_sprite.image, (
            int(max(vertexes_xs) - min(vertexes_xs) + space_multiplier * 2),
            int(max(vertexes_ys) - min(vertexes_ys) + space_multiplier * 2)))
        floor_sprite.rect = pygame.Rect(min(vertexes_xs) - space_multiplier,
                                        min(vertexes_ys) - space_multiplier,
                                        max(vertexes_xs) - min(vertexes_xs) + space_multiplier * 2,
                                        max(vertexes_ys) - min(vertexes_ys) + space_multiplier * 2)
        self._floor = Game_Object(min(vertexes_xs) - space_multiplier, min(vertexes_ys) - space_multiplier,
                                  max(vertexes_xs) - min(vertexes_xs) + space_multiplier * 2,
                                  max(vertexes_ys) - min(vertexes_ys) + space_multiplier * 2,
                                  floor_sprite, 'floor')

    def make_barycenter(self):
        barycenter_x = 0
        barycenter_y = 0
        for room in self._rooms:
            barycenter_x += room.x + room.width / 2
            barycenter_y += room.y + room.height / 2
        barycenter_x /= len(self._rooms)
        barycenter_y /= len(self._rooms)
        barycenter = Vertex(barycenter_x, barycenter_y)
        return barycenter

    def make_rooms(self, room_number, room_type, query_out):
        self._rooms = []
        for sol in query_out:
            for i in range(0, room_number):
                room_sprite = pygame.sprite.Sprite()
                if room_type[i] == 'bathroom':
                    room_sprite.image = pygame.transform.scale(self._type_to_sprite['bathroom'],
                                                               (int(sol["R" + str(i) + "W"]),
                                                                int(sol["R" + str(i) + "H"])))
                elif room_type[i] == 'kitchen':
                    room_sprite.image = pygame.transform.scale(self._type_to_sprite['kitchen'],
                                                               (int(sol["R" + str(i) + "W"]),
                                                                int(sol["R" + str(i) + "H"])))
                elif room_type[i] == 'bedroom':
                    room_sprite.image = pygame.transform.scale(self._type_to_sprite['bedroom'],
                                                               (int(sol["R" + str(i) + "W"]),
                                                                int(sol["R" + str(i) + "H"])))
                else:
                    room_sprite.image = pygame.transform.scale(self._type_to_sprite['hall'],
                                                               (int(sol["R" + str(i) + "W"]),
                                                                int(sol["R" + str(i) + "H"])))

                room_sprite.rect = pygame.Rect(sol["R" + str(i) + "X"], sol["R" + str(i) + "Y"],
                                               sol["R" + str(i) + "W"],
                                               sol["R" + str(i) + "H"])
                room = Room(sol["R" + str(i) + "X"], sol["R" + str(i) + "Y"], sol["R" + str(i) + "W"],
                            sol["R" + str(i) + "H"], i, room_sprite, room_type[i])
                room.vertex1 = Vertex(room.x, room.y + room.height)
                room.vertex2 = Vertex(room.x + room.width, room.y + room.height)
                room.vertex3 = Vertex(room.x + room.width, room.y)
                room.vertex4 = Vertex(room.x, room.y)
                self._rooms.append(room)

    def build_query(self, bathroom_no, bedroom_no, hall_no, kitchen_no, room_distance_threshold, room_number):
        head_variables = ""
        predicate_head = "generateEnvironment(EnvWidth, EnvHeight, "
        query_start = "generateEnvironment(" + str(self._env_width) + ", " + str(self._env_height) + ", "
        for i in range(0, room_number):
            head_variables += "R" + str(i) + "X" + ", "
            head_variables += "R" + str(i) + "Y" + ", "
            head_variables += "R" + str(i) + "W" + ", "
            head_variables += "R" + str(i) + "H" + ", "
        head_variables = head_variables[:-2]
        predicate_head = predicate_head + head_variables
        predicate_head += ") "
        query = query_start + head_variables + ") "
        predicate_body = ":- repeat, "
        room_type = []
        for i in range(0, bedroom_no):
            room_type.append('bedroom')
        for i in range(0, bathroom_no):
            room_type.append('bathroom')
        for i in range(0, kitchen_no):
            room_type.append('kitchen')
        for i in range(0, hall_no):
            room_type.append('hall')
        for i in range(0, room_number):
            if room_type[i] == 'bedroom':
                predicate_body += "random(" + str(12.0 * self._multiplier) + ", " + str(
                    17.0 * self._multiplier) + ", R" + str(i) + "W), "
                predicate_body += "random(" + str(12.0 * self._multiplier) + ", " + str(
                    17.0 * self._multiplier) + ", R" + str(i) + "H), "
                predicate_body += "WSUB" + str(i) + " is EnvWidth - R" + str(i) + "W, random(0.0, WSUB" + str(
                    i) + ", R" + str(i) + "X), "
                predicate_body += "HSUB" + str(i) + " is EnvHeight - R" + str(i) + "H, random(0.0, HSUB" + str(
                    i) + ", R" + str(i) + "Y), "
            if room_type[i] == 'bathroom':
                predicate_body += "random(" + str(8.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", R" + str(i) + "W), "
                predicate_body += "random(" + str(8.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", R" + str(i) + "H), "
                predicate_body += "WSUB" + str(i) + " is EnvWidth - R" + str(i) + "W, random(0.0, WSUB" + str(
                    i) + ", R" + str(i) + "X), "
                predicate_body += "HSUB" + str(i) + " is EnvHeight - R" + str(i) + "H, random(0.0, HSUB" + str(
                    i) + ", R" + str(i) + "Y), "
            if room_type[i] == 'kitchen':
                predicate_body += "random(" + str(10.0 * self._multiplier) + ", " + str(
                    15.0 * self._multiplier) + ", R" + str(i) + "W), "
                predicate_body += "random(" + str(10.0 * self._multiplier) + ", " + str(
                    15.0 * self._multiplier) + ", R" + str(i) + "H), "
                predicate_body += "WSUB" + str(i) + " is EnvWidth - R" + str(i) + "W, random(0.0, WSUB" + str(
                    i) + ", R" + str(i) + "X), "
                predicate_body += "HSUB" + str(i) + " is EnvHeight - R" + str(i) + "H, random(0.0, HSUB" + str(
                    i) + ", R" + str(i) + "Y), "
            if room_type[i] == 'hall':
                predicate_body += "random(" + str(15.0 * self._multiplier) + ", " + str(
                    20.0 * self._multiplier) + ", R" + str(i) + "W), "
                predicate_body += "random(" + str(15.0 * self._multiplier) + ", " + str(
                    20.0 * self._multiplier) + ", R" + str(i) + "H), "
                predicate_body += "WSUB" + str(i) + " is EnvWidth - R" + str(i) + "W, random(0.0, WSUB" + str(
                    i) + ", R" + str(i) + "X), "
                predicate_body += "HSUB" + str(i) + " is EnvHeight - R" + str(i) + "H, random(0.0, HSUB" + str(
                    i) + ", R" + str(i) + "Y), "
        for i in range(0, room_number):
            for j in range(i + 1, room_number):
                predicate_body += "{(R" + str(i) + "X + R" + str(i) + "W + " + str(
                    self._fake_collision_mt * self._multiplier) + " =< R" + str(j) + "X ; R" + str(j) + "X + R" + str(
                    j) + "W + " + str(self._fake_collision_mt * self._multiplier) + " =< R" + str(i) + "X) ; (R" + str(
                    i) + "Y + R" + str(i) + "H + " + str(self._fake_collision_mt * self._multiplier) + " =< R" + str(
                    j) + "Y ; R" + str(j) + "Y + R" + str(j) + "H + " + str(
                    self._fake_collision_mt * self._multiplier) + " =< R" + str(i) + "Y)}, "
        if room_number > 1:
            predicate_body += "CentreX is ("
            for i in range(0, room_number):
                predicate_body += "R" + str(i) + "X + "
            predicate_body = predicate_body[:-3]
            predicate_body += ") / " + str(room_number) + ", "
            predicate_body += "CentreY is ("
            for i in range(0, room_number):
                predicate_body += "R" + str(i) + "Y + "
            predicate_body = predicate_body[:-3]
            predicate_body += ") / " + str(room_number) + ", "

            for i in range(0, room_number):
                predicate_body += "RoomDistance" + str(i) + " is "
                predicate_body += "sqrt(((R" + str(i) + "X + R" + str(i) + "W/2) - (CentreX))^2 + ((R" + str(
                    i) + "Y + R" + str(i) + "H/2) - (CentreY))^2), "
                predicate_body += "{DistanceRoom" + str(i) + " =< " + str(
                    room_distance_threshold * self._multiplier) + "}, "
        predicate_body = predicate_body[:-2]
        predicate_body += ", !"
        return predicate_body, predicate_head, query, room_type

    def makes_sprites(self):
        self._type_to_sprite = dict(hall=pygame.image.load('../textures/hall_texture.png').convert_alpha(),
                                    kitchen=pygame.image.load('../textures/kitchen_texture.png').convert_alpha(),
                                    bedroom=pygame.image.load('../textures/bedroom_texture.png').convert_alpha(),
                                    bathroom=pygame.image.load('../textures/bathroom_texture.png').convert_alpha(),
                                    door=pygame.image.load('../textures/door_texture.png').convert_alpha(),
                                    toilet=pygame.image.load('../textures/toilet_texture.png').convert_alpha(),
                                    shower=pygame.image.load('../textures/shower_texture.png').convert_alpha(),
                                    bed=pygame.image.load('../textures/green_bed_texture.png').convert_alpha(),
                                    bedside=pygame.image.load('../textures/bedside_texture.png').convert_alpha(),
                                    sofa=pygame.image.load('../textures/sofa_texture.png').convert_alpha(),
                                    hall_table=pygame.image.load('../textures/hall_table_texture.png').convert_alpha(),
                                    table=pygame.image.load('../textures/table_texture.png').convert_alpha(),
                                    chair=pygame.image.load('../textures/chair_texture.png').convert_alpha(),
                                    desk=pygame.image.load('../textures/desk_texture.png').convert_alpha(),
                                    sink=pygame.image.load('../textures/sink_texture.png').convert_alpha(),
                                    wardrobe=pygame.image.load('../textures/wardrobe_texture.png').convert_alpha(),
                                    cupboard=pygame.image.load('../textures/wardrobe_texture.png').convert_alpha(),
                                    floor=pygame.image.load('../textures/floor_texture.png').convert_alpha(),
                                    agent=pygame.image.load('../textures/agent_texture_mockup.png').convert_alpha(),
                                    objective=pygame.image.load(
                                        '../textures/objective_texture_mockup.png').convert_alpha())
        agent_sprite = pygame.sprite.Sprite()
        agent_sprite.image = pygame.transform.scale(self._type_to_sprite['agent'],
                                                    (int(self._agent.width), int(self._agent.height)))
        agent_sprite.rect = pygame.Rect(self._agent.x, self._agent.y, self._agent.width, self._agent.height)
        self._agent.sprite = agent_sprite
        self._agent.image = self._agent.sprite.image
        objective_sprite = pygame.sprite.Sprite()
        objective_sprite.image = pygame.transform.scale(self._type_to_sprite['objective'],
                                                        (int(self._objective.width), int(self._objective.height)))
        objective_sprite.rect = pygame.Rect(self._objective.x, self._objective.y, self._objective.width,
                                            self._objective.height)
        self._objective.sprite = objective_sprite

    def get_rooms(self, flag):
        result = []
        for room in (x for x in self._rooms if x.type == flag):
            result.append(room)
        return result

    def populate_kitchen(self, kitchen, desk_no, table_no):
        head_variables = ""
        predicate_head = "generateKitchen" + str(kitchen.index) + "(ZeroX, ZeroY, RoomWidth, RoomHeight, "
        query = "generateKitchen" + str(kitchen.index) + "(" + str(kitchen.x) + ", " + str(kitchen.y) + ", " + str(
            kitchen.width) + ", " + str(kitchen.height) + ", "
        for i in range(0, desk_no):
            head_variables += "D" + str(i) + "X" + ", "
            head_variables += "D" + str(i) + "Y" + ", "
            head_variables += "D" + str(i) + "W" + ", "
            head_variables += "D" + str(i) + "H" + ", "

            query += "D" + str(i) + "X" + ", "
            query += "D" + str(i) + "Y" + ", "
            query += "D" + str(i) + "W" + ", "
            query += "D" + str(i) + "H" + ", "
        for i in range(0, table_no):
            head_variables += "KTA" + str(i) + "X" + ", "
            head_variables += "KTA" + str(i) + "Y" + ", "
            head_variables += "KTA" + str(i) + "W" + ", "
            head_variables += "KTA" + str(i) + "H" + ", "

            query += "KTA" + str(i) + "X" + ", "
            query += "KTA" + str(i) + "Y" + ", "
            query += "KTA" + str(i) + "W" + ", "
            query += "KTA" + str(i) + "H" + ", "
        for i in range(0, 4 * table_no):
            head_variables += "C" + str(i) + "X" + ", "
            head_variables += "C" + str(i) + "Y" + ", "
            head_variables += "C" + str(i) + "W" + ", "
            head_variables += "C" + str(i) + "H" + ", "

            query += "C" + str(i) + "X" + ", "
            query += "C" + str(i) + "Y" + ", "
            query += "C" + str(i) + "W" + ", "
            query += "C" + str(i) + "H" + ", "

        query = query[:-2]
        predicate_head = predicate_head + head_variables
        predicate_head = predicate_head[:-2]
        predicate_head += ") "
        query += ")"

        predicate_body = ":- repeat, "
        predicate_body += "Rwidthbound is RoomWidth + ZeroX, Rheightbound is RoomHeight + ZeroY, random(" + str(
            1.5 * self._multiplier) + ", " + str(1.8 * self._multiplier) + ", DeskSize), "

        first_angle, second_angle, third_angle, fourth_angle = [], [], [], []

        first_angle_disabled = False
        second_angle_disabled = False
        third_angle_disabled = False
        fourth_angle_disabled = False

        if kitchen.door.x == kitchen.x and kitchen.door.width == 0:
            first_angle_disabled = True
            fourth_angle_disabled = True
        elif kitchen.door.x == kitchen.x + kitchen.width and kitchen.door.width == 0:
            second_angle_disabled = True
            third_angle_disabled = True
        elif kitchen.door.y == kitchen.y and kitchen.door.height == 0:
            fourth_angle_disabled = True
            third_angle_disabled = True
        elif kitchen.door.y == kitchen.y + kitchen.height and kitchen.door.height == 0:
            first_angle_disabled = True
            second_angle_disabled = True

        for i in range(0, desk_no):

            positioned = False
            while not positioned:
                new_position = random.randint(1, 4)
                obstacle_found = False
                if new_position == 1 and not first_angle_disabled:
                    if len(first_angle) < 2:
                        if len(first_angle) == 1:
                            counter_orientation_pre = first_angle[0][1]
                            counter_orientation_new = 1 - counter_orientation_pre

                            if counter_orientation_pre == 0:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in fourth_angle:
                                        obstacle_found = True

                            if counter_orientation_pre == 1:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in second_angle:
                                        obstacle_found = True

                            if not obstacle_found:
                                if counter_orientation_new == 0:
                                    predicate_body += "D" + str(i) + "X is ZeroX + D" + str(
                                        first_angle[0][0]) + "W, {D" + str(i) + "Y = Rheightbound - D" + str(
                                        i) + "H}, D" + str(i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - 2*DeskSize,  random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), "
                                    first_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "X is ZeroX, {D" + str(
                                        i) + "Y = Rheightbound - DeskSize - D" + str(i) + "H}, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - 2*DeskSize,  random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                    first_angle.append((i, 1))
                                positioned = True
                        else:
                            option_zero = True
                            option_one = True
                            for j in range(0, desk_no):
                                if (j, 0) in second_angle:
                                    option_zero = False
                            for j in range(0, desk_no):
                                if (j, 1) in fourth_angle:
                                    option_one = False
                            if option_zero and option_one:
                                if random.randint(0, 1) == 0:
                                    predicate_body += "D" + str(i) + "X is ZeroX, {D" + str(
                                        i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), "
                                    first_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "X is ZeroX, {D" + str(
                                        i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - DeskSize,  random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                    first_angle.append((i, 1))
                                positioned = True
                            if option_zero and not option_one:
                                predicate_body += "D" + str(i) + "X is ZeroX, {D" + str(
                                    i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                    i) + "H is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), "
                                first_angle.append((i, 0))
                                positioned = True
                            if option_one and not option_zero:
                                predicate_body += "D" + str(i) + "X is ZeroX, {D" + str(
                                    i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                    i) + "W is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomHeight - DeskSize,  random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                first_angle.append((i, 1))
                                positioned = True

                if new_position == 2 and not second_angle_disabled:
                    if len(second_angle) < 2:
                        if len(second_angle) == 1:
                            counter_orientation_pre = second_angle[0][1]
                            counter_orientation_new = 1 - counter_orientation_pre
                            if counter_orientation_pre == 1:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in first_angle:
                                        obstacle_found = True
                            if counter_orientation_pre == 0:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in third_angle:
                                        obstacle_found = True
                            if not obstacle_found:
                                if counter_orientation_new == 0:
                                    predicate_body += "{D" + str(i) + "Y = Rheightbound - DeskSize}, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - 2*DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                        i) + "X is Rwidthbound - DeskSize - D" + str(i) + "W, "
                                    second_angle.append((i, 0))
                                else:
                                    predicate_body += "{D" + str(i) + "Y = Rheightbound - DeskSize - D" + str(
                                        i) + "H}, D" + str(i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - 2*DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                        i) + "X is Rwidthbound - DeskSize, "
                                    second_angle.append((i, 1))
                                positioned = True
                        else:
                            option_zero = True
                            option_one = True
                            for j in range(0, desk_no):
                                if (j, 0) in first_angle:
                                    option_zero = False
                            for j in range(0, desk_no):
                                if (j, 1) in third_angle:
                                    option_one = False
                            if option_zero and option_one:
                                if random.randint(0, 1) == 0:
                                    predicate_body += "{D" + str(i) + "Y = Rheightbound - DeskSize}, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                        i) + "X is Rwidthbound - D" + str(i) + "W, "
                                    second_angle.append((i, 0))
                                else:
                                    predicate_body += "{D" + str(i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                        i) + "X is Rwidthbound - DeskSize, "
                                    second_angle.append((i, 1))
                                positioned = True
                            if option_zero and not option_one:
                                predicate_body += "{D" + str(i) + "Y = Rheightbound - DeskSize}, D" + str(
                                    i) + "H is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                    i) + "X is Rwidthbound - D" + str(i) + "W, "
                                second_angle.append((i, 0))
                                positioned = True
                            if option_one and not option_zero:
                                predicate_body += "{D" + str(i) + "Y = Rheightbound - D" + str(i) + "H}, D" + str(
                                    i) + "W is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                    i) + "X is Rwidthbound - DeskSize, "
                                second_angle.append((i, 1))
                                positioned = True

                if new_position == 3 and not third_angle_disabled:
                    if len(third_angle) < 2:
                        if len(third_angle) == 1:
                            counter_orientation_pre = third_angle[0][1]
                            counter_orientation_new = 1 - counter_orientation_pre
                            if counter_orientation_pre == 1:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in fourth_angle:
                                        obstacle_found = True
                            if counter_orientation_pre == 0:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in second_angle:
                                        obstacle_found = True
                            if not obstacle_found:
                                if counter_orientation_new == 0:
                                    predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - 2*DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                        i) + "X is Rwidthbound - DeskSize - D" + str(i) + "W, "
                                    third_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "Y is ZeroY + DeskSize, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - 2*DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                        i) + "X is Rwidthbound - DeskSize, "
                                    third_angle.append((i, 1))
                                positioned = True
                        else:
                            option_zero = True
                            option_one = True
                            for j in range(0, desk_no):
                                if (j, 0) in fourth_angle:
                                    option_zero = False
                            for j in range(0, desk_no):
                                if (j, 1) in second_angle:
                                    option_one = False
                            if option_zero and option_one:
                                if random.randint(0, 1) == 0:
                                    predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                        i) + "X is Rwidthbound - D" + str(i) + "W, "
                                    third_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                        i) + "X is Rwidthbound - DeskSize, "
                                    third_angle.append((i, 1))
                                positioned = True
                            if option_zero and not option_one:
                                predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                    i) + "H is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), D" + str(
                                    i) + "X is Rwidthbound - D" + str(i) + "W, "
                                third_angle.append((i, 0))
                                positioned = True
                            if option_one and not option_zero:
                                predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                    i) + "W is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), D" + str(
                                    i) + "X is Rwidthbound - DeskSize, "
                                third_angle.append((i, 1))
                                positioned = True

                if new_position == 4 and not fourth_angle_disabled:
                    if len(fourth_angle) < 2:
                        if len(fourth_angle) == 1:
                            counter_orientation_pre = fourth_angle[0][1]
                            counter_orientation_new = 1 - counter_orientation_pre
                            if counter_orientation_pre == 1:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in third_angle:
                                        obstacle_found = True
                            if counter_orientation_pre == 0:
                                for j in range(0, desk_no):
                                    if (j, counter_orientation_new) in first_angle:
                                        obstacle_found = True
                            if not obstacle_found:
                                if counter_orientation_new == 0:
                                    predicate_body += "D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "X is ZeroX + DeskSize, D" + str(i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - 2*DeskSize, RoomSupBound is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                        i) + ", RoomSupBound, D" + str(i) + "W), "
                                    fourth_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "X is ZeroX, D" + str(
                                        i) + "Y is ZeroY + DeskSize, D" + str(i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - 2*DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                    fourth_angle.append((i, 1))
                                positioned = True
                        else:
                            option_zero = True
                            option_one = True
                            for j in range(0, desk_no):
                                if (j, 0) in third_angle:
                                    option_zero = False
                            for j in range(0, desk_no):
                                if (j, 1) in first_angle:
                                    option_one = False
                            if option_zero and option_one:
                                if random.randint(0, 1) == 0:
                                    predicate_body += "D" + str(i) + "X is ZeroX, D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "H is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), "
                                    fourth_angle.append((i, 0))
                                else:
                                    predicate_body += "D" + str(i) + "X is ZeroX, D" + str(i) + "Y is ZeroY, D" + str(
                                        i) + "W is DeskSize, DeskInfBound" + str(
                                        i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                        i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                        i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                    fourth_angle.append((i, 1))
                                positioned = True
                            if option_zero and not option_one:
                                predicate_body += "D" + str(i) + "X is ZeroX, D" + str(i) + "Y is ZeroY, D" + str(
                                    i) + "H is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomWidth * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomWidth - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "W), "
                                fourth_angle.append((i, 0))
                                positioned = True
                            if option_one and not option_zero:
                                predicate_body += "D" + str(i) + "X is ZeroX, D" + str(i) + "Y is ZeroY, D" + str(
                                    i) + "W is DeskSize, DeskInfBound" + str(
                                    i) + " is RoomHeight * (7/10) - DeskSize, DeskSupBound" + str(
                                    i) + " is RoomHeight - DeskSize, random(DeskInfBound" + str(
                                    i) + ", DeskSupBound" + str(i) + ", D" + str(i) + "H), "
                                fourth_angle.append((i, 1))
                                positioned = True

        predicate_body += "random(" + str(0.7 * self._multiplier) + ", " + str(
            1.0 * self._multiplier) + ", ChairSize), "
        for i in range(0, table_no):
            predicate_body += "KTA" + str(i) + "WInfBound is RoomWidth*(1/5), KTA" + str(
                i) + "WSupBound is RoomWidth*(3/10), random(KTA" + str(i) + "WInfBound, KTA" + str(
                i) + "WSupBound, KTA" + str(i) + "W), "
            predicate_body += "KTA" + str(i) + "HInfBound is RoomHeight*(1/5), KTA" + str(
                i) + "HSupBound is RoomHeight*(3/10), random(KTA" + str(i) + "HInfBound, KTA" + str(
                i) + "HSupBound, KTA" + str(i) + "H), "

            chair_start_index = i * 4
            for k in range(chair_start_index, chair_start_index + 4):
                predicate_body += "C" + str(k) + "W is ChairSize, C" + str(k) + "H is C" + str(k) + "W, "

            first_side_occupied = False
            second_side_occupied = False
            third_side_occupied = False
            fourth_side_occupied = False

            for j in range(0, desk_no):
                if (j, 1) in first_angle or (j, 1) in fourth_angle:
                    first_side_occupied = True
                if (j, 0) in first_angle or (j, 0) in second_angle:
                    second_side_occupied = True
                if (j, 1) in second_angle or (j, 1) in third_angle:
                    third_side_occupied = True
                if (j, 0) in third_angle or (j, 0) in fourth_angle:
                    fourth_side_occupied = True

            if first_side_occupied:
                predicate_body += "KTA" + str(i) + "XInfBound is ZeroX + DeskSize + ChairSize, "
            else:
                predicate_body += "KTA" + str(i) + "XInfBound is ZeroX + ChairSize, "
            if second_side_occupied:
                predicate_body += "KTA" + str(i) + "YSupBound is Rheightbound - DeskSize - ChairSize - KTA" + str(
                    i) + "H, "
            else:
                predicate_body += "KTA" + str(i) + "YSupBound is Rheightbound - ChairSize - KTA" + str(i) + "H, "
            if third_side_occupied:
                predicate_body += "KTA" + str(i) + "XSupBound is Rwidthbound - DeskSize - ChairSize - KTA" + str(
                    i) + "W, "
            else:
                predicate_body += "KTA" + str(i) + "XSupBound is Rwidthbound - ChairSize - KTA" + str(i) + "W, "
            if fourth_side_occupied:
                predicate_body += "KTA" + str(i) + "YInfBound is ZeroY + DeskSize + ChairSize, "
            else:
                predicate_body += "KTA" + str(i) + "YInfBound is ZeroY + ChairSize, "

            predicate_body += "random(KTA" + str(i) + "XInfBound, KTA" + str(i) + "XSupBound, KTA" + str(
                i) + "X), random(KTA" + str(i) + "YInfBound, KTA" + str(i) + "YSupBound, KTA" + str(i) + "Y), "

            predicate_body += "C" + str(chair_start_index) + "X is KTA" + str(i) + "X + ((KTA" + str(
                i) + "W - ChairSize)/2), C" + str(chair_start_index) + "Y is KTA" + str(i) + "Y + KTA" + str(i) + "H, "
            predicate_body += "C" + str(chair_start_index + 1) + "X is KTA" + str(i) + "X + KTA" + str(
                i) + "W, C" + str(
                chair_start_index + 1) + "Y is KTA" + str(i) + "Y + ((KTA" + str(i) + "H - ChairSize)/2), "
            predicate_body += "C" + str(chair_start_index + 2) + "X is KTA" + str(i) + "X + ((KTA" + str(
                i) + "W - ChairSize)/2), C" + str(chair_start_index + 2) + "Y is KTA" + str(i) + "Y - ChairSize, "
            predicate_body += "C" + str(chair_start_index + 3) + "X is KTA" + str(i) + "X - ChairSize, C" + str(
                chair_start_index + 3) + "Y is KTA" + str(i) + "Y + ((KTA" + str(i) + "H - ChairSize)/2), "

        for j in range(0, table_no):
            if kitchen.door.width == 0:
                predicate_body += "{(" + str(
                    kitchen.door.x + kitchen.door.width + self._door_fake_collision_mt * self._multiplier) + " =< KTA" + str(
                    j) + "X - ChairSize ; KTA" + str(j) + "X + KTA" + str(j) + "W + ChairSize =< " + str(
                    kitchen.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    kitchen.door.y + kitchen.door.height) + " =< KTA" + str(j) + "Y - ChairSize ; KTA" + str(
                    j) + "Y + KTA" + str(j) + "H + ChairSize =< " + str(kitchen.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(kitchen.door.x + kitchen.door.width) + " =< KTA" + str(
                    j) + "X - ChairSize ; KTA" + str(j) + "X + KTA" + str(j) + "W + ChairSize =< " + str(
                    kitchen.door.x) + ") ; (" + str(
                    kitchen.door.y + kitchen.door.height + self._door_fake_collision_mt * self._multiplier) + " =< KTA" + str(
                    j) + "Y - ChairSize ; KTA" + str(j) + "Y + KTA" + str(j) + "H + ChairSize =< " + str(
                    kitchen.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        predicate_body = predicate_body[:-2]
        predicate_body += ", !"
        print("Kitchen predicate is", (predicate_head + predicate_body))
        self._prolog.assertz(predicate_head + predicate_body)

        for sol in self._prolog.query(query):
            for i in range(0, desk_no):
                desk_sprite = pygame.sprite.Sprite()
                desk_sprite.image = self._type_to_sprite['desk']
                sprite_orientation = "S"
                if (i, 0) in first_angle or (i, 0) in second_angle or (i, 0) in third_angle or (i, 0) in fourth_angle:
                    desk_sprite.image = pygame.transform.rotate(desk_sprite.image, 90)
                    sprite_orientation = "E"
                desk_sprite.image = pygame.transform.scale(desk_sprite.image,
                                                           (int(sol["D" + str(i) + "W"]), int(sol["D" + str(i) + "H"])))
                desk_sprite.rect = pygame.Rect(sol["D" + str(i) + "X"], sol["D" + str(i) + "Y"],
                                               sol["D" + str(i) + "W"], sol["D" + str(i) + "H"])
                desk = Game_Object(sol["D" + str(i) + "X"], sol["D" + str(i) + "Y"], sol["D" + str(i) + "W"],
                                   sol["D" + str(i) + "H"], desk_sprite, 'desk')
                desk.orientation = sprite_orientation
                kitchen.children.append(desk)

            for i in range(0, table_no):
                table_sprite = pygame.sprite.Sprite()
                table_sprite.image = self._type_to_sprite['table']
                table_sprite.image = pygame.transform.scale(table_sprite.image, (
                    int(sol["KTA" + str(i) + "W"]), int(sol["KTA" + str(i) + "H"])))
                table_sprite.rect = pygame.Rect(sol["KTA" + str(i) + "X"], sol["KTA" + str(i) + "Y"],
                                                sol["KTA" + str(i) + "W"], sol["KTA" + str(i) + "H"])
                table = Game_Object(sol["KTA" + str(i) + "X"], sol["KTA" + str(i) + "Y"], sol["KTA" + str(i) + "W"],
                                    sol["KTA" + str(i) + "H"], table_sprite, 'table')

                for j in range(i * 4, i * 4 + 4):
                    chair_sprite = pygame.sprite.Sprite()
                    chair_sprite.image = self._type_to_sprite['chair']
                    chair_sprite.image = pygame.transform.rotate(chair_sprite.image, ((j + 2) % 4) * 90)
                    chair_sprite.image = pygame.transform.scale(chair_sprite.image, (
                        int(sol["C" + str(j) + "W"]), int(sol["C" + str(j) + "H"])))
                    chair_sprite.rect = pygame.Rect(sol["C" + str(j) + "X"], sol["C" + str(j) + "Y"],
                                                    sol["C" + str(j) + "W"], sol["C" + str(j) + "H"])
                    chair = Game_Object(sol["C" + str(j) + "X"], sol["C" + str(j) + "Y"], sol["C" + str(j) + "W"],
                                        sol["C" + str(j) + "H"], chair_sprite, 'chair')
                    if j == i * 4:
                        chair.orientation = "S"
                    elif j == i * 4 + 1:
                        chair.orientation = "E"
                    elif j == i * 4 + 2:
                        chair.orientation = "N"
                    else:
                        chair.orientation = "W"
                    table.children.append(chair)
                kitchen.children.append(table)
        self._prolog.retract(predicate_head + predicate_body)

    def populate_bedroom(self, bedroom, bed_no, wardrobe_no):
        head_variables = ""
        predicate_head = "generateBedroom" + str(bedroom.index) + "(ZeroX, ZeroY, RoomWidth, RoomHeight, "
        query = "generateBedroom" + str(bedroom.index) + "(" + str(bedroom.x) + ", " + str(bedroom.y) + ", " + str(
            bedroom.width) + ", " + str(bedroom.height) + ", "

        for i in range(0, bed_no):
            head_variables += "B" + str(i) + "X" + ", "
            head_variables += "B" + str(i) + "Y" + ", "
            head_variables += "B" + str(i) + "W" + ", "
            head_variables += "B" + str(i) + "H" + ", "
            query += "B" + str(i) + "X" + ", "
            query += "B" + str(i) + "Y" + ", "
            query += "B" + str(i) + "W" + ", "
            query += "B" + str(i) + "H" + ", "

        for i in range(0, bed_no):
            head_variables += "BS" + str(i) + "X" + ", "
            head_variables += "BS" + str(i) + "Y" + ", "
            head_variables += "BS" + str(i) + "W" + ", "
            head_variables += "BS" + str(i) + "H" + ", "
            query += "BS" + str(i) + "X" + ", "
            query += "BS" + str(i) + "Y" + ", "
            query += "BS" + str(i) + "W" + ", "
            query += "BS" + str(i) + "H" + ", "

        for i in range(0, wardrobe_no):
            head_variables += "W" + str(i) + "X" + ", "
            head_variables += "W" + str(i) + "Y" + ", "
            head_variables += "W" + str(i) + "W" + ", "
            head_variables += "W" + str(i) + "H" + ", "
            query += "W" + str(i) + "X" + ", "
            query += "W" + str(i) + "Y" + ", "
            query += "W" + str(i) + "W" + ", "
            query += "W" + str(i) + "H" + ", "

        predicate_head = predicate_head + head_variables
        predicate_head = predicate_head[:-2]
        predicate_head += ") "

        query = query[:-2]
        query += ")"

        predicate_body = ":- repeat, "
        predicate_body += "Rwidthbound is RoomWidth + ZeroX, Rheightbound is RoomHeight + ZeroY, "

        for i in range(0, bed_no):
            predicate_body += "{B" + str(i) + "X + B" + str(i) + "W =< Rwidthbound, B" + str(i) + "Y + B" + str(
                i) + "H =< Rheightbound}, "
            predicate_body += "{BS" + str(i) + "X >= ZeroX, BS" + str(i) + "Y >= ZeroY, BS" + str(i) + "X + BS" + str(
                i) + "W =< Rwidthbound, BS" + str(i) + "Y + BS" + str(i) + "H =< Rheightbound}, "

        bed_info = []
        wardrobe_info = []

        while True:
            for i in range(0, bed_no):
                bed_info.append((random.randint(0, 1), random.randint(1, 4)))
            for i in range(0, wardrobe_no):
                wardrobe_info.append((random.randint(1, 4)))

            side1_sum = side2_sum = side3_sum = side4_sum = 0

            for bed_tuple in bed_info:
                if bed_tuple[1] == 1:
                    if bed_tuple[0] == 0:
                        side1_sum += 3.0
                        side1_sum += 2.0
                    else:
                        side1_sum += 6.0
                        side1_sum += 2.0
                if bed_tuple[1] == 2:
                    if bed_tuple[0] == 0:
                        side2_sum += 6.0
                        side2_sum += 2.0
                    else:
                        side2_sum += 3.0
                        side2_sum += 2.0
                if bed_tuple[1] == 3:
                    if bed_tuple[0] == 0:
                        side3_sum += 3.0
                        side3_sum += 2.0
                    else:
                        side3_sum += 6.0
                        side3_sum += 2.0
                if bed_tuple[1] == 4:
                    if bed_tuple[0] == 0:
                        side4_sum += 6.0
                        side4_sum += 2.0
                    else:
                        side4_sum += 3.0
                        side4_sum += 2.0

            for wardrobe_side in wardrobe_info:
                if wardrobe_side == 1:
                    side1_sum += 7.5
                if wardrobe_side == 2:
                    side2_sum += 7.5
                if wardrobe_side == 3:
                    side3_sum += 7.5
                if wardrobe_side == 4:
                    side4_sum += 7.5

            side1_sum *= self._multiplier
            side2_sum *= self._multiplier
            side3_sum *= self._multiplier
            side4_sum *= self._multiplier

            if bedroom.door.x == bedroom.x and bedroom.door.width == 0:
                side1_top = (bedroom.y + bedroom.height) - (bedroom.door.y + bedroom.door.height)
                side1_bot = bedroom.door.y - bedroom.y
                if (
                        side1_sum <= side1_top or side1_sum <= side1_bot) and side2_sum <= bedroom.height and side3_sum <= bedroom.width and side4_sum <= bedroom.height:
                    break
            if bedroom.door.x == bedroom.x + bedroom.width and bedroom.door.width == 0:
                side3_top = (bedroom.y + bedroom.height) - (bedroom.door.y + bedroom.door.height)
                side3_bot = bedroom.door.y - bedroom.y
                if side1_sum <= bedroom.width and side2_sum <= bedroom.height and (
                        side3_sum <= side3_top or side3_sum <= side3_bot) and side4_sum <= bedroom.height:
                    break
            if bedroom.door.y == bedroom.y + bedroom.height and bedroom.door.height == 0:
                side2_left = bedroom.door.x - bedroom.x
                side2_right = (bedroom.x + bedroom.width) - (bedroom.door.x + bedroom.door.width)
                if side1_sum <= bedroom.width and (
                        side2_sum <= side2_left or side2_sum <= side2_right) and side3_sum <= bedroom.width and side4_sum <= bedroom.height:
                    break
            else:
                side4_left = bedroom.door.x - bedroom.x
                side4_right = (bedroom.x + bedroom.width) - (bedroom.door.x + bedroom.door.width)
                if side1_sum <= bedroom.width and side2_sum <= bedroom.height and side3_sum <= bedroom.width and (
                        side4_sum <= side4_left or side4_sum <= side4_right):
                    break
            bed_info = []
            wardrobe_info = []

        for i in range(0, bed_no):
            if bed_info[i][0] == 1:
                predicate_body += "random(" + str(2.0 * self._multiplier) + ", " + str(
                    3.0 * self._multiplier) + ", B" + str(i) + "W" + "), "
                predicate_body += "{B" + str(i) + "H = B" + str(i) + "W + " + str(3.0 * self._multiplier) + "}" + ", "
            else:
                predicate_body += "random(" + str(5.0 * self._multiplier) + ", " + str(
                    6.0 * self._multiplier) + ", B" + str(i) + "W" + "), "
                predicate_body += "{B" + str(i) + "H = B" + str(i) + "W - " + str(3.0 * self._multiplier) + "}" + ", "
            if bed_info[i][1] == 1:
                predicate_body += "{B" + str(i) + "X = ZeroX}, random(ZeroY, Rheightbound, B" + str(i) + "Y" + "), "
            elif bed_info[i][1] == 2:
                predicate_body += "{B" + str(i) + "Y + B" + str(
                    i) + "H = Rheightbound}, random(ZeroX, Rwidthbound, B" + str(i) + "X" + "), "
            elif bed_info[i][1] == 3:
                predicate_body += "{B" + str(i) + "X + B" + str(
                    i) + "W = Rwidthbound}, random(ZeroY, Rheightbound, B" + str(i) + "Y" + "), "
            elif bed_info[i][1] == 4:
                predicate_body += "{B" + str(i) + "Y = ZeroY}, random(ZeroX, Rwidthbound, B" + str(i) + "X" + "), "

        for i in range(0, bed_no):
            if bed_info[i][1] == 1:
                if random.randint(1, 2) == 1:
                    predicate_body += "{BS" + str(i) + "X = ZeroX, BS" + str(i) + "Y = B" + str(i) + "Y + B" + str(
                        i) + "H}, random(" + str(1.5 * self._multiplier) + ", " + str(
                        2.0 * self._multiplier) + ", BS" + str(i) + "W), {BS" + str(i) + "H = BS" + str(i) + "W}, "
                else:
                    predicate_body += "{BS" + str(i) + "X = ZeroX, BS" + str(i) + "Y + BS" + str(i) + "H = B" + str(
                        i) + "Y}, random(" + str(1.5 * self._multiplier) + ", " + str(
                        2.0 * self._multiplier) + ", BS" + str(i) + "W), {BS" + str(i) + "H = BS" + str(i) + "W}, "
            elif bed_info[i][1] == 2:
                if random.randint(1, 2) == 1:
                    predicate_body += "{BS" + str(i) + "Y + BS" + str(i) + "H = Rheightbound, BS" + str(
                        i) + "X = B" + str(i) + "X + B" + str(i) + "W}, random(" + str(
                        1.5 * self._multiplier) + ", " + str(2.0 * self._multiplier) + ", BS" + str(
                        i) + "W), {BS" + str(
                        i) + "H = BS" + str(i) + "W}, "
                else:
                    predicate_body += "{BS" + str(i) + "Y + BS" + str(i) + "H = Rheightbound, BS" + str(
                        i) + "X + BS" + str(i) + "W = B" + str(i) + "X}, random(" + str(
                        1.5 * self._multiplier) + ", " + str(2.0 * self._multiplier) + ", BS" + str(
                        i) + "W), {BS" + str(
                        i) + "H = BS" + str(i) + "W}, "
            elif bed_info[i][1] == 3:
                if random.randint(1, 2) == 1:
                    predicate_body += "{BS" + str(i) + "X + BS" + str(i) + "W = Rwidthbound, BS" + str(
                        i) + "Y = B" + str(i) + "Y + B" + str(i) + "H}, random(" + str(
                        1.5 * self._multiplier) + ", " + str(2.0 * self._multiplier) + ", BS" + str(
                        i) + "W), {BS" + str(
                        i) + "H = BS" + str(i) + "W}, "
                else:  # sotto
                    predicate_body += "{BS" + str(i) + "X + BS" + str(i) + "W = Rwidthbound, BS" + str(
                        i) + "Y + BS" + str(i) + "H = B" + str(i) + "Y}, random(" + str(
                        1.5 * self._multiplier) + ", " + str(2.0 * self._multiplier) + ", BS" + str(
                        i) + "W), {BS" + str(
                        i) + "H = BS" + str(i) + "W}, "
            elif bed_info[i][1] == 4:
                if random.randint(1, 2) == 1:
                    predicate_body += "{BS" + str(i) + "Y = ZeroY, BS" + str(i) + "X = B" + str(i) + "X + B" + str(
                        i) + "W}, random(" + str(1.5 * self._multiplier) + ", " + str(
                        2.0 * self._multiplier) + ", BS" + str(i) + "W), {BS" + str(i) + "H = BS" + str(i) + "W}, "
                else:
                    predicate_body += "{BS" + str(i) + "Y = ZeroY, BS" + str(i) + "X + BS" + str(i) + "W = B" + str(
                        i) + "X}, random(" + str(1.5 * self._multiplier) + ", " + str(
                        2.0 * self._multiplier) + ", BS" + str(i) + "W), {BS" + str(i) + "H = BS" + str(i) + "W}, "

        for i in range(0, wardrobe_no):
            predicate_body += "{W" + str(i) + "X + W" + str(i) + "W =< Rwidthbound, W" + str(i) + "Y + W" + str(
                i) + "H =< Rheightbound}, "

        for i in range(0, wardrobe_no):
            if wardrobe_info[i] == 1:
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", W" + str(i) + "W" + "), "
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    7.5 * self._multiplier) + ", W" + str(i) + "H" + "), "
                predicate_body += "{W" + str(i) + "X = ZeroX}, random(ZeroY, Rheightbound, W" + str(i) + "Y" + "), "
            elif wardrobe_info[i] == 2:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    7.5 * self._multiplier) + ", W" + str(i) + "W" + "), "
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", W" + str(i) + "H" + "), "
                predicate_body += "{W" + str(i) + "Y + W" + str(
                    i) + "H = Rheightbound}, random(ZeroX, Rwidthbound, W" + str(i) + "X" + "), "
            elif wardrobe_info[i] == 3:
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", W" + str(i) + "W" + "), "
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    7.5 * self._multiplier) + ", W" + str(i) + "H" + "), "
                predicate_body += "{W" + str(i) + "X + W" + str(
                    i) + "W = Rwidthbound}, random(ZeroY, Rheightbound, W" + str(i) + "Y" + "), "
            elif wardrobe_info[i] == 4:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    7.5 * self._multiplier) + ", W" + str(i) + "W" + "), "
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", W" + str(i) + "H" + "), "
                predicate_body += "{W" + str(i) + "Y = ZeroY}, random(ZeroX, Rwidthbound, W" + str(i) + "X" + "), "

        for i in range(0, bed_no):
            for j in range(i + 1, bed_no):
                predicate_body += "{(B" + str(i) + "X + B" + str(i) + "W =< B" + str(j) + "X ; B" + str(
                    j) + "X + B" + str(j) + "W =< B" + str(i) + "X) ; (B" + str(i) + "Y + B" + str(i) + "H =< B" + str(
                    j) + "Y ; B" + str(j) + "Y + B" + str(j) + "H =< B" + str(i) + "Y)}, "

        for j in range(0, bed_no):
            if bedroom.door.width == 0:
                predicate_body += "{(" + str(
                    bedroom.door.x + bedroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< B" + str(
                    j) + "X ; B" + str(j) + "X + B" + str(j) + "W =< " + str(
                    bedroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height) + " =< B" + str(j) + "Y ; B" + str(j) + "Y + B" + str(
                    j) + "H =< " + str(bedroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bedroom.door.x + bedroom.door.width) + " =< B" + str(j) + "X ; B" + str(
                    j) + "X + B" + str(j) + "W =< " + str(bedroom.door.x) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< B" + str(
                    j) + "Y ; B" + str(j) + "Y + B" + str(j) + "H =< " + str(
                    bedroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for i in range(0, bed_no):
            for j in range(i + 1, bed_no):
                predicate_body += "{(BS" + str(i) + "X + BS" + str(i) + "W =< BS" + str(j) + "X ; BS" + str(
                    j) + "X + BS" + str(j) + "W =< BS" + str(i) + "X) ; (BS" + str(i) + "Y + BS" + str(
                    i) + "H =< BS" + str(j) + "Y ; BS" + str(j) + "Y + BS" + str(j) + "H =< BS" + str(i) + "Y)}, "

        for j in range(0, bed_no):
            if bedroom.door.width == 0:
                predicate_body += "{(" + str(
                    bedroom.door.x + bedroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< BS" + str(
                    j) + "X ; BS" + str(j) + "X + BS" + str(j) + "W =< " + str(
                    bedroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height) + " =< BS" + str(j) + "Y ; BS" + str(j) + "Y + BS" + str(
                    j) + "H =< " + str(bedroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bedroom.door.x + bedroom.door.width) + " =< BS" + str(j) + "X ; BS" + str(
                    j) + "X + BS" + str(j) + "W =< " + str(bedroom.door.x) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< BS" + str(
                    j) + "Y ; BS" + str(j) + "Y + BS" + str(j) + "H =< " + str(
                    bedroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for i in range(0, wardrobe_no):
            for j in range(i + 1, wardrobe_no):
                predicate_body += "{(W" + str(i) + "X + W" + str(i) + "W =< W" + str(j) + "X ; W" + str(
                    j) + "X + W" + str(j) + "W =< W" + str(i) + "X) ; (W" + str(i) + "Y + W" + str(i) + "H =< W" + str(
                    j) + "Y ; W" + str(j) + "Y + W" + str(j) + "H =< W" + str(i) + "Y)}, "

        for j in range(0, wardrobe_no):
            if bedroom.door.width == 0:
                predicate_body += "{(" + str(
                    bedroom.door.x + bedroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< W" + str(
                    j) + "X ; W" + str(j) + "X + W" + str(j) + "W =< " + str(
                    bedroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height) + " =< W" + str(j) + "Y ; W" + str(j) + "Y + W" + str(
                    j) + "H =< " + str(bedroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bedroom.door.x + bedroom.door.width) + " =< W" + str(j) + "X ; W" + str(
                    j) + "X + W" + str(j) + "W =< " + str(bedroom.door.x) + ") ; (" + str(
                    bedroom.door.y + bedroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< W" + str(
                    j) + "Y ; W" + str(j) + "Y + W" + str(j) + "H =< " + str(
                    bedroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for i in range(0, bed_no):
            for j in range(0, bed_no):
                if i != j:
                    predicate_body += "{(BS" + str(i) + "X + BS" + str(i) + "W =< B" + str(j) + "X ; B" + str(
                        j) + "X + B" + str(j) + "W =< BS" + str(i) + "X) ; (BS" + str(i) + "Y + BS" + str(
                        i) + "H =< B" + str(j) + "Y ; B" + str(j) + "Y + B" + str(j) + "H =< BS" + str(i) + "Y)}, "

        for j in range(0, bed_no):
            for i in range(0, wardrobe_no):
                predicate_body += "{(W" + str(i) + "X + W" + str(i) + "W =< B" + str(j) + "X ; B" + str(
                    j) + "X + B" + str(j) + "W =< W" + str(i) + "X) ; (W" + str(i) + "Y + W" + str(i) + "H =< B" + str(
                    j) + "Y ; B" + str(j) + "Y + B" + str(j) + "H =< W" + str(i) + "Y)}, "

        for i in range(0, bed_no):
            for j in range(0, wardrobe_no):
                predicate_body += "{(BS" + str(i) + "X + BS" + str(i) + "W =< W" + str(j) + "X ; W" + str(
                    j) + "X + W" + str(j) + "W =< BS" + str(i) + "X) ; (BS" + str(i) + "Y + BS" + str(
                    i) + "H =< W" + str(j) + "Y ; W" + str(j) + "Y + W" + str(j) + "H =< BS" + str(i) + "Y)}, "

        predicate_body = predicate_body[:-2]
        predicate_body += ", !"

        print(("Bedroom's predicate " + str(bedroom.index) + " is:"))
        print((predicate_head + predicate_body))
        self._prolog.assertz(predicate_head + predicate_body)

        for sol in self._prolog.query(query):
            for i in range(0, bed_no):
                bed_sprite = pygame.sprite.Sprite()
                bed_sprite.image = self._type_to_sprite['bed']
                sprite_orientation = "S"
                if bed_info[i][1] == 1:
                    if bed_info[i][0] == 0:
                        bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 90)
                        sprite_orientation = "E"
                    else:
                        if random.randint(0, 1) == 0:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 180)
                            sprite_orientation = "N"

                elif bed_info[i][1] == 4:
                    if bed_info[i][0] == 0:
                        if random.randint(0, 1) == 0:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 90)
                            sprite_orientation = "E"
                        else:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, -90)
                            sprite_orientation = "W"

                elif bed_info[i][1] == 3:
                    if bed_info[i][0] == 0:
                        bed_sprite.image = pygame.transform.rotate(bed_sprite.image, -90)
                        sprite_orientation = "W"
                    else:
                        if random.randint(0, 1) == 0:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 180)
                            sprite_orientation = "N"

                elif bed_info[i][1] == 2:
                    if bed_info[i][0] == 0:
                        if random.randint(0, 1) == 0:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 90)
                            sprite_orientation = "E"
                        else:
                            bed_sprite.image = pygame.transform.rotate(bed_sprite.image, -90)
                            sprite_orientation = "W"
                    else:
                        bed_sprite.image = pygame.transform.rotate(bed_sprite.image, 180)
                        sprite_orientation = "N"

                bed_sprite.image = pygame.transform.scale(bed_sprite.image,
                                                          (int(sol["B" + str(i) + "W"]), int(sol["B" + str(i) + "H"])))
                bed_sprite.rect = pygame.Rect(sol["B" + str(i) + "X"], sol["B" + str(i) + "Y"], sol["B" + str(i) + "W"],
                                              sol["B" + str(i) + "H"])
                bed = Game_Object(sol["B" + str(i) + "X"], sol["B" + str(i) + "Y"], sol["B" + str(i) + "W"],
                                  sol["B" + str(i) + "H"], bed_sprite, 'bed')
                bed.orientation = sprite_orientation

                bedside_sprite = pygame.sprite.Sprite()
                bedside_sprite.image = self._type_to_sprite['bedside']
                bedside_sprite.image = pygame.transform.scale(bedside_sprite.image, (
                    int(sol["BS" + str(i) + "W"]), int(sol["BS" + str(i) + "H"])))
                bedside_sprite.rect = pygame.Rect(sol["BS" + str(i) + "X"], sol["BS" + str(i) + "Y"],
                                                  sol["BS" + str(i) + "W"], sol["BS" + str(i) + "H"])
                bedside = Game_Object(sol["BS" + str(i) + "X"], sol["BS" + str(i) + "Y"], sol["BS" + str(i) + "W"],
                                      sol["BS" + str(i) + "H"], bedside_sprite, 'bedside')
                bed.children.append(bedside)
                bedroom.children.append(bed)

            for i in range(0, wardrobe_no):
                wardrobe_sprite = pygame.sprite.Sprite()
                wardrobe_sprite.image = self._type_to_sprite['wardrobe']
                sprite_orientation = "S"
                if wardrobe_info[i] == 2:
                    wardrobe_sprite.image = pygame.transform.rotate(wardrobe_sprite.image, 90)
                    sprite_orientation = "E"

                elif wardrobe_info[i] == 4:
                    wardrobe_sprite.image = pygame.transform.rotate(wardrobe_sprite.image, -90)
                    sprite_orientation = "E"

                wardrobe_sprite.image = pygame.transform.scale(wardrobe_sprite.image, (
                    int(sol["W" + str(i) + "W"]), int(sol["W" + str(i) + "H"])))
                wardrobe_sprite.rect = pygame.Rect(sol["W" + str(i) + "X"], sol["W" + str(i) + "Y"],
                                                   sol["W" + str(i) + "W"], sol["W" + str(i) + "H"])
                wardrobe = Game_Object(sol["W" + str(i) + "X"], sol["W" + str(i) + "Y"], sol["W" + str(i) + "W"],
                                       sol["W" + str(i) + "H"], wardrobe_sprite, 'wardrobe')
                wardrobe.orientation = sprite_orientation
                bedroom.children.append(wardrobe)
        self._prolog.retract(predicate_head + predicate_body)

    def populate_bathroom(self, bathroom, toilet_no, shower_no, sink_no):
        head_variables = ""
        predicate_head = "generateBathroom" + str(bathroom.index) + "(ZeroX, ZeroY, RoomWidth, RoomHeight, "
        query = "generateBathroom" + str(bathroom.index) + "(" + str(bathroom.x) + ", " + str(bathroom.y) + ", " + str(
            bathroom.width) + ", " + str(bathroom.height) + ", "
        for i in range(0, toilet_no):
            head_variables += "T" + str(i) + "X" + ", "
            head_variables += "T" + str(i) + "Y" + ", "
            head_variables += "T" + str(i) + "W" + ", "
            head_variables += "T" + str(i) + "H" + ", "
            query += "T" + str(i) + "X" + ", "
            query += "T" + str(i) + "Y" + ", "
            query += "T" + str(i) + "W" + ", "
            query += "T" + str(i) + "H" + ", "

        for i in range(0, shower_no):
            head_variables += "S" + str(i) + "X" + ", "
            head_variables += "S" + str(i) + "Y" + ", "
            head_variables += "S" + str(i) + "W" + ", "
            head_variables += "S" + str(i) + "H" + ", "
            query += "S" + str(i) + "X" + ", "
            query += "S" + str(i) + "Y" + ", "
            query += "S" + str(i) + "W" + ", "
            query += "S" + str(i) + "H" + ", "

        for i in range(0, sink_no):
            head_variables += "SI" + str(i) + "X" + ", "
            head_variables += "SI" + str(i) + "Y" + ", "
            head_variables += "SI" + str(i) + "W" + ", "
            head_variables += "SI" + str(i) + "H" + ", "
            query += "SI" + str(i) + "X" + ", "
            query += "SI" + str(i) + "Y" + ", "
            query += "SI" + str(i) + "W" + ", "
            query += "SI" + str(i) + "H" + ", "

        predicate_head = predicate_head + head_variables
        predicate_head = predicate_head[:-2]
        predicate_head += ") "

        query = query[:-2]
        query += ")"

        predicate_body = ":- repeat, "
        predicate_body += "Rwidthbound is RoomWidth + ZeroX, Rheightbound is RoomHeight + ZeroY, "
        for i in range(0, toilet_no):
            predicate_body += "{T" + str(i) + "X + T" + str(i) + "W =< Rwidthbound, T" + str(i) + "Y + T" + str(
                i) + "H =< Rheightbound}, "

        toilet_info = []
        for i in range(0, toilet_no):
            toilet_info.append((random.randint(1, 4)))

        for i in range(0, toilet_no):
            if toilet_info[i] == 1:
                predicate_body += "random(" + str(1.0 * self._multiplier) + ", " + str(
                    1.3 * self._multiplier) + ", T" + str(i) + "H" + "), "
                predicate_body += "{T" + str(i) + "X = ZeroX, T" + str(i) + "W = T" + str(i) + "H + " + str(
                    0.7 * self._multiplier) + "}, THSUB" + str(i) + " is Rheightbound - T" + str(
                    i) + "H, random(ZeroY, THSUB" + str(i) + ", T" + str(i) + "Y" + "), "

            elif toilet_info[i] == 2:
                predicate_body += "random(" + str(1.0 * self._multiplier) + ", " + str(
                    1.3 * self._multiplier) + ", T" + str(i) + "W" + "), "
                predicate_body += "{T" + str(i) + "Y + T" + str(i) + "H = Rheightbound, T" + str(i) + "H = T" + str(
                    i) + "W + " + str(0.7 * self._multiplier) + "}, TWSUB" + str(i) + " is Rwidthbound - T" + str(
                    i) + "W, random(ZeroX, TWSUB" + str(i) + ", T" + str(i) + "X" + "), "

            elif toilet_info[i] == 3:
                predicate_body += "random(" + str(1.0 * self._multiplier) + ", " + str(
                    1.3 * self._multiplier) + ", T" + str(i) + "H" + "), "
                predicate_body += "{T" + str(i) + "X + T" + str(i) + "W = Rwidthbound, T" + str(i) + "W = T" + str(
                    i) + "H + " + str(0.7 * self._multiplier) + "}, THSUB" + str(i) + " is Rheightbound - T" + str(
                    i) + "H, random(ZeroY, THSUB" + str(i) + ", T" + str(i) + "Y" + "), "

            elif toilet_info[i] == 4:
                predicate_body += "random(" + str(1.0 * self._multiplier) + ", " + str(
                    1.3 * self._multiplier) + ", T" + str(i) + "W" + "), "
                predicate_body += "{T" + str(i) + "Y = ZeroY, T" + str(i) + "H = T" + str(i) + "W + " + str(
                    0.7 * self._multiplier) + "}, TWSUB" + str(i) + " is Rwidthbound - T" + str(
                    i) + "W, random(ZeroX, TWSUB" + str(i) + ", T" + str(i) + "X" + "), "

        shower_info = []
        for i in range(0, shower_no):
            shower_info.append(random.randint(1, 4))
        for i in range(0, shower_no):
            if shower_info[i] == 1:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    4.0 * self._multiplier) + ", S" + str(i) + "W), S" + str(i) + "H = S" + str(i) + "W, S" + str(
                    i) + "X = ZeroX, SHSUB" + str(i) + " is Rheightbound - S" + str(i) + "H, random(ZeroY, SHSUB" + str(
                    i) + ", S" + str(i) + "Y), "

            if shower_info[i] == 2:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    4.0 * self._multiplier) + ", S" + str(i) + "W), S" + str(i) + "H = S" + str(i) + "W, S" + str(
                    i) + "Y is Rheightbound - S" + str(i) + "H, SWSUB" + str(i) + " is Rwidthbound - S" + str(
                    i) + "W, random(ZeroX, SWSUB" + str(i) + ", S" + str(i) + "X), "

            if shower_info[i] == 3:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    4.0 * self._multiplier) + ", S" + str(i) + "W), S" + str(i) + "H = S" + str(i) + "W, S" + str(
                    i) + "X is Rwidthbound - S" + str(i) + "W, SHSUB" + str(i) + " is Rheightbound - S" + str(
                    i) + "H, random(ZeroY, SHSUB" + str(i) + ", S" + str(i) + "Y), "

            if shower_info[i] == 4:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    4.0 * self._multiplier) + ", S" + str(i) + "W), S" + str(i) + "H = S" + str(i) + "W, S" + str(
                    i) + "Y = ZeroY, SWSUB" + str(i) + " is Rwidthbound - S" + str(i) + "W, random(ZeroX, SWSUB" + str(
                    i) + ", S" + str(i) + "X), "

        sink_info = []
        for i in range(0, sink_no):
            sink_info.append((random.randint(1, 4)))
        for i in range(0, sink_no):
            if sink_info[i] == 1:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.5 * self._multiplier) + ", SI" + str(i) + "H" + "), "
                predicate_body += "{SI" + str(i) + "X = ZeroX, SI" + str(i) + "W = SI" + str(
                    i) + "H * (2/3)}, SIHSUB" + str(i) + " is Rheightbound - SI" + str(
                    i) + "H, random(ZeroY, SIHSUB" + str(i) + ", SI" + str(i) + "Y" + "), "

            elif sink_info[i] == 2:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.5 * self._multiplier) + ", SI" + str(i) + "W" + "), "
                predicate_body += "{SI" + str(i) + "Y + SI" + str(i) + "H = Rheightbound, SI" + str(i) + "H = SI" + str(
                    i) + "W * (2/3)}, SIWSUB" + str(i) + " is Rwidthbound - SI" + str(
                    i) + "W, random(ZeroX, SIWSUB" + str(i) + ", SI" + str(i) + "X" + "), "

            elif sink_info[i] == 3:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.5 * self._multiplier) + ", SI" + str(i) + "H" + "), "
                predicate_body += "{SI" + str(i) + "X + SI" + str(i) + "W = Rwidthbound, SI" + str(i) + "W = SI" + str(
                    i) + "H * (2/3)}, SIHSUB" + str(i) + " is Rheightbound - SI" + str(
                    i) + "H, random(ZeroY, SIHSUB" + str(i) + ", SI" + str(i) + "Y" + "), "

            elif sink_info[i] == 4:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.5 * self._multiplier) + ", SI" + str(i) + "W" + "), "
                predicate_body += "{SI" + str(i) + "Y = ZeroY, SI" + str(i) + "H = SI" + str(
                    i) + "W * (2/3)}, SIWSUB" + str(i) + " is Rwidthbound - SI" + str(
                    i) + "W, random(ZeroX, SIWSUB" + str(i) + ", SI" + str(i) + "X" + "), "

        for j in range(0, shower_no):
            for i in range(0, toilet_no):
                predicate_body += "{(T" + str(i) + "X + T" + str(i) + "W =< S" + str(j) + "X ; S" + str(
                    j) + "X + S" + str(j) + "W =< T" + str(i) + "X) ; (T" + str(i) + "Y + T" + str(i) + "H =< S" + str(
                    j) + "Y ; S" + str(j) + "Y + S" + str(j) + "H =< T" + str(i) + "Y)}, "

        for j in range(0, shower_no):
            if bathroom.door.width == 0:
                predicate_body += "{(" + str(
                    bathroom.door.x + bathroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< S" + str(
                    j) + "X ; S" + str(j) + "X + S" + str(j) + "W =< " + str(
                    bathroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height) + " =< S" + str(j) + "Y ; S" + str(j) + "Y + S" + str(
                    j) + "H =< " + str(bathroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bathroom.door.x + bathroom.door.width) + " =< S" + str(j) + "X ; S" + str(
                    j) + "X + S" + str(j) + "W =< " + str(bathroom.door.x) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< S" + str(
                    j) + "Y ; S" + str(j) + "Y + S" + str(j) + "H =< " + str(
                    bathroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for j in range(0, shower_no):
            for i in range(0, sink_no):
                predicate_body += "{(SI" + str(i) + "X + SI" + str(i) + "W =< S" + str(j) + "X ; S" + str(
                    j) + "X + S" + str(j) + "W =< SI" + str(i) + "X) ; (SI" + str(i) + "Y + SI" + str(
                    i) + "H =< S" + str(j) + "Y ; S" + str(j) + "Y + S" + str(j) + "H =< SI" + str(i) + "Y)}, "

        for j in range(0, sink_no):
            if bathroom.door.width == 0:
                predicate_body += "{(" + str(
                    bathroom.door.x + bathroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< SI" + str(
                    j) + "X ; SI" + str(j) + "X + SI" + str(j) + "W =< " + str(
                    bathroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height) + " =< SI" + str(j) + "Y ; SI" + str(j) + "Y + SI" + str(
                    j) + "H =< " + str(bathroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bathroom.door.x + bathroom.door.width) + " =< SI" + str(
                    j) + "X ; SI" + str(
                    j) + "X + SI" + str(j) + "W =< " + str(bathroom.door.x) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< SI" + str(
                    j) + "Y ; SI" + str(j) + "Y + SI" + str(j) + "H =< " + str(
                    bathroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for j in range(0, sink_no):
            for i in range(0, toilet_no):
                predicate_body += "{(T" + str(i) + "X + T" + str(i) + "W =< SI" + str(j) + "X ; SI" + str(
                    j) + "X + SI" + str(j) + "W =< T" + str(i) + "X) ; (T" + str(i) + "Y + T" + str(
                    i) + "H =< SI" + str(j) + "Y ; SI" + str(j) + "Y + SI" + str(j) + "H =< T" + str(i) + "Y)}, "

        for j in range(0, toilet_no):
            if bathroom.door.width == 0:
                predicate_body += "{(" + str(
                    bathroom.door.x + bathroom.door.width + self._door_fake_collision_mt * self._multiplier) + " =< T" + str(
                    j) + "X ; T" + str(j) + "X + T" + str(j) + "W =< " + str(
                    bathroom.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height) + " =< T" + str(j) + "Y ; T" + str(j) + "Y + T" + str(
                    j) + "H =< " + str(bathroom.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(bathroom.door.x + bathroom.door.width) + " =< T" + str(j) + "X ; T" + str(
                    j) + "X + T" + str(j) + "W =< " + str(bathroom.door.x) + ") ; (" + str(
                    bathroom.door.y + bathroom.door.height + self._door_fake_collision_mt * self._multiplier) + " =< T" + str(
                    j) + "Y ; T" + str(j) + "Y + T" + str(j) + "H =< " + str(
                    bathroom.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        predicate_body = predicate_body[:-2]
        predicate_body += ", !"

        print("The predicate to generate the bathroom is: ")
        print((predicate_head + predicate_body))
        self._prolog.assertz(predicate_head + predicate_body)

        for sol in self._prolog.query(query):
            for i in range(0, toilet_no):
                toilet_sprite = pygame.sprite.Sprite()
                toilet_sprite.image = self._type_to_sprite['toilet']
                sprite_orientation = "S"
                if toilet_info[i] == 1:
                    toilet_sprite.image = pygame.transform.rotate(toilet_sprite.image, 90)
                    sprite_orientation = "E"

                elif toilet_info[i] == 3:
                    toilet_sprite.image = pygame.transform.rotate(toilet_sprite.image, -90)
                    sprite_orientation = "W"

                elif toilet_info[i] == 4:
                    toilet_sprite.image = pygame.transform.rotate(toilet_sprite.image, 180)
                    sprite_orientation = "N"

                toilet_sprite.image = pygame.transform.scale(toilet_sprite.image, (
                    int(sol["T" + str(i) + "W"]), int(sol["T" + str(i) + "H"])))
                toilet_sprite.rect = pygame.Rect(sol["T" + str(i) + "X"], sol["T" + str(i) + "Y"],
                                                 sol["T" + str(i) + "W"], sol["T" + str(i) + "H"])
                toilet = Game_Object(sol["T" + str(i) + "X"], sol["T" + str(i) + "Y"], sol["T" + str(i) + "W"],
                                     sol["T" + str(i) + "H"], toilet_sprite, 'toilet')
                toilet.orientation = sprite_orientation
                bathroom.children.append(toilet)

            for i in range(0, shower_no):
                shower_sprite = pygame.sprite.Sprite()
                shower_sprite.image = self._type_to_sprite['shower']
                sprite_orientation = "S"
                if shower_info[i] == 1:
                    shower_sprite.image = pygame.transform.rotate(shower_sprite.image, 90)
                    sprite_orientation = "E"

                elif shower_info[i] == 3:
                    shower_sprite.image = pygame.transform.rotate(shower_sprite.image, -90)
                    sprite_orientation = "W"

                elif shower_info[i] == 4:
                    shower_sprite.image = pygame.transform.rotate(shower_sprite.image, 180)
                    sprite_orientation = "N"

                shower_sprite.image = pygame.transform.scale(shower_sprite.image, (
                    int(sol["S" + str(i) + "W"]), int(sol["S" + str(i) + "H"])))
                shower_sprite.rect = pygame.Rect(sol["S" + str(i) + "X"], sol["S" + str(i) + "Y"],
                                                 sol["S" + str(i) + "W"], sol["S" + str(i) + "H"])
                shower = Game_Object(sol["S" + str(i) + "X"], sol["S" + str(i) + "Y"], sol["S" + str(i) + "W"],
                                     sol["S" + str(i) + "H"], shower_sprite, 'shower')
                shower.orientation = sprite_orientation
                bathroom.children.append(shower)

            for i in range(0, sink_no):
                sink_sprite = pygame.sprite.Sprite()
                sink_sprite.image = self._type_to_sprite['sink']
                sprite_orientation = "S"
                if sink_info[i] == 1:
                    sink_sprite.image = pygame.transform.rotate(sink_sprite.image, 90)
                    sprite_orientation = "E"

                elif sink_info[i] == 3:
                    sink_sprite.image = pygame.transform.rotate(sink_sprite.image, -90)
                    sprite_orientation = "W"

                elif sink_info[i] == 2:
                    sink_sprite.image = pygame.transform.rotate(sink_sprite.image, 180)
                    sprite_orientation = "N"

                sink_sprite.image = pygame.transform.scale(sink_sprite.image, (
                    int(sol["SI" + str(i) + "W"]), int(sol["SI" + str(i) + "H"])))
                sink_sprite.rect = pygame.Rect(sol["SI" + str(i) + "X"], sol["SI" + str(i) + "Y"],
                                               sol["SI" + str(i) + "W"], sol["SI" + str(i) + "H"])
                sink = Game_Object(sol["SI" + str(i) + "X"], sol["SI" + str(i) + "Y"], sol["SI" + str(i) + "W"],
                                   sol["SI" + str(i) + "H"], sink_sprite, 'sink')
                sink.orientation = sprite_orientation
                bathroom.children.append(sink)

        self._prolog.retract(predicate_head + predicate_body)

    def populate_hall(self, hall, table_no, sofa_no, cupboard_no, sofa_dist_ths):
        head_variables = ""
        predicate_head = "generateHall" + str(hall.index) + "(ZeroX, ZeroY, RoomWidth, RoomHeight, "
        query = "generateHall" + str(hall.index) + "(" + str(hall.x) + ", " + str(hall.y) + ", " + str(
            hall.width) + ", " + str(hall.height) + ", "

        for i in range(0, table_no):
            head_variables += "TA" + str(i) + "X" + ", "
            head_variables += "TA" + str(i) + "Y" + ", "
            head_variables += "TA" + str(i) + "W" + ", "
            head_variables += "TA" + str(i) + "H" + ", "
            query += "TA" + str(i) + "X" + ", "
            query += "TA" + str(i) + "Y" + ", "
            query += "TA" + str(i) + "W" + ", "
            query += "TA" + str(i) + "H" + ", "

        for i in range(0, 4 * table_no):
            head_variables += "C" + str(i) + "X" + ", "
            head_variables += "C" + str(i) + "Y" + ", "
            head_variables += "C" + str(i) + "W" + ", "
            head_variables += "C" + str(i) + "H" + ", "
            query += "C" + str(i) + "X" + ", "
            query += "C" + str(i) + "Y" + ", "
            query += "C" + str(i) + "W" + ", "
            query += "C" + str(i) + "H" + ", "

        for i in range(0, sofa_no):
            head_variables += "SO" + str(i) + "X" + ", "
            head_variables += "SO" + str(i) + "Y" + ", "
            head_variables += "SO" + str(i) + "W" + ", "
            head_variables += "SO" + str(i) + "H" + ", "
            query += "SO" + str(i) + "X" + ", "
            query += "SO" + str(i) + "Y" + ", "
            query += "SO" + str(i) + "W" + ", "
            query += "SO" + str(i) + "H" + ", "

        for i in range(0, cupboard_no):
            head_variables += "CB" + str(i) + "X" + ", "
            head_variables += "CB" + str(i) + "Y" + ", "
            head_variables += "CB" + str(i) + "W" + ", "
            head_variables += "CB" + str(i) + "H" + ", "
            query += "CB" + str(i) + "X" + ", "
            query += "CB" + str(i) + "Y" + ", "
            query += "CB" + str(i) + "W" + ", "
            query += "CB" + str(i) + "H" + ", "

        predicate_head = predicate_head + head_variables
        predicate_head = predicate_head[:-2]
        predicate_head += ") "

        query = query[:-2]
        query += ")"

        predicate_body = ":- repeat, "

        predicate_body += "Rwidthbound is RoomWidth + ZeroX, Rheightbound is RoomHeight + ZeroY, "

        predicate_body += "random(" + str(0.7 * self._multiplier) + ", " + str(
            1.0 * self._multiplier) + ", ChairSize), "
        for i in range(0, table_no):
            predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                6.0 * self._multiplier) + ", TA" + str(
                i) + "W), random(" + str(2.5 * self._multiplier) + ", " + str(6.0 * self._multiplier) + ", TA" + str(
                i) + "H), "
            predicate_body += "{TA" + str(i) + "W * TA" + str(i) + "H >= " + str(
                8.0 * self._multiplier ** 2) + ", TA" + str(
                i) + "W * TA" + str(i) + "H =< " + str(15.0 * self._multiplier ** 2) + "}, "

            chair_start_index = i * 4
            for k in range(chair_start_index, chair_start_index + 4):
                predicate_body += "C" + str(k) + "W is ChairSize, C" + str(k) + "H is C" + str(k) + "W, "

            predicate_body += "TA" + str(i) + "XInf is ZeroX + ChairSize, TA" + str(
                i) + "XSup is Rwidthbound - ChairSize - TA" + str(i) + "W, TA" + str(
                i) + "YInf is ZeroY + ChairSize, TA" + str(i) + "YSup is Rheightbound - TA" + str(
                i) + "H - ChairSize, random(TA" + str(i) + "XInf, TA" + str(i) + "XSup, TA" + str(
                i) + "X), random(TA" + str(i) + "YInf, TA" + str(i) + "YSup, TA" + str(i) + "Y), "

            predicate_body += "C" + str(chair_start_index) + "X is TA" + str(i) + "X + ((TA" + str(
                i) + "W - ChairSize)/2), C" + str(chair_start_index) + "Y is TA" + str(i) + "Y + TA" + str(i) + "H, "
            predicate_body += "C" + str(chair_start_index + 1) + "X is TA" + str(i) + "X + TA" + str(i) + "W, C" + str(
                chair_start_index + 1) + "Y is TA" + str(i) + "Y + ((TA" + str(i) + "H - ChairSize)/2), "
            predicate_body += "C" + str(chair_start_index + 2) + "X is TA" + str(i) + "X + ((TA" + str(
                i) + "W - ChairSize)/2), C" + str(chair_start_index + 2) + "Y is TA" + str(i) + "Y - ChairSize, "
            predicate_body += "C" + str(chair_start_index + 3) + "X is TA" + str(i) + "X - ChairSize, C" + str(
                chair_start_index + 3) + "Y is TA" + str(i) + "Y + ((TA" + str(i) + "H - ChairSize)/2), "

        for i in range(0, cupboard_no):
            predicate_body += "{CB" + str(i) + "X + CB" + str(i) + "W =< Rwidthbound, CB" + str(i) + "Y + CB" + str(
                i) + "H =< Rheightbound}, "

        cupboard_info = []
        for i in range(0, cupboard_no):
            cupboard_info.append(random.randint(1, 4))
        for i in range(0, cupboard_no):
            if cupboard_info[i] == 1:
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", CB" + str(
                    i) + "W" + "), "
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", CB" + str(
                    i) + "H" + "), "
                predicate_body += "{CB" + str(i) + "X = ZeroX}, random(ZeroY, Rheightbound, CB" + str(i) + "Y" + "), "
            elif cupboard_info[i] == 2:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", CB" + str(
                    i) + "W" + "), "
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", CB" + str(
                    i) + "H" + "), "
                predicate_body += "{CB" + str(i) + "Y + CB" + str(
                    i) + "H = Rheightbound}, random(ZeroX, Rwidthbound, CB" + str(i) + "X" + "), "
            elif cupboard_info[i] == 3:
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", CB" + str(
                    i) + "W" + "), "
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", CB" + str(
                    i) + "H" + "), "
                predicate_body += "{CB" + str(i) + "X + CB" + str(
                    i) + "W = Rwidthbound}, random(ZeroY, Rheightbound, CB" + str(i) + "Y" + "), "
            elif cupboard_info[i] == 4:
                predicate_body += "random(" + str(3.0 * self._multiplier) + ", " + str(
                    12.0 * self._multiplier) + ", CB" + str(
                    i) + "W" + "), "
                predicate_body += "random(" + str(1.5 * self._multiplier) + ", " + str(
                    2.0 * self._multiplier) + ", CB" + str(
                    i) + "H" + "), "
                predicate_body += "{CB" + str(i) + "Y = ZeroY}, random(ZeroX, Rwidthbound, CB" + str(i) + "X" + "), "

        sofa_info = []
        directions = [1, 2, 3, 4]
        for i in range(0, sofa_no):
            sofa_info.append(directions.pop(
                random.randint(0, len(directions) - 1)))
        for i in range(0, sofa_no):
            if sofa_info[i] == 1 or sofa_info[i] == 3:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.0 * self._multiplier) + ", SO" + str(
                    i) + "W), random(" + str(6.0 * self._multiplier) + ", " + str(
                    8.0 * self._multiplier) + ", SO" + str(
                    i) + "H), "
            else:
                predicate_body += "random(" + str(2.5 * self._multiplier) + ", " + str(
                    3.0 * self._multiplier) + ", SO" + str(
                    i) + "H), random(" + str(6.0 * self._multiplier) + ", " + str(
                    8.0 * self._multiplier) + ", SO" + str(
                    i) + "W), "

            if sofa_info[i] == 1:
                predicate_body += "SO" + str(i) + "HSUB is Rheightbound - SO" + str(i) + "H, random(ZeroY, SO" + str(
                    i) + "HSUB, SO" + str(i) + "Y), SO" + str(i) + "WSUB is ZeroX + RoomWidth/2 - SO" + str(
                    i) + "W, random(ZeroX, SO" + str(i) + "WSUB, SO" + str(i) + "X), "

            elif sofa_info[i] == 2:
                predicate_body += "SO" + str(i) + "HSUB1 is ZeroY + RoomHeight/2, SO" + str(
                    i) + "HSUB2 is Rheightbound - SO" + str(i) + "H, random(SO" + str(i) + "HSUB1, SO" + str(
                    i) + "HSUB2, SO" + str(i) + "Y), SO" + str(i) + "WSUB is Rwidthbound - SO" + str(
                    i) + "W, random(ZeroX, SO" + str(i) + "WSUB, SO" + str(i) + "X), "
            elif sofa_info[i] == 3:
                predicate_body += "SO" + str(i) + "HSUB is Rheightbound - SO" + str(i) + "H, random(ZeroY, SO" + str(
                    i) + "HSUB, SO" + str(i) + "Y), SO" + str(i) + "WSUB1 is ZeroX + RoomWidth/2, SO" + str(
                    i) + "WSUB2 is Rwidthbound - SO" + str(i) + "W, random(SO" + str(i) + "WSUB1, SO" + str(
                    i) + "WSUB2, SO" + str(i) + "X), "
            elif sofa_info[i] == 4:
                predicate_body += "SO" + str(i) + "HSUB is ZeroY + RoomHeight/2 - SO" + str(
                    i) + "H, random(ZeroY, SO" + str(
                    i) + "HSUB, SO" + str(i) + "Y), SO" + str(i) + "WSUB is Rwidthbound - SO" + str(
                    i) + "W, random(ZeroX, SO" + str(i) + "WSUB, SO" + str(i) + "X), "

        for j in range(0, sofa_no):
            for i in range(0, cupboard_no):
                predicate_body += "{(CB" + str(i) + "X + CB" + str(i) + "W =< SO" + str(j) + "X - " + str(
                    sofa_dist_ths * self._multiplier) + "; SO" + str(j) + "X + SO" + str(j) + "W =< CB" + str(
                    i) + "X - " + str(sofa_dist_ths * self._multiplier) + ") ; (CB" + str(i) + "Y + CB" + str(
                    i) + "H =< SO" + str(j) + "Y - " + str(sofa_dist_ths * self._multiplier) + " ; SO" + str(
                    j) + "Y + SO" + str(j) + "H =< CB" + str(i) + "Y - " + str(
                    sofa_dist_ths * self._multiplier) + ")}, "

        for j in range(0, sofa_no):
            if hall.door.width == 0:
                predicate_body += "{(" + str(
                    hall.door.x + hall.door.width + self._door_fake_collision_mt * self._multiplier) + " =< SO" + str(
                    j) + "X ; SO" + str(j) + "X + SO" + str(j) + "W =< " + str(
                    hall.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    hall.door.y + hall.door.height) + " =< SO" + str(j) + "Y ; SO" + str(j) + "Y + SO" + str(
                    j) + "H =< " + str(hall.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(hall.door.x + hall.door.width) + " =< SO" + str(j) + "X ; SO" + str(
                    j) + "X + SO" + str(j) + "W =< " + str(hall.door.x) + ") ; (" + str(
                    hall.door.y + hall.door.height + self._door_fake_collision_mt * self._multiplier) + " =< SO" + str(
                    j) + "Y ; SO" + str(j) + "Y + SO" + str(j) + "H =< " + str(
                    hall.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for i in range(0, cupboard_no):
            for j in range(i + 1, cupboard_no):
                predicate_body += "{(CB" + str(i) + "X + CB" + str(i) + "W =< CB" + str(j) + "X ; CB" + str(
                    j) + "X + CB" + str(j) + "W =< CB" + str(i) + "X) ; (CB" + str(i) + "Y + CB" + str(
                    i) + "H =< CB" + str(
                    j) + "Y ; CB" + str(j) + "Y + CB" + str(j) + "H =< CB" + str(i) + "Y)}, "

        for j in range(0, cupboard_no):
            if hall.door.width == 0:
                predicate_body += "{(" + str(
                    hall.door.x + hall.door.width + self._door_fake_collision_mt * self._multiplier) + " =< CB" + str(
                    j) + "X ; CB" + str(j) + "X + CB" + str(j) + "W =< " + str(
                    hall.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    hall.door.y + hall.door.height) + " =< CB" + str(j) + "Y ; CB" + str(j) + "Y + CB" + str(
                    j) + "H =< " + str(hall.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(hall.door.x + hall.door.width) + " =< CB" + str(j) + "X ; CB" + str(
                    j) + "X + CB" + str(j) + "W =< " + str(hall.door.x) + ") ; (" + str(
                    hall.door.y + hall.door.height + self._door_fake_collision_mt * self._multiplier) + " =< CB" + str(
                    j) + "Y ; CB" + str(j) + "Y + CB" + str(j) + "H =< " + str(
                    hall.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for i in range(0, sofa_no):
            for j in range(i + 1, sofa_no):
                predicate_body += "{(SO" + str(i) + "X + SO" + str(i) + "W =< SO" + str(j) + "X - " + str(
                    sofa_dist_ths * self._multiplier) + "; SO" + str(j) + "X + SO" + str(j) + "W =< SO" + str(
                    i) + "X - " + str(sofa_dist_ths * self._multiplier) + ") ; (SO" + str(i) + "Y + SO" + str(
                    i) + "H =< SO" + str(j) + "Y - " + str(sofa_dist_ths * self._multiplier) + "; SO" + str(
                    j) + "Y + SO" + str(j) + "H =< SO" + str(i) + "Y - " + str(
                    sofa_dist_ths * self._multiplier) + ")}, "

        for j in range(0, sofa_no):
            for i in range(0, table_no):
                predicate_body += "{(TA" + str(i) + "X + TA" + str(i) + "W + ChairSize =< SO" + str(j) + "X - " + str(
                    sofa_dist_ths * self._multiplier) + "; SO" + str(j) + "X + SO" + str(j) + "W =< TA" + str(
                    i) + "X - ChairSize - " + str(sofa_dist_ths * self._multiplier) + ") ; (TA" + str(
                    i) + "Y + TA" + str(i) + "H + ChairSize =< SO" + str(j) + "Y - " + str(
                    sofa_dist_ths * self._multiplier) + " ; SO" + str(j) + "Y + SO" + str(j) + "H =< TA" + str(
                    i) + "Y - ChairSize - " + str(sofa_dist_ths * self._multiplier) + ")}, "

        for j in range(0, table_no):
            if hall.door.width == 0:
                predicate_body += "{(" + str(
                    hall.door.x + hall.door.width + self._door_fake_collision_mt * self._multiplier) + " =< TA" + str(
                    j) + "X - ChairSize; TA" + str(j) + "X + TA" + str(j) + "W + ChairSize =< " + str(
                    hall.door.x - self._door_fake_collision_mt * self._multiplier) + ") ; (" + str(
                    hall.door.y + hall.door.height) + " =< TA" + str(j) + "Y - ChairSize ; TA" + str(
                    j) + "Y + TA" + str(
                    j) + "H + ChairSize =< " + str(hall.door.y) + ")}, "
            else:
                predicate_body += "{(" + str(hall.door.x + hall.door.width) + " =< TA" + str(
                    j) + "X - ChairSize; TA" + str(
                    j) + "X + TA" + str(j) + "W + ChairSize =< " + str(hall.door.x) + ") ; (" + str(
                    hall.door.y + hall.door.height + self._door_fake_collision_mt * self._multiplier) + " =< TA" + str(
                    j) + "Y - ChairSize ; TA" + str(j) + "Y + TA" + str(j) + "H + ChairSize =< " + str(
                    hall.door.y - self._door_fake_collision_mt * self._multiplier) + ")}, "

        for j in range(0, cupboard_no):
            for i in range(0, table_no):
                predicate_body += "{(TA" + str(i) + "X + TA" + str(i) + "W + ChairSize =< CB" + str(j) + "X - " + str(
                    sofa_dist_ths * self._multiplier) + "; CB" + str(j) + "X + CB" + str(j) + "W =< TA" + str(
                    i) + "X - ChairSize - " + str(sofa_dist_ths * self._multiplier) + ") ; (TA" + str(
                    i) + "Y + TA" + str(i) + "H + ChairSize =< CB" + str(j) + "Y - " + str(
                    sofa_dist_ths * self._multiplier) + " ; CB" + str(j) + "Y + CB" + str(j) + "H =< TA" + str(
                    i) + "Y - ChairSize - " + str(sofa_dist_ths * self._multiplier) + ")}, "

        for i in range(0, table_no):
            for j in range(i + 1, table_no):
                predicate_body += "{(TA" + str(i) + "X + TA" + str(i) + "W + ChairSize*2 =< TA" + str(j) + "X - " + str(
                    sofa_dist_ths * self._multiplier) + " ; TA" + str(j) + "X + TA" + str(j) + "W =< TA" + str(
                    i) + "X - ChairSize*2 - " + str(sofa_dist_ths * self._multiplier) + ") ; (TA" + str(
                    i) + "Y + TA" + str(i) + "H + ChairSize*2 =< TA" + str(j) + "Y - " + str(
                    sofa_dist_ths * self._multiplier) + " ; TA" + str(j) + "Y + TA" + str(j) + "H =< TA" + str(
                    i) + "Y - ChairSize*2 - " + str(sofa_dist_ths * self._multiplier) + ")}, "

        predicate_body = predicate_body[:-2]
        predicate_body += ", !"
        self._prolog.assertz(predicate_head + predicate_body)
        print(("Hall's query " + str(hall.index) + " is : " + predicate_head + predicate_body))

        for sol in self._prolog.query(query):
            for i in range(0, cupboard_no):
                cupboard_sprite = pygame.sprite.Sprite()
                cupboard_sprite.image = self._type_to_sprite['wardrobe']
                sprite_orientation = "S"
                if cupboard_info[i] == 2 or cupboard_info[i] == 4:
                    cupboard_sprite.image = pygame.transform.rotate(cupboard_sprite.image, 90)
                    sprite_orientation = "E"
                cupboard_sprite.image = pygame.transform.scale(cupboard_sprite.image, (
                    int(sol["CB" + str(i) + "W"]), int(sol["CB" + str(i) + "H"])))
                cupboard_sprite.rect = pygame.Rect(sol["CB" + str(i) + "X"], sol["CB" + str(i) + "Y"],
                                                   sol["CB" + str(i) + "W"], sol["CB" + str(i) + "H"])
                cupboard = Game_Object(sol["CB" + str(i) + "X"], sol["CB" + str(i) + "Y"], sol["CB" + str(i) + "W"],
                                       sol["CB" + str(i) + "H"], cupboard_sprite, 'cupboard')
                cupboard.orientation = sprite_orientation
                hall.children.append(cupboard)

            for i in range(0, sofa_no):
                sofa_sprite = pygame.sprite.Sprite()
                sofa_sprite.image = self._type_to_sprite['sofa']
                sprite_orientation = "S"
                if sofa_info[i] == 1:
                    sofa_sprite.image = pygame.transform.rotate(sofa_sprite.image, 90)
                    sprite_orientation = "E"

                elif sofa_info[i] == 2:
                    sofa_sprite.image = pygame.transform.rotate(sofa_sprite.image, 180)
                    sprite_orientation = "N"

                elif sofa_info[i] == 3:
                    sofa_sprite.image = pygame.transform.rotate(sofa_sprite.image, -90)
                    sprite_orientation = "W"

                sofa_sprite.image = pygame.transform.scale(sofa_sprite.image,
                                                           (
                                                               int(sol["SO" + str(i) + "W"]),
                                                               int(sol["SO" + str(i) + "H"])))
                sofa_sprite.rect = pygame.Rect(sol["SO" + str(i) + "X"], sol["SO" + str(i) + "Y"],
                                               sol["SO" + str(i) + "W"],
                                               sol["SO" + str(i) + "H"])
                sofa = Game_Object(sol["SO" + str(i) + "X"], sol["SO" + str(i) + "Y"], sol["SO" + str(i) + "W"],
                                   sol["SO" + str(i) + "H"], sofa_sprite, 'sofa')
                sofa.orientation = sprite_orientation
                hall.children.append(sofa)

            for i in range(0, table_no):
                table_sprite = pygame.sprite.Sprite()
                table_sprite.image = self._type_to_sprite['hall_table']
                table_sprite.image = pygame.transform.scale(table_sprite.image,
                                                            (int(sol["TA" + str(i) + "W"]),
                                                             int(sol["TA" + str(i) + "H"])))
                table_sprite.rect = pygame.Rect(sol["TA" + str(i) + "X"], sol["TA" + str(i) + "Y"],
                                                sol["TA" + str(i) + "W"],
                                                sol["TA" + str(i) + "H"])
                table = Game_Object(sol["TA" + str(i) + "X"], sol["TA" + str(i) + "Y"], sol["TA" + str(i) + "W"],
                                    sol["TA" + str(i) + "H"], table_sprite, 'hall_table')

                for j in range(i * 4, i * 4 + 4):
                    chair_sprite = pygame.sprite.Sprite()
                    chair_sprite.image = self._type_to_sprite['chair']
                    chair_sprite.image = pygame.transform.rotate(chair_sprite.image, ((j + 2) % 4) * (90))
                    chair_sprite.image = pygame.transform.scale(chair_sprite.image,
                                                                (int(sol["C" + str(j) + "W"]),
                                                                 int(sol["C" + str(j) + "H"])))
                    chair_sprite.rect = pygame.Rect(sol["C" + str(j) + "X"], sol["C" + str(j) + "Y"],
                                                    sol["C" + str(j) + "W"], sol["C" + str(j) + "H"])
                    chair = Game_Object(sol["C" + str(j) + "X"], sol["C" + str(j) + "Y"], sol["C" + str(j) + "W"],
                                        sol["C" + str(j) + "H"], chair_sprite, 'chair')
                    if j == i * 4:
                        chair.orientation = "S"
                    elif j == i * 4 + 1:
                        chair.orientation = "E"
                    elif j == i * 4 + 2:
                        chair.orientation = "N"
                    else:
                        chair.orientation = "W"
                    table.children.append(chair)
                hall.children.append(table)
        self._prolog.retract(predicate_head + predicate_body)

    def project_segments(self, logger=None):
        is_agent_looking_at_objective = False
        angle_range = 120
        step = 3
        eye_point = self._agent.sprite.rect.center
        slope = (self._agent._target_rot + angle_range / 2) % 360
        points = []

        for i in range(0, angle_range, step):
            is_agent_looking_at_objective = False
            x = math.cos(math.radians(slope)) * 220
            y = math.sin(math.radians(slope)) * 220
            view_point = (eye_point[0] + x, eye_point[1] - y)
            slope = (slope - step) % 360
            intersection_points = []
            intersection_points_distances = []

            for room in self._rooms:
                intersection_point = self._checker.check_line_room_collision((eye_point[0], eye_point[1], view_point[0],
                                                                              view_point[1]), room)
                if intersection_point is not None:
                    intersection_points.append(intersection_point)
                for room_child in room.children:
                    intersection_point = self._checker.check_line_rect_collision((eye_point[0], eye_point[1],
                                                                                  view_point[0], view_point[1]),
                                                                                 room_child.sprite.rect)
                    if intersection_point is not None:
                        intersection_points.append(intersection_point)
                    for child in room_child.children:
                        intersection_point = self._checker.check_line_rect_collision((eye_point[0], eye_point[1],
                                                                                      view_point[0], view_point[1]),
                                                                                     child.sprite.rect)
                        if intersection_point is not None:
                            intersection_points.append(intersection_point)
            intersection_point_floor = self._checker.check_line_rect_collision((eye_point[0], eye_point[1],
                                                                                view_point[0], view_point[1]),
                                                                               self._floor.sprite.rect)
            if intersection_point_floor is not None:
                any_room_contains_point = False
                for room in self._rooms:
                    if self._checker.check_rect_contains_point(room.sprite.rect, intersection_point_floor):
                        any_room_contains_point = True
                        break
                if not any_room_contains_point:
                    intersection_points.append(intersection_point_floor)
            intersection_point_objective = self._checker.check_line_rect_collision((eye_point[0], eye_point[1],
                                                                                    view_point[0], view_point[1]),
                                                                                   self._objective.sprite.rect)
            if intersection_point_objective is not None:
                intersection_points.append(intersection_point_objective)
            for point in intersection_points:
                intersection_points_distances.append(self._checker.point_point_distance(eye_point, point))
            if len(intersection_points) > 0:
                chosen_index = np.argmin(intersection_points_distances)
                chosen_point = intersection_points[chosen_index]
                if chosen_point == intersection_point_objective:
                    is_agent_looking_at_objective = True

                points.append((slope / 359, intersection_points_distances[chosen_index] / 220,
                               is_agent_looking_at_objective))
            else:
                points.append((slope / 359, 1, False))

        return points, is_agent_looking_at_objective

    def save_generated_model(self):
        serialized_floor = dict(x=self._floor.x, y=self._floor.y, width=self._floor.width, height=self._floor.height)

        serialized_environment = dict(roomNumber=len(self._rooms), floor=serialized_floor)

        for room in self._rooms:
            serialized_room = dict(x=room.x, y=room.y, width=room.width, height=room.height, type=room.type,
                                   children=[], door=dict(x=room.door.x, y=room.door.y, width=room.door.width,
                                                          height=room.door.height))
            for child in room.children:
                serialized_child = dict(x=child.x, y=child.y, width=child.width, height=child.height, type=child.type,
                                        orientation=child.orientation, children=[])
                for ch in child.children:
                    serialized_child_child = dict(x=ch.x, y=ch.y, width=ch.width, height=ch.height, type=ch.type,
                                                  orientation=ch.orientation)
                    serialized_child["children"].append(serialized_child_child)
                serialized_room["children"].append(serialized_child)

            serialized_environment["R" + str(room.index)] = serialized_room

        with open('./environments/_environment ' + str(
                str(datetime.datetime.now().year) + '-' + str(datetime.datetime.now().month) + '-' + str(
                    datetime.datetime.now().day) + " " + str(datetime.datetime.now().hour) + "-" + str(
                    datetime.datetime.now().minute) + "-" + str(datetime.datetime.now().second)) + ".json",
                  'w') as outfile:
            json.dump(serialized_environment, outfile)
