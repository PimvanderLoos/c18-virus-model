import os

import tornado
from mesa.visualization import ModularVisualization
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

relative_path = os.path.relpath(os.path.dirname(__file__) + "/web",
                                os.path.dirname(ModularVisualization.__file__ + "/templates"))
"""
The relative path between mesa's directory for scripts and templates and ours.
This allows us to inject our own files.
"""


class CustomPageHandler(tornado.web.RequestHandler):
    """ Handler for the HTML template which holds the visualization. """

    def get(self):
        elements = self.application.visualization_elements
        for i, element in enumerate(elements):
            element.index = i
        self.render(
            relative_path + "/custom_modular_template.html",
            port=self.application.port,
            model_name=self.application.model_name,
            description=self.application.description,
            package_includes=self.application.package_includes,
            local_includes=self.application.local_includes,
            scripts=self.application.js_code,
        )


class GridPublisher(tornado.web.RequestHandler):
    """ Handler for the page that displays the current width/height of the grid """

    def initialize(self, server: 'CustomModularServer'):
        self.server = server

    def get(self):
        width, height = self.server.model.grid_canvas.get_canvas_dimensions()
        self.write("{} {}".format(width, height))


class CustomModularServer(ModularServer):
    custom_page_handler = (r"/", CustomPageHandler)

    def __init__(self, model_cls, visualization_elements, name="Mesa Model", model_params={}):
        """ Create a new visualization server with the given elements. """
        self.model = None

        # Load our own static files.
        static_file_handler = (
            r"/static1/(.*)",
            tornado.web.StaticFileHandler,
            {"path": os.path.dirname(__file__) + "/web"},
        )

        grid_publisher_handler = (r"/grid_data", GridPublisher, {'server': self})

        self.handlers = [grid_publisher_handler, self.custom_page_handler, self.socket_handler,
                         self.static_handler, self.local_handler, static_file_handler]

        model_params['server'] = self
        super().__init__(model_cls, visualization_elements, name, model_params)

    def rebuild(self) -> None:
        """
        Rebuilds the javascript code.
        """
        self.js_code = []
        for element in self.visualization_elements:
            for include_file in element.package_includes:
                self.package_includes.add(include_file)
            for include_file in element.local_includes:
                self.local_includes.add(include_file)
            self.js_code.append(element.js_code)

    def reset_model(self):
        """ Reinstantiate the model object, using the current parameters. """

        model_params = {'server': self}
        for key, val in self.model_kwargs.items():
            if isinstance(val, UserSettableParameter):
                if (
                        val.param_type == "static_text"
                ):  # static_text is never used for setting params
                    continue
                model_params[key] = val.value
            else:
                model_params[key] = val

        self.model = self.model_cls(**model_params)
