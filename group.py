#group.py
from collections import deque
import random
from common import MEMORY_LENGTH
from animal import Erbast, Carviz
from vegetob import Vegetob

class Group:
    def __init__(self, group_list, memory_length):
        # Initialize a Group with a list of animals and memory length.
        self.id = id(self)  # Unique identifier for the group
        self.pos = group_list[0].pos if group_list else None  # Group position based on first animal
        self.group_list = group_list  # List of animals in the group
        self.memory = deque([animal.pos for animal in group_list], maxlen=memory_length)  # Memory of visited positions
        self.energy = sum(animal.energy for animal in group_list)  # Total energy of the group
        self.count = len(group_list)  # Number of animals in the group
        self.new_pos = None  # Intended new position after movement
        print(f"{self.__class__.__name__} created at {self.pos} with {self.count} members and total energy {self.energy}.")

    def decide(self, grid, species, neighborhood):
        # Decide whether to stay or move based on the evaluation of surrounding positions.
        scores = {}
        for animal in self.group_list:
            animal.memory.appendleft(self.pos)  # Add current position to memory of each group member

        # Evaluate all neighboring positions within the specified neighborhood range
        for dx in range(-neighborhood, neighborhood + 1):
            for dy in range(-neighborhood, neighborhood + 1):
                new_pos = (self.pos[0] + dx, self.pos[1] + dy)
                if self.is_valid_move(new_pos, grid):
                    scores[new_pos] = self.evaluate_position(new_pos, species)

        # Determine the best position to move to, if any
        self.new_pos = max(scores, key=scores.get) if scores else self.pos
        decision = "stay" if self.new_pos == self.pos else "move"
        print(f"{self.__class__.__name__} at {self.pos} decides to {decision} at/to {self.new_pos}.")
        return decision == "move"

    def is_valid_move(self, new_pos, grid):
        # Check if the new position is valid (within grid and not water).
        return 0 <= new_pos[0] < grid.shape[0] and 0 <= new_pos[1] < grid.shape[1] and grid[new_pos] == 0

    def evaluate_position(self, new_pos, species):
        # Evaluate the desirability of a new position based on various factors.
        visited_score = -10 if any(new_pos == mem for mem in self.memory) else 5  # Penalize if position is in memory
        predator_classes = ['Carviz', 'Pride']
        prey_classes = ['Erbast', 'Herd']
        vegetob_classes = ['Vegetob']

        # Check for presence of predators, prey, or vegetation in the new position
        predator_score = -50 if any(isinstance(e, globals()[cls]) for cls in predator_classes if cls in globals() for e in species.get(new_pos, [])) else 0
        prey_score = 20 if any(isinstance(e, globals()[cls]) for cls in prey_classes if cls in globals() for e in species.get(new_pos, [])) else 0
        vegetob_score = 30 if any(isinstance(e, globals()[cls]) for cls in vegetob_classes if cls in globals() for e in species.get(new_pos, [])) else 0

        score = visited_score + predator_score + prey_score + vegetob_score
        print(f"Evaluating position {new_pos} for {self.__class__.__name__} at {self.pos}: score {score}.")
        return score

    def move(self, grid, species):
        # Move the group to the new position if possible and update energy.
        if self.is_valid_move(self.new_pos, grid):
            move_cost = 1
            if self.energy >= move_cost * len(self.group_list):  # Ensure enough energy for all group members to move
                self.energy -= move_cost * len(self.group_list)
                for animal in self.group_list:
                    animal.energy -= move_cost  # Deduct energy from each group member
                    animal.pos = self.new_pos  # Update position of each group member
                print(f"{self.__class__.__name__} moving from {self.pos} to {self.new_pos} with remaining energy {self.energy}.")
                self.update_position(species)
            else:
                print(f"Not enough energy for {self.__class__.__name__} to move.")

    def update_position(self, species):
        # Update the group's position in the species dictionary.
        if self.pos in species:
            species[self.pos].remove(self)  # Remove group from current position in species dictionary
            if not species[self.pos]:
                del species[self.pos]  # Delete position if no entities left

        if self.new_pos in species:
            species[self.new_pos].append(self)  # Add group to new position
        else:
            species[self.new_pos] = [self]  # Create new entry if position is empty

        self.pos = self.new_pos  # Update group's position
        print(f"{self.__class__.__name__} has moved to {self.new_pos}.")

    def should_remove(self):
        # Check if the group should be removed (all members should be removed).
        return not self.group_list or all(animal.should_remove() for animal in self.group_list)

