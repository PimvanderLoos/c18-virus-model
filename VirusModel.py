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


class VirusAgent(Agent):
    """ An agent with fixed initial wealth."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.infected = model.random.randrange(0, 100) < BASE_INFECTION_CHANCE

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

    def step(self):
        self.move()
        if not self.infected:
            return

        for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=3, moore=True):
            self.handle_contact(other_agent)

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

        # Create agents
        for uid in range(self.num_agents):
            agent = VirusAgent(uid, self)
            self.schedule.add(agent)

            # Add the agent to a random grid cell
            pos_x = self.random.randrange(self.grid.width)
            pos_y = self.random.randrange(self.grid.height)
            self.grid.place_agent(agent, (pos_x, pos_y))

        self.datacollector = DataCollector(
            model_reporters={"infected": get_infection_rate},
            agent_reporters={"Position": "pos"})

    def step(self):
        self.datacollector.collect(self)
        '''Advance the model by one step.'''
        self.schedule.step()


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
server.port = 8521
server.launch()


# num_agents = 200
# grid_width = 100
# grid_height = 100
# model_steps = 450
#
# # model = VirusModel(num_agents=num_agents, grid_width=grid_width, grid_height=grid_height)
#
# grid = CanvasGrid(agent_portrayal, grid_width, grid_height, grid_width * 2, grid_height * 2)
# server = ModularServer(VirusModel,
#                        [grid],
#                        "Virus Model",
#                        {"num_agents": num_agents, "grid_width": grid_width, "grid_height": grid_height})
# server.port = 8521
# server.launch()
# model = server.model_cls
#
# # for run in range(model_steps):
# #     model.step()
# #
# # plt.plot(model.datacollector.get_model_vars_dataframe())
# # plt.show()
#
# # agent_dataframe = model.datacollector.get_agent_vars_dataframe()
# # agents_array = np.reshape(agent_dataframe.to_numpy(), (model_steps, num_agents))
# #
# # fig = plt.figure()
# # ax = fig.gca()
# # ax.set_xticks(range(grid_width))
# # ax.set_yticks(range(grid_height))
# # plt.grid()
# # plt.axis('off')
# #
# # percentage_to_draw = 10
# # # for agent_idx in range(10):
# # for agent_idx in range(num_agents):
# #     if model.random.randrange(0, 100) > percentage_to_draw:
# #         continue
# #     agent_color = (model.random.randrange(0, 255, 1) / 255.0,
# #                    model.random.randrange(0, 255, 1) / 255.0,
# #                    model.random.randrange(0, 255, 1) / 255.0)
# #     for run in range(model_steps - 1):
# #         pos = agents_array[run][agent_idx]
# #         next_pos = agents_array[run + 1][agent_idx]
# #
# #         if abs(pos[0] - next_pos[0]) is (grid_width - 1) or abs(pos[1] - next_pos[1]) is (grid_height - 1):
# #             continue
# #
# #         line = mlines.Line2D([pos[0], next_pos[0]], [pos[1], next_pos[1]], color=agent_color)
# #         ax.add_line(line)
# # plt.show()





