from random import seed, Random
from unittest import TestCase

from virus import Virus
from virus_test import TestResult, TestOutcome, RESULT_ACTIVE_DAY, VirusTest


# Perhaps this could have a better name? Can't be worse, I guess.
class TestTestResult(TestCase):
    def setUp(self):
        self.result_day = 20
        self.test_result = TestResult(TestOutcome.POSITIVE, self.result_day)


class TestGetResults(TestTestResult):
    def test_too_early(self):
        assert self.test_result.get_result(self.result_day - RESULT_ACTIVE_DAY - 1) == TestOutcome.UNTESTED

    def test_lower_bound(self):
        assert self.test_result.get_result(self.result_day) == TestOutcome.POSITIVE

    def test_upper_bound(self):
        assert self.test_result.get_result(self.result_day + RESULT_ACTIVE_DAY) == TestOutcome.POSITIVE

    def test_too_old(self):
        assert self.test_result.get_result(self.result_day + RESULT_ACTIVE_DAY + 1) == TestOutcome.UNTESTED


class TestVirusTest(TestCase):
    def setUp(self):
        self.result_delay = 7
        self.random = Random()
        self.random.randrange(1, 2)
        seed(1)
        self.false_negative_rate = 0
        self.false_positive_rate = 0
        self.virus_test = VirusTest(result_delay=self.result_delay, random=self.random,
                                    false_negative_rate=self.false_negative_rate,
                                    false_positive_rate=self.false_positive_rate)
        self.virus_positive = Virus(self.random, 100)
        self.virus_negative = Virus(self.random, 0)


def skip_to_day(virus_test: VirusTest, current, goal):
    """
    Skips to a given day for the virus test.
    :param virus_test: The VirusTest object to progress to the given day.
    :param current: The current day.
    :param goal: The goal day (inclusive).
    """
    for day in range(current, goal + 1):
        virus_test.new_day(day)


class TestDayProgression(TestVirusTest):
    def test_perform_test(self):
        self.virus_test.perform_test(0, self.virus_negative)
        self.virus_test.perform_test(7, self.virus_positive)
        self.virus_test.perform_test(9, self.virus_positive)

    def test_new_day(self):
        assert self.virus_test.get_result(0) == TestOutcome.UNTESTED

        invalidation_delay = self.virus_test.result_delay + RESULT_ACTIVE_DAY
        """
        The number of days after a test was performed after which the test is no longer valid.
        """

        empty_day = 2 + invalidation_delay + 1
        """
        A day some time after the test performed on day 2 where no tests will be active.
        """

        self.virus_test.perform_test(0, self.virus_negative)
        self.virus_test.perform_test(2, self.virus_positive)
        self.virus_test.perform_test(empty_day + 1, self.virus_positive)

        # UNTESTED, because the delay is 7 days.
        assert self.virus_test.get_result(0) == TestOutcome.UNTESTED

        # NEGATIVE, because after 7 days, the result is finally known.
        skip_to_day(self.virus_test, 0, 7)
        assert self.virus_test.get_result(7) == TestOutcome.NEGATIVE

        # POSITIVE, because there was a test with a positive result on the second day.
        skip_to_day(self.virus_test, 8, 9)
        assert self.virus_test.get_result(9) == TestOutcome.POSITIVE

        # UNTESTED, because the result is invalidated on the 'empty day'.
        skip_to_day(self.virus_test, 8, empty_day)
        assert self.virus_test.get_result(empty_day) == TestOutcome.UNTESTED

        # POSITIVE, because of the test performed the day after the `empty_day`
        skip_to_day(self.virus_test, empty_day, empty_day + 1 + self.result_delay)
        assert self.virus_test.get_result(empty_day + 1 + self.result_delay) == TestOutcome.POSITIVE
