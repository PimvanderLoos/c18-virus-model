from mesa.space import MultiGrid
import math
from enum import Enum
import numpy as np


def get_square():
    portrayal = {"Shape": "rect",
                 "w": 1,
                 "h": 1,
                 "Filled": "true",
                 "r": 0.5,
                 "Layer": 0}
    return portrayal


def seat_portrayal():
    portrayal = get_square()
    portrayal["Color"] = "brown"
    return portrayal


def wall_portrayal():
    portrayal = get_square()
    portrayal["Color"] = "grey"
    return portrayal


class Side(Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


class Seat:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.available = True


class LectureRoom:
    def __init__(self, room_id, x_min, y_min, x_max, y_max, entry_side, entry_side_offset=2):
        """
        :param room_id: The unique ID of this room.
        :param x_min: The lower bound x-coordinate of this room (includes the wall!)
        :param y_min: The lower bound y-coordinate of this room (includes the wall!)
        :param x_max: The upper bound x-coordinate of this room (includes the wall!)
        :param y_max: The upper bound y-coordinate of this room (includes the wall!)
        :param entry_side: On which side of the room to make the entry. This can be any one of the "Side" enum.
        :param entry_side_offset: The number of squares to leave empty on the entry side (where the lecturer would stand).
        """
        self.room_id = room_id
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
        self.entry_side = entry_side

        if entry_side == Side.NORTH:
            self.x_entry = x_min + math.floor((x_max - x_min) / 2)
            self.y_entry = y_max
        elif entry_side == Side.EAST:
            self.x_entry = x_max
            self.y_entry = y_min + math.floor((y_max - y_min) / 2)
        elif entry_side == Side.SOUTH:
            self.x_entry = x_min + math.floor((x_max - x_min) / 2)
            self.y_entry = y_min
        elif entry_side == Side.WEST:
            self.x_entry = x_min
            self.y_entry = y_min + math.floor((y_max - y_min) / 2)

        x_min_seat_offset = entry_side_offset if self.entry_side == Side.WEST else 0
        y_min_seat_offset = entry_side_offset if self.entry_side == Side.SOUTH else 0
        x_max_seat_offset = entry_side_offset if self.entry_side == Side.EAST else 0
        y_max_seat_offset = entry_side_offset if self.entry_side == Side.NORTH else 0

        self.x_min_seat = self.x_min + 1 + x_min_seat_offset
        self.x_max_seat = self.x_max - 1 - x_max_seat_offset
        self.y_min_seat = self.y_min + 1 + y_min_seat_offset
        self.y_max_seat = self.y_max - 1 - y_max_seat_offset

        self.seats = []
        self.populate_seats()

    def is_in_room(self, x, y):
        """
        Checks if a given coordinate pair is inside this room. Note that this does NOT include the walls!
        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: True if the given coordinate pair lies within the usable area of the room.
        """
        return self.x_min < x < self.x_max and self.y_min < y < self.y_max

    def populate_seats(self):
        for x in range(self.x_min_seat, self.x_max_seat):
            for y in range(self.y_min_seat, self.y_max_seat):
                self.seats.append(Seat(x, y))

    def is_wall(self, x, y):
        if x == self.x_entry and y == self.y_entry:
            return False
        if x > self.x_max or x < self.x_min or y > self.y_max or y < self.y_min:
            return False
        return x == self.x_min or x == self.x_max or y == self.y_min or y == self.y_max

    def is_seat(self, x, y):
        return self.x_min_seat < x < self.x_max_seat and self.y_min_seat < y < self.y_max_seat

    def get_seat(self, x, y):
        for seat in self.seats:
            if seat.x == x and seat.y == y:
                return seat
        return None

    def get_portrayal(self, x, y):
        if self.is_wall(x, y):
            return wall_portrayal()
        if self.is_seat(x, y):
            return seat_portrayal()
        return None


class RoomGrid(MultiGrid):
    def __init__(self, width: int, height: int, torus: bool, room_count=20, room_size=15):
        """
         :param room_count: The number of rooms (excluding break room).
         :param room_size: The size of each regular room (excluding break room).
                    This value describes the length of any one of its walls, as it's a square.
                    This describes the usable area of the each room, so walls are not included.
        """
        super().__init__(width, height, torus)
        self.room_count = room_count
        self.room_size = room_size + 1  # Add 1 to account for the walls.
        self.room_row_size = math.ceil(math.sqrt(room_count))
        self.rooms = np.empty((self.room_row_size, self.room_row_size), dtype=LectureRoom)
        self.rows = np.empty(self.room_row_size, dtype=object)
        self.generate_rooms()

    def generate_rooms(self):
        # Precompute these here so it's easier to find the corresponding row of a given y value later on.
        for row in range(self.room_row_size):
            vertical_offset = int(math.floor((row + 1) / 2) * 4) if row > 0 else 0

            y_min = row * self.room_size + vertical_offset
            y_max = y_min + self.room_size
            self.rows[row] = (y_min, y_max)

        for room_idx in range(self.room_count):
            self.generate_room(room_idx)

    def generate_room(self, room_idx):
        row = int(math.ceil((room_idx + 1) / self.room_row_size) - 1)
        col = int((room_idx + 1) - (row * self.room_row_size) - 1)

        if row % 2 == 0:
            entry_side = Side.NORTH
        else:
            entry_side = Side.SOUTH

        x_min = col * self.room_size
        x_max = x_min + self.room_size

        y_coordinates = self.rows[row]
        y_min = y_coordinates[0]
        y_max = y_coordinates[1]

        self.rooms[row][col] = LectureRoom(room_idx, x_min, y_min, x_max, y_max, entry_side)

    def get_portrayal(self, x, y):
        if x == 0 or y == 0 or x == (self.width - 1) or y == (self.height - 1):
            return wall_portrayal()

        room = self.get_room(x, y)
        return None if room is None else room.get_portrayal(x, y)

    def get_room(self, x, y):
        """
        Gets the room at a given point. Note that this does include the walls!
        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: The room at the given coordinates, if one such room could be found. Otherwise None.
        """
        col = math.ceil(x / self.room_size) - 1
        if col > (self.room_row_size - 1):
            return None

        row = -1
        for row_idx in range(self.room_row_size):
            row_coordinates = self.rows[row_idx]
            if row_coordinates[0] <= y <= row_coordinates[1]:
                row = row_idx
                break
        if row == -1:
            return None

        return self.rooms[row][col]
