#main.py
from planisuss import Planisuss

if __name__=="__main__":
    size=10  # Size of grid
    water_prob=0.1  # Probability of cell being water
    vegetob_prob=0.5  # Probability of spawning Vegetob
    growth=2  # Growth rate of Vegetob
    erbast_prob=0.3  # Probability of spawning Erbast
    carviz_prob=0.3  # Probability of spawning Carviz
    max_day=15  # Maximum number of days to run simulation
    max_density=100  # Maximum density for Vegetob

    # Initialize the simulation
    simulation=Planisuss(size,water_prob,vegetob_prob,erbast_prob,carviz_prob,max_day,max_density,growth)

    # Start the simulation
    simulation.simulate()

    '''planisuss/
│
├── common.py
├── vegetob.py
├── animal.py
├── group.py
├── planisuss.py
└── main.py
'''