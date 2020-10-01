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


class Rooster(Rooster):
    """ An agent with fixed initial wealth."""
    def __init__(self, Agent, Model):
        super().__init__(Agent, Model)

        self.lecture_halls = [] #the lecture halls this agent will have to be present
        self.rooster = [(1,2)]  #the step numbers where the agent needs to be somewhere.