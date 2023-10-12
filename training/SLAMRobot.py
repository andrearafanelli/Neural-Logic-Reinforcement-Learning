import tensorflow as tf
import numpy as np
from collections import deque
import random
import pygame
from utils.utils import ExitException

EPOCHS = 1


class SLAMAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=100000)
        self.temp_memory = deque(maxlen=200)
        self.gamma = 1
        self.epsilon = 1.0
        self.epsilon_min = 0.025
        self.epsilon_decay = 0.996
        self.learning_rate = 0.01
        self.learning_rate_decay = 0.01
        self.random_actions = [0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        self.model = self._build_model()
        np.set_printoptions(threshold=np.inf, linewidth=np.inf)

    def _build_model(self):

        model = tf.keras.Sequential([
            tf.keras.layers.Dense(units=25, activation='relu', input_shape=(self.state_size, 3)),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(units=50, activation='relu'),
            tf.keras.layers.Dense(units=100, activation='relu'),
            tf.keras.layers.Dense(units=50, activation='relu'),
            tf.keras.layers.Dense(units=25, activation='relu'),
            tf.keras.layers.Dense(units=self.action_size, activation='softmax')])

        optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(optimizer=optimizer, loss='mse')

        return model

    def remember(self, state, action, reward, next_state, terminal):
        if reward == 0:
            self.memory.append((state, action, reward, next_state, terminal))
        else:
            self.temp_memory.append((state, action, reward, next_state, terminal))

    def act(self, state):
        current_min_distance = 1
        for i in range(len(state[0])):
            if state[0][i][1] < current_min_distance and not state[0][i][2]:
                current_min_distance = state[0][i][1]
        if current_min_distance < 0.049:
            out = random.randrange(self.action_size - 1)
            return out, False
        if np.random.rand() <= self.epsilon:
            if state[0][18][2] or state[0][19][2] or state[0][20][2]:
                return 2, False
            return self.random_actions[random.randrange(len(self.random_actions) - 1)], True
        act_values = self.model.predict(state)
        return np.argmax(act_values[0]), False

    def act_move_2_door(self, me, door, logger=None):
        # guided to the middle of the door
        if logger: logger.debug(0, f"me & door: {(me.x, me.y)} {(door.x + door.width / 2, door.y + door.height / 2)}")
        # actions: 0 left, 1 right, 2 forward
        out = 2
        dx = me.x - door.x
        dy = me.y - door.y
        if door.width < 0.5:
            # vertical door
            if dx > 0:
                me.x, me.y = int(door.x - 2), int(door.y + door.height / 2)
                me._target_rot = 180
            elif dx < 0:
                me.x, me.y = int(door.x + 2), int(door.y + door.height / 2)
                me._target_rot = 0
            else:
                pass
        elif door.height < 0.5:
            # horizontal door
            if dy > 0:
                me.x, me.y = int(door.x + door.width / 2), int(door.y - 2)
                me._target_rot = 270
            elif dx < 0:
                me.x, me.y = int(door.x + door.width / 2), int(door.y + 2)
                me._target_rot = 90
            else:
                pass
        if logger: logger.debug(0, "moved to the door!")
        return out

    def replay(self, batch_size):
        minibatch = []

        if len(self.temp_memory) > 0:
            minibatch.extend(self.temp_memory)
            self.memory.extend(self.temp_memory)
            self.temp_memory = []

        if len(self.memory) > batch_size:
            try:
                minibatch.extend(random.sample(self.memory, batch_size - len(minibatch)))
            except:
                print('Error:', len(self.memory), batch_size, len(minibatch))
        else:
            minibatch.extend(random.sample(self.memory, len(self.memory) - len(minibatch)))

        entropy = 0.0

        for i, [state, action, reward, next_state, terminal] in enumerate(minibatch):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.display.quit()
                    pygame.quit()
                    raise ExitException("User quit while replaying/fitting", None)
            target = reward
            if not terminal:
                print("predict..")
                target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))
            out = self.model.predict(state)
            target_f = out.copy()
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=EPOCHS, verbose=0, use_multiprocessing=True)
            policy_probs = np.squeeze(tf.nn.softmax(out, axis=1))
            entropy -= np.sum(policy_probs * np.log2(policy_probs + 1e-10))

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        if len(minibatch) > 0:
            entropy_out = entropy / len(minibatch)
        else:
            entropy_out = entropy

        return entropy_out, self.epsilon

    def save(self, fn):
        self.model.save(fn)
        print(f"actual epsilon: {str(self.epsilon)}")

    def load(self, name, last_random_value):
        self.model.load_weights(name)
        self.epsilon = last_random_value
