from typing import Iterator, List

from mesa.space import MultiGrid, Coordinate
from enum import Enum
import numpy as np

from Util import *


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
            self.y_min_lecturer_area = y_max - (entry_side_offset + 1)
            self.y_max_lecturer_area = y_max - 1
            self.x_min_lecturer_area = x_min + 1
            self.x_max_lecturer_area = x_max - 1
        elif entry_side == Side.EAST:
            self.x_entry = x_max
            self.y_entry = y_min + math.floor((y_max - y_min) / 2)
            self.y_min_lecturer_area = y_min + 1
            self.y_max_lecturer_area = y_max - 1
            self.x_min_lecturer_area = x_max - 1
            self.x_max_lecturer_area = x_max - (entry_side_offset + 1)
        elif entry_side == Side.SOUTH:
            self.x_entry = x_min + math.floor((x_max - x_min) / 2)
            self.y_entry = y_min
            self.y_min_lecturer_area = y_min + 1
            self.y_max_lecturer_area = y_min + (entry_side_offset + 1)
            self.x_min_lecturer_area = x_min + 1
            self.x_max_lecturer_area = x_max - 1
        elif entry_side == Side.WEST:
            self.x_entry = x_min
            self.y_entry = y_min + math.floor((y_max - y_min) / 2)
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

    def room_available(self):
        for seat in self.seats:
            if seat.available:
                return True
        return False

    def is_in_room(self, x, y):
        """
        Checks if a given coordinate pair is inside this room. Note that this does NOT include the walls!
        :param x: The x-coordinate to check.
        :param y: The y-coordinate to check.
        :return: True if the given coordinate pair lies within the usable area of the room.
        """
        return self.x_min < x < self.x_max and self.y_min < y < self.y_max

    def populate_seats(self):
        for x in range(self.x_min_seat, self.x_max_seat + 1):
            for y in range(self.y_min_seat, self.y_max_seat + 1):
                self.seats.append(Seat(x, y))

    def is_wall(self, x, y):
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

    def is_lecturer_area(self, x, y):
        return self.x_min_lecturer_area <= x <= self.x_max_lecturer_area and \
               self.y_min_lecturer_area <= y <= self.y_max_lecturer_area

    def is_seat(self, x, y):
        """
        Checks if the given position is a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the given position is a seat.
        """
        return self.x_min_seat <= x <= self.x_max_seat and self.y_min_seat <= y <= self.y_max_seat

    def is_entry(self, x, y):
        """
        Checks if the given position is the door to this room.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the given position is the door to this room.
        """
        return x == self.x_entry and y == self.y_entry

    def is_available(self, x, y):
        """
        Checks if the given position is available. I.e. it's not a wall or a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: True if the position is available.
        """
        return self.is_entry(x, y) or self.is_lecturer_area(x, y)

    def get_seat(self, x, y):
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

    def get_portrayal(self, x, y):
        """
        Gets the portrayal of the square at the given position. The portrayal determines how it's rendered.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The portrayal at the given position if it's a special place (e.g. a wall or a seat).
                 If the space is empty, this will return None.
        """
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
        self.rooms_list = []
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

        r = LectureRoom(room_idx, x_min, y_min, x_max, y_max, entry_side)
        self.rooms[row][col] = r
        self.rooms_list.append(r)

    def is_edge(self, x, y):
        return x == 0 or y == 0 or x == (self.width - 1) or y == (self.height - 1)

    def is_wall(self, x, y):
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

    def is_available(self, x, y, allowed_in_rooms=True):
        """
        Checks if the given position is available. I.e. it's not a wall or a seat.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :param allowed_in_rooms: Whether or not to consider rooms as available or not. When set to False, this method
                                 will consider any position in any room to be unavailable.
        :return: True if the position is available.
        """
        if self.is_edge(x, y):
            return False

        room = self.get_room(x, y)
        if room is None:
            return True

        if allowed_in_rooms:
            return not room.is_wall(x, y)
        return room.is_available(x, y)

    def get_portrayal(self, x, y):
        if self.is_edge(x, y):
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

    def is_path_obstructed(self, x_0, y_0, x_1, y_1):
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

    def get_random_pos(self, random, allowed_in_rooms=False):
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
