from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
from CanvasRoomGrid import *
from RoomGrid import *

BASE_INFECTION_CHANCE = 3
SPREAD_CHANCE = 8
SPREAD_DISTANCE_SQ = 1.5 * 1.5
#0 TO 100 when zero then each person will sit next to different persons and different classrooms.
#When 100 then each person sits in the same room and next to the same people.
SCHEDULE_SIMILARITY = 0

#def get_rooster(room_similarity, model):

class VirusAgent(Agent):
    """ An agent with fixed initial wealth."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.infected = model.random.randrange(0, 100) < BASE_INFECTION_CHANCE
### contact tracing
        self.contact_infected = False        
        self.time_infected = 0
        self.time_contact_infected = 0
 #       self.weeks_rooster = get_rooster(room_similarity, model)
        print("bug stop")
        
    def list_removing(self, detection_time = 4*8):
        if self.infected:
            self.time_infected += 1
        if self.contact_infected:
            self.time_contact_infected += 1
        if (self.time_infected > detection_time) | (self.time_contact_infected > detection_time): 
            self.model.removing_agents.append(self)
###
 
    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def within_distance(self, other_agent):
        delta_x = self.pos[0] - other_agent.pos[0]
        delta_y = self.pos[1] - other_agent.pos[1]
        return (delta_x * delta_x + delta_y * delta_y) < SPREAD_DISTANCE_SQ

    def handle_contact(self, other_agent):
        # if not self.within_distance(other_agent):
        #     return

        if self.model.random.randrange(0, 100) < SPREAD_CHANCE:
            other_agent.infected = True
            
### contact tracing
    def trace_contact(self):
        if self.infected:
            for other_agent in self.model.grid.get_neighbors(pos = self.pos, radius = 1, moore = True):
                other_agent.contact_infected = True
                other_agent.time_contact_infected = max(self.time_infected, other_agent.time_contact_infected)
                

    def step(self):
        self.move()
        if not self.infected:
            return

        for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=3, moore=True):
            self.handle_contact(other_agent)
            
        #for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=3, moore=True):
        #   self.handle_contact(other_agent)
        self.trace_contact()
            
        
            
### contact tracing
        self.list_removing()
###

        # for other_agent in self.model.grid.get_cell_list_contents([self.pos]):
        #     self.handle_contact(other_agent)


def get_infection_rate(model):
    return int(np.sum([agent.infected for agent in model.schedule.agents]))


class VirusModel(Model):
    """A model with some number of agents."""
    def __init__(self, num_agents, grid_width, grid_height):
        self.num_agents = num_agents
        self.schedule = RandomActivation(self)
        self.grid = RoomGrid(grid_width, grid_height, False)
        self.running = True
        self.removing_agents = []
        self.removed_agents = []
        #x = self.grid.rooms[0][0].seats[0]
        # Create agents
        for uid in range(self.num_agents):
            agent = VirusAgent(uid, self)
            self.schedule.add(agent)

            # Add the agent to a random grid cell
            (pos_x, pos_y) = self.grid.get_random_pos(self.random)
            self.grid.place_agent(agent, (pos_x, pos_y))

        self.datacollector = DataCollector(
            model_reporters={"infected": get_infection_rate},
            agent_reporters={"Position": "pos"})

    def step(self):
        self.datacollector.collect(self)
        '''Advance the model by one step.'''
        self.schedule.step()
### contact tracing
        self.removed_agents.append(self.removing_agents)
        try:
            for agent in self.removing_agents:
                self.grid.remove_agent(agent)
                self.schedule.remove(agent)
                self.removing_agents.remove(agent)
            self.removing_agents = []
            
                
        except:
            print(str("removed_agents"))
###


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5}
    if agent.infected:
        portrayal["Color"] = "red"
        portrayal["Layer"] = 0
    else:
        portrayal["Color"] = "green"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    return portrayal


grid_width = 100
grid_height = 100
num_agents = 300

grid = CanvasRoomGrid(agent_portrayal, grid_width, grid_height, 900, 900)
chart = ChartModule([{"Label": "infected",
                      "Color": "Black"}],
                    data_collector_name='datacollector')
server = ModularServer(VirusModel,
                       [grid, chart],
                       "Virus Model",
                       {"num_agents": num_agents, "grid_width": grid_width, "grid_height": grid_height})
server.port = 8538
server.launch()