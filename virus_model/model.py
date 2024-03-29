import random

import pandas as pd
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement

from virus_model.canvas_room_grid import CanvasRoomGrid
from virus_model.modular_server import CustomModularServer
from virus_model.rooster import *
from virus_model.virus import *
from virus_model.virus_test import VirusTest, TestOutcome

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

    def __init__(self, unique_id: int, model: 'VirusModel'):
        super().__init__(unique_id, model)
        self.model = model
        self.in_lecture = False
        self.agent_id = unique_id
        self.day_time = 0
        self.rooster_agent = RoosterAgent(self, self.model)
        self.room: Optional[LectureRoom] = None
        self.seat: Optional[Seat] = None
        self.virus_test = VirusTest(self.model.test_delay, self.model.random)

        """
        The day rooster where the agent will sit or walk.
        """
        self.virus = self.__create_virus()
        self.quarantine = False
        """
        Keeps track of whether this agent is under quarantine or not
        """
        self.quarantine_duration = 0
        """
        Keeps track of the remaining number of days this agent will be quarantined.
        """
        self.day_tested = float(np.nan)
        """
        Keeps track of the day when tested
        """

        self.df_contacts = pd.DataFrame(columns=["unique_id", "time_contact"])
        """
        Traces the last contact to each other agent
        """

    def __create_virus(self) -> Virus:
        """
        Creates the `Virus` object for this agent.
        """
        percentile = self.unique_id / self.model.num_agents
        if percentile > (self.model.base_infection_rate / 100):
            state = DiseaseState.HEALTHY
        else:
            val = self.unique_id % 4
            if val == 0:
                state = DiseaseState.INFECTED
            elif val == 1:
                state = DiseaseState.TESTABLE
            elif val == 2:
                state = DiseaseState.INFECTIOUS
            else:
                state = DiseaseState.SYMPTOMATIC

        return Virus(self.model.random, state)

    def enforce_quarantine(self, days: int) -> None:
        """
        Places this agent under quarantine.

        :param days: The number of days this agent will be quarantined for.
        """
        self.quarantine = True
        self.quarantine_duration = days

    def move(self) -> None:
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False,
            radius=1, in_break_room=True)
        if len(possible_steps) == 0:
            return

        new_position = self.random.choice(possible_steps)

        self.model.grid.move_agent(self, new_position)

    def handle_contact(self, other_agent: 'VirusAgent') -> None:
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

    def set_room(self) -> None:
        """
        updates the `Room` this agent is in. If they have a break in their schedule,
        the room will be set to None, otherwise to the room specified in the schedule.
        """
        room_id = self.rooster_agent.rooster[0]  # What does this do?
        if room_id == self.model.rooster_model.break_room_id:
            self.room = None
        else:
            self.room = self.model.grid.rooms_list[room_id]

    def set_seat(self, random_seat: bool = True) -> None:
        """
        Updates the seat of this agent. If this agent is currently not in a room, their seat will be made available again.

        :param random_seat: Whether to attempt to randomly assign a seat.
        """
        if self.room is None:
            if self.seat is not None:
                self.seat.available = True
                self.seat = None
            return

        found_seat = None
        if random_seat:
            threshold = self.room.get_capacity() / 4
            """
            At which point we'll abandon the idea of randomly assigning agents to seats, as it'll take too long and 
            becomes less and less important.
            """

            available_seat_count = sum([seat.available for seat in self.room.seats])
            if available_seat_count < threshold:
                random_seat = False

            found_seat = self.room.seats[0]
            while not found_seat.available:
                found_seat = self.room.seats[self.model.random.randrange(self.room.get_capacity())]

        if not random_seat:
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

    def new_day(self, day: int) -> None:
        """
        Handles the start of a new day.

        :param day: The number of the new day (assuming the models started at 0).
        """
        self.virus.handle_disease_progression(day)
        self.virus_test.new_day(day)

        if self.virus_test.get_result(self.model.day) == TestOutcome.NEGATIVE:
            self.quarantine_duration = 0

        self.testing()
        self.quarantine_agents(self.model.last_contact_days)

        if self.quarantine:
            self.quarantine_duration -= 1
            if self.quarantine_duration <= 0:
                self.quarantine = False

        self.day_time = 0

    def testing(self, reason="routine") -> None:
        """"
        testing agents (if virus testable)

        :param reason: Checking if routine testing or contact tracing suggestion
        """
        if (self.quarantine or
                self.virus.is_deceased()):
            return

        if reason == "routine":
            if (not self.virus.is_infected() or
                    self.model.random.randrange(0, 100) > self.model.daily_testing_chance):
                return

        self.day_tested = self.model.day
        self.virus_test.perform_test(self.model.day, self.virus)

    def quarantine_agents(self, last_contact_days) -> None:  # , detection_days = 1
        """"
        quarantine agents after being tested positive or having contact to positive tested person

        :param last_contact_days: Quarantining agent if contact to positive agent in the last last_contact_days
        """
        if self.virus_test.get_result(self.model.day) == TestOutcome.POSITIVE:

            ids_contact = self.df_contacts.loc[
                (self.day_tested - self.df_contacts["time_contact"]) <= last_contact_days, "unique_id"].unique()
            for other_agent in self.model.schedule.agent_buffer(shuffled=False):
                if (other_agent.unique_id in list(ids_contact)) & (not other_agent.quarantine):
                    if self.model.random.randrange(0, 100) < self.model.participation_tracing:
                        other_agent.testing(reason="risk_contact")
                        other_agent.enforce_quarantine(10)

            if not self.quarantine:
                self.enforce_quarantine(10)

    def trace_contact(self, distance_tracking) -> None:
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

    def move_to_random_position(self) -> None:
        """
        Moves this agent to a random position on the grid. Note that only 'valid' positions are considered
        (see RoomGrid#is_available(int, int, False).
        """
        (pos_x, pos_y) = self.model.grid.get_random_pos(self.random, in_break_room=self.room is None)

        # If the agent doesn't exist on the grid at the moment, place them.
        # Otherwise, move them. This is required, because move has to remove the agent
        # From the grid in the old position, which will cause an NPE if it doesn't exist.
        if self.pos is None:
            self.model.grid.place_agent(self, (pos_x, pos_y))
        else:
            self.model.grid.move_agent(self, (pos_x, pos_y))

    def do_rooster_step(self, room_rooster_id: int) -> None:
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

    def step(self) -> None:
        """
        Executes a single step in the model for this agent.
        """
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

        if self.model.choice_of_measure == 'contact_tracing':
            self.trace_contact(self.model.distance_tracking)
        self.day_time += 1


