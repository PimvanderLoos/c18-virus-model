from enum import Enum
from functools import total_ordering

DISEASE_PROGRESSION_TO_TESTABLE = 4
"""
The number of days after the initial infection after which an agent shows up positive on tests.
(See: `Virus.DiseaseState.TESTABLE`).
"""

DISEASE_PROGRESSION_TO_INFECTIOUS = 1
"""
The number of days after an agent became testable (see: `DISEASE_PROGRESSION_TO_TESTABLE`) after which an agent becomes
infectious. (See: `Virus.DiseaseState.INFECTIOUS`).
"""

DISEASE_PROGRESSION_TO_SYMPTOMATIC = 3
"""
The number of days after an agent became infectious (see: `DISEASE_PROGRESSION_TO_INFECTIOUS`) after which an agent
becomes symptomatic. (See: `Virus.DiseaseState.SYMPTOMATIC`).
"""

DISEASE_PROGRESSION_TO_OUTCOME = 7
"""
The number of days after an agent became symptomatic (see: `DISEASE_PROGRESSION_TO_SYMPTOMATIC`) after which an agent
either dies or recovers.
"""

RECOVERY_COOLDOWN = 9999
"""
The number of days after which an agent recovered from the disease after which they can get infected again.
"""

DISEASE_LETHALITY = 1
"""
The lethality of the virus, expressed as a percentage (0 - 100) of agents that will die after being infected.
"""


class Virus:
    def __init__(self, random, base_infection_chance):
        """
        Create a new Virus object for an agent. Note that this doesn't immediately mean that the agent is infected.
        It only means that they can be infected.

        :param random: The random instance to use for randomization.
        :param base_infection_chance: The base change (percentage between 0 and 100) that the agent starts with an
        infection.
        """
        self.random = random
        if random.randrange(0, 100) < base_infection_chance:
            self.disease_state = DiseaseState.INFECTIOUS
        else:
            self.disease_state = DiseaseState.HEALTHY

        self.__next_disease_update = self.__get_next_update()
        """
        Describes the day on which the next update to the disease stage will be applied.
        """

    def is_infectious(self):
        """
        Checks if the current state of the disease can spread the disease to other agents.

        :return: True if the disease in its current state can spread to other agents.
        """
        return self.disease_state >= DiseaseState.INFECTIOUS

    def is_infected(self):
        """
        Checks if the owner of this Virus is currently infected or not.

        Note that this includes all states greater than INFECTED as well (e.g. SYMPTOMATIC).

        :return: True if the owner of this Virus is infected.
        """
        return self.disease_state >= DiseaseState.INFECTED

    def is_testable(self):
        """
        Checks if the agent can show up on tests.

        :return: True if the agent can be tested.
        """
        return self.disease_state >= DiseaseState.TESTABLE

    def handle_disease_progression(self, day):
        """
        Handles the disease progression for this agent. If they are not at least infected, nothing happens.

        However, if they are infected, they might move up on the disease progression, based on the time.

        :param day: The current day.
        """
        if self.disease_state < DiseaseState.INFECTED:
            return

        if day >= self.__next_disease_update:
            self.__go_to_next_state(day)

    def __go_to_next_state(self, day):
        """
        Advances the disease to the next stage.
        """
        if self.disease_state is DiseaseState.DECEASED:
            return

        if self.disease_state is DiseaseState.SYMPTOMATIC:
            if self.random.randrange(0, 100) < DISEASE_LETHALITY:
                self.disease_state = DiseaseState.DECEASED
            else:
                self.disease_state = DiseaseState.HEALTHY
                self.__set_stage(DiseaseState.RECOVERED, day)
        else:
            self.__set_stage(self.disease_state.next(), day)

    def __set_stage(self, new_state, day):
        """
        Updates the current stage to the defined stage.

        :param new_state: The new state of the disease.
        :param day: The day on which this is applied.
        """
        self.disease_state = new_state
        self.__next_disease_update = day + self.__get_next_update()

    def __get_next_update(self):
        if self.disease_state < DiseaseState.INFECTED:
            return 9999

        if self.disease_state is DiseaseState.INFECTED:
            return DISEASE_PROGRESSION_TO_TESTABLE
        elif self.disease_state is DiseaseState.TESTABLE:
            return DISEASE_PROGRESSION_TO_INFECTIOUS
        elif self.disease_state is DiseaseState.INFECTIOUS:
            return DISEASE_PROGRESSION_TO_SYMPTOMATIC
        elif self.disease_state is DiseaseState.SYMPTOMATIC:
            return DISEASE_PROGRESSION_TO_OUTCOME
        elif self.disease_state is DiseaseState.RECOVERED:
            return RECOVERY_COOLDOWN
        else:
            return 9999

    def infect(self, infection_chance, day):
        """
        Attempts to infect the agent.

        :param infection_chance: The chance of the infection being spread.
        :param day: The day on which the infection takes place.
        """
        if self.disease_state >= DiseaseState.INFECTED or self.disease_state is DiseaseState.DECEASED:
            return

        if self.disease_state == DiseaseState.RECOVERED and day < self.__next_disease_update:
            return

        if self.random.randrange(0, 100) < infection_chance:
            self.__set_stage(DiseaseState.INFECTED, day)


@total_ordering
class DiseaseState(Enum):
    """
    Represents the various stages of the virus we are modeling. Starting at `DiseaseState.INFECTED`, higher values
    indicate increase further disease progression.
    """

    DECEASED = 1
    """
    This represents the state of the agent where they died from the virus.
    """

    HEALTHY = 2
    """
    This represents the state of the agent where they are completely healthy in regards to this specific virus.
    """

    RECOVERED = 3
    """
    This represents the state of the agent where they recovered after having had the virus.
    """

    INFECTED = 4
    """
    This represents the state of the agent where they have been infected with the virus, but they cannot spread it
    further, nor does it show up in tests.
    """

    TESTABLE = 5
    """
    This represents the state of the agent where they have been infected with the virus, but they cannot spread it
    further. However, it will show up in tests.
    """

    INFECTIOUS = 6
    """
    This represents the state of the agent where they have been infected with the virus and they can spread it to other
    agents. However, they don't show any symptoms yet.
    """

    SYMPTOMATIC = 7
    """
    This represents the state of the agent where they are showing symptoms of the virus.
    """

    def next(self):
        new = self.value + 1
        if new > 7:
            raise ValueError('Enumeration ended')
        return DiseaseState(new)

    def previous(self):
        new = self.value - 1
        if new < 1:
            raise ValueError('Enumeration ended')
        return DiseaseState(new)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
