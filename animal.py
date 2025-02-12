#animal.py
from common import MEMORY_LENGTH, AGING
import random
from collections import deque
from vegetob import Vegetob

class Animal:
    def __init__(self, pos, memory_length):
        # Initialize an Animal with position, memory length, and other attributes
        self.id = id(self)  # Unique identifier for the animal
        self.pos = pos  # Current position of the animal
        self.new_pos = pos  # Intended new position after movement
        self.energy = 10  # Initial energy level
        self.age = 0  # Initial age
        self.lifetime = random.randint(40, 60)  # Random lifespan between 40 and 60 days
        self.memory = deque([], maxlen=memory_length)  # Memory of visited positions
        self.max_energy = 20  # Maximum energy level
        self.social_attitude = random.uniform(0, 1)  # Social behavior trait
        self.count = 1  # Count of this animal
        print(f"{self.__class__.__name__} created at {self.pos} with lifetime {self.lifetime} and initial energy {self.energy}.")

    def decide(self, grid, species, neighborhood):
        # Decide whether to stay or move based on the evaluation of surrounding positions
        scores = {}
        self.memory.appendleft(self.pos)  # Add current position to memory

        # Evaluate all neighboring positions within the specified neighborhood range
        for dx in range(-neighborhood, neighborhood + 1):
            for dy in range(-neighborhood, neighborhood + 1):
                new_pos = (self.pos[0] + dx, self.pos[1] + dy)
                if 0 <= new_pos[0] < grid.shape[0] and 0 <= new_pos[1] < grid.shape[1] and grid[new_pos] == 0:
                    scores[new_pos] = self.evaluate_position(new_pos, species)

        # Determine the best position to move to, if any
        self.new_pos = max(scores, key=scores.get) if scores else self.pos
        decision = "stay" if self.new_pos == self.pos else "move"
        print(f"{self.__class__.__name__} at {self.pos} decides to {decision} at/to {self.new_pos}.")
        return decision == "move"

    def evaluate_position(self, new_pos, species):
        # Evaluate the desirability of a new position based on various factors
        visited_score = -10 if new_pos in self.memory else 5  # Penalize if position is in memory
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
        # Move the animal to the new position if possible and update energy
        if grid[self.new_pos] == 0:  # Ensure the new position is not water
            move_cost = 1
            if self.energy >= move_cost:
                self.energy -= move_cost  # Deduct energy for moving
                print(f"{self.__class__.__name__} moving from {self.pos} to {self.new_pos} with remaining energy {self.energy}.")
                if self in species[self.pos]:
                    species[self.pos].remove(self)  # Remove from current position in species dictionary
                self.pos = self.new_pos  # Update to new position
                species.setdefault(self.new_pos, []).append(self)  # Add to new position in species dictionary
            else:
                print(f"Not enough energy for {self.__class__.__name__} to move.")
        else:
            print(f"Cannot move {self.__class__.__name__} to water.")

    def age_up(self, species, aging):
        # Increase the age of the animal and reduce energy periodically
        self.age += 1
        if self.age % 10 == 0:
            self.energy -= aging  # Deduct energy every 10 days
            print(f"{self.__class__.__name__} at {self.pos} aged up to {self.age} and now has {self.energy} energy.")
        if self.age >= self.lifetime:
            self.spawn_offspring(species)
            self.die()

    def should_remove(self):
        # Check if the animal should be removed (energy is 0 or lifetime exceeded)
        return self.energy <= 0 or self.age >= self.lifetime

    def die(self):
        # Handle the death of the animal
        print(f"{self.__class__.__name__} {self.id} died at age {self.age}.")

    def spawn_offspring(self, species):
        # Spawn offspring with shared energy and attributes
        offspring_energy = self.energy // 2  # Split energy between offspring
        offspring1 = self.__class__(self.pos, self.memory.maxlen)
        offspring2 = self.__class__(self.pos, self.memory.maxlen)
        offspring1.energy = offspring_energy
        offspring2.energy = offspring_energy
        offspring1.lifetime = offspring2.lifetime = self.lifetime
        offspring1.social_attitude = offspring2.social_attitude = self.social_attitude
        species.setdefault(self.pos, []).append(offspring1)
        species.setdefault(self.pos, []).append(offspring2)
        print(f"{self.__class__.__name__} {self.id} spawned two offspring at {self.pos}.")

class Erbast(Animal):
    def graze(self, species):
        # Allow Erbast to graze on Vegetob and increase energy
        vegetob = next((e for e in species.get(self.pos, []) if isinstance(e, Vegetob)), None)
        if vegetob:
            print(f"Erbast at {self.pos} is grazing.")
            while self.energy < self.max_energy and vegetob.density > 0:
                self.energy += 1  # Increase energy while grazing
                vegetob.density -= 1  # Decrease Vegetob density
                print(f"Erbast at {self.pos} increased energy to {self.energy}, Vegetob density reduced to {vegetob.density}.")
            if vegetob.density == 0:
                print(f"Vegetob at {self.pos} completely grazed by Erbast.")
                species[self.pos].remove(vegetob)  # Remove Vegetob if fully grazed

class Carviz(Animal):
    def predate(self, species):
        # Allow Carviz to hunt and predate on prey
        from group import Pride
        if not any(isinstance(animal, Pride) and self in animal.group_list for animal in species.get(self.pos, [])):
            target = self.identify_target(species.get(self.pos, []))
            if target and self.hunt(target):
                self.energy += target.energy  # Increase energy after successful hunt
                species[self.pos].remove(target)  # Remove prey after hunt
                print(f"Carviz {self.id} successfully hunted Erbast at {self.pos}.")
            else:
                print(f"No suitable target or failed hunt for Carviz {self.id} at {self.pos}.")

    def identify_target(self, entities):
        # Identify the most energy-rich prey to hunt
        prey_classes = ['Erbast', 'Herd']
        target = max((e for e in entities if any(isinstance(e, globals()[cls]) for cls in prey_classes if cls in globals())), key=lambda e: e.energy, default=None)
        print(f"Carviz {self.id} identified target {target.__class__.__name__ if target else 'None'} at {self.pos}.")
        return target

    def hunt(self, target):
        # Attempt to hunt the target based on success probability
        individual_success_probability = self.calculate_individual_success(target)
        success = random.random() < individual_success_probability
        print(f"Carviz {self.id} hunting target at {self.pos} with success probability {individual_success_probability}: {'success' if success else 'failure'}.")
        return success

    def calculate_individual_success(self, target):
        # Calculate the probability of a successful hunt
        hunting_ability = self.energy * 1.2  # Increase hunting ability
        target_difficulty = max(1, target.energy)  # Ensure non-zero target difficulty
        return hunting_ability / target_difficulty