class VirusModel(Model):
    """
    This is a model that simulates the spread of Covid-19 in the setting of a university building.

    It was developed by Sharif Hamed, Jonas Schweisthal, Leanne de Vree, and Pim van der Loos for the 2020/2021 RUG course Design of Multi-Agent Systems.
    
    """

    def __init__(self, num_agents: int, grid_width: int, grid_height: int, base_infection_rate: float,
                 spread_distance: int, spread_chance: int, daily_testing_chance: int, choice_of_measure: str,
                 test_delay: int, participation_tracing: int, last_contact_days: int, distance_tracking: int,
                 seed: int = None, grid_canvas: Optional[CanvasRoomGrid] = None,
                 server: Optional[CustomModularServer] = None,
                 room_count: int = 10, room_size: int = 15, break_room_size: int = 20, *args, **kwargs):
        """
        Initializes a new Virus Model.

        :param num_agents: The number of agents that will participate in the model.
        :param grid_width: The width of the grid.
        :param grid_height: The height of the grid.
        :param base_infection_rate: The percentage of agents starting with the infection.
        :param spread_distance: The distance the virus can spread to other agents.
        :param spread_chance: The probability of the virus spreading to nearby agents after 1 tick (15 min).
        :param daily_testing_chance: The probability of an agent being tested at the start of each day.
        :param choice_of_measure: Which measures to enable to attempt to prevent the spread of the virus.
        :param test_delay: The number of days it takes to get the result of a test.
        :param seed: The seed to use for the random module. This can be a numerical value or None (default).
        None means that the random module will be random.
        """
        super().__init__(*args, **kwargs)
        if seed is not None:
            self.random = random.Random(seed)

        self.grid_canvas = grid_canvas

        self.num_agents = num_agents
        self.base_infection_rate = base_infection_rate
        """
        Describes the chance of an agent being infected at the start of the model
        """

        self.test_delay = test_delay
        """
        The number of days after an agent was tested the test results are available.
        """

        self.spread_distance = spread_distance
        self.spread_chance = spread_chance
        """
        Describes the chance of the virus spreading to another agent. Applied every step.
        """
        self.participation_tracing = participation_tracing
        self.last_contact_days = last_contact_days

        self.schedule = RandomActivation(self)
        self.grid = RoomGrid(grid_width, grid_height, False, room_count=room_count,
                             room_size=room_size, break_room_size=break_room_size)

        if self.grid_canvas is not None and server is not None:
            new_width, new_height = self.grid.get_total_dimensions()
            print("new width: {}, new height: {}".format(new_width, new_height))
            self.grid_canvas.update_dimensions(server, new_width, new_height)

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
        self.distance_tracking = distance_tracking

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
                             "tested total": get_tested_count, "tested pending": get_tested_pending_count,
                             "tested positive": get_tested_positive_count,
                             "tested negative": get_tested_negative_count})

    def set_day_step(self) -> None:
        """
        Updates the 'day_step' variable, so it gets the number of steps
        that have passed for the current day (so the time of day).
        """
        self.day_step = (self.total_steps % DAY_DURATION)

    def clear_rooms(self) -> None:
        """
        Resets all the seats in all the rooms back to 'available'.
        """
        for room in self.grid.rooms_list:
            for seat in room.seats:
                seat.available = True

    def next_day(self) -> None:
        """
        Handles the start of a new day.
        """
        self.rooster_model.make_day_rooster()
        self.day = int(self.schedule.steps / DAY_DURATION)
        for agent in self.schedule.agent_buffer(shuffled=False):
            agent.new_day(self.day)

        self.virtual_steps = self.day * NIGHT_DURATION
        print("NEXT DAY: {}".format(self.day))

    def step(self) -> None:
        """
        Executes a step for the model.
        """
        self.clear_rooms()
        self.set_day_step()
        self.datacollector.collect(self)
        if self.schedule.steps % DAY_DURATION == 0:
            self.next_day()

        # Skip weekends
        if self.day % 7 > 4:
            self.schedule.steps += DAY_DURATION
            return  # Just return, everything will be updated on the next call

        '''Advance the model by one step.'''
        self.schedule.step()

        self.total_steps = self.schedule.steps + self.virtual_steps


