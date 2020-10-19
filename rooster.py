from typing import Optional

from room_grid import *

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

    def new_day(self, day_duration: int, model):
        # pass
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

    def get_available_room(self, model) -> Optional[LectureRoom]:
        for room in self.model.grid.rooms_list:
            if room.room_available():
                return room
        return None

    def get_seat(self, room) -> Optional[Seat]:
        for seat in room.seats:
            if seat.available:
                return seat
        return None


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

    def get_random_room_id(self) -> Tuple[int, Optional[LectureRoom]]:
        room_id = self.model.random.randrange(self.model.grid.room_count + 1)
        if room_id == self.break_room_id:
            return room_id, None

        room = self.model.grid.rooms_list[room_id]

        if not room.room_available():
            return self.get_random_room_id()

        room.is_reserved = True
        return room_id, room

    def make_day_rooster(self):
        rooster = self.rooster
        for agent_id in range(rooster.shape[1]):

            lectures = 0
            breaks = 0

            for timeslot in range(0, rooster.shape[0], DAY_PART_DURATION):
                for schedule_id in range(self.model.grid.room_count):
                    room_id, room = self.get_random_room_id()
                    room_capacity = 999999 if room is None else room.get_capacity()

                    if room_id != self.break_room_id and lectures < 3 and (rooster[timeslot, :] == room_id).sum() < room_capacity:
                        rooster[timeslot:timeslot+DAY_PART_DURATION, agent_id] = room_id
                        lectures += 1
                        break

                    if breaks < 1 and room_id == self.break_room_id:
                        rooster[timeslot:timeslot+DAY_PART_DURATION, agent_id] = room_id
                        breaks += 1
                        break
