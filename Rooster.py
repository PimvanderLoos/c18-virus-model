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
DAY_PART_DURATION = 8  # steps to make 2 hours
DAY_DURATION = 8 * 4
AMOUNT_OF_ROOMS = 21
LECTURES_PER_DAY = 3
AMOUNT_OF_AGENTS = 800

class RoosterAgent:
    def __init__(self, agent, model):
        """
        Steps at the beginning of the day is needed to find out at which time the agent is in the day.
        """
        self.rooster = []
        self.agent_id = agent.agent_id
        self.model = model
        self.rooster = self.model.rooster_model.rooster[:, self.agent_id]

    def new_day(self, day_duration, model):
        # pass
        rooster = []
        for i in range(int(day_duration / DAY_PART_DURATION)):
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


class RoosterModel:
    def __init__(self, model):
        self.model = model

        self.break_room_id = self.model.grid.room_count
        """
        The ID of the 'break' room. I.e. the room where agents go to if they don't have any lectures.
        """

        self.rooster = np.full((DAY_DURATION, model.num_agents), self.break_room_id)
        """
        Rooster where rows are the steps in a day and col are all the agents.
        Defaults to the break room.
        """
        
    def make_day_rooster(self):
        rooster = self.rooster
        for col in range(rooster.shape[1]):

            lectures = 0
            breaks = 0

            for row in range(0, rooster.shape[0], DAY_PART_DURATION):
                for room_id in range(self.model.grid.room_count):
                    room = self.model.grid.get_room_from_id(room_id)
                    room_capacity = room.get_capacity()

                    if room_id != self.break_room_id and lectures < 3 and (rooster[row, :] == room_id).sum() < room_capacity:
                        rooster[row:row+DAY_PART_DURATION, col] = room_id
                        lectures += 1
                        break

                    if breaks < 1 and room_id == self.break_room_id:
                        rooster[row:row+DAY_PART_DURATION, col] = room_id
                        breaks += 1
                        break
