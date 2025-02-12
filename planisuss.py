#planisuss.py
import numpy as np
import matplotlib.pyplot as plt
import random
import matplotlib.patches as patches
import pickle
from vegetob import Vegetob
from animal import Erbast, Carviz
from group import Herd, Pride
from common import NEIGHBORHOOD, MEMORY_LENGTH, AGING

class Planisuss:
    def __init__(self, size, water_prob, vegetob_prob, erbast_prob, carviz_prob, max_day, max_density, growth):
        # Initialize the Planisuss world with given parameters.
        self.size = size
        self.water_prob = water_prob
        self.vegetob_prob = vegetob_prob
        self.erbast_prob = erbast_prob
        self.carviz_prob = carviz_prob
        self.max_day = max_day
        self.max_density = max_density
        self.growth = growth
        self.neighborhood = NEIGHBORHOOD
        self.memory_length = MEMORY_LENGTH
        self.aging = AGING
        self.grid = np.zeros((size, size), dtype=int)  # 2D grid representing the world
        self.species = {}  # Dictionary to store species by position
        self.day = 1
        self.paused = False
        self.initialize_grid()
        self.population_log = []
        self.herd_trajectories = {}
        self.daily_snapshots = []
        self.cell_logs = {}
        print("Initialized Planisuss world.")

    def initialize_grid(self):
        # Initialize grid with water boundaries and spawn species based on probabilities.
        print("Initial setup of the grid:")
        for x in range(self.size):
            for y in range(self.size):
                if x == 0 or y == 0 or x == self.size - 1 or y == self.size - 1:
                    self.grid[x, y] = 1  # Set boundaries to water
                else:
                    if random.random() < self.water_prob:
                        self.grid[x, y] = 1  # Randomly set water cells based on probability
                    else:
                        self.spawn_species((x, y), "Vegetob", self.vegetob_prob)
                        self.spawn_species((x, y), "Erbast", self.erbast_prob)
                        self.spawn_species((x, y), "Carviz", self.carviz_prob)

    def spawn_species(self, pos, species_name, spawn_prob):
        # Spawn species at the given position based on spawn probability.
        if random.random() < spawn_prob:
            species_class = globals()[species_name]
            if species_name == "Vegetob":
                new_entity = species_class(pos, self.max_density, self.growth)
            else:
                new_entity = species_class(pos, self.memory_length)
            if pos not in self.species:
                self.species[pos] = []
            self.species[pos].append(new_entity)
            print(f"Spawned {species_name} at {pos} with initial properties: {vars(new_entity)}")

    def action(self):
        # Perform daily actions for all entities in the world.
        print(f"Actions for Day {self.day}:")
        self.grow_vegetob()
        self.group_erbasts_into_herds()
        self.group_carviz_into_prides()
        self.move_herds()
        self.move_prides()
        self.move_erbasts()
        self.move_carviz()
        self.graze_erbasts()
        self.predate_carviz()
        self.struggle()
        self.spawn_erbasts()
        self.spawn_carviz()
        self.remove_dead_entities()

        # Log daily snapshot
        daily_snapshot = {
            'day': self.day,
            'species': {pos: [entity.__class__.__name__ for entity in entities] for pos, entities in self.species.items()}
        }
        self.daily_snapshots.append(daily_snapshot)
        print(f"Logged snapshot for Day {self.day}.")

        # Log total population of the day
        total_population = sum(len(entities) for entities in self.species.values())
        self.population_log.append(total_population)
        print(f"Total population for Day {self.day}: {total_population}")

    def grow_vegetob(self):
        # Grow Vegetob entities and remove grazed Erbasts if surrounded by max density Vegetob.
        for pos, entities in list(self.species.items()):
            for entity in entities:
                if isinstance(entity, Vegetob):
                    entity.grow()
                    if self.is_completely_surrounded_by_max_density(pos):
                        print(f"Erbasts at {pos} are overwhelmed by Vegetob.")
                        entities[:] = [e for e in entities if not isinstance(e, Erbast)]
            entities[:] = [e for e in entities if not e.should_remove()]
            if not entities:
                del self.species[pos]

    def is_completely_surrounded_by_max_density(self, pos):
        # Check if a position is completely surrounded by max density Vegetob.
        x, y = pos
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                new_pos = (x + dx, y + dy)
                vegetob = next((e for e in self.species.get(new_pos, []) if isinstance(e, Vegetob)), None)
                if not vegetob or vegetob.density < self.max_density:
                    return False
        return True

    def group_erbasts_into_herds(self):
        # Group multiple Erbasts into a Herd.
        for pos, entities in list(self.species.items()):
            erbasts = [e for e in entities if isinstance(e, Erbast)]
            if len(erbasts) > 1:
                herd = Herd(erbasts, self.memory_length)
                self.species[pos] = [e for e in entities if not isinstance(e, Erbast)]
                self.species[pos].append(herd)
                self.herd_trajectories[herd.id] = [herd.pos]
                print(f"Formed a herd at {pos} with {len(herd.group_list)} erbasts.")

    def group_carviz_into_prides(self):
        # Group multiple Carviz into a Pride.
        for pos, entities in list(self.species.items()):
            carviz = [e for e in entities if isinstance(e, Carviz)]
            if len(carviz) > 1:
                pride = Pride(carviz, self.memory_length)
                self.species[pos] = [e for e in entities if not isinstance(e, Carviz)]
                self.species[pos].append(pride)
                self.herd_trajectories[pride.id] = [pride.pos]
                print(f"Formed a pride at {pos} with {len(pride.group_list)} carviz.")

    def move_herds(self):
        # Move all Herds based on their decisions.
        for pos, entities in list(self.species.items()):
            herds = [e for e in entities if isinstance(e, Herd)]
            for herd in herds:
                decision = herd.decide(self.grid, self.species, self.neighborhood)
                if decision:
                    herd.move(self.grid, self.species)
                    self.herd_trajectories[herd.id].append(herd.pos)
                    print(f"Herd moved to {herd.pos}.")

    def move_prides(self):
        # Move all Prides based on their decisions.
        for pos, entities in list(self.species.items()):
            prides = [e for e in entities if isinstance(e, Pride)]
            for pride in prides:
                decision = pride.decide(self.grid, self.species, self.neighborhood)
                if decision:
                    pride.move(self.grid, self.species)
                    self.herd_trajectories[pride.id].append(pride.pos)
                    print(f"Pride moved to {pride.pos}.")

    def move_erbasts(self):
        # Move all Erbasts not in herds based on their decisions.
        for pos, entities in list(self.species.items()):
            erbasts = [e for e in entities if isinstance(e, Erbast)]
            for erbast in erbasts:
                if erbast.social_attitude < 0.5 or not any(isinstance(e, Herd) for e in entities):
                    decision = erbast.decide(self.grid, self.species, self.neighborhood)
                    if decision:
                        erbast.move(self.grid, self.species)
                        print(f"Erbast moved to {erbast.pos}.")

    def move_carviz(self):
        # Move all Carviz not in prides based on their decisions.
        for pos, entities in list(self.species.items()):
            carviz = [e for e in entities if isinstance(e, Carviz)]
            for carvi in carviz:
                if carvi.social_attitude < 0.5 or not any(isinstance(e, Pride) for e in entities):
                    decision = carvi.decide(self.grid, self.species, self.neighborhood)
                    if decision:
                        carvi.move(self.grid, self.species)
                        print(f"Carviz moved to {carvi.pos}.")

    def graze_erbasts(self):
        # Allow all Erbasts and Herds to graze.
        for pos, entities in list(self.species.items()):
            erbasts = [e for e in entities if isinstance(e, Erbast) or isinstance(e, Herd)]
            for erbast in erbasts:
                erbast.graze(self.species)

    def predate_carviz(self):
        # Allow all Carviz and Prides to predate.
        for pos, entities in list(self.species.items()):
            carviz = [e for e in entities if isinstance(e, Carviz) or isinstance(e, Pride)]
            for carvi in carviz:
                carvi.predate(self.species)

    def struggle(self):
        # Resolve struggles between Herds and Prides.
        for pos, entities in list(self.species.items()):
            herds = [e for e in entities if isinstance(e, Herd)]
            if len(herds) > 1:
                main_herd = herds[0]
                for herd in herds[1:]:
                    main_herd.group_list.extend(herd.group_list)
                    entities.remove(herd)
                    self.herd_trajectories.pop(herd.id, None)
                print(f"Herds at {pos} have merged.")

            prides = [e for e in entities if isinstance(e, Pride)]
            if len(prides) > 1:
                main_pride = prides[0]
                for pride in prides[1:]:
                    main_pride.group_list.extend(pride.group_list)
                    entities.remove(pride)
                    self.herd_trajectories.pop(pride.id, None)
                print(f"Prides at {pos} have merged.")

    def spawn_erbasts(self):
        # Spawn offspring for all Erbasts.
        for pos, entities in list(self.species.items()):
            erbasts = [e for e in entities if isinstance(e, Erbast)]
            for erbast in erbasts:
                erbast.age_up(self.species, self.aging)  # Pass the species dictionary

    def spawn_carviz(self):
        # Spawn offspring for all Carviz.
        for pos, entities in list(self.species.items()):
            carviz = [e for e in entities if isinstance(e, Carviz)]
            for carvi in carviz:
                carvi.age_up(self.species, self.aging)

    def remove_dead_entities(self):
        # Remove all dead entities from the species dictionary.
        for pos, entities in list(self.species.items()):
            entities[:] = [e for e in entities if not e.should_remove()]
            if not entities:
                del self.species[pos]
        print(f"Removed dead entities for Day {self.day}.")

    def plot(self):
        # Plot the current state of the grid.
        fig, ax = plt.subplots()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"Planisuss World Simulation - Day {self.day}")

        species_colors = {
            'Vegetob': '#00ff00',  # Green
            'Erbast': '#ffaaaa',  # Light Red
            'Carviz': '#ffffaa',  # Light Yellow
            'Herd': '#ff0000',  # Red
            'Pride': '#ffff00'  # Yellow
        }

        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x, y] == 1:
                    color = '#0000ff'  # Blue, Water
                    rect = patches.Rectangle((y, x), 1, 1, linewidth=0, edgecolor=None, facecolor=color)
                    ax.add_patch(rect)
                else:
                    color = '#ffffff'  # White, Ground
                    rect = patches.Rectangle((y, x), 1, 1, linewidth=0, edgecolor=None, facecolor=color)
                    ax.add_patch(rect)

                if (x, y) in self.species:
                    for entity in self.species[(x, y)]:
                        if isinstance(entity, Vegetob):
                            green_intensity = max(1 - entity.density / self.max_density, 0.3)  # Ensure minimum green intensity
                            color = (0, green_intensity, 0)  # Varying shades of green
                            circle = patches.Circle((y + 0.5, x + 0.5), 0.3, edgecolor=None, facecolor=color)
                            ax.add_patch(circle)
                        elif isinstance(entity, Erbast):
                            color = species_colors['Erbast']
                            circle = patches.Circle((y + 0.5, x + 0.5), 0.2, edgecolor=None, facecolor=color)
                            ax.add_patch(circle)
                        elif isinstance(entity, Carviz):
                            color = species_colors['Carviz']
                            circle = patches.Circle((y + 0.5, x + 0.5), 0.2, edgecolor=None, facecolor=color)
                            ax.add_patch(circle)
                        elif isinstance(entity, Herd):
                            color = species_colors['Herd']
                            circle = patches.Circle((y + 0.5, x + 0.5), 0.2, edgecolor=None, facecolor=color)
                            ax.add_patch(circle)
                        elif isinstance(entity, Pride):
                            color = species_colors['Pride']
                            circle = patches.Circle((y + 0.5, x + 0.5), 0.2, edgecolor=None, facecolor=color)
                            ax.add_patch(circle)

        legend_handles = [
            patches.Patch(color=species_colors['Vegetob'], label='Vegetob'),
            patches.Patch(color=species_colors['Erbast'], label='Erbast'),
            patches.Patch(color=species_colors['Carviz'], label='Carviz'),
            patches.Patch(color=species_colors['Herd'], label='Herd'),
            patches.Patch(color=species_colors['Pride'], label='Pride')
        ]
        ax.legend(handles=legend_handles, loc='upper right')

        plt.xlim(0, self.size)
        plt.ylim(0, self.size)
        plt.gca().invert_yaxis()

        def on_press(event):
            # Handle key press events for pausing, continuing, resetting, and closing the simulation.
            if event.key == 'p':
                self.paused = True
                print("Simulation paused.")
            elif event.key == 'c':
                self.paused = False
                print("Simulation continued.")
            elif event.key == 'r':
                self.reset_simulation()
                print("Simulation reset.")
            elif event.key == 'q':
                plt.close(fig)
                print("Simulation closed.")

        fig.canvas.mpl_connect('key_press_event', on_press)
        plt.draw()
        plt.pause(0.01)  # Pause for interaction

    def plot_population(self):
        # Plot the population growth over time.
        plt.figure()
        plt.plot(self.population_log, label='Total Population Over Time')
        plt.xlabel('Day')
        plt.ylabel('Population')
        plt.title('Population Growth')
        plt.legend()
        plt.show()

    def plot_herd_trajectories(self):
        # Plot the trajectories of herds over time.
        plt.figure()
        for herd_id, positions in self.herd_trajectories.items():
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            plt.plot(x_coords, y_coords, label=f'Herd {herd_id}')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        plt.title('Herd Trajectories Over Time')
        plt.legend()
        plt.show()

    def plot_cell_details(self, cell_pos):
        # Plot details for a specific cell over time.
        cell_log = [log[cell_pos] for log in self.cell_logs if cell_pos in log]
        if not cell_log:
            print(f"No data for cell {cell_pos}")
            return
        days = list(range(1, len(cell_log) + 1))
        vegetob_density = [log['Vegetob'].density for log in cell_log if 'Vegetob' in log]
        erbast_count = [len([e for e in log['entities'] if isinstance(e, Erbast)]) for log in cell_log]

        plt.figure()
        plt.plot(days, vegetob_density, label='Vegetob Density')
        plt.plot(days, erbast_count, label='Erbast Count')
        plt.xlabel('Day')
        plt.ylabel('Count / Density')
        plt.title(f'Cell {cell_pos} Details Over Time')
        plt.legend()
        plt.show()

    def plot_population_trends(self):
        # Plot population trends of different species over time.
        species_population = {'Vegetob': [], 'Erbast': [], 'Carviz': [], 'Herd': [], 'Pride': []}
        days = list(range(1, self.max_day + 1))

        for day in days:
            count = {'Vegetob': 0, 'Erbast': 0, 'Carviz': 0, 'Herd': 0, 'Pride': 0}
            for snapshot in self.daily_snapshots:
                if snapshot['day'] == day:
                    for entities in snapshot['species'].values():
                        for entity in entities:
                            count[entity] += 1
            for species, c in count.items():
                species_population[species].append(c)

        plt.figure()
        for species, counts in species_population.items():
            plt.plot(days, counts, label=species)
        plt.xlabel('Day')
        plt.ylabel('Population')
        plt.title('Population Trends Over Time')
        plt.legend()
        plt.show()

    def simulate(self):
        # Run the simulation.
        print("Starting the simulation:")
        self.log_snapshot()  # Log the initial state
        self.plot()  # Display initial state

        while self.day < self.max_day:
            if not plt.get_fignums():
                break
            if not self.paused:
                self.day += 1  # Increment day counter at the beginning of the loop
                print(f"Day {self.day}")
                self.action()
                self.plot()
                self.log_snapshot()  # Log the state after actions are performed
                plt.pause(0.1)  # Adjust pause duration for simulation speed

        self.plot_population()
        self.plot_population_trends()

    def log_snapshot(self):
        # Log the daily snapshot of the simulation state.
        daily_snapshot = {
            'day': self.day,
            'species': {pos: [entity.__class__.__name__ for entity in entities] for pos, entities in self.species.items()}
        }
        self.daily_snapshots.append(daily_snapshot)

        # Log total population for the day
        total_population = sum(len(entities) for entities in self.species.values())
        self.population_log.append(total_population)
        print(f"Logged snapshot for Day {self.day} with total population {total_population}.")

    def reset_simulation(self):
        # Reset the simulation to the initial state.
        self.__init__(self.size, self.water_prob, self.vegetob_prob, self.erbast_prob, self.carviz_prob, self.max_day, self.max_density, self.growth)
        self.simulate()

    def save_simulation(self,filename="C:\\Users\\Tiger\\Desktop\\Python Project\\Planisuss_data.pkl"):
        # Save the simulation state to a file.
        with open(filename,'wb') as f:
            pickle.dump(self,f)
        print(f"Simulation saved to {filename}")

    @staticmethod
    def load_simulation(filename="C:\\Users\\Tiger\\Desktop\\Python Project\\Planisuss_data.pkl"):
        # Load a simulation state from a file.
        with open(filename,'rb') as f:
            return pickle.load(f)