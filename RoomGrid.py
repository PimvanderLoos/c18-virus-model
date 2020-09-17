from mesa.space import MultiGrid
import math
from enum import Enum


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


class Room:
    def __init__(self, room_id, x_min, y_min, x_max, y_max, entry_side):
        """
        :param room_id: The unique ID of this room.
        :param x_min: The lower bound x-coordinate of this room (includes the wall!)
        :param y_min: The lower bound y-coordinate of this room (includes the wall!)
        :param x_max: The upper bound x-coordinate of this room (includes the wall!)
        :param y_max: The upper bound y-coordinate of this room (includes the wall!)
        :param entry_side: On which side of the room to make the entry. This can be any one of the "Side" enum.
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
        x_min_offset = 2 if self.entry_side == Side.WEST else 0
        y_min_offset = 2 if self.entry_side == Side.SOUTH else 0
        x_max_offset = 2 if self.entry_side == Side.EAST else 0
        y_max_offset = 2 if self.entry_side == Side.NORTH else 0

        for x in range(self.x_min + 2 + x_min_offset, self.x_max - 1 - x_max_offset):
            for y in range(self.y_min + 2 + y_min_offset, self.y_max - 1 - y_max_offset):
                self.seats.append(Seat(x, y))

    def is_wall(self, x, y):
        if x == self.x_entry and y == self.y_entry:
            return False
        if x > self.x_max or x < self.x_min or y > self.y_max or y < self.y_min:
            return False
        return x == self.x_min or x == self.x_max or y == self.y_min or y == self.y_max

    def is_seat(self, x, y):
        for seat in self.seats:
            if seat.x == x and seat.y == y:
                return True
        return False

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
        self.rooms = []
        self.room_row_size = math.ceil(math.sqrt(room_count))

        self.generate_rooms()

    def generate_rooms(self):
        for room_idx in range(self.room_count):
            self.generate_room(room_idx)

    def generate_room(self, room_idx):
        row = math.ceil((room_idx + 1) / self.room_row_size) - 1
        col = (room_idx + 1) - (row * self.room_row_size) - 1

        if row % 2 == 0:
            entry_side = Side.NORTH
        else:
            entry_side = Side.SOUTH

        x_min = col * self.room_size
        x_max = x_min + self.room_size

        vertical_offset = int(math.floor((row + 1) / 2) * 4) if row > 0 else 0
        print("row: {:}, vOffset: {:}, res: {:}".format(row, vertical_offset, math.floor((row + 1) / 2)))

        y_min = row * self.room_size + vertical_offset
        y_max = y_min + self.room_size

        self.rooms.append(Room(room_idx, x_min, y_min, x_max, y_max, entry_side))

    def get_portrayal(self, x, y):
        if x == 0 or y == 0 or x == (self.width - 1) or y == (self.height - 1):
            return wall_portrayal()

        for room in self.rooms:
            portrayal = room.get_portrayal(x, y)
            if portrayal is not None:
                return portrayal
        return None

    def get_room(self, x, y):
        """
        Gets the room at a given point. Note that this does NOT include the walls!
        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: The room at the given coordinates, if one such room could be found. Otherwise None.
        """
        for room in self.rooms:
            if room.is_in_room(x, y):
                return room
        return None

