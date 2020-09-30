from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule, TextElement
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter                                               
from CanvasRoomGrid import *
from Virus import *
from RoomGrid import *
import pandas as pd
import numpy as np

# BASE_INFECTION_CHANCE = 3
"""
Describes the chance of an agent being infected at the start of the model
"""

# SPREAD_CHANCE = 8
"""
Describes the chance of the virus spreading to another agent. Applied every step.
"""

DAY_DURATION = 8 * 4
"""
The number of ticks that fit into a day. Remember that every tick is 15 minutes, so 8 * 4 ticks = 8 hours.
"""

NIGHT_DURATION = 24 * 4 - DAY_DURATION
"""
The number of ticks that fit into a 'night'.
"""


class VirusAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.virus = Virus(self.model.random, model.base_infection_chance)
        self.quarantine = False
        """
        Keeps track of whether this agent is under quarantine or not
        """

        self.quarantine_duration = 0
        """
        Keeps track of the remaining number of days this agent will be quarantined.
        """
        self.test_result = 0
        """
        Keeps track of testing status: 0 is not tested, -1 is negative, 1 is positive
        """
        self.day_tested = float(np.nan)
        """
        Keeps track of the day when tested
        """
#        self.day_start_testable = np.inf
#        self.days_testable = 0
        self.df_contacts = pd.DataFrame(columns = ["unique_id", "time_contact"])
        """
        Traces the last contact to each other agent
        """

    def enforce_quarantine(self, days):
        """
        Places this agent under quarantine.

        :param days: The number of days this agent will be quarantined for.
        """
        self.quarantine = True
        self.quarantine_duration = days

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False,
            radius=1)
        new_position = self.random.choice(possible_steps)

        self.model.grid.move_agent(self, new_position)

    def handle_contact(self, other_agent):
        """
        Attempts to spread the virus to another agent. This only has an effect if the other agent isn't already infected.

        Make sure that this agent is even infectious before calling this method!
        :param other_agent: The victim.
        """
        # We assume that there's only a single strain  of the disease, so you cannot get infected more than once.
        if other_agent.virus.is_infected():
            return

        # You cannot infect people who aren't there.
        if other_agent.quarantine:
            return

        # The virus can't go through walls, so don't do anything if there's a wall between this agent and the other one.
        if self.model.grid.is_path_obstructed(self.pos[0], self.pos[1], other_agent.pos[0], other_agent.pos[1]):
            return

        other_agent.virus.infect(self.model.spread_chance, self.model.day)

    def new_day(self, day):
        """
        Handles the start of a new day.

        :param day: The number of the new day (assuming the models started at 0).
        """
        self.virus.handle_disease_progression(day)
        
        self.testing()
        self.quarantine_agents()

        if self.quarantine:
            self.quarantine_duration -= 1
            if self.quarantine_duration <= 0:
                self.quarantine = False
                self.test_result = 0
                

    def testing(self ): #daily_testing_chance = self.model.daily_testing_chance
        """"
        testing agents (if virus testable)
        
        :param daily_testing_chance: The chance per day getting tested for an agent
        """
        if (self.model.random.randrange(0, 100) < self.model.daily_testing_chance) & (self.virus.disease_state != DiseaseState.DECEASED):
            self.day_tested = self.model.day
            if self.virus.disease_state >= DiseaseState.TESTABLE:
                self.test_result = 1
            else:
                self.test_result = -1
        
        

    def quarantine_agents(self, last_contact_days = 3): #, detection_days = 1
        """"
        quarantine agents after being tested positive or having contact to positive tested person
        
        :param last_contact_days: Quarantining agent if contact to positive agent in the last last_contact_days
        """
#        if self.virus.disease_state >= DiseaseState.TESTABLE:
#            self.day_start_testable = min(self.day_start_testable, self.model.day)
#            self.days_testable = self.model.day - self.day_start_testable
        
#        if self.days_testable >= detection_days:
#           self.enforce_quarantine(14)
#           ids_contact = self.df_contacts.loc[self.days_testable - np.floor(self.df_contacts["time_contact"]/(24*4)) <= tracking_days_removing, "unique_id"].unique()
#           for other_agent in self.model.schedule.agent_buffer(shuffled=False):
#              if other_agent.unique_id in ids_contact:
#                   other_agent.enforce_quarantine(14)
        
        if self.test_result == 1:
            
            ids_contact = self.df_contacts.loc[self.day_tested - np.floor(self.df_contacts["time_contact"]/(24*4)) <= last_contact_days, "unique_id"].unique()
            for other_agent in self.model.schedule.agent_buffer(shuffled=False):
                if (other_agent.unique_id in ids_contact) & (other_agent.quarantine == False):
                    other_agent.enforce_quarantine(14)            
            
            if self.quarantine == False:
                self.enforce_quarantine(14)
                    
                
    def trace_contact(self, distance_tracking = 1):
        """"
        tracing contact to each agent in certain radius with time of last contact
        
        :param distance_tracking: radius of moore-distance within contacts are traced
        """
        if self.quarantine == False:
            
            for other_agent in self.model.grid.get_neighbors(pos = self.pos, radius = distance_tracking, moore = True):
                if other_agent.quarantine == False:
                    self.df_contacts = self.df_contacts.append({"unique_id": other_agent.unique_id, "time_contact":self.model.total_steps},
                                                               ignore_index=True)
                    self.df_contacts = self.df_contacts.groupby("unique_id").max().reset_index()
                    other_agent.df_contacts = other_agent.df_contacts.append({"unique_id": self.unique_id, "time_contact":self.model.total_steps},
                                                               ignore_index=True)
                    other_agent.df_contacts = other_agent.df_contacts.groupby("unique_id").max().reset_index()
                

    def step(self):
        # No zombies allowed
        if self.virus.disease_state == DiseaseState.DECEASED or self.quarantine:
            return

        self.move()

        if not self.virus.is_infectious():
            return

        for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=self.model.spread_distance, moore=True):
            self.handle_contact(other_agent)
            
        if self.model.choice_of_measure == 'Contact Tracing':

            self.trace_contact()



def get_infection_rate(model):
    return int(np.sum([agent.virus.is_infected() for agent in model.schedule.agents]))


def get_death_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.DECEASED for agent in model.schedule.agents]))

def get_quarantined_count(model):
    return int(np.sum([agent.quarantine == True for agent in model.schedule.agents]))


class VirusModel(Model):
    """A model with some number of agents."""

    def __init__(self, num_agents, grid_width, grid_height,
                 base_infection_chance, spread_distance, spread_chance,
                 detection_time, daily_testing_chance, choice_of_measure):
        self.num_agents = num_agents
        self.base_infection_chance = base_infection_chance
        self.spread_distance = spread_distance
        self.spread_chance = spread_chance
        self.detection_time = detection_time
        self.schedule = RandomActivation(self)
        self.grid = RoomGrid(grid_width, grid_height, False)
        self.running = True
        self.day = 0
        self.total_steps = 0
        """
        Describes the 'total' number of steps taken by the model so far, including the virtual 'night' steps.
        """

        self.virtual_steps = 0
        """
        Describes the number of 'virtual' steps taken by the model. These are the skipped steps that represent the
        'night'.
        """
        self.daily_testing_chance = daily_testing_chance
        self.choice_of_measure = choice_of_measure

        # Create agents
        for uid in range(self.num_agents):
            agent = VirusAgent(uid, self)
            self.schedule.add(agent)

            # Add the agent to a 'random' grid cell
            (pos_x, pos_y) = self.grid.get_random_pos(self.random)
            self.grid.place_agent(agent, (pos_x, pos_y))

        self.datacollector = DataCollector(
            model_reporters={"infected": get_infection_rate, "deaths": get_death_count, "quarantined": get_quarantined_count},
            agent_reporters={"Position": "pos"})

    def next_day(self):
        """
        Handles the start of a new day.
        """
        self.day = int(self.schedule.steps / DAY_DURATION)
        for agent in self.schedule.agent_buffer(shuffled=False):
            agent.new_day(self.day)

        self.virtual_steps = self.day * NIGHT_DURATION
        print("NEXT DAY: {}".format(self.day))

    def step(self):
        self.datacollector.collect(self)
        if self.schedule.steps % DAY_DURATION == 0:
            self.next_day()

        '''Advance the model by one step.'''
                
        self.schedule.step()

        self.total_steps = self.schedule.steps + self.virtual_steps

