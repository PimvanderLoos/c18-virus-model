import math
from abc import ABC, abstractmethod
from random import Random
from typing import Iterator, List, Optional

from mesa.space import MultiGrid, Coordinate
from enum import Enum
import numpy as np

from util import *

SNUG_FIT_BUFFER = 10
"""
The number of additional tiles to add to the grid when snug_fit is enabled.
"""

HALLWAY_WIDTH = 3
"""
The width of the hallway.
"""


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
    portrayal["Color"] = "rgba(99, 44, 4, 0.4)"
    return portrayal


def wall_portrayal():
    portrayal = get_square()
    portrayal["Color"] = "rgba(0, 0, 0, 0.65)"
    return portrayal


def error_portrayal():
    portrayal = get_square()
    portrayal["Color"] = "purple"
    return portrayal


def error_portrayal2():
    portrayal = get_square()
    portrayal["Color"] = "orange"
    return portrayal


class Side(Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


class RoomType(Enum):
    LECTURE_ROOM = 1
    BREAK_ROOM = 2


class Seat:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.available = True


class Room(ABC):
    def __init__(self, room_id: int, x_min: int, y_min: int, x_max: int, y_max: int, entry_side: Side):
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

    def is_in_room(self, x: int, y: int) -> bool:
        """
        Checks if a given coordinate pair is inside this room. Note that this does NOT include the walls!

        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: True if the given coordinate pair lies within the usable area of the room.
        """
        return self.x_min < x < self.x_max and self.y_min < y < self.y_max

    def is_wall(self, x: int, y: int) -> bool:
        """
        Checks if the given position is a wall.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the given position is a wall.
        """
        if x == self.x_entry and y == self.y_entry:
            return False
        if x > self.x_max or x < self.x_min or y > self.y_max or y < self.y_min:
            return False
        return x == self.x_min or x == self.x_max or y == self.y_min or y == self.y_max

    def is_entry(self, x: int, y: int) -> bool:
        """
        Checks if the given position is the door to this room.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the given position is the door to this room.
        """
        return x == self.x_entry and y == self.y_entry

    def get_portrayal(self, x: int, y: int):
        """
        Gets the portrayal of the square at the given position. The portrayal determines how it's rendered.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The portrayal at the given position if it's a special place (e.g. a wall or a seat).
                 If the space is empty, this will return None.
        """
        if self.is_wall(x, y):
            return wall_portrayal()
        return None

    @abstractmethod
    def get_room_type(self):
        """
        Gets the type of room this is. See `RoomType`.

        :return: The type of room.
        """
        raise NotImplementedError


class BreakRoom(Room):
    def __init__(self, room_id: int, x_min: int, y_min: int, x_max: int, y_max: int, entry_side: Side):
        """
        :param room_id: The unique ID of this room.
        :param x_min: The lower bound x-coordinate of this room (includes the wall!)
        :param y_min: The lower bound y-coordinate of this room (includes the wall!)
        :param x_max: The upper bound x-coordinate of this room (includes the wall!)
        :param y_max: The upper bound y-coordinate of this room (includes the wall!)
        :param entry_side: On which side of the room to make the entry. This can be any one of the "Side" enum.
        """
        super().__init__(room_id, x_min, y_min, x_max, y_max, entry_side)
        self.height = y_max - y_min

    def get_room_type(self):
        return RoomType.BREAK_ROOM

    # def get_portrayal(self, x: int, y: int):
    #     if self.is_in_room(x, y):
    #         return seat_portrayal()


class LectureRoom(Room):
    def __init__(self, room_id: int, x_min: int, y_min: int, x_max: int, y_max: int,
                 entry_side: Side, entry_side_offset: int = 2):
        """
        :param room_id: The unique ID of this room.
        :param x_min: The lower bound x-coordinate of this room (includes the wall!)
        :param y_min: The lower bound y-coordinate of this room (includes the wall!)
        :param x_max: The upper bound x-coordinate of this room (includes the wall!)
        :param y_max: The upper bound y-coordinate of this room (includes the wall!)
        :param entry_side: On which side of the room to make the entry. This can be any one of the "Side" enum.
        :param entry_side_offset: The number of squares to leave empty on the entry side (where the lecturer would stand).
        """
        super().__init__(room_id, x_min, y_min, x_max, y_max, entry_side)

        self.is_reserved = False

        if entry_side == Side.NORTH:
            self.y_min_lecturer_area = y_max - (entry_side_offset + 1)
            self.y_max_lecturer_area = y_max - 1
            self.x_min_lecturer_area = x_min + 1
            self.x_max_lecturer_area = x_max - 1
        elif entry_side == Side.EAST:
            self.y_min_lecturer_area = y_min + 1
            self.y_max_lecturer_area = y_max - 1
            self.x_min_lecturer_area = x_max - 1
            self.x_max_lecturer_area = x_max - (entry_side_offset + 1)
        elif entry_side == Side.SOUTH:
            self.y_min_lecturer_area = y_min + 1
            self.y_max_lecturer_area = y_min + (entry_side_offset + 1)
            self.x_min_lecturer_area = x_min + 1
            self.x_max_lecturer_area = x_max - 1
        elif entry_side == Side.WEST:
            self.y_min_lecturer_area = y_min + 1
            self.y_max_lecturer_area = y_max - 1
            self.x_min_lecturer_area = x_min + (entry_side_offset + 1)
            self.x_max_lecturer_area = x_min + 1

        x_min_seat_offset = entry_side_offset if self.entry_side == Side.WEST else 0
        y_min_seat_offset = entry_side_offset if self.entry_side == Side.SOUTH else 0
        x_max_seat_offset = entry_side_offset if self.entry_side == Side.EAST else 0
        y_max_seat_offset = entry_side_offset if self.entry_side == Side.NORTH else 0

        self.x_min_seat = self.x_min + 2 + x_min_seat_offset
        self.x_max_seat = self.x_max - 2 - x_max_seat_offset
        self.y_min_seat = self.y_min + 2 + y_min_seat_offset
        self.y_max_seat = self.y_max - 2 - y_max_seat_offset

        self.seats = []
        self.populate_seats()

    def get_room_type(self):
        return RoomType.LECTURE_ROOM

    def get_capacity(self) -> int:
        """
        Gets the total number of seats that exist in this room. This does not take any measures or occupancy status into
        account.

        :return: The total number of seats in this room.
        """
        return len(self.seats)

    def room_available(self) -> bool:
        for seat in self.seats:
            if seat.available:
                return True
        return False

    def populate_seats(self):
        for x in range(self.x_min_seat, self.x_max_seat + 1):
            for y in range(self.y_min_seat, self.y_max_seat + 1):
                self.seats.append(Seat(x, y))

    def is_lecturer_area(self, x: int, y: int) -> bool:
        return self.x_min_lecturer_area <= x <= self.x_max_lecturer_area and \
               self.y_min_lecturer_area <= y <= self.y_max_lecturer_area

    def is_seat(self, x: int, y: int) -> bool:
        """
        Checks if the given position is a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the given position is a seat.
        """
        return self.x_min_seat <= x <= self.x_max_seat and self.y_min_seat <= y <= self.y_max_seat

    def is_available(self, x: int, y: int) -> bool:
        """
        Checks if the given position is available. I.e. it's not a wall or a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the position is available.
        """
        return self.is_entry(x, y) or self.is_lecturer_area(x, y)

    def get_seat(self, x: int, y: int) -> Optional[Seat]:
        """
        Gets the seat at the given position, if one such seat exists.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The seat at the given position if it exists, otherwise None.
        """
        for seat in self.seats:
            if seat.x == x and seat.y == y:
                return seat
        return None

    def get_portrayal(self, x: int, y: int):
        """
        Gets the portrayal of the square at the given position. The portrayal determines how it's rendered.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The portrayal at the given position if it's a special place (e.g. a wall or a seat).
                 If the space is empty, this will return None.
        """
        portrayal = super().get_portrayal(x, y)
        if portrayal is not None:
            return portrayal

        if self.is_seat(x, y):
            return seat_portrayal()
        return None


class RoomGrid(MultiGrid):
    def __init__(self, width: int, height: int, torus: bool, room_count: int = 20, room_size: int = 15,
                 snug_fit: bool = True, break_room_size: int = 22):
        """
         :param width: The width of the grid.
         :param height: The height of the grid.
         :param torus: Boolean whether the grid wraps or not.
         :param room_count: The number of rooms (excluding break room).
         :param room_size: The size of each regular room (excluding break room).
                    This value describes the length of any one of its walls, as it's a square.
                    This describes the usable area of the each room, so walls are not included.
         :param snug_fit: Whether to trim the width/height of the grid to the required size.
         :param break_room_size: The size of the break room.
        """
        self.room_count = room_count
        self.break_room: Optional[BreakRoom] = None
        self.room_size = room_size + 1  # Add 1 to account for the walls.
        self.room_row_size = math.ceil(math.sqrt(room_count))
        self.break_room_size = break_room_size
        self.rooms = np.empty((self.room_row_size + 1, self.room_row_size), dtype=Room)
        self.rooms_list = []
        self.rows = np.empty(self.room_row_size + 1, dtype=object)
        self.vertical_room_count = 0
        self.generate_rooms()
        if snug_fit:
            width, height = self.get_total_dimensions()
        super().__init__(width, height, torus)

    def get_total_dimensions(self) -> [int, int]:
        """
        Returns the total dimensions being used by all the rooms together (including the buffer: `SNUG_FIT_BUFFER`).

        :return: The x and y dimensions.
        """
        # For both width and height, add 1 additional square to account for the outer walls.
        width = self.room_size * self.room_row_size + 1 + SNUG_FIT_BUFFER
        lecture_rooms_height = self._get_vertical_lecture_height()
        break_room_height = self.break_room.height + HALLWAY_WIDTH
        height = lecture_rooms_height + break_room_height + SNUG_FIT_BUFFER
        return width, height

    def _get_vertical_lecture_height(self) -> int:
        """
        Gets the vertical space taken up by the lecture rooms.
        """
        vertical_offset = 1 + self.__get_vertical_offset_for_row(self.vertical_room_count - 1)
        return self.room_size * self.vertical_room_count + vertical_offset

    def generate_rooms(self):
        # Precompute these here so it's easier to find the corresponding row of a given y value later on.
        for row in range(self.room_row_size):
            vertical_offset = self.__get_vertical_offset_for_row(row)

            y_min = row * self.room_size + vertical_offset
            y_max = y_min + self.room_size
            self.rows[row] = (y_min, y_max)

        for room_idx in range(self.room_count):
            self.generate_lecture_room(room_idx)

        self.generate_break_room()

    def __get_vertical_offset_for_row(self, row: int) -> int:
        """
        Calculates the vertical offset for a given row.

        This is calculated using the number of the row and the width of the hallways: `HALLWAY_WIDTH`.

        :param row: The row number to get the vertical offset for.
        :return: The vertical offset for the row in number of squares.
        """
        # Add 1 to HALLWAY_WIDTH to account for the additional wall that's required.
        return int(math.floor((row + 1) / 2) * (HALLWAY_WIDTH + 1)) if row > 0 else 0

    def generate_lecture_room(self, room_idx: int):
        row = int(math.ceil((room_idx + 1) / self.room_row_size) - 1)
        col = int((room_idx + 1) - (row * self.room_row_size) - 1)

        self.vertical_room_count = max(self.vertical_room_count, row + 1)

        if row % 2 == 0:
            entry_side = Side.NORTH
        else:
            entry_side = Side.SOUTH

        x_min = col * self.room_size
        x_max = x_min + self.room_size

        y_coordinates = self.rows[row]
        y_min = y_coordinates[0]
        y_max = y_coordinates[1]

        r = LectureRoom(room_idx, x_min, y_min, x_max, y_max, entry_side)
        self.rooms[row][col] = r
        self.rooms_list.append(r)

    def generate_break_room(self):
        y_min = self.rows[self.vertical_room_count - 1][1] + HALLWAY_WIDTH
        y_max = y_min + int(self.break_room_size / 1.5)
        x_min = 0
        x_max = x_min + int(self.break_room_size * 1.5)
        room = BreakRoom(self.room_count, x_min, y_min, x_max, y_max, Side.EAST)
        self.rows[self.vertical_room_count] = (y_min, y_max)
        self.rooms[self.vertical_room_count][0] = room
        self.break_room = room

    def is_edge(self, x: int, y: int) -> bool:
        return x == 0 or y == 0 or x == (self.width - 1) or y == (self.height - 1)

    def is_wall(self, x: int, y: int) -> bool:
        """
        Checks if there is a wall at the given position.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if there is a wall at the given position, otherwise False.
        """
        if self.is_edge(x, y):
            return True

        room = self.get_room(x, y)
        if room is None:
            return False
        return room.is_wall(x, y)

    def is_available(self, x: int, y: int, allowed_in_rooms: bool = True) -> bool:
        """
        Checks if the given position is available. I.e. it's not a wall or a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :param allowed_in_rooms: Whether or not to consider lecture rooms as available or not. When set to False, this
                                 method will consider any position in any room to be unavailable.
        :return: True if the position is available.
        """
        if self.is_edge(x, y):
            return False

        room = self.get_room(x, y)
        if room is None:
            return True

        if room.is_wall(x, y):
            return False

        if allowed_in_rooms:
            return True

        if room.get_room_type() == RoomType.BREAK_ROOM:
            return True

        return room.is_available(x, y)

    def get_portrayal(self, x: int, y: int):
        if self.is_edge(x, y):
            return wall_portrayal()

        room = self.get_room(x, y)
        return None if room is None else room.get_portrayal(x, y)

    def get_room_from_id(self, room_id: int) -> Optional[LectureRoom]:
        """
        Gets the room with the given ID.

        :param room_id: The ID of the room to get.
        :return: The room with the given ID if it exists, otherwise None.
        """
        if room_id > self.room_count:
            return None
        return self.rooms_list[room_id]

    def get_room(self, x: int, y: int) -> Optional[Room]:
        """
        Gets the room at a given point. Note that this does include the walls!

        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: The room at the given coordinates, if one such room could be found. Otherwise None.
        """
        # TODO: Break room might be bigger than combined lecture rooms.
        col = math.ceil(x / self.room_size) - 1
        if col > (self.room_row_size - 1):
            return None

        row = -1
        for row_idx in range(self.vertical_room_count + 1):
            row_coordinates = self.rows[row_idx]
            if row_coordinates[0] <= y <= row_coordinates[1]:
                row = row_idx
                break
        if row == -1:
            return None

        # If the row is room_row_size, it's on the row of the break room,
        # which has only a single column.
        if row == self.vertical_room_count:
            col = 0

        return self.rooms[row][col]

    def is_path_obstructed(self, x_0: int, y_0: int, x_1: int, y_1: int) -> bool:
        """
        Checks if the path between two positions is obstructed by any walls.
        :param x_0: The x-coordinate of the first positions.
        :param y_0: The y-coordinate of the first positions.
        :param x_1: The x-coordinate of the second positions.
        :param y_1: The y-coordinate of the second positions.
        :return: True if there is a wall between the two given positions, otherwise False.
        """
        for coord in get_line_between_points(x_0, y_0, x_1, y_1):
            if self.is_wall(coord[0], coord[1]):
                return True
        return False

    def get_random_pos(self, random: Random, allowed_in_rooms: bool = False) -> [int, int]:
        """
        Gets a random available position on this grid. See #is_available for more information

        :param random: The random object to use to get random values.
        :param allowed_in_rooms: True to allow the selected positions to be inside rooms.
        :return: A random available position on this grid.
        """
        pos_x = pos_y = 0
        while not self.is_available(pos_x, pos_y, allowed_in_rooms):
            pos_x = random.randrange(self.width)
            pos_y = random.randrange(self.height)
        return pos_x, pos_y

    def get_neighborhood(
            self,
            pos: Coordinate,
            moore: bool,
            include_center: bool = False,
            radius: int = 1,
            allowed_in_rooms: bool = False,
    ) -> List[Coordinate]:
        """ Return a list of cells that are in the neighborhood of a
        certain point.

        Args:
            pos: Coordinate tuple for the neighborhood to get.
            moore: If True, return Moore neighborhood
                   (including diagonals)
                   If False, return Von Neumann neighborhood
                   (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise, return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.
            allowed_in_rooms: True to allow the agents to walk around freely inside the rooms.

        Returns:
            A list of coordinate tuples representing the neighborhood;
            With radius 1, at most 9 if Moore, 5 if Von Neumann (8 and 4
            if not including the center).

        """
        return list(self.iter_neighborhood(pos, moore, include_center, radius, allowed_in_rooms))

    def iter_neighborhood(
            self,
            pos: Coordinate,
            moore: bool,
            include_center: bool = False,
            radius: int = 1,
            allowed_in_rooms: bool = False,
    ) -> Iterator[Coordinate]:
        """ Return an iterator over cell coordinates that are in the
        neighborhood of a certain point.

        Args:
            pos: Coordinate tuple for the neighborhood to get.
            moore: If True, return Moore neighborhood
                        (including diagonals)
                   If False, return Von Neumann neighborhood
                        (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise, return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.
            allowed_in_rooms: True to allow the agents to walk around freely inside the rooms.

        Returns:
            A list of coordinate tuples representing the neighborhood. For
            example with radius 1, it will return list with number of elements
            equals at most 9 (8) if Moore, 5 (4) if Von Neumann (if not
            including the center).

        """
        x, y = pos
        coordinates = set()  # type = Set[Coordinate]
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0 and not include_center:
                    continue
                # Skip coordinates that are outside manhattan distance
                if not moore and abs(dx) + abs(dy) > radius:
                    continue
                # Skip if not a torus and new coords out of bounds.
                if not self.torus and (
                        not (0 <= dx + x < self.width) or not (0 <= dy + y < self.height)
                ):
                    continue

                px, py = self.torus_adj((x + dx, y + dy))

                # Skip if new coords out of bounds or not available.
                if self.out_of_bounds((px, py)) or not self.is_available(px, py, allowed_in_rooms):
                    continue

                coords = (px, py)
                if coords not in coordinates:
                    coordinates.add(coords)
                    yield coords
