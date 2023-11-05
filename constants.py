from enum import IntEnum


class MAZE_TILE(IntEnum):
    PATH = 0
    WALL = 1
    START = 2
    END = 3

class SEARCH_TYPE(IntEnum):
    DEPTH_FIRST = 0
    BREADTH_FIRST = 1

WALL_COLOR = "grey"
START_COLOR = "green"
END_COLOR = "blue"
PATH_COLOR = "white"
SOLUTION_COLOR = "orange"
EXPLORED_COLOR = "yellow"