def agent_portrayal(agent):
    if agent.quarantine or agent.virus.disease_state is DiseaseState.DECEASED:
        return {}

    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5}

    # Useful site for picking colors: https://rgbcolorcode.com/
    if agent.virus.disease_state is DiseaseState.HEALTHY:
        portrayal["Color"] = "rgba(43,255,0,1)"  # Bright green
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    elif agent.virus.disease_state is DiseaseState.INFECTED:
        portrayal["Color"] = "rgba(0,0,255,1)"  # Blue
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    elif agent.virus.disease_state is DiseaseState.TESTABLE:
        portrayal["Color"] = "rgba(255,0,212,1)"  # Bright purple
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    elif agent.virus.disease_state is DiseaseState.INFECTIOUS:
        portrayal["Color"] = "rgba(255,0,0,1)"  # Red
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    elif agent.virus.disease_state is DiseaseState.SYMPTOMATIC:
        portrayal["Color"] = "rgba(102,0,0,1)"  # Dark red
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    elif agent.virus.disease_state is DiseaseState.RECOVERED:
        portrayal["Color"] = "rgba(8,323,222,1)"  # Bright turquoise
        portrayal["Layer"] = 0

    return portrayal

class TimeElement(TextElement):
    def __init__(self):
        pass

    def render(self, model):
        days = 1 + int(model.total_steps / 96)           
        hours = 9 + int((model.total_steps % 96) / 4)
        quarters = 15 * (model.total_steps % 4)
        
        if quarters == 0:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters) +  "0"         
        else:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters)
    
time_element = TimeElement()

grid_width = 100
grid_height = 100
num_agents = 300

# Includes adjustable sliders for the user in the visualization        
model_params = {
        "static_text": UserSettableParameter('static_text', value="The options below allow you to adjust the parameter settings. After setting the options to the desired values, click 'Reset' and restart the simulation."),
        "choice_of_measure": UserSettableParameter('choice', 'Mitigation measure applied', value='No measures',
                                              choices=['No measures', 'Contact Tracing']),
        # "contacttracing_option": UserSettableParameter('checkbox', 'Measure: Contact Tracing', value=True),
        "num_agents": UserSettableParameter("slider", "Number of agents", 300, 10, 1000, 10),
        "grid_width": grid_width,
        "grid_height": grid_height,
        "base_infection_chance": UserSettableParameter("slider", "Base infection probability", 3, 0, 100, 1),
        "spread_distance": UserSettableParameter("slider", "Spread distance (in meters)", 2, 1, 10, 1),
        "spread_chance": UserSettableParameter("slider", "Spread probability", 8, 1, 100, 1),
        "detection_time": UserSettableParameter("slider", "Detection time (in hours)", 32, 1, 120, 1),
        "daily_testing_chance":UserSettableParameter("slider", "Daily probability of getting tested per agent", 10, 1, 100, 1)
}
       

grid = CanvasRoomGrid(agent_portrayal, grid_width, grid_height, 900, 900)
chart = ChartModule([{"Label": "infected",
                      "Color": "Black"},
                     {"Label": "deaths",
                      "Color": "Red"}, 
                     {"Label": "quarantined",
                      "Color": "Yellow"}],
                    data_collector_name='datacollector')
server = ModularServer(VirusModel,
                       [time_element,grid, chart],
                       "Virus Model",
                       model_params)
server.port = 8528
server.launch()