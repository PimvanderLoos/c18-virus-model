import os
from typing import Set, Tuple


def get_line_between_points(x_0: int, y_0: int, x_1: int, y_1: int) -> Set[Tuple[int, int]]:
    """
    Gets a line between two coordinate pairs represented by a list of tuple[x, y].
    The line is found using Bresenham's line algorithm.
    See: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

    :param x_0: The x-coordinate of the first point.
    :param y_0: The y-coordinate of the first point.
    :param x_1: The x-coordinate of the second point.
    :param y_1: The y-coordinate of the second point.
    :return: A list of coordinates that make up the line between the two points.
    """

    coordinates = set()

    dx = x_1 - x_0
    dy = y_1 - y_0

    x_step = 1 if dx >= 0 else -1
    y_step = 1 if dy >= 0 else -1

    dx = abs(dx)
    dy = -abs(dy)

    x = x_0
    y = y_0
    error = dx + dy
    while True:
        coordinates.add((x, y))
        if x == x_1 and y == y_1:
            break
        error2 = error * 2
        if error2 >= dy:
            error += dy
            x += x_step
        if error2 <= dx:
            error += dx
            y += y_step
    return coordinates


def get_directory(file: str) -> str:
    directory = file.rstrip(os.sep)
    if not os.path.exists(directory):
        raise FileNotFoundError("Path does not exist: \"{}\"!".format(directory))

    if not os.path.isdir(directory):
        raise NotADirectoryError("Path is not a directory: \"{}\"!".format(directory))
    return directory
