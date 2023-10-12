import json
import random

import numpy as np
import pygame
import cv2

from SLAMRobot import SLAMAgent
from metrics import MetricsLogger
from utils.utils import Check_Collisions, Game_Object, Room, Agent, ExitException
from datetime import datetime
from pygame import Rect

EPISODES = 5000
REPLIES = 100


class Training:
    def __init__(self, env_width, env_heigth, multiplier, environment, path='./metrics/'):
        self._changed = None
        self._type_to_sprite = None
        self._screen = None
        self._agent = Agent(9999, 9999, 8, 8, 0, 'agent', 90)
        self._objective = Game_Object(9800, 9800, 15, 15, 0, 'objective')
        self._rooms = []
        self._env_width = env_width
        self._env_height = env_heigth
        self._frame_size = (int(self._env_width), int(self._env_height))
        self._multiplier = multiplier
        self._environment = environment
        self._agent_start_x = 198
        self._agent_start_y = 268
        self._checker = Check_Collisions()
        self._is_agent_looking = False
        self._floor = None
        self._logger = MetricsLogger(path, 'metric_name', ['id', 'entropy', 'epsilon', 'terminal', 'number-rooms',
                                                           'env-width', 'env-height', 'frame-count', 'frames-tot',
                                                           'score', 'room-changes', 'random-actions', 'reward'])
        self._dist_to_objective = 0
        self._frame_count = 0
        self._tot_frames = 100
        self._score = 0
        self._doors = []
        self._video_writer = None
        self._font = None
        self._door_step = 0
        self._action = 2
        self._frame_since_cross = 0

    def run_training(self, render_on=False, video_rec_on=False, logic_drive_on=False):
        slam_agent, speed, state_size = self.training_setup()
        if video_rec_on: self.video_recorder_setup()
        if logic_drive_on:
            self._logger.debug(0, "With LOGIC_DRIVER")
        else:
            self._logger.debug(0, "WITHOUT any driver")
        for i in range(1, EPISODES):
            reward_accumulator = 0
            terminal = False
            self._frame_count, self._score = 0, 0
            self._dist_to_objective = 1000
            random_actions = 0
            room_changes = 0
            state = np.reshape(self._environment.project_segments()[0], [1, state_size, 3])
            self.reset_objective()
            self.reset_agent()
            while not self.on_freespace(self._agent):
                self.reset_agent()
            while not self.on_freespace_objective(self._objective):
                self.reset_objective()

            while not terminal:
                self._frame_count += 1
                self._frame_since_cross += 1
                if self.user_quit(slam_agent):
                    return
                if render_on:
                    random_actions, reward, state, terminal = self.reward_in_rendering_final(random_actions, slam_agent,
                                                                                             speed, state, state_size,
                                                                                             terminal, logic_drive_on)
                    if self._changed and self._frame_count > 10:
                        room_changes += 1
                        self._logger.debug(self._frame_count, "room change!")
                else:
                    random_actions, reward, state, terminal = self.reward_no_render(random_actions, slam_agent, speed,
                                                                                    state, state_size, terminal)
                reward_accumulator += reward
                if video_rec_on: self.video_record_frame()

            self._logger.debug(self._frame_count, "Start agent replay.")
            try:
                entropy, exploration = slam_agent.replay(REPLIES)
                self._logger.log(self._frame_count, [i, entropy, exploration, terminal,
                                                     len(self._rooms), self._env_width, self._env_height,
                                                     self._frame_count, self._tot_frames,
                                                     self._score, room_changes, random_actions,
                                                     reward_accumulator])
                self._logger.debug(self._frame_count, "Agent replay completed.")
            except ExitException as e:
                self._logger.debug(self._frame_count, e)
                return

        self._logger.close()
        self._logger.debug(self._frame_count, "Weights saving...")
        slam_agent.save("test")
        self._logger.debug(self._frame_count, "Weights saving completed.")
        pygame.quit()

    def training_setup(self):
        state_size = 40
        slam_agent = SLAMAgent(state_size, 3)
        speed = 2
        pygame.init()
        pygame.font.init()
        fontpath = pygame.font.get_default_font()
        size = 24
        self._font = pygame.font.Font(fontpath, size)
        self.generate_target_pos()
        self._screen = pygame.display.set_mode(self._frame_size)
        self._environment._agent = self._agent
        self._environment._objective = self._objective
        self._environment._floor = self._floor
        self._environment._screen = self._screen
        self._tot_frames = int((100 * len(self._rooms)) + 0.005 * (self._env_width * self._env_height))
        self._logger.debug(self._frame_count,
                           f"training with: {self._tot_frames} frames {EPISODES} episodes {REPLIES} replies")
        return slam_agent, speed, state_size

    def reward_no_render(self, random_actions, slam_agent, speed, state, state_size, terminal):
        reward = 0
        action, was_it_random = slam_agent.act(state)
        if was_it_random:
            random_actions += 1
        self.update_agent_pos_by_action(action, speed)
        if self.is_agent_colliding_world():
            terminal = True
        elif self._frame_count > self._tot_frames:
            terminal = True
        reward += 1
        next_state = np.reshape(self._environment.project_segments()[0], [1, state_size, 3])
        if self._environment.project_segments()[1]:
            reward += 3
            new_dist_to_objective = self._checker.point_point_distance((self._agent.x, self._agent.y),
                                                                       (self._objective.x,
                                                                        self._objective.y))
            if new_dist_to_objective < self._dist_to_objective:
                self._dist_to_objective = new_dist_to_objective
                reward += 5
        slam_agent.remember(state, action, reward, next_state, terminal)
        state = next_state
        return random_actions, reward, state, terminal

    def reward_in_rendering_final(self, random_actions, slam_agent, speed, state, state_size,
                                  terminal, logic_drive_on):
        reward = 0
        if logic_drive_on and self._door_step == 0 and self._frame_since_cross > 20 and self.is_front_to_door(
                self._agent):
            self._door_step = 1  # door seen
        if self._door_step > 0:
            self._door_step += 1
            self._logger.debug(self._frame_count, f"door crossing step: {self._door_step}")
            # rule based navigation
            door = self.get_closest_door(self._agent)
            if door:
                if self._action != 2:
                    self._action = 2
                    self._logger.debug(self._frame_count, "1 step forward")
                else:
                    self._action = slam_agent.act_move_2_door(self._agent, door, self._logger)
                    self._door_step = 0
            else:
                self._logger.debug(self._frame_count, "lost door!")
                self._door_step = 0
            was_it_random = False
        else:
            # neural based navigation
            self._action, was_it_random = slam_agent.act(state)

        if was_it_random:
            random_actions += 1
        room_changed = self.visual_scene_update(self._action, speed)
        reward = self.make_reward(reward, room_changed)

        if self.is_agent_colliding_world():
            terminal = True
            next_state = state
        elif self._frame_count > self._tot_frames:
            terminal = True
            next_state = state
        else:
            next_state = np.reshape(self._environment.project_segments()[0], [1, state_size, 3])

        if self._frame_count > 5:
            slam_agent.remember(state, self._action, reward, next_state, terminal)

        state = next_state
        return random_actions, reward, state, terminal

    def make_reward(self, reward, room_changed):
        if self._frame_count % 10 == 0 and reward > 0:
            reward -= 1
            self._logger.debug(self._frame_count, 'rew -1')
        if self._environment.project_segments()[1]:
            reward += 3
            new_dist_to_objective = self._checker.point_point_distance((self._agent.x, self._agent.y),
                                                                       (self._objective.x,
                                                                        self._objective.y))
            self._logger.debug(self._frame_count, 'rew 3')
            if new_dist_to_objective < self._dist_to_objective:
                self._dist_to_objective = new_dist_to_objective
                reward += 5
                self._logger.debug(self._frame_count, 'rew 5')
        if self._agent.sprite.rect.colliderect(self._objective.sprite.rect):
            self.reset_objective()
            reward += 10
            self._logger.debug(self._frame_count, 'rew 10')
            self._score += 1
        self._changed = room_changed
        if self._changed:
            reward += 1
            self._logger.debug(self._frame_count, 'rew 1')
            self._frame_since_cross = 0
        return reward

    def visual_scene_update(self, action, speed):
        self._screen.fill((30, 30, 30))
        room_changed = self.update_agent_pos_by_action(action, speed)
        self._environment._rooms = self._rooms
        self._environment._screen = self._screen
        self._environment.draw_model()
        pygame.display.update()

        return room_changed

    def on_freespace(self, target):
        res = True
        for r in self._rooms:
            for c in r.children:
                if c.x < target.x < target.x + target.width < c.x + c.width and \
                        c.y < target.y < target.y + target.height < c.y + c.height:
                    return False
        return res

    def on_freespace_objective(self, target):
        res = True
        rt = target.sprite.rect
        for r in self._rooms:
            for c in r.children:
                rc = Rect(c.x, c.y, c.width, c.height)
                if rt.colliderect(rc):
                    return False
        return res

    def room_sensor(self):
        for i, room in enumerate(self._rooms):
            if room.x < self._agent.x < room.x + room.width and \
                    room.y < self._agent.y < room.y + room.height:
                return i
        return -1

    def update_agent_pos_by_action(self, action, speed):
        if action == 0:
            self._agent._target_rot = (self._agent._target_rot + 45) % 360
        elif action == 1:
            self._agent._target_rot = (self._agent._target_rot - 45) % 360
        elif action == 2:
            if self._agent._target_rot == 90:
                self._agent.y -= speed
            elif self._agent._target_rot == 270:
                self._agent.y += speed
            elif self._agent._target_rot == 180:
                self._agent.x -= speed
            elif self._agent._target_rot == 0:
                self._agent.x += speed
            elif self._agent._target_rot == 45:
                self._agent.y -= speed
                self._agent.x += speed
            elif self._agent._target_rot == 135:
                self._agent.x -= speed
                self._agent.y -= speed
            elif self._agent._target_rot == 225:
                self._agent.x -= speed
                self._agent.y += speed
            elif self._agent._target_rot == 315:
                self._agent.x += speed
                self._agent.y += speed
        if self.room_sensor() != self._agent._last_room:
            self._agent._last_room = self.room_sensor()
            return True
        return False

    @staticmethod
    def user_quit(slam_agent):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    slam_agent.save("test")
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()
                return True
        return False

    def reset_agent(self):
        self._agent._target_rot = 90
        ridx = random.randint(0, len(self._rooms) - 1)
        self._agent.x = int(random.uniform(self._rooms[ridx].x * 1.15,
                                           (self._rooms[ridx].x + self._rooms[ridx].width * 0.85)))
        self._agent.y = int(random.uniform(self._rooms[ridx].y * 1.15,
                                           (self._rooms[ridx].y + self._rooms[ridx].height * 0.85)))
        self._agent.sprite.rect.x = self._agent_start_x
        self._agent.sprite.rect.y = self._agent_start_y
        self._agent.last_room = self.room_sensor()

    def reset_objective(self):
        ridx = random.randint(0, len(self._rooms) - 1)
        self._objective.x = int(random.uniform(self._rooms[ridx].x * 1.15,
                                               (self._rooms[ridx].x + self._rooms[ridx].width * 0.85)))
        self._objective.y = int(random.uniform(self._rooms[ridx].y * 1.15,
                                               (self._rooms[ridx].y + self._rooms[ridx].height * 0.85)))
        self._objective.sprite.rect.x = self._objective.x
        self._objective.sprite.rect.y = self._objective.y

    def is_agent_colliding_world(self):
        is_agent_in_room = False
        for room in self._rooms:
            if not room.sprite.rect.contains(self._agent.sprite.rect):
                pass

            else:
                is_agent_in_room = True
                for room_child in room.children:
                    if self._agent.sprite.rect.colliderect(room_child.sprite.rect):
                        self._logger.debug(self._frame_count, "Collision due to a room's object")
                        return True
                    for child in room_child.children:
                        if self._agent.sprite.rect.colliderect(child.sprite.rect):
                            self._logger.debug(self._frame_count, "Collision due to an object's object")
                            return True
        if not is_agent_in_room:
            if not self._floor.sprite.rect.contains(self._agent.sprite.rect):
                self._logger.debug(self._frame_count, "Collision with floor")
                return True
        return False

    def load_model(self, file_path, render_on):
        self._logger.debug(self._frame_count, f"Training on map: {file_path}")
        with open("./environments/" + file_path, 'r') as infile:
            json_string = infile.read()

        deserialized_environment_dict = json.loads(json_string)
        room_number = deserialized_environment_dict["roomNumber"]
        floor_dict = deserialized_environment_dict["floor"]

        self._env_width = floor_dict["width"] + (8 * room_number * self._multiplier)
        self._env_height = floor_dict["height"] + (8 * room_number * self._multiplier)
        self._frame_size = (int(self._env_width), int(self._env_height))
        self._screen = pygame.display.set_mode(self._frame_size)
        self._rooms = []
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

        floor_sprite = pygame.sprite.Sprite()
        floor_sprite.image = pygame.transform.scale(self._type_to_sprite['floor'],
                                                    (int(floor_dict["width"]), int(floor_dict["height"])))
        floor_sprite.rect = pygame.Rect(floor_dict["x"], floor_dict["y"], floor_dict["width"], floor_dict["height"])
        self._floor = Game_Object(floor_dict["x"], floor_dict["y"], floor_dict["width"], floor_dict["height"],
                                  floor_sprite, 'floor')
        for i in range(0, room_number):
            room_dict = deserialized_environment_dict["R" + str(i)]
            room_sprite = pygame.sprite.Sprite()
            room_sprite.image = pygame.transform.scale(self._type_to_sprite[room_dict["type"]],
                                                       (int(room_dict["width"]), int(room_dict["height"])))
            room_sprite.rect = pygame.Rect(room_dict["x"], room_dict["y"], room_dict["width"], room_dict["height"])
            deserialized_room = Room(room_dict["x"], room_dict["y"], room_dict["width"], room_dict["height"], i,
                                     room_sprite, room_dict["type"])
            door_dict = room_dict["door"]
            door_sprite = pygame.sprite.Sprite()
            if door_dict["width"] != 0:
                door_sprite.image = pygame.transform.scale(pygame.transform.rotate(self._type_to_sprite['door'], 90),
                                                           (int(2.5 * self._multiplier), int(1.0 * self._multiplier)))
            else:
                door_sprite.image = pygame.transform.scale(self._type_to_sprite['door'],
                                                           (int(1.0 * self._multiplier), int(2.5 * self._multiplier)))
            door_sprite.rect = pygame.Rect(door_dict["x"], door_dict["y"], door_dict["width"], door_dict["height"])
            deserialized_room.door = Game_Object(door_dict["x"], door_dict["y"], door_dict["width"],
                                                 door_dict["height"], door_sprite, 'door')
            self._doors.append(deserialized_room.door)
            for child_dict in room_dict["children"]:
                child_rotation = 0
                if child_dict["orientation"] == "W":
                    child_rotation = -90
                elif child_dict["orientation"] == "N":
                    child_rotation = 180
                elif child_dict["orientation"] == "E":
                    child_rotation = 90
                child_sprite = pygame.sprite.Sprite()
                child_sprite.image = pygame.transform.scale(
                    pygame.transform.rotate(self._type_to_sprite[child_dict["type"]], child_rotation),
                    (int(child_dict["width"]), int(child_dict["height"])))
                child_sprite.rect = pygame.Rect(child_dict["x"], child_dict["y"], child_dict["width"],
                                                child_dict["height"])
                deserialized_child = Game_Object(child_dict["x"], child_dict["y"], child_dict["width"],
                                                 child_dict["height"], child_sprite, child_dict["type"])
                deserialized_room.children.append(deserialized_child)

                for childchild_dict in child_dict["children"]:
                    childchild_rotation = 0
                    if childchild_dict["orientation"] == "W":
                        childchild_rotation = -90
                    elif childchild_dict["orientation"] == "N":
                        childchild_rotation = 180
                    elif childchild_dict["orientation"] == "E":
                        childchild_rotation = 90
                    childchild_sprite = pygame.sprite.Sprite()

                    childchild_sprite.image = pygame.transform.scale(
                        pygame.transform.rotate(self._type_to_sprite[childchild_dict["type"]], childchild_rotation),
                        (int(childchild_dict["width"]), int(childchild_dict["height"])))
                    childchild_sprite.rect = pygame.Rect(childchild_dict["x"], childchild_dict["y"],
                                                         childchild_dict["width"], childchild_dict["height"])
                    deserialized_child_child = Game_Object(childchild_dict["x"], childchild_dict["y"],
                                                           childchild_dict["width"], childchild_dict["height"],
                                                           childchild_sprite, childchild_dict["type"])
                    deserialized_child.children.append(deserialized_child_child)
            self._rooms.append(deserialized_room)

        agent_sprite = pygame.sprite.Sprite()
        agent_sprite.image = pygame.transform.scale(self._type_to_sprite['agent'], (int(self._agent.width),
                                                                                    int(self._agent.height)))
        agent_sprite.rect = pygame.Rect(self._agent.x, self._agent.y, self._agent.width, self._agent.height)
        self._agent.sprite = agent_sprite
        self._agent.image = self._agent.sprite.image

        objective_sprite = pygame.sprite.Sprite()
        objective_sprite.image = pygame.transform.scale(self._type_to_sprite['objective'], (int(self._objective.width),
                                                                                            int(self._objective.height)))
        objective_sprite.rect = pygame.Rect(self._objective.x, self._objective.y, self._objective.width,
                                            self._objective.height)
        self._objective.sprite = objective_sprite
        self.multiplier = 1.0

    def generate_target_pos(self):
        self._environment._objective_position = []
        for room in self._rooms:
            pos = (int(random.uniform(room.x * 1.15, room.x + room.width * 0.85)),
                   int(random.uniform(room.y * 1.15, room.y + room.height * 0.85)))
            self._environment._objective_position.append(pos)

    def is_front_to_door(self, thing: Game_Object):
        ths_w, ths_d = 4, 12
        p1 = np.array((thing.x + thing.width / 2, thing.y + thing.height / 2))
        for i, door in enumerate(self._doors):
            p2 = np.array((door.x + door.width / 2, door.y + door.height / 2))
            in_front = abs(p1[0] - p2[0]) < ths_d and abs(p1[1] - p2[1]) < ths_w
            in_front |= abs(p1[1] - p2[1]) < ths_d and abs(p1[0] - p2[0]) < ths_w
            if in_front:
                self._logger.debug(self._frame_count, "door in front")
                return True
        return False

    def get_closest_door(self, thing: Game_Object):
        ths_w, ths_d = 10, 40
        p1 = np.array((thing.x + thing.width / 2, thing.y + thing.height / 2))
        for i, door in enumerate(self._doors):
            p2 = np.array((door.x + door.width / 2, door.y + door.height / 2))
            in_front = abs(p1[0] - p2[0]) < ths_d and abs(p1[1] - p2[1]) < ths_w
            in_front |= abs(p1[1] - p2[1]) < ths_d and abs(p1[0] - p2[0]) < ths_w
            if in_front:
                self._logger.debug(self._frame_count, "this door in front")
                return door
        return None

    def video_recorder_setup(self):
        video_filename = f'video/simulation_{datetime.now().strftime("%Y%m%d-%H%M")}.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        self._video_writer = cv2.VideoWriter(video_filename, fourcc, 30.0, self._frame_size, isColor=True)

    def video_record_frame(self):
        text_surface = self._font.render(f'{self._frame_count}', True, (255, 255, 255))
        self._screen.blit(text_surface, (10, 10))
        pygame_surface = pygame.surfarray.array3d(self._screen)
        numpy_surface = np.transpose(pygame_surface, (1, 0, 2))
        bgr_frame = cv2.cvtColor(numpy_surface, cv2.COLOR_RGB2BGR)
        self._video_writer.write(bgr_frame)