def agent_portrayal(agent: VirusAgent):
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
def get_infection_rate(model: VirusModel) -> int:
    return int(np.sum([agent.virus.is_infected() for agent in model.schedule.agents]))


def get_death_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.DECEASED for agent in model.schedule.agents]))


def get_quarantined_count(model: VirusModel) -> int:
    return int(np.sum([agent.quarantine for agent in model.schedule.agents]))


def get_healty_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.HEALTHY for agent in model.schedule.agents]))


def get_recovered_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.RECOVERED for agent in model.schedule.agents]))


def get_infected_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.INFECTED for agent in model.schedule.agents]))


def get_testable_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.TESTABLE for agent in model.schedule.agents]))


def get_infectious_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.INFECTIOUS for agent in model.schedule.agents]))


def get_symptomatic_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus.disease_state == DiseaseState.SYMPTOMATIC for agent in model.schedule.agents]))


def get_tested_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus_test.get_test_stats().get_total_count() for agent in model.schedule.agents]))


def get_tested_pending_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus_test.get_test_stats().get_pending_count() for agent in model.schedule.agents]))


def get_tested_positive_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus_test.get_test_stats().get_positive_count() for agent in model.schedule.agents]))


def get_tested_negative_count(model: VirusModel) -> int:
    return int(np.sum([agent.virus_test.get_test_stats().get_negative_count() for agent in model.schedule.agents]))