class Herd(Group):
    def graze(self, species):
        # Allow the Herd to graze on Vegetob and increase energy.
        vegetob = next((e for e in species.get(self.pos, []) if isinstance(e, Vegetob)), None)
        if vegetob:
            print(f"Herd at {self.pos} is grazing.")
            for animal in sorted(self.group_list, key=lambda e: e.energy):
                if vegetob.density > 0 and animal.energy < animal.max_energy:
                    animal.energy += 1  # Increase energy while grazing
                    vegetob.density -= 1  # Decrease Vegetob density
                    print(f"Herd member increased energy to {animal.energy}, Vegetob density reduced to {vegetob.density}.")
                if vegetob.density == 0:
                    print(f"Vegetob at {self.pos} completely grazed by Herd.")
                    species[self.pos].remove(vegetob)  # Remove Vegetob if fully grazed
                    break

class Pride(Group):
    def average_social_attitude(self):
        # Calculate the average social attitude of the Pride members.
        if len(self.group_list) == 0:
            return 0
        avg_attitude = sum(animal.social_attitude for animal in self.group_list) / len(self.group_list)
        print(f"Pride {self.id} average social attitude: {avg_attitude}.")
        return avg_attitude

    def predate(self, species):
        # Allow the Pride to predate on prey.
        other_prides = [e for e in species.get(self.pos, []) if isinstance(e, Pride) and e is not self]
        if other_prides:
            self.resolve_conflicts(other_prides, species)
        else:
            self.hunt_group(species)

    def resolve_conflicts(self, other_prides, species):
        # Resolve conflicts with other Prides, either by joining or fighting.
        for other in sorted(other_prides, key=lambda x: len(x.group_list)):
            if self.evaluate_joining(other):
                self.join_pride(other)
                species[self.pos].remove(other)
                print(f"Pride {self.id} joined with another Pride at {self.pos}.")
            else:
                self.fight(other)
                if not self.group_list:
                    print(f"Pride {self.id} lost all members in the fight at {self.pos}.")
                    break
                if not other.group_list:
                    print(f"Other Pride lost all members in the fight at {self.pos}.")
                    species[self.pos].remove(other)

    def evaluate_joining(self, other):
        # Evaluate whether to join with another Pride based on social attitude.
        join = (self.average_social_attitude() + other.average_social_attitude()) / 2 > 0.5
        print(f"Evaluating joining of Pride {self.id} with another Pride at {self.pos}: {'join' if join else 'fight'}.")
        return join

    def join_pride(self, other):
        # Join with another Pride.
        self.group_list.extend(other.group_list)
        other.group_list.clear()
        print(f"Pride {self.id} joined with another Pride, new member count: {len(self.group_list)}.")

    def fight(self, other):
        # Fight with another Pride.
        while self.group_list and other.group_list:
            self_member = max(self.group_list, key=lambda x: x.energy)
            other_member = max(other.group_list, key=lambda x: x.energy)
            fight_cost = min(self_member.energy, other_member.energy * 0.5)
            self_member.energy -= fight_cost
            other_member.energy -= fight_cost
            if self_member.energy <= other_member.energy:
                self.group_list.remove(self_member)
                print(f"Pride member {self_member.id} removed after fight.")
            else:
                other.group_list.remove(other_member)
                print(f"Other Pride member {other_member.id} removed after fight.")

    def hunt_group(self, species):
        # Hunt as a Pride for prey.
        target = self.identify_target(species.get(self.pos, []))
        if target and self.group_hunt(target):
            energy_share = target.energy // len(self.group_list)
            for animal in self.group_list:
                animal.energy += energy_share
            species[self.pos].remove(target)
            print(f"Pride {self.id} successfully hunted {target.__class__.__name__} at {self.pos}.")
        else:
            print(f"Pride {self.id} failed to hunt at {self.pos}.")

    def identify_target(self, entities):
        # Identify the most energy-rich prey to hunt.
        target = max((e for e in entities if isinstance(e, Erbast) or isinstance(e, Herd)), key=lambda e: e.energy, default=None)
        print(f"Pride {self.id} identified target {target.__class__.__name__ if target else 'None'} at {self.pos}.")
        return target

    def group_hunt(self, target):
        # Attempt to hunt the target based on Pride success probability.
        collective_success_probability = sum(animal.energy for animal in self.group_list) / (target.energy * 1.5)
        success = random.random() < collective_success_probability
        print(f"Pride {self.id} hunting target at {self.pos} with success probability {collective_success_probability}: {'success' if success else 'failure'}.")
        return success