from enum import Enum
from numbers import Number
from random import Random

from virus import Virus

RESULT_ACTIVE_DAY = 7
"""
The number of days a result remains active. If no new results are available and the last test was more than this number
of days ago, the result will return UNTESTED.
"""


class TestOutcome(Enum):
    UNTESTED = 1,
    """
    The agent has not yet been tested. 
    """

    POSITIVE = 2,
    """
    The result of the test indicates that the agent is infected with the virus.
    """

    NEGATIVE = 3
    """
    The result of the test indicates that the agent is not infected with the virus.
    """


class TestResult:
    def __init__(self, test_outcome: TestOutcome, result_day: Number):
        """
        Creates a new TestResult.

        :param test_outcome: The outcome of the test. Should be either positive or negative.
        :param result_day: The day on which the result is publicized. Before this day, the outcome cannot be accessed.
        """
        self.__test_outcome = test_outcome
        self.__result_day = result_day

    def get_result(self, day) -> TestOutcome:
        """
        Gets the outcome of this test if it is available, otherwise, it'll return `TestOutcome.UNTESTED`.

        :param day: The day on which to retrieve the test result.
        :return: The outcome of the result if that is available, otherwise `TestOutcome.UNTESTED`.
        """
        return TestOutcome.UNTESTED if day >= self.__result_day else self.__test_outcome


class VirusTest:
    def __init__(self, result_delay: Number, random: Random, false_negative_rate=0, false_positive_rate=0):
        """
        Creates a new VirusTest object. This object allows you to create new tests and obtain their results.

        :param result_delay: The number of days between performing a test and its result being available.
        :param false_negative_rate: The rate of false negatives.
        :param false_positive_rate: The rate of false positives.
        """
        self.result_delay = result_delay
        self.random = random
        self.false_negative_rate = false_negative_rate
        self.false_positive_rate = false_positive_rate
        self.__test_results = []

    def new_day(self, day):
        """
        Handles the start of a new day.

        :param day: The number of the new day.
        """
        self.__test_results = [result for result in self.__test_results if result.day >= (day - RESULT_ACTIVE_DAY)]

        start = 0
        """
        The first index to keep in the list. For example, when set to 1, only index 0 will be removed.
        """
        invalid_day = day - RESULT_ACTIVE_DAY
        """
        The day after which the result is no longer valid.
        """
        result_day = day - self.result_delay
        """
        The day on which the result is published.
        """
        for idx in range(0, len(self.__test_results)):
            test_result = self.__test_results[idx]
            # Remove any tests that are no longer useful.
            if test_result.day < invalid_day:
                start = idx
                continue

            # Always get the latest valid result.
            if test_result.day >= result_day:
                start = idx
        self.__test_results = self.__test_results[start:]

    def get_result(self, day) -> TestOutcome:
        """
        Gets the result of the latest test if one is available on this day. (It might not be because of delays).

        :param day: The number of the new day.
        :return: The `TestOutcome` associated with the current status of the tests.
        """
        if len(self.__test_results) > 0:
            return self.__test_results[0].get_result(day)
        return TestOutcome.UNTESTED

    def do_test(self, day, virus_state: Virus):
        """
        Performs a test using a given `Virus` object.

        :param day: The number of the day.
        :param virus_state: The `Virus` to test.
        """
        if virus_state.is_infected():
            # If the actual virus status is positive, check against the false negative rate.
            if self.random.randrange(0, 100) < self.false_negative_rate:
                test_outcome = TestOutcome.NEGATIVE
            else:
                test_outcome = TestOutcome.POSITIVE
        else:
            # If the actual virus status is negative, check against the false positive rate.
            if self.random.randrange(0, 100) < self.false_positive_rate:
                test_outcome = TestOutcome.POSITIVE
            else:
                test_outcome = TestOutcome.NEGATIVE

        self.__test_results.append(TestResult(test_outcome, day + self.result_delay))
