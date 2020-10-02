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
DAY_PARTS = 4
DAY_PART_DURATION = 8 #steps to make 2 hours
DAY_DURATION = 8 * 4
AMOUNT_OF_ROOMS = 21
ROOM_CAPACITY = 168
LECTURES_PER_DAY = 3
AMOUNT_OF_AGENTS = 800

class Rooster_agent:
    def __init__(self, Agent, Model):
        """
            Steps at the beginning of the day is needed to find out at which time the agent is in the day.
        """
        self.rooster = []
        self.agent_id = Agent.agent_id

    def get_rooster(self, model):
        self.rooster = model.rooster_model.rooster[:, self.agent_id]

    def new_day(self, DAY_DURATION, model):
        rooster = []
        for i in range(int(DAY_DURATION/DAY_PART_DURATION)):
            for j in range(DAY_PART_DURATION):
                room = self.get_available_room(model)
                seat = self.get_seat(room)
                """
                    step is the time of the day.
                """
                step = i+j
                self.rooster.append((room, seat, step))
                self.steps_at_beginning_day = model.total_steps

    def get_available_room(self, model):
        for row in range(model.grid.rooms[:][0].size):
            for col in range(model.grid.rooms[0][:].size):
                if model.grid.rooms[row][col].room_available():
                    return model.grid.rooms[row][col]

    def get_seat(self, room):
        for seat in room.seats:
            if seat.available:
                return seat

class Rooster_model:
    def __init__(self, Model):
       # amount of rooms
        self.rooster = np.full(((DAY_DURATION), Model.num_agents), 20)
    """
        rooster where rows are the steps in a day and col are all the agents
    """
    def make_day_rooster(self, Model):
        rooster = self.rooster
        for col in range(rooster.shape[1]):
            if col == 168:
                x = 1
            lectures = 0
            breaks = 0
            for row in range(0, rooster.shape[0], DAY_PART_DURATION):
                for i in range(AMOUNT_OF_ROOMS):
                    if(i != 21 and lectures < 3 and (rooster[row, :] == i).sum() <= ROOM_CAPACITY):
                        rooster[row:row+DAY_PART_DURATION, col] = i
                        lectures += 1
                        break
                    if (breaks < 1 and i == 20):
                        rooster[row:row+DAY_PART_DURATION, col] = i
                        breaks += 1
                        break
        print("bug stop")


