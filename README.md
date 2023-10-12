# Neuro-Symbolic Reinforcement Learning

## Observation 🔍

The observation simulates a set of 40 laser proximity sensors (geometrically, they are treated as segments starting from the center of the robot which collide with the environment generating intersection points which are then given to the agent) and has the shape of an array of tuples each containing 3 informations:
- Angle: the angle of the direction the sensor was facing, relative to the environment ([0,359]);
- Distance: the distance between the agent and the eventual point of intersection found (a high number is set instead if nothing was hit);
- isObject: boolean flag telling the agent whether the eventual point hit an objective or not (assumes the agent can recognize objectives);

## Actions 🏃

There are 3 possible actions: rotate right by 45°, rotate left by 45° or move in the faced direction.

## Task 🎯

The task is to collect as many objectives as possible within 1500 time steps (approximately 15 seconds). The agent provided in the code succeedes in completing the task and definitely outperforms a human player. Reward is 1 for every objective collected.

## Reward 🎁

- reward = -1, small penalty after every 10 frames elapsed. This prevents dawdling.
- reward = 1, for changing rooms. Reinforces systematic area coverage.
- reward = 3, for looking towards target when in same room. Aligns with goal-finding.
- reward = 5, for moving towards target. Motivates motion planning.
- reward = 10, for reaching target; this strongly reinforces successful mission completion.
