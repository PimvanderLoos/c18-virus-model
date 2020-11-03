from mesa.visualization.modules import CanvasGrid
from collections import defaultdict

from virus_model.modular_server import CustomModularServer


class CanvasRoomGrid(CanvasGrid):
    def __init__(self, portrayal_method, grid_width: int, grid_height: int,
                 canvas_width: int = 500, canvas_height: int = 500):
        """ Instantiate a new CanvasGrid.

        Args:
            portrayal_method: function to convert each object on the grid to
                              a portrayal, as described above.
            grid_width, grid_height: Size of the grid, in cells.
            canvas_height, canvas_width: Size of the canvas to draw in the
                                         client, in pixels. (default: 500x500)
        """
        self.package_includes.append("ResettableCanvasModule.js")
        self.portrayal_method = portrayal_method
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        new_element = "new ResettableCanvasModule({}, {}, {}, {})".format(
            self.canvas_width, self.canvas_height, self.grid_width, self.grid_height
        )

        self.js_code = "elements.push(" + new_element + ");"

    def get_canvas_dimensions(self) -> [int, int]:
        """
        Gets the width and height of the canvas.
        """
        return self.canvas_width, self.canvas_height

    def update_dimensions(self, server: CustomModularServer, x: int, y: int) -> None:
        """
        Updates the x/y dimensions of the grid.

        :param server: The server that owns this grid. This server will have to be rebuilt to reflect the changes.
        :param x: The new width.
        :param y: The new height.
        """
        self.canvas_width = x * 10
        self.canvas_height = y * 10
        self.grid_width = x
        self.grid_height = y

        new_element = "new ResettableCanvasModule({}, {}, {}, {})".format(
            self.canvas_width, self.canvas_height, self.grid_width, self.grid_height
        )

        self.js_code = "elements.push(" + new_element + ");"
        server.rebuild()

    def render(self, model):
        """
        Renders the room grid.

        :param model: The model containing a room grid.
        :return: The dictionary containing the rendered portrayals.
        """
        grid_state = defaultdict(list)
        for x in range(model.grid.width):
            for y in range(model.grid.height):

                portrayal = model.grid.get_portrayal(x, y)
                if portrayal is not None:
                    portrayal["x"] = x
                    portrayal["y"] = y
                    grid_state[portrayal["Layer"]].append(portrayal)

                cell_objects = model.grid.get_cell_list_contents([(x, y)])
                for obj in cell_objects:
                    portrayal = self.portrayal_method(obj)
                    if portrayal:
                        portrayal["x"] = x
                        portrayal["y"] = y
                        grid_state[portrayal["Layer"]].append(portrayal)

        return grid_state