def get_quarantined_infected(model: VirusModel) -> int:
    return int(np.sum([agent.quarantine & (agent.virus.is_infected()) for agent in model.schedule.agents]))


def get_quarantined_healthy(model: VirusModel) -> int:
    return int(
        np.sum([agent.quarantine & (not agent.virus.is_infected()) for agent in model.schedule.agents]))


def get_notquarantined_infected(model: VirusModel) -> int:
    return int(np.sum([(agent.quarantine is False) & (agent.virus.is_infected()) for agent in model.schedule.agents]))


disease_states = [DiseaseState.DECEASED, DiseaseState.HEALTHY, DiseaseState.RECOVERED, DiseaseState.INFECTED,
                  DiseaseState.TESTABLE, DiseaseState.INFECTIOUS, DiseaseState.SYMPTOMATIC]


class TimeElement(TextElement):
    def __init__(self):
        super().__init__()

    def render(self, model: VirusModel) -> str:
        days = 1 + int(model.total_steps / 96)
        hours = 9 + int((model.total_steps % 96) / 4)
        quarters = 15 * (model.total_steps % 4)

        if quarters == 0:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters) + "0"
        else:
            return "Day: " + str(days) + ", Time: " + str(hours) + ":" + str(quarters)

class PlotTitle1(TextElement):
    def __init__(self):
        super().__init__()
        
    def render(self, model: VirusModel) -> str:
        return "<br><b>Total infections, deaths and quarantined</b>"
        
class PlotTitle2(TextElement):
    def __init__(self):
        super().__init__()
        
    def render(self, model: VirusModel) -> str:
        return "<br><b>Progression of disease states</b>"
    
class PlotTitle3(TextElement):
    def __init__(self):
        super().__init__()
        
    def render(self, model: VirusModel) -> str:
        return "<br><b>Progression of quarantined agents</b>"

class PlotTitle4(TextElement):
    def __init__(self):
        super().__init__()
        
    def render(self, model: VirusModel) -> str:
        return "<br><b>Performed tests</b>"

time_element = TimeElement()
plot_title1 = PlotTitle1()
plot_title2 = PlotTitle2()
plot_title3 = PlotTitle3()
plot_title4 = PlotTitle4()


DEFAULT_GRID_WIDTH = 100
DEFAULT_GRID_HEIGHT = 100
DEFAULT_NUM_AGENTS = 800
DEFAULT_MITIGATION = 'no_measures'
DEFAULT_BASE_INFECTION_RATE = 3
DEFAULT_ROOM_SIZE = 15
DEFAULT_ROOM_COUNT = 10
DEFAULT_BREAK_ROOM_SIZE = 32
DEFAULT_SPREAD_DISTANCE = 2
DEFAULT_SPREAD_CHANCE = 10
DEFAULT_DAILY_TEST_CHANCE = 5
DEFAULT_TEST_DELAY = 2
DEFAULT_RANDOM_SEED = None
DEFAULT_PARTICIPATION_TRACING = 40
DEFAULT_LAST_CONTACT_DAYS = 14
DEFAULT_DISTANCE_TRACKING = 2

