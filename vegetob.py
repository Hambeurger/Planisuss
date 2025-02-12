#vegetob.py
import numpy as np

class Vegetob:
    def __init__(self, pos, max_density, growth):
        # Initialize Vegetob with position, max density, and growth rate
        self.density = np.random.randint(5, max_density + 1)  # Random initial density between 5 and max_density
        self.pos = pos  # Position of Vegetob in the grid
        self.growth = growth  # Growth rate per day
        print(f"Vegetob created at {self.pos} with initial density {self.density}.")

    def grow(self):
        # Grow Vegetob, increasing its density up to a maximum of 100
        self.density = min(self.density + self.growth, 100)  # Ensure density does not exceed 100
        print(f"Vegetob at {self.pos} grew to {self.density} density.")

    def should_remove(self):
        # Check if Vegetob should be removed (density is 0 or less)
        return self.density <= 0  # Return True if density is 0 or less, indicating removal
