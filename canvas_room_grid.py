from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from collections import defaultdict

from modular_server import CustomModularServer


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
        super().__init__(portrayal_method, grid_width, grid_height, canvas_width, canvas_height)

    def updateDimensions(self, server: CustomModularServer, x: int, y: int):
        self.canvas_width = x * 10
        self.canvas_height = y * 10
        self.grid_width = x
        self.grid_height = y

        new_element = "new CanvasModule({}, {}, {}, {})".format(
            self.canvas_width, self.canvas_height, self.grid_width, self.grid_height
        )

        self.js_code = "elements.push(" + new_element + ");"
        server.rebuild()

    def render(self, model):
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