# Includes adjustable sliders for the user in the visualization
model_params = {
    "Description": UserSettableParameter('static_text',
                                         value="This simulation model represents a university building in "
                                               "which agents (students) attend lectures in classrooms. It "
                                               "simulates the spread of a virus in the building. The plots "
                                               "below the main visualization show the spread of the virus. "
                                               "<br>The simulation allows for testing the situation without measures "
                                               "and with contact tracing on, meaning that not only "
                                               "positively tested agents but also contacts of those infected "
                                               "agents will be put into quarantine (removed from the simulation). "
                                               "<br>Please see the readme file and our report for more details."),
    "static_text": UserSettableParameter('static_text',
                                         value="The options below allow you to adjust the parameter settings. "
                                               "After setting the options to the desired values, "
                                               "click 'Reset' and restart the simulation."),
    "choice_of_measure": UserSettableParameter('choice', 'Mitigation measure applied', value=DEFAULT_MITIGATION,
                                               choices=['no_measures', 'contact_tracing']),
    # "contacttracing_option": UserSettableParameter('checkbox', 'Measure: Contact Tracing', value=True),
    "num_agents": UserSettableParameter("slider", "Number of agents", DEFAULT_NUM_AGENTS, 10, 1000, 10),
    "grid_width": DEFAULT_GRID_WIDTH,
    "grid_height": DEFAULT_GRID_HEIGHT,
    "test_delay": DEFAULT_TEST_DELAY,
    "seed": DEFAULT_RANDOM_SEED,
    "room_size": UserSettableParameter("slider", "Room size",
                                       DEFAULT_ROOM_SIZE, 5, 40, 1),
    "room_count": UserSettableParameter("slider", "Room count",
                                        DEFAULT_ROOM_COUNT, 1, 20, 1),
    "break_room_size": UserSettableParameter("slider", "break room size",
                                             DEFAULT_BREAK_ROOM_SIZE, 5, 80, 1),
    "base_infection_rate": UserSettableParameter("slider", "Base infection rate (%)",
                                                 DEFAULT_BASE_INFECTION_RATE, 0, 100, 0.1),
    "spread_distance": UserSettableParameter("slider", "Spread distance (in meters)",
                                             DEFAULT_SPREAD_DISTANCE, 1, 10, 1),
    "spread_chance": UserSettableParameter("slider", "Spread probability", DEFAULT_SPREAD_CHANCE, 1, 100, 1),
    "daily_testing_chance": UserSettableParameter("slider", "Daily probability of getting tested per agent",
                                                  DEFAULT_DAILY_TEST_CHANCE, 1, 100, 1),
    "participation_tracing": UserSettableParameter("slider", "Proportion of tracing participation",
                                                   DEFAULT_PARTICIPATION_TRACING, 1, 100, 1),
    "last_contact_days": UserSettableParameter("slider", "Number of Days for tracing last contact",
                                               DEFAULT_LAST_CONTACT_DAYS, 1, 14, 1),
    "distance_tracking": UserSettableParameter("slider", "Radius of tracing contacts (in meters)",
                                               DEFAULT_DISTANCE_TRACKING, 1, 5, 1),

    "legend": UserSettableParameter('static_text',
                                    value="<b>Legend</b> <br> "
                                          "<style>"
                                          "span {"
                                          "    font-size: 16px;"
                                          "    font-weight: bold;"
                                          "}"
                                          ".well {"
                                          "    background-image: linear-gradient(to bottom,#dbdbdb 0,#dbdbdb 100%)"
                                          "}"
                                          "</style>"
                                          "<span style=color:rgba(43,200,0,1);>Green</span> dot: healthy agent. <br> "
                                          "<span style=color:blue;>Blue</span> dot: infected agent. <br> "
                                          "<span style=color:red;>Red</span> dot: infectious agent. <br> "
                                          "<span style=color:rgba(255,0,212,1);>Bright purple</span> dot: testable agent. <br> "
                                          "<span style=color:rgba(102,0,0,1);>Dark red</span> dot: symptomatic agent. <br> "
                                          "<span style=color:rgba(8,323,222,1);>Bright turquoise</span> dot: recovered agent. <br> "
                                          "<span style=color:rgba(0,0,0,0.65);>Grey</span> square: wall. <br> "
                                          "<span style=color:rgba(99,44,4,0.4);>Brown</span> square: classroom seat. <br> "
                                          "<span style=color:white>White</span> square: space where the agent can move. ")
}


def create_canvas_room_grid(width: int = DEFAULT_GRID_WIDTH, height: int = DEFAULT_GRID_HEIGHT) -> CanvasRoomGrid:
    """
    Creates a new `CanvasRoomGrid`.

    :param width: The initial width of the grid.
    :param height:  The initial height of the grid.
    :return: The newly created `CanvasRoomGrid`
    """
    return CanvasRoomGrid(agent_portrayal, width, height, 900, 900)
