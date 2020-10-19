from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule

from modular_server import CustomModularServer
from virus_model import VirusModel, time_element, model_params, create_grid

grid = create_grid()
chart = ChartModule([{"Label": "infected",
                      "Color": "Black"},
                     {"Label": "deaths",
                      "Color": "Red"},
                     {"Label": "quarantined",
                      "Color": "Yellow"}],
                    data_collector_name='datacollector')
chart_disease_state = ChartModule([{"Label": "just infected",
                                    "Color": "rgba(0,0,255,1)"},
                                   {"Label": "testable",
                                    "Color": "rgba(255,0,212,1)"},
                                   {"Label": "infectious",
                                    "Color": "rgba(255,0,0,1)"},
                                   {"Label": "symptomatic",
                                    "Color": "rgba(102,0,0,1)"},
                                   {"Label": "recovered",
                                    "Color": "rgba(8,323,222,1)"},
                                   {"Label": "deaths",
                                    "Color": "Brown"}
                                   ],
                                  # include healthy? {"Label": "healthy", "Color": "rgba(43,255,0,1)"},
                                  data_collector_name='datacollector')
chart_quarantined = ChartModule([{"Label": "quarantined: infected",
                                  "Color": "Green"},
                                 {"Label": "quarantined: healthy",
                                  "Color": "Yellow"},
                                 {"Label": "not quarantined: infected",
                                  "Color": "Red"}],
                                data_collector_name='datacollector')
chart_testing = ChartModule([{"Label": "tested total",
                              "Color": "Black"},
                             {"Label": "tested negative",
                              "Color": "Blue"},
                             {"Label": "tested positive",
                              "Color": "Red"}],
                            data_collector_name='datacollector')

model_params['grid_canvas'] = grid
server = CustomModularServer(VirusModel,
                             [time_element, grid, chart, chart_disease_state, chart_quarantined, chart_testing],
                             "Virus Model", model_params)

server.port = 8543
server.launch()
