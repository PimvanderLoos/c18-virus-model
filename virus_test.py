from enum import Enum
from random import Random

from typing import List

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
    def __init__(self, test_outcome: TestOutcome, result_day: int):
        """
        Creates a new TestResult.

        :param test_outcome: The outcome of the test. Should be either positive or negative.
        :param result_day: The day on which the result is publicized. Before this day, the outcome cannot be accessed.
        """
        self.__test_outcome = test_outcome
        self.__result_day = result_day

    def get_result(self, day: int) -> TestOutcome:
        """
        Gets the outcome of this test if it is available, otherwise, it'll return `TestOutcome.UNTESTED`.

        :param day: The day on which to retrieve the test result.
        :return: The outcome of the result if that is available, otherwise `TestOutcome.UNTESTED`.
        """
        if self.__result_day <= day <= (self.__result_day + RESULT_ACTIVE_DAY):
            return self.__test_outcome

        return TestOutcome.UNTESTED

    def get_raw_result(self) -> TestOutcome:
        """
        Gets the raw outcome of this test, disregarding any delays.

        :return: The outcome of this test.
        """
        return self.__test_outcome

    def get_result_day(self) -> int:
        """
        Gets the day on which the result of the test will become available.

        :return: The number of the day on which the test result will be available.
        """
        return self.__result_day


class TestStatistics:
    """
    This class keeps track of all the tests that have been performed for the entire duration of the model.
    """
    def __init__(self):
        self.__total = 0
        self.__positive = 0
        self.__negative = 0
        self.__pending = 0

    def add_test_result(self, outcome: TestOutcome) -> None:
        """
        Adds the result of a test to the statistics.

        When adding a result, the number of pending results is decremented,
        so make that that the result was be registered first.

        :param outcome: The result of the test.
        """
        if outcome == TestOutcome.POSITIVE:
            self.__positive += 1
        elif outcome == TestOutcome.NEGATIVE:
            self.__negative += 1
        else:
            raise ValueError("Trying to add test statistic for untested result. This is invalid.")
        self.__pending -= 1

    def register_new_result(self) -> None:
        """
        Registers a new result. Registering simply means added the result as pending.
        """
        self.__pending += 1
        self.__total += 1

    def get_pending_count(self) -> int:
        """
        Gets the number of tests whose results are not yet available.

        :return: The number of tests whose results are not yet available.
        """
        return self.__pending

    def get_total_count(self) -> int:
        """
        Gets the total number of tests performed on this VirusTest far.

        This includes the tests whose result is not known yet.

        :return: The total number of tests performed on this VirusTest far.
        """
        return self.__total

    def get_positive_count(self) -> int:
        """
        Gets the total number of tests that returned a positive (= infected) result so far.

        :return: The total number of tests that returned a positive result so far.
        """
        return self.__positive

    def get_negative_count(self) -> int:
        """
        Gets the total number of tests that returned a negative (= not infected) result so far.

        :return: The total number of tests that returned a negative result so far.
        """
        return self.__negative


class VirusTest:
    def __init__(self, result_delay: int, random: Random, false_negative_rate: int = 0, false_positive_rate: int = 0):
        """
        Creates a new VirusTest object. This object allows you to create new tests and obtain their results.

        :param result_delay: The number of days between performing a test and its result being available.
        :param false_negative_rate: The rate of false negatives. 0 (disabled) by default.
        :param false_positive_rate: The rate of false positives. 0 (disabled) by default.
        """
        self.result_delay = result_delay
        self.random = random
        self.false_negative_rate = false_negative_rate
        self.false_positive_rate = false_positive_rate
        self.__test_queue: List[TestResult] = []
        self.test_stats = TestStatistics()

    def new_day(self, day: int) -> None:
        """
        Handles the start of a new day.

        :param day: The number of the new day.
        """
        start = 0
        """
        The first index to keep in the list. For example, when set to 1, only index 0 will be removed.
        """
        invalidation_day = day - RESULT_ACTIVE_DAY
        """
        The day after which the result is no longer valid.
        """

        for idx in range(0, len(self.__test_queue)):
            test_result = self.__test_queue[idx]
            test_result_day = test_result.get_result_day()

            if self.result_delay > 0 and test_result_day == day:
                self.test_stats.add_test_result(test_result.get_raw_result())

            # Remove any tests that are no longer useful.
            if test_result_day < invalidation_day:
                start = idx + 1
                continue

            # Always get the latest valid result.
            if test_result_day <= day:
                start = idx
        self.__test_queue = self.__test_queue[start:]

    def get_result(self, day: int) -> TestOutcome:
        """
        Gets the result of the latest test if one is available on this day. (It might not be because of delays).

        :param day: The number of the new day.
        :return: The `TestOutcome` associated with the current status of the tests.
        """
        if len(self.__test_queue) > 0:
            return self.__test_queue[0].get_result(day)
        return TestOutcome.UNTESTED

    def perform_test(self, day: int, virus_state: Virus) -> None:
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

        self.test_stats.register_new_result()
        if self.result_delay == 0:
            self.test_stats.add_test_result(test_outcome)

        self.__test_queue.append(TestResult(test_outcome, day + self.result_delay))

    def get_test_queue_size(self) -> int:
        """
        Gets the number of tests queued up.

        Whether or not a test is in the queue doesn't say anything about whether or not its result is known;
        It merely means that the result is available right now or will be at some point in the future.

        :return: The number of tests currently queued up.
        """
        return len(self.__test_queue)

    def get_test_stats(self) -> TestStatistics:
        """
        Gets the statistics of the tests performed so far.

        :return: The statistics object containing all info regarding the number of tests performed so far as well as
        their outcomes.
        """
        return self.test_stats
