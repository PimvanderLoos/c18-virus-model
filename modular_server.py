from mesa.visualization.ModularVisualization import ModularServer


class CustomModularServer(ModularServer):
    def __init__(self, model_cls, visualization_elements, name="Mesa Model", model_params={}):
        model_params['server'] = self
        super().__init__(model_cls, visualization_elements, name, model_params)

    def rebuild(self):
        self.js_code = []
        for element in self.visualization_elements:
            for include_file in element.package_includes:
                self.package_includes.add(include_file)
            for include_file in element.local_includes:
                self.local_includes.add(include_file)
            self.js_code.append(element.js_code)
