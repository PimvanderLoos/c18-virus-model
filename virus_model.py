import pandas as pd
import numpy as np
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement, ChartModule

from canvas_room_grid import CanvasRoomGrid
from room_grid import RoomGrid
from rooster import *
from virus import *

""" TODO list
Things we still want to program:
- Change the values for the parameters to more realistic, literature-based values. 
- Next to night-time, also remove weekends from the visualization in the simulation.
- Instead of a base infection probability, have a deterministic number of agents being infected at first. This allows for running experiments with the same starting state.
- Agents that are quarantined but receive a negative test, can come back and do not have to be taken out of the simulation for the usual 14 days.
- Add a slider for the number of classrooms and the size of each classroom.
- Possible addition: add other types of rooms next to lecture rooms, e.g. break room or lab rooms. These would have a different mapping compared to lecture rooms.
- Possible addition: next to contact tracing, more possible mitigation measures: such as social distancing or having a % of agents wearing face masks.
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
        self.model = model
        self.in_lecture = False
        self.agent_id = unique_id
        self.day_time = 0
        self.rooster_agent = RoosterAgent(self, model)
        self.room = None
        self.seat = None

        """
        The day rooster where the agent will sit or walk.
        """
        self.virus = Virus(self.model.random, model.base_infection_chance)
        self.quarantine = False
        """
        Keeps track of whether this agent is under quarantine or not
        """
        self.quarantine_duration = 0
        """
        Keeps track of the remaining number of days this agent will be quarantined.
        """
        self.test_result = 0  # np.nan
        """
        Keeps track of testing status: 0 is not tested, -1 is negative, 1 is positive
        """
        self.day_tested = float(np.nan)
        """
        Keeps track of the day when tested
        """

        self.df_contacts = pd.DataFrame(columns=["unique_id", "time_contact"])
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
        if len(possible_steps) == 0:
            print("Failed to find position for agent {}: Current position: [{} {}]".format(
                self.unique_id, self.pos[0], self.pos[1]))
            return

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

        print(self.model.spread_chance)
        other_agent.virus.infect(self.model.spread_chance, self.model.day)

    def set_room(self):
        room_id = self.rooster_agent.rooster[0]  # What does this do?
        if room_id == self.model.rooster_model.break_room_id:
            self.room = None
        else:
            self.room = self.model.grid.rooms_list[room_id]

    def set_seat(self, random=True):
        if self.room is None:
            self.seat = None
            return

        found_seat = None
        if random:
            threshold = self.room.get_capacity() / 4
            """
            At which point we'll abandon the idea of randomly assigning agents to seats, as it'll take too long and 
            becomes less and less important.
            """

            available_seat_count = sum([seat.available for seat in self.room.seats])
            if available_seat_count < threshold:
                random = False

            found_seat = self.room.seats[0]
            while not found_seat.available:
                found_seat = self.room.seats[self.model.random.randrange(self.room.get_capacity())]

        if not random:
            for seat in self.room.seats:
                if seat.available:
                    found_seat = seat
                    break

        if found_seat is None:
            print("Failed to find a seat for agent {} in room {}!".format(self.unique_id, self.room.room_id))
            self.seat = None
            return

        found_seat.available = False
        new_position = (found_seat.x, found_seat.y)
        self.model.grid.move_agent(self, new_position)
        self.seat = found_seat

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

        self.day_time = 0

    def testing(self):
        """"
        testing agents (if virus testable)
        """
        if not self.quarantine and \
                (self.model.random.randrange(0, 100) < self.model.daily_testing_chance) & \
                (self.virus.disease_state != DiseaseState.DECEASED):
            self.day_tested = self.model.day
            if self.virus.disease_state >= DiseaseState.TESTABLE:
                self.test_result = 1
            else:
                self.test_result = -1

    def quarantine_agents(self, last_contact_days=3):  # , detection_days = 1
        """"
        quarantine agents after being tested positive or having contact to positive tested person
        
        :param last_contact_days: Quarantining agent if contact to positive agent in the last last_contact_days
        """
        if self.test_result == 1:

            ids_contact = self.df_contacts.loc[
                (self.day_tested - self.df_contacts["time_contact"]) <= last_contact_days, "unique_id"].unique()
            for other_agent in self.model.schedule.agent_buffer(shuffled=False):
                if (other_agent.unique_id in list(ids_contact)) & (not other_agent.quarantine):
                    other_agent.enforce_quarantine(14)

            if not self.quarantine:
                self.enforce_quarantine(14)

    def trace_contact(self, distance_tracking=1):
        """"
        tracing contact to each agent in certain radius with time of last contact
        
        :param distance_tracking: radius of moore-distance within contacts are traced
        """
        if not self.quarantine:

            for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=distance_tracking, moore=True):
                if not other_agent.quarantine:
                    self.df_contacts = self.df_contacts.append(
                        {"unique_id": other_agent.unique_id, "time_contact": self.model.day},
                        ignore_index=True)
                    self.df_contacts = self.df_contacts.groupby("unique_id").max().reset_index()
                    other_agent.df_contacts = other_agent.df_contacts.append(
                        {"unique_id": self.unique_id, "time_contact": self.model.day},
                        ignore_index=True)
                    other_agent.df_contacts = other_agent.df_contacts.groupby("unique_id").max().reset_index()

    def move_to_random_position(self):
        """
        Moves this agent to a random position on the grid. Note that only 'valid' positions are considered
        (see RoomGrid#is_available(int, int, False).
        """
        (pos_x, pos_y) = self.model.grid.get_random_pos(self.random)

        # If the agent doesn't exist on the grid at the moment, place them.
        # Otherwise, move them. This is required, because move has to remove the agent
        # From the grid in the old position, which will cause an NPE if it doesn't exist.
        if self.pos is None:
            self.model.grid.place_agent(self, (pos_x, pos_y))
        else:
            self.model.grid.move_agent(self, (pos_x, pos_y))

    def do_rooster_step(self, room_rooster_id):
        """
        Takes care of whatever the agent has to do this step according to their schedule/rooster.
        :param room_rooster_id: The ID of the room they should be in. If they are not already there,
                                they will have to move. Special ID 20 means that they are free to move around.
        """
        next_in_lecture = room_rooster_id != self.model.rooster_model.break_room_id

        # If they are already in the room they are supposed to be in, do nothing.
        if self.room is not None and self.room.room_id == room_rooster_id:
            # Nothing needs to happen, so just pass. It doesn't return to
            # make sure that self.in_lecture is properly updated at the end.
            pass

        # If they have to be in a (different) lecture next, move them.
        elif next_in_lecture:
            self.room = self.model.grid.rooms_list[room_rooster_id]
            self.set_seat()

        # If their lecture has ended, move them to a random position.
        elif self.in_lecture and not next_in_lecture:
            self.room = None
            self.seat = None
            self.move_to_random_position()

        self.in_lecture = next_in_lecture

    def step(self):
        # No zombies allowed
        if self.virus.disease_state == DiseaseState.DECEASED or self.quarantine:
            self.day_time += 1
            return

        room_rooster_id = self.rooster_agent.rooster[self.model.day_step]
        self.do_rooster_step(room_rooster_id)

        # Free to move around wherever they want! Just not in the rooms.
        if not self.in_lecture:
            self.move()

        if not self.virus.is_infectious():
            self.day_time += 1
            return

        for other_agent in self.model.grid.get_neighbors(pos=self.pos, radius=self.model.spread_distance, moore=True):
            self.handle_contact(other_agent)

        if self.model.choice_of_measure == 'Contact Tracing':
            self.trace_contact()
        self.day_time += 1


class VirusModel(Model):
    """A model with some number of agents."""

    def __init__(self, num_agents, grid_width, grid_height, base_infection_chance, spread_distance, spread_chance,
                 daily_testing_chance, choice_of_measure, *args, **kwargs):
        """
        Initializes a new Virus Model.
        :param num_agents: The number of agents that will participate in the model.
        :param grid_width: The width of the grid.
        :param grid_height: The height of the grid.
        :param base_infection_chance: The probability of an agent starting with the infection.
        :param spread_distance: The distance the virus can spread to other agents.
        :param spread_chance: The probability of the virus spreading to nearby agents after 1 tick (15 min).
        :param daily_testing_chance: The probability of an agent being tested at the start of each day.
        :param choice_of_measure: Which measures to enable to attempt to prevent the spread of the virus.
        """
        super().__init__(*args, **kwargs)

        self.num_agents = num_agents
        self.base_infection_chance = base_infection_chance
        """
        Describes the chance of an agent being infected at the start of the model
        """

        self.spread_distance = spread_distance
        self.spread_chance = spread_chance
        """
        Describes the chance of the virus spreading to another agent. Applied every step.
        """

        self.schedule = RandomActivation(self)
        self.grid = RoomGrid(grid_width, grid_height, False, room_count=10)
        self.running = True
        self.day = 0
        self.total_steps = 0
        self.day_step = 0
        """
        The number of ticks that have passed in any given day. This value is therefore always between [0, DAY_DURATION]
        """

        self.rooster_model = RoosterModel(self)
        self.rooster_model.make_day_rooster()
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

            agent.move_to_random_position()
            agent.set_room()
            agent.set_seat()

        self.datacollector = DataCollector(
            model_reporters={"infected": get_infection_rate, "deaths": get_death_count,
                             "quarantined": get_quarantined_count,
                             "healthy": get_healty_count, "just infected": get_infected_count,
                             "testable": get_testable_count,
                             "infectious": get_infectious_count, "symptomatic": get_symptomatic_count,
                             "recovered": get_recovered_count,
                             "quarantined: infected": get_quarantined_infected,
                             "quarantined: healthy": get_quarantined_healthy,
                             "not quarantined: infected": get_notquarantined_infected,
                             "tested total": get_tested_count, "tested positive": get_tested_positive_count,
                             "tested negative": get_tested_negative_count},
            agent_reporters={"Position": "pos"})

    def set_day_step(self):
        self.day_step = (self.total_steps % DAY_DURATION)

    def clear_rooms(self):
        for room in self.grid.rooms_list:
            room.is_reserved = False
            for seat in room.seats:
                seat.available = True

    def next_day(self):
        """
        Handles the start of a new day.
        """
        self.rooster_model.make_day_rooster()
        self.day = int(self.schedule.steps / DAY_DURATION)
        for agent in self.schedule.agent_buffer(shuffled=False):
            agent.new_day(self.day)

        self.virtual_steps = self.day * NIGHT_DURATION
        print("NEXT DAY: {}".format(self.day))

    def step(self):
        self.clear_rooms()
        self.set_day_step()
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


# Functions for the Datacollector
def get_infection_rate(model):
    return int(np.sum([agent.virus.is_infected() for agent in model.schedule.agents]))


def get_death_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.DECEASED for agent in model.schedule.agents]))


def get_quarantined_count(model):
    return int(np.sum([agent.quarantine for agent in model.schedule.agents]))


def get_healty_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.HEALTHY for agent in model.schedule.agents]))


def get_recovered_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.RECOVERED for agent in model.schedule.agents]))


def get_infected_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.INFECTED for agent in model.schedule.agents]))


def get_testable_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.TESTABLE for agent in model.schedule.agents]))


def get_infectious_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.INFECTIOUS for agent in model.schedule.agents]))


def get_symptomatic_count(model):
    return int(np.sum([agent.virus.disease_state == DiseaseState.SYMPTOMATIC for agent in model.schedule.agents]))


def get_tested_count(model):
    return int(np.sum([agent.test_result in [-1, 1] for agent in model.schedule.agents]))


def get_tested_positive_count(model):
    return int(np.sum([agent.test_result in [1] for agent in model.schedule.agents]))


def get_tested_negative_count(model):
    return int(np.sum([agent.test_result in [-1] for agent in model.schedule.agents]))


def get_quarantined_infected(model):
    return int(np.sum([agent.quarantine & (agent.virus.is_infected()) for agent in model.schedule.agents]))


def get_quarantined_healthy(model):
    return int(
        np.sum([agent.quarantine & (not agent.virus.is_infected()) for agent in model.schedule.agents]))


def get_notquarantined_infected(model):
    return int(np.sum([(agent.quarantine == False) & (agent.virus.is_infected()) for agent in model.schedule.agents]))


disease_states = [DiseaseState.DECEASED, DiseaseState.HEALTHY, DiseaseState.RECOVERED, DiseaseState.INFECTED,
                  DiseaseState.TESTABLE, DiseaseState.INFECTIOUS, DiseaseState.SYMPTOMATIC]


class TimeElement(TextElement):
    def __init__(self):
        super().__init__()

    def render(self, model):
        days = 1 + int(model.total_steps / 96)
        hours = 9 + int((model.total_steps % 96) / 4)
        quarters = 15 * (model.total_steps % 4)

        if quarters == 0:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters) + "0"
        else:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters)


time_element = TimeElement()

grid_width = 100
grid_height = 100
num_agents = 800

# Includes adjustable sliders for the user in the visualization
model_params = {
    "Description": UserSettableParameter('static_text',
                                         value="This simulation model represents a university building in "
                                               "which agents (students) attend lectures in classrooms. It "
                                               "simulates the spread of a virus in the building. The plots "
                                               "below the main visualization show the spread of the virus. "),
    "static_text": UserSettableParameter('static_text',
                                         value="The options below allow you to adjust the parameter settings. "
                                               "After setting the options to the desired values, "
                                               "click 'Reset' and restart the simulation."),
    "choice_of_measure": UserSettableParameter('choice', 'Mitigation measure applied', value='No measures',
                                               choices=['No measures', 'Contact Tracing']),
    # "contacttracing_option": UserSettableParameter('checkbox', 'Measure: Contact Tracing', value=True),
    "num_agents": UserSettableParameter("slider", "Number of agents", num_agents, 10, 1000, 10),
    "grid_width": grid_width,
    "grid_height": grid_height,
    "base_infection_chance": UserSettableParameter("slider", "Base infection probability", 3, 0, 100, 1),
    "spread_distance": UserSettableParameter("slider", "Spread distance (in meters)", 2, 1, 10, 1),
    "spread_chance": UserSettableParameter("slider", "Spread probability", 8, 1, 100, 1),
    "daily_testing_chance": UserSettableParameter("slider", "Daily probability of getting tested per agent", 10, 1, 100,
                                                  1),
    "legend": UserSettableParameter('static_text',
                                    value="<b>Legend</b> <br> "
                                          "Green dot: healthy agent. <br> "
                                          "Blue dot: infected agent. <br> "
                                          "Red dot: infectious agent. <br> "
                                          "Bright purple dot: testable agent. <br> "
                                          "Grey square: wall. <br> "
                                          "Red square: classroom seat. <br> "
                                          "White square: space where the agent can move. ")
}

grid = CanvasRoomGrid(agent_portrayal, grid_width, grid_height, 900, 900)
chart = ChartModule([{"Label": "infected",
                      "Color": "Black"},
                     {"Label": "deaths",
                      "Color": "Red"},
                     {"Label": "quarantined",
                      "Color": "Yellow"}],
                    data_collector_name='datacollector')
chart_disease_state = ChartModule([{"Label": "just infected",
                                    "Color": "rgba(0,0,255,1)"},
                                   {"Label": "testable",
                                    "Color": "rgba(255,0,212,1)"},
                                   {"Label": "infectious",
                                    "Color": "rgba(255,0,0,1)"},
                                   {"Label": "symptomatic",
                                    "Color": "rgba(102,0,0,1)"},
                                   {"Label": "recovered",
                                    "Color": "rgba(8,323,222,1)"},
                                   {"Label": "deaths",
                                    "Color": "Brown"}
                                   ],
                                  # include healthy? {"Label": "healthy", "Color": "rgba(43,255,0,1)"},
                                  data_collector_name='datacollector')
chart_quarantined = ChartModule([{"Label": "quarantined: infected",
                                  "Color": "Green"},
                                 {"Label": "quarantined: healthy",
                                  "Color": "Yellow"},
                                 {"Label": "not quarantined: infected",
                                  "Color": "Red"}],
                                data_collector_name='datacollector')
chart_testing = ChartModule([{"Label": "tested total",
                              "Color": "Black"},
                             {"Label": "tested negative",
                              "Color": "Blue"},
                             {"Label": "tested positive",
                              "Color": "Red"}],
                            data_collector_name='datacollector')

server = ModularServer(VirusModel,
                       [time_element, grid, chart, chart_disease_state, chart_quarantined, chart_testing],
                       "Virus Model",
                       model_params)

server.port = 8543
server.launch